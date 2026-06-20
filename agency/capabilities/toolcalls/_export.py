"""Spec 336 S4 — distil the ephemeral tool-call capture into a durable export.

The `toolcalls.export` verb (and the Stop hook) reads the top calls from the
ephemeral store and produces the durable signal — the top calls + responses + new
-spec SUGGESTIONS (the dogfooding fold-back, Goal 6) — written to a report file
(FULL, never truncated) and recorded as a `ToolcallExport` artefact, so the value
survives even when the high-volume store is pruned.
"""
from __future__ import annotations

import os


def heuristic_suggestions(top: list[dict]) -> list[dict]:
    """Deterministic new-spec suggestions from the ranked top calls (no LLM).

    Patterns: a repeated command → a shell template; a repeated read → an index;
    a high-volume call → an output filter. Each item: ``{pattern, suggestion}``.
    """
    out: list[dict] = []
    for row in top:
        tool = row.get("tool", "")
        calls = int(row.get("calls", 0))
        shape = (row.get("shape") or "").strip().splitlines()[0:1]
        shape = shape[0] if shape else ""
        if calls >= 3 and tool == "Bash":
            out.append({"pattern": f"`{shape[:80]}` ran {calls}×",
                        "suggestion": "save a `shell.define` template (or a capability) "
                                      "for this repeated command"})
        elif calls >= 3 and tool == "Read":
            out.append({"pattern": f"Read repeated {calls}×",
                        "suggestion": "consider an index/cache so the same file is not re-read"})
        elif int(row.get("bytes", 0)) > 50_000:
            out.append({"pattern": f"{tool} produced {row.get('bytes', 0)} bytes",
                        "suggestion": "add an output filter / pagination for this high-volume call"})
    return out


def render(top: list[dict], suggestions: list[dict], session: str) -> str:
    """The FULL markdown report — never truncated (no-truncate policy)."""
    lines = [f"# Tool-call export — session {session or '?'}", "",
             f"## Top {len(top)} calls (frequency × payload cost)", ""]
    for r in top:
        lines.append(f"- **{r.get('tool', '?')}** ×{r.get('calls', 0)} "
                     f"({r.get('bytes', 0)} bytes) — `{(r.get('shape') or '')[:120]}`")
    if not top:
        lines.append("- _(no tool calls captured)_")
    lines += ["", "## New-spec suggestions (dogfooding fold-back)", ""]
    lines += ([f"- {s['pattern']} → {s['suggestion']}" for s in suggestions]
              or ["- _(no strong repeated/expensive patterns this session)_"])
    return "\n".join(lines) + "\n"


def _export_path(store_path: str, session: str) -> str:
    base = os.path.dirname(store_path) or "."
    name = (session or "session").replace(":", "_").replace("/", "_")
    return os.path.join(base, "sessions", f"{name}-toolcalls.md")


def _llm_on() -> bool:
    try:
        from agency import _config
        return str(_config.config_get("toolcalls.suggest_via_llm")).strip().lower() \
            in ("true", "1", "yes", "on")
    except Exception:                                           # noqa: BLE001
        return False


def _llm_suggestions(ctx, report: str) -> list[dict]:
    """Optional richer suggestions via the Spec 092 LLM driver — behind the
    `toolcalls.suggest_via_llm` flag. Best-effort: [] when no client/key."""
    try:
        client = ctx.get_driver("llm")
        prompt = ("From these top tool calls, propose up to 3 new agency specs, "
                  "one per line as '<pattern> → <spec idea>':\n\n" + report)
        text = client.complete(prompt) if hasattr(client, "complete") else ""
    except Exception:                                           # noqa: BLE001
        return []
    return [{"pattern": "llm", "suggestion": ln.strip("-• ").strip()}
            for ln in (text or "").splitlines() if ln.strip()][:3]


def run(ctx, *, top_n: int = 20, apply: bool = False, prune: bool = False) -> dict:
    """Build the export; with ``apply`` write the FULL report + record a durable
    ``ToolcallExport`` artefact (so the signal survives a ``prune``)."""
    store = ctx.toolcalls
    if store is None:
        return {"top": [], "suggestions": [], "report": "", "written": "",
                "export_id": ""}
    top = store.top_calls(top_n)
    rows = store.rows()
    session = rows[-1]["session"] if rows else ""
    suggestions = heuristic_suggestions(top)
    report = render(top, suggestions, session)
    if _llm_on():
        extra = _llm_suggestions(ctx, report)
        if extra:
            suggestions = suggestions + extra
            report = render(top, suggestions, session)
    written, export_id = "", ""
    if apply:
        export_id = ctx.record_and_serve("ToolcallExport", {
            "session": session, "top_n": int(top_n), "suggestions": len(suggestions)})
        if store.path != ":memory:":
            path = _export_path(store.path, session)
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(report)                            # FULL — never truncated
                written = path
            except OSError as exc:
                written = f"write failed: {exc}"
        if prune:
            store.prune()
    return {"top": top, "suggestions": suggestions, "report": report,
            "written": written, "export_id": export_id}
