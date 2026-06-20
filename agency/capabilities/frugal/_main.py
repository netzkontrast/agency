# agency-scaffold: v1
"""frugal — the lazy-senior-dev discipline as a capability (Spec 348, the ponytail port).

Frugal forces the laziest solution that actually works: the ladder
YAGNI -> stdlib -> native -> installed-dep -> one line -> minimum, with a
non-negotiable safety floor (validate / secure / accessibility never cut). The
verbs EXPOSE the core discipline (``agency/_frugal.py``, Spec 332 — the single
source for the ladder + floor); they never re-define it. ``debt`` harvests the
deliberate ``frugal:`` shortcut markers into queryable provenance.

Use when: you want to read or switch the active frugal level, pull the ruleset
for a host that injects via a tool/prompt call (the ponytail-MCP port), harvest
the deferred shortcuts, or show the frugal reference card / impact scoreboard.
Triggers:
- "be lazy" / "lazy mode" / "simplest solution" / "yagni" / "do less"
- A host with no always-on hook that must pull the discipline as a tool/prompt
- "what did we defer" / "list the shortcuts" / "ponytail debt"
Red flags:
- Over-engineering / boilerplate / a new dependency for a few lines → frugal.instructions
- Hand-writing the ladder text → it lives in core _frugal (single source)
- A frugal: shortcut with no named upgrade path → frugal.debt flags it
"""
from __future__ import annotations

import functools
import json
import re
import subprocess
from pathlib import Path

from ... import _events, _frugal
from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# AGENCY-DRIFT: frugal-comment-prefixes — the comment styles debt harvests
# markers from. Comment-prefixed ONLY (Spec 348-review M3) so a "frugal:" in a
# string literal or prose is never harvested.
_MARKER = re.compile(
    r"(?:#|//|--|;|%|<!--|/\*)\s*(?:ponytail|frugal):\s*(.+?)\s*(?:-->|\*/)?\s*$")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".codegraph"}
# prose files: '#' is a heading, '--'/'%' are text — a marker there is a false
# positive (debt harvests deliberate shortcuts in CODE comments, not prose).
_PROSE_EXT = {".md", ".markdown", ".rst", ".txt"}
_DATA = Path(__file__).parent / "data"
_TOP_N = 10   # tunable: the wire return caps at the top-N findings (full set lives in the graph)
# AGENCY-DRIFT: frugal-analyze-tags — map analyze.quality's rule CODES onto the
# ponytail over-engineering tags (analyze/_quality.py: Q001 unused-import, Q002
# long-line, Q003 long-function, Q004 long-file). Keep synced if analyze adds a rule.
_TAG = {"Q001": "delete", "Q002": "shrink", "Q003": "shrink", "Q004": "yagni"}


@functools.cache
def _bench() -> dict:
    """The published benchmark medians (a static committed constant; read once)."""
    return json.loads((_DATA / "benchmark.json").read_text(encoding="utf-8"))


