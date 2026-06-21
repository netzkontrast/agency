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


# The frugal ladder as a WALKABLE discipline (Spec 348 §7 — the templates primitive):
# the rungs of agency/_frugal._LADDER expressed as skill phases, so the discipline is a
# recorded `develop.skill_walk("frugal")` (one phase at a time, provenance per rung), not
# just injected prose. Spec 347 later derives the drivable lifecycle MACHINE from this walk
# surface (Spec 346); this is the walk. Phase names mirror the ladder rungs (single source:
# the rung TEXT lives in _frugal._LADDER; here only the structural phase graph).
_LADDER_SKILL = {
    "name": "frugal",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"over-?engineer|simplif|bloat|yagni|minimal|lazy|do less|shortest",
                     "confidence": 0.7},
    "phases": [
        {"index": 1, "name": "necessity", "produces": ["necessity_decision"]},     # YAGNI rung
        {"index": 2, "name": "stdlib", "produces": ["stdlib_check"]},
        {"index": 3, "name": "native", "produces": ["native_check"]},
        {"index": 4, "name": "installed-dep", "produces": ["dep_check"]},
        {"index": 5, "name": "one-line", "produces": ["one_line_check"]},
        {"index": 6, "name": "minimum", "produces": ["minimum_impl"], "gate": "hard"},
    ],
}


