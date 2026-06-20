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

import json
import re
import subprocess
from pathlib import Path

from ... import _frugal
from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# AGENCY-DRIFT: frugal-comment-prefixes — the comment styles debt harvests
# markers from. Comment-prefixed ONLY (Spec 348-review M3) so a "frugal:" in a
# string literal or prose is never harvested.
_MARKER = re.compile(
    r"(?:#|//|--|;|%|<!--|/\*)\s*(?:ponytail|frugal):\s*(.+?)\s*(?:-->|\*/)?\s*$")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".codegraph"}
_DATA = Path(__file__).parent / "data"
_TOP_N = 10   # tunable: the wire return caps at the top-N markers (full ledger lives in the graph)


class FrugalCapability(CapabilityBase):
    name = "frugal"
    home = "lifecycle"   # a discipline parameterizing HOW work proceeds (cf. mode/select; Spec 347)
    ontology = OntologyExtension(nodes={"DebtMarker": ["file", "line"]})
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
        lvl = _frugal._norm(level) if level else _frugal.frugal_level()
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
            for ln, text, ceiling, upgrade, has_trigger in self._scan(f):
                self.ctx.record_and_serve("DebtMarker", {
                    "file": f, "line": ln, "text": text, "ceiling": ceiling,
                    "upgrade": upgrade, "has_trigger": has_trigger})
                rows.append({"file": f, "line": ln, "text": text, "ceiling": ceiling,
                             "upgrade": upgrade, "has_trigger": has_trigger})
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
        bench = json.loads((_DATA / "benchmark.json").read_text(encoding="utf-8"))
        return {"benchmark": bench,
                "this_repo": "per-repo savings are not computable (the unbuilt "
                             "version was never written) — run frugal.debt for the "
                             "only real per-repo number."}

    # ── helpers ───────────────────────────────────────────────────────────────
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

    @staticmethod
    def _parse(text: str) -> tuple[str, str, bool]:
        """``<ceiling>, <upgrade>`` → (ceiling, upgrade, has_trigger). No comma =
        no named upgrade path (a rot risk — surfaced, never dropped)."""
        if "," in text:
            ceiling, upgrade = (p.strip() for p in text.split(",", 1))
        else:
            ceiling, upgrade = text.strip(), ""
        return ceiling, upgrade, bool(upgrade)

    def _scan(self, path: str):
        """Yield (line_no, text, ceiling, upgrade, has_trigger) per marker in a file."""
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, ValueError):
            return
        for i, line in enumerate(lines, 1):
            m = _MARKER.search(line)
            if m:
                text = m.group(1).strip()
                ceiling, upgrade, has_trigger = self._parse(text)
                yield i, text, ceiling, upgrade, has_trigger