class FrugalCapability(CapabilityBase):
    name = "frugal"
    home = "lifecycle"   # a discipline parameterizing HOW work proceeds (cf. mode/select; Spec 347)
    ontology = OntologyExtension(
        nodes={"DebtMarker": ["file", "line"], "FrugalReview": ["scope", "files"],
               "FrugalFinding": ["file", "line"]})
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    # ── level / set_level / instructions / help (Slice 1) ─────────────────────
    @verb(role="transform")
    def level(self) -> dict:
        """Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full).

        Returns: ``{level}`` — one of off|lite|full|ultra.
        chain_next: ``frugal.set_level(level)`` to change it; ``frugal.instructions`` for the ruleset.
        """
        return {"level": _frugal.frugal_level()}

    @verb(role="effect")
    def set_level(self, level: str) -> dict:
        """Persist the frugal level (durable across processes via the Spec 334 config).

        Inputs: level (str — off|lite|full|ultra; an invalid value falls back to full).
        Returns: ``{level}`` — the normalized, persisted level.
        chain_next: the new level governs the SessionStart inject + the per-verb stamp.
        """
        return {"level": _frugal.set_frugal_level(level)}

    @verb(role="transform")
    def instructions(self, level: str = "") -> dict:
        """Return the frugal ruleset text at a level — the ponytail-MCP port
        (``ponytail_instructions``). For an external / no-hook host whose only
        injection point is a tool or prompt pull; agency-internal agents already
        receive the discipline via the SessionStart inject (Spec 348 §4).

        Inputs: level (str — off|lite|full|ultra; empty = the active level).
        Returns: ``{level, instructions}`` (instructions is empty at level off).
        chain_next: inject the returned text as the session's discipline.
        """
        lvl = _frugal.normalized(level) if level else _frugal.frugal_level()
        return {"level": lvl, "instructions": _frugal.render(lvl)}

    @verb(role="transform")
    def help(self) -> dict:
        """The frugal reference card (the ponytail-help info): the discipline +
        the levels table + how to switch + what is configurable.

        Returns: ``{help}`` — the complete help text (empty at level off).
        chain_next: ``frugal.set_level`` to switch; ``frugal.instructions`` for just the ruleset.
        """
        return {"help": _frugal.help_text()}

    # ── debt / gain (Slice 2 — analysis verbs) ────────────────────────────────
    @verb(role="effect")
    def debt(self, paths: str = "") -> dict:
        """Harvest deliberate ``frugal:``/``ponytail:`` shortcut markers into a
        debt ledger — each a ``DebtMarker`` node SERVING the intent, so "what did
        we defer" is a query, not a re-grep (the substrate's edge over the JS
        original). Scans tracked source (``git ls-files``, the Spec 348-review M6
        fold — native ignore, not a hand-rolled set) under ``paths``, falling back
        to a filesystem walk for an untracked path. Matches **comment-prefixed**
        markers only (M3) across ``#`` ``//`` ``--`` ``<!-- -->`` ``;`` ``%`` ``/* */``.

        Inputs: paths (str — optional path filter; empty = all tracked source).
        Returns: token-bounded ``{markers, no_trigger, top: [...]}`` — the FULL
                 ledger is in the graph (DebtMarker nodes); the wire caps at the
                 top-N (Spec 348-review Sev3#5: full capture, bounded return).
        chain_next: query the DebtMarker nodes for the full ledger.
        """
        rows: list[dict] = []
        for f in self._tracked_files(paths):
            for row in self._scan(f):
                self.ctx.record_and_serve("DebtMarker", row)
                rows.append(row)
        no_trigger = sum(1 for r in rows if not r["has_trigger"])
        rows.sort(key=lambda r: (r["has_trigger"], r["file"], r["line"]))
        return {"markers": len(rows), "no_trigger": no_trigger, "top": rows[:_TOP_N]}

    @verb(role="transform")
    def gain(self) -> dict:
        """The frugal impact scoreboard — the published benchmark medians (a
        documented external constant sourced from ``data/benchmark.json``, the
        CLAUDE.md #8 exception, NOT a frozen snapshot) plus a pointer to the only
        real per-repo number (``frugal.debt``). Never invents a per-repo savings
        figure — the unbuilt version was never written, so there is no baseline.

        Returns: ``{benchmark, this_repo}``.
        chain_next: ``frugal.debt`` for the live ledger; ``frugal.instructions`` for the ruleset.
        """
        return {"benchmark": _bench(),
                "this_repo": {"computable": False,
                              "reason": "the unbuilt version was never written — no baseline",
                              "use": "frugal.debt"}}

    @verb(role="effect")
    def review(self, scope: str = "diff", ref: str = "", paths: str = "") -> dict:
        """Review for over-engineering ONLY (delete/stdlib/native/yagni/shrink) —
        distinct from analyze's multi-axis pass. ``scope="diff"`` (default) reviews
        the working-tree changes vs ``ref`` (default HEAD); ``scope="repo"`` reviews
        tracked source under ``paths``. COMPOSES ``analyze.quality`` on the in-scope
        Python files for the DECIDABLE bloat subset (unused imports → delete, long
        functions/files/lines → shrink/yagni), records a ``FrugalReview`` node
        SERVING the intent, and frames the rest: the stdlib/native/shrink JUDGMENT
        is the reviewer's call — a deterministic pass cannot decide "reinvents the
        stdlib", so a Spec 147 Driver seam sharpens it with an LLM when wired.

        Inputs: scope ("diff"|"repo"), ref (str — diff base, default HEAD), paths (str).
        Returns: token-bounded ``{scope, files, decidable_findings: [top-N
                 {tag, rule, file, line, message}], tags, note}``.
        chain_next: apply the cuts; ``frugal.review`` again; ``frugal.debt`` for deferrals.
        """
        files = (self._changed_files(ref) if scope == "diff"
                 else self._tracked_files(paths))
        py = [f for f in files if f.endswith(".py")]
        findings: list[dict] = []
        for f in py:
            r = self.ctx.call("analyze", "quality", path=f)
            for fnd in (r.get("findings") or []):
                rule = fnd.get("rule", "")
                findings.append({"tag": _TAG.get(rule, "shrink"), "rule": rule,
                                 "file": f, "line": fnd.get("line", 0),
                                 "message": fnd.get("message", "")})
        findings.sort(key=lambda x: (x["file"], x["line"]))
        # Record the review aggregate AND each finding as a durable FrugalFinding
        # node SERVING the intent (mirrors debt → DebtMarker) — so the judgment is
        # a query, not a dropped tail. The wire return stays token-bounded (top-N),
        # but the FULL findings live in the graph (Jules review Sev1: a counts-only
        # FrugalReview lost the file/line/rule judgment to the graph).
        self.ctx.record_and_serve("FrugalReview", {
            "scope": scope, "files": len(py), "decidable": len(findings)})
        for fnd in findings:
            self.ctx.record_and_serve("FrugalFinding", fnd)
        return {"scope": scope, "files": len(py), "findings": len(findings),
                "decidable_findings": findings[:_TOP_N],
                "tags": ["delete", "stdlib", "native", "yagni", "shrink"],
                "note": "Decidable bloat only (unused imports + long functions/files "
                        "via analyze). The stdlib/native/shrink JUDGMENT is the "
                        "reviewer's — frame the diff with the tags above; a Driver "
                        "(LLM) sharpens it (Spec 147 seam). Non-Python files are "
                        "skipped (analyze is Python-only in v1)."}

    # ── helpers ───────────────────────────────────────────────────────────────
    def _changed_files(self, ref: str) -> list[str]:
        """Files changed vs ``ref`` (default HEAD) — tracked modifications AND new
        untracked files, so a freshly-added over-built file is reviewed too."""
        out: list[str] = []
        for cmd in (["git", "diff", "--name-only", ref or "HEAD"],
                    ["git", "ls-files", "--others", "--exclude-standard"]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                out += [ln for ln in r.stdout.splitlines() if ln.strip()]
            except Exception:
                pass
        return sorted(set(out))

    def _tracked_files(self, paths: str) -> list[str]:
        """Tracked source under ``paths`` via ``git ls-files`` (honours .gitignore
        — M6); falls back to a noise-skipping walk for an untracked path."""
        try:
            r = subprocess.run(["git", "ls-files", "--", paths or "."],
                               capture_output=True, text=True, timeout=10)
            files = [ln for ln in r.stdout.splitlines() if ln.strip()]
            if files:
                return files
        except Exception:
            pass
        base = Path(paths) if paths else Path(".")
        if base.is_file():
            return [str(base)]
        return [str(f) for f in base.rglob("*")
                if f.is_file() and not (_SKIP_DIRS & set(f.parts))]

    def _scan(self, path: str):
        """Yield one marker dict per comment-prefixed ``frugal:``/``ponytail:`` marker
        in a CODE file — prose files are skipped (a markdown ``# frugal:`` heading is
        not a code comment). Shape ``{file, line, text, ceiling, upgrade, has_trigger}``;
        the convention is ``<ceiling>, <upgrade>`` (no comma = no named upgrade path)."""
        if Path(path).suffix.lower() in _PROSE_EXT:
            return
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, ValueError):
            return
        for i, line in enumerate(lines, 1):
            m = _MARKER.search(line)
            if not m:
                continue
            text = m.group(1).strip()
            ceiling, _, upgrade = text.partition(",")
            upgrade = upgrade.strip()
            yield {"file": path, "line": i, "text": text, "ceiling": ceiling.strip(),
                   "upgrade": upgrade, "has_trigger": bool(upgrade)}