class FrugalCapability(CapabilityBase):
    name = "frugal"
    home = "lifecycle"   # a discipline parameterizing HOW work proceeds (cf. mode/select; Spec 347)
    ontology = OntologyExtension(
        nodes={"DebtMarker": ["file", "line"], "FrugalReview": ["scope", "files"],
               "FrugalFinding": ["file", "line"]},
        skills={"frugal": _LADDER_SKILL})
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    # Spec 349b §2 — declarative event-bus subscriptions (were import-time
    # `_events.subscribe` calls). Each `handler` names a module-level function
    # below; the engine bootstrap loop resolves + registers them.
    subscriptions = (
        _events.Subscription(event="PreToolUse", handler="on_first_tool_use",
                             once_per="session.tool", name="frugal.first_use"),
        _events.Subscription(event="SessionStart", handler="on_session_start",
                             once_per="session", once_fail_emit=True,
                             name="frugal.session_inject"),
    )

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
    def debt(self, paths: str = "", write: str = "") -> dict:
        """Harvest deliberate ``frugal:``/``ponytail:`` shortcut markers into a
        debt ledger — each a ``DebtMarker`` node SERVING the intent, so "what did
        we defer" is a query, not a re-grep (the substrate's edge over the JS
        original). Scans tracked source (``git ls-files``, the Spec 348-review M6
        fold — native ignore, not a hand-rolled set) under ``paths``, falling back
        to a filesystem walk for an untracked path. Matches **comment-prefixed**
        markers only (M3) across ``#`` ``//`` ``--`` ``<!-- -->`` ``;`` ``%`` ``/* */``.
        When ``write`` is set, ALSO project the ledger to that markdown file and
        bind it as a graph ``Document`` (``document.ingest``, Spec 292) — the
        ponytail ``PONYTAIL-DEBT.md`` feature, substrate-native + round-trippable.

        Inputs: paths (str — optional path filter; empty = all tracked source),
                write (str — optional markdown path for the document-backed ledger).
        Returns: token-bounded ``{markers, no_trigger, top: [...]}`` (+ ``written``
                 / ``document_id`` when ``write`` is set) — the FULL ledger is in
                 the graph (DebtMarker nodes); the wire caps at the top-N.
        chain_next: query the DebtMarker nodes, or open the written ledger Document.
        """
        rows: list[dict] = []
        for f in self._tracked_files(paths):
            for row in self._scan(f):
                self.ctx.record_and_serve("DebtMarker", row)
                rows.append(row)
        no_trigger = sum(1 for r in rows if not r["has_trigger"])
        rows.sort(key=lambda r: (r["has_trigger"], r["file"], r["line"]))
        result = {"markers": len(rows), "no_trigger": no_trigger, "top": rows[:_TOP_N]}
        if write:
            result.update(self._write_ledger(rows, write))
        return result

    @verb(role="transform")
    def gain(self, paths: str = "") -> dict:
        """The frugal impact scoreboard — the published benchmark medians (a
        documented external constant sourced from ``data/benchmark.json``, the
        CLAUDE.md #8 exception, NOT a frozen snapshot) PLUS the LIVE per-repo
        marker count (a read-only scan — the only honest per-repo number; never an
        invented savings figure, since the unbuilt version was never written).
        Read-only: ``debt`` owns the DebtMarker nodes; gain only counts.

        Inputs: paths (str — optional scope for the live count; empty = all tracked source).
        Returns: ``{benchmark, this_repo: {markers, computable, use, note}}``.
        chain_next: ``frugal.debt`` for the full queryable ledger; ``frugal.instructions``.
        """
        markers = sum(1 for f in self._tracked_files(paths) for _ in self._scan(f))
        return {"benchmark": _bench(),
                "this_repo": {"markers": markers, "computable": True, "use": "frugal.debt",
                              "note": "live frugal:/ponytail: marker count (read-only); "
                                      "run frugal.debt for the full queryable ledger"}}

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
        untracked files, so a freshly-added over-built file is reviewed too. On an
        unborn HEAD (a repo with no commits yet) there is no revision to diff against:
        ``git diff HEAD`` errors and the list came back empty (Jules review), so a
        brand-new repo's first commit was unreviewable. Fall back to every staged +
        untracked file instead."""
        base = ref or "HEAD"
        if base == "HEAD" and not self._has_commit():
            cmds = (["git", "ls-files", "--cached"],
                    ["git", "ls-files", "--others", "--exclude-standard"])
        else:
            cmds = (["git", "diff", "--name-only", base],
                    ["git", "ls-files", "--others", "--exclude-standard"])
        out: list[str] = []
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                out += [ln for ln in r.stdout.splitlines() if ln.strip()]
            except Exception:
                pass
        return sorted(set(out))

    def _has_commit(self) -> bool:
        """True when HEAD resolves to a commit; False on an unborn HEAD or non-repo."""
        try:
            r = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"],
                               capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

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

    def _write_ledger(self, rows: list[dict], path: str) -> dict:
        """Project the debt rows to a markdown ledger file AND bind it as a graph
        ``Document`` via ``document.ingest`` (Spec 292 file<->graph round-trip).
        The DebtMarker nodes stay the canonical queryable ledger; the file is a
        round-trippable view. Returns ``{written, document_id}`` (document_id
        omitted if the bind fails — a ledger write must never break ``debt``)."""
        out_lines = ["# Frugal debt ledger", "",
                     f"{len(rows)} marker(s); "
                     f"{sum(1 for r in rows if not r['has_trigger'])} with no upgrade trigger.",
                     ""]
        cur = ""
        for r in sorted(rows, key=lambda r: (r["file"], r["line"])):
            if r["file"] != cur:
                cur = r["file"]
                out_lines.append(f"\n## {cur}")
            trigger = r["upgrade"] or "_(no upgrade path — rot risk)_"
            out_lines.append(f"- L{r['line']}: {r['ceiling']} → {trigger}")
        Path(path).write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        out = {"written": path}
        try:                       # bind as a Document (core-function compose; Spec 292)
            doc = self.ctx.call("document", "ingest", path=path, audit=False)
            if isinstance(doc, dict) and doc.get("document_id"):
                out["document_id"] = doc["document_id"]
        except Exception:          # a ledger write must never break debt
            pass
        return out


# ── Spec 349a — the first-use-once event subscriber (the reference subscriber) ──
# A generic frugal nudge for ANY tool without a tailored hint — so a new or unlisted
# tool (Grep, Read, an MCP verb, a future tool) is never silently skipped (Jules
# review: the map was a closed set of Bash/Write/Edit). The entries below only
# REFINE the reflex for the common additive tools.
_GENERIC_FIRST_USE_HINT = (
    "laziest solution that works first — reach for a dedicated verb or a stdlib / "
    "native feature before new code or a new dependency; smallest change that does "
    "the job (the floor still holds: validate / secure / accessible).")
_FIRST_USE_HINTS = {
    "Bash": "prefer a dedicated tool/verb over raw bash where one fits; shortest command that works.",
    "Write": "does this file need to exist? (YAGNI) — stdlib/native before new code; shortest working file.",
    "Edit": "smallest diff that works — delete before you add.",
}


def on_first_tool_use(engine, event) -> str:
    """Spec 349a — on the FIRST PreToolUse of a tool in a session, return a frugal
    hint for that tool; the bus dedups (once per session.tool) so it fires once. A
    tool with no tailored hint gets the generic reflex — never a silent gap (Jules
    review). Silent at frugal level 'off'. The reference subscriber for the bus."""
    if _frugal.frugal_level() == "off":
        return ""
    tool = (event or {}).get("tool_name", "")
    if not tool:
        return ""
    hint = _FIRST_USE_HINTS.get(tool, _GENERIC_FIRST_USE_HINT)
    return f"[frugal] {hint}"


def on_session_start(engine, event) -> str:
    """Spec 348/349a — deliver the FULL frugal discipline (the deep ponytail-port
    card) ONCE per session. SessionStart fires on startup AND resume AND every
    compaction, so a direct inject would repeat the heavy card each time; the bus
    dedups (once_per='session') so it lands exactly once. Fail-open to EMIT
    (once_fail_emit=True) — the mandatory discipline must reach the agent even if
    the dedup store is unavailable (a duplicate card beats a missing one). Silent
    at frugal level 'off' / session_inject='off' (session_inject_text returns '')."""
    return _frugal.session_inject_text()

# Spec 349b §2 — both subscriptions are DECLARED as data on FrugalCapability
# (`subscriptions = (...)`), registered by the engine bootstrap loop. The
# import-time `_events.subscribe` calls were removed (the loop is the one reader).