# ── Spec 349a — the first-use-once event subscriber (the reference subscriber) ──
_FIRST_USE_HINTS = {
    "Bash": "prefer a dedicated tool/verb over raw bash where one fits; shortest command that works.",
    "Write": "does this file need to exist? (YAGNI) — stdlib/native before new code; shortest working file.",
    "Edit": "smallest diff that works — delete before you add.",
}


def on_first_tool_use(engine, event) -> str:
    """Spec 349a — on the FIRST PreToolUse of a tool in a session, return a frugal
    hint for that tool; the bus dedups (once per session.tool) so it fires once.
    Silent at frugal level 'off'. The reference subscriber for the pillar event bus."""
    if _frugal.frugal_level() == "off":
        return ""
    hint = _FIRST_USE_HINTS.get((event or {}).get("tool_name", ""))
    return f"[frugal] {hint}" if hint else ""


_events.subscribe("PreToolUse", on_first_tool_use,
                  once_per="session.tool", name="frugal.first_use")


def on_session_start(engine, event) -> str:
    """Spec 348/349a — deliver the FULL frugal discipline (the deep ponytail-port
    card) ONCE per session. SessionStart fires on startup AND resume AND every
    compaction, so a direct inject would repeat the heavy card each time; the bus
    dedups (once_per='session') so it lands exactly once. Fail-open to EMIT
    (once_fail_emit=True) — the mandatory discipline must reach the agent even if
    the dedup store is unavailable (a duplicate card beats a missing one). Silent
    at frugal level 'off' / session_inject='off' (session_inject_text returns '')."""
    return _frugal.session_inject_text()


_events.subscribe("SessionStart", on_session_start,
                  once_per="session", once_fail_emit=True,
                  name="frugal.session_inject")
