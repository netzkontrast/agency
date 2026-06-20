# agency-scaffold: v1
"""analyze — multi-axis decidable code analysis (Spec 042).

Analyze runs decidable transforms over source and reports findings on the quality, security, performance, and architecture axes as graph nodes the orchestrator can reason about, rather than prose opinions. Scope WHAT to analyze with codegraph first — `codegraph impact <symbol>` (blast radius of a change), `codegraph callers <symbol>` (every call site), `codegraph explore "<area>"` (understand an unfamiliar area) — before running the transforms, so the analysis follows the real dependency edges.

Use when: assessing a codebase or diff for quality, security, performance, or architecture problems before review or shipping — surfaces decidable findings as graph artefacts.
Triggers:
- Unsure whether a change is safe to ship
- Suspected security or performance regressions in a diff
- A codebase area that feels risky or unfamiliar before review
- Scoping a risky change → `codegraph impact <symbol>` (blast radius) + `codegraph callers <symbol>` (call sites) before the analyzers
Red flags:
- Shipping a risky diff with no analysis → run capability_analyze_security first
- Hand-waving 'looks fine' on unfamiliar code → get findings via capability_analyze_quality
- Guessing a change's blast radius → `codegraph impact <symbol>` gives it directly from the call graph
"""
from __future__ import annotations

import time

from agency.capability import (
    ArtefactSchemas, CapabilityBase, RenderTemplates, verb,
)
from agency.ontology import OntologyExtension
from agency.skill import phase as _phase  # Spec 286 — shared phase() builder

from . import (_architecture, _decay, _findings, _paths, _performance,
                _quality, _security)


_AXES = ("quality", "security", "performance", "architecture", "paths")


# Spec 057 — rule-axis registry. Each analyzer module declares the rule prefixes
# it owns via a module-level ``AXIS_PREFIXES`` constant; the registry unions them
# at import time so adding a new tool means dropping in a wrapper (+ one import),
# never editing a central if-elif here.
def _build_axis_registry(modules=None) -> tuple[dict[int, dict[str, str]], int]:
    """Union every analyzer module's ``AXIS_PREFIXES`` into a length-bucketed
    prefix→axis lookup. Returns ``({prefix_len: {prefix: axis}}, max_prefix_len)``
    so the lookup can iterate longest-prefix-first (RUF before R). Raises
    ValueError when two modules claim the same prefix for DIFFERENT axes;
    same-axis overlaps are idempotently unioned. ``modules`` overrides the
    default analyzer set (used by tests to inject colliding declarations)."""
    if modules is None:
        from . import (_architecture, _bandit, _paths, _performance, _quality,
                       _radon, _ruff, _security)
        modules = (_quality, _security, _performance, _architecture, _paths,
                   _ruff, _bandit, _radon)
    by_len: dict[int, dict[str, str]] = {}
    seen: dict[str, tuple[str, str]] = {}            # prefix -> (axis, module)
    for mod in modules:
        for axis, prefixes in getattr(mod, "AXIS_PREFIXES", {}).items():
            for p in prefixes:
                if p in seen and seen[p][0] != axis:
                    prev_axis, prev_mod = seen[p]
                    raise ValueError(
                        f"axis-prefix collision: {p!r} owned by both "
                        f"{prev_mod} (axis={prev_axis}) and "
                        f"{mod.__name__} (axis={axis})")
                seen[p] = (axis, mod.__name__)
                by_len.setdefault(len(p), {})[p] = axis
    return by_len, max(by_len, default=1)


_AXIS_LOOKUP, _MAX_PREFIX_LEN = _build_axis_registry()


def _rule_axis(rule: str) -> str:
    """Map a finding's rule code to its axis via longest-prefix-first lookup."""
    for n in range(min(len(rule), _MAX_PREFIX_LEN), 0, -1):
        axis = _AXIS_LOOKUP.get(n, {}).get(rule[:n])
        if axis:
            return axis
    return ""


_CODE_ANALYSIS_SKILL = {
    "name": "code-analysis",
    "kind": "discipline",
    "phases": [
        _phase(1, "scope", ["path", "lang"]),
        _phase(2, "axes", ["axes"]),
        _phase(3, "run", ["analysis_id", "totals"]),
        _phase(4, "review", ["findings_summary"]),
        _phase(5, "apply", ["applied"], gate="hard"),
    ],
}


_IMPROVEMENT_PLAN_SCHEMA = {
    "name": "improvement-plan",
    "required": ["analysis_id", "items"],
}




class AnalyzeCapability(CapabilityBase):
    name = "analyze"
    home = "capability"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={
            "Analysis": ["path", "axes", "started_at"],
            "Finding": ["rule", "severity", "file", "line", "message", "evidence"],
        },
        enums={
            ("Finding", "severity"): {"info", "warn", "fail"},
            # Spec 048: 'paths' joins the axis set as a graph-walking
            # analyzer; the others are file-tree walkers.
            ("Analysis", "axis"): set(_AXES),
        },
        edges={"HAS_FINDING", "IMPROVES", "CLEANS"},
        schemas={"improvement-plan": _IMPROVEMENT_PLAN_SCHEMA},
        skills={"code-analysis": _CODE_ANALYSIS_SKILL},
    )

    # ---------------------------------------------------------------
    # Four transform verbs — one per axis. Each is PURE (no graph
    # writes) and returns {findings, counts}. The act verbs below
    # compose them with provenance recording.
    # ---------------------------------------------------------------

    @verb(role="transform")
    def quality(self, path: str = ".", lang: str = "py") -> dict:
        """Decidable lint findings: unused imports, long lines, long functions, long files.

        Inputs: path (str — file or dir), lang (str — only 'py' in v1).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: ``analyze.run`` to record findings as graph nodes.
        """
        if lang != "py":
            return {"findings": [], "counts": {"info": 0, "warn": 0, "fail": 0}}
        findings = _quality.scan(path)
        return {"findings": [f.to_dict() for f in findings],
                "counts": _findings.count_by_severity(findings)}

    @verb(role="transform")
    def security(self, path: str = ".", lang: str = "py") -> dict:
        """Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True.

        Inputs: path (str — file or dir), lang (str — only 'py' in v1).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: ``analyze.run`` to record findings.
        """
        if lang != "py":
            return {"findings": [], "counts": {"info": 0, "warn": 0, "fail": 0}}
        findings = _security.scan(path)
        return {"findings": [f.to_dict() for f in findings],
                "counts": _findings.count_by_severity(findings)}

    @verb(role="transform")
    def graph(self, node_type: str = "", scope: str = "", limit: int = 50) -> dict:
        """Query the provenance graph — a census of node types + a typed listing (read the graph).

        The missing read surface: code-mode exposes only ``call_tool``, so the graph
        was queryable only one intent at a time via ``memory_graph_provenance``. This
        analyzes the graph itself — count every node label live, and list one label's
        rows (optionally filtered) — so "read the graph" is a first-class query.

        Inputs: node_type (label to list, e.g. 'Reflection'/'Intent'; '' → census only);
                scope (filter Reflection/Event rows by their scope/name); limit (max rows).
        Returns: ``{census: {label: count}, nodes: [...]}`` — the LIVE graph, not a snapshot.
        chain_next: drill an intent via ``memory_graph_provenance``, or re-query a node_type.
        """
        mem = self.ctx.memory
        labels = sorted(getattr(getattr(self.ctx.registry, "ontology", None), "nodes", {})
                        or {"Intent": 0, "Reflection": 0, "Event": 0, "Invocation": 0,
                            "Artefact": 0, "Lifecycle": 0, "Gate": 0})
        census = {}
        for lab in labels:
            try:
                count = len(mem.find(lab))
            except Exception:
                count = 0
            if count:
                census[lab] = count
        nodes = []
        if node_type:
            for row in mem.find(node_type):
                if scope and (row.get("scope") or row.get("name")) != scope:
                    continue
                nodes.append(row)
            nodes = nodes[: max(1, int(limit))]
        return {"census": census, "nodes": nodes}

    @verb(role="transform")
    def performance(self, path: str = ".", lang: str = "py") -> dict:
        """AST-based hot-path lint: nested O(n²), += in loop, unbounded while True.

        Inputs: path (str — file or dir), lang (str — only 'py' in v1).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: ``analyze.run``.
        """
        if lang != "py":
            return {"findings": [], "counts": {"info": 0, "warn": 0, "fail": 0}}
        findings = _performance.scan(path)
        return {"findings": [f.to_dict() for f in findings],
                "counts": _findings.count_by_severity(findings)}

    @verb(role="transform")
    def architecture(self, path: str = ".") -> dict:
        """Dependency-graph + structural checks: import cycles, file LOC thresholds.

        Inputs: path (str — file or package root).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: ``analyze.run``.
        """
        findings = _architecture.scan(path)
        return {"findings": [f.to_dict() for f in findings],
                "counts": _findings.count_by_severity(findings)}

    @verb(role="transform")
    def paths(self, root_intent_id: str = "",
              max_paths: int = 10) -> dict:
        """Spec 048 intent-path analysis: long chains + verb sequences.

        Inputs: root_intent_id (str — empty = all user-owned roots),
                max_paths (int — cap when scanning all roots).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: read findings to identify composite-verb candidates.
        """
        findings = _paths.scan(self.ctx.memory,
                                root_intent_id=root_intent_id,
                                max_paths=max_paths)
        return {"findings": [f.to_dict() for f in findings],
                "counts": _findings.count_by_severity(findings)}

    # ---------------------------------------------------------------
    # Two act verbs — compose + record provenance.
    # ---------------------------------------------------------------

    @verb(role="act")
    def run(self, path: str = ".", axes: list = None, lang: str = "py") -> dict:
        """Run the requested analysis axes and record an Analysis + per-Finding nodes.

        Inputs: path (str), axes (list[str] — default: all four),
                lang (str — only 'py' in v1).
        Returns: ``{analysis_id, totals: {axis: {info, warn, fail}}}``
                — compact summary; detail lives in the graph as
                Analysis → HAS_FINDING → Finding nodes.
        chain_next: ``analyze.improve(analysis_id)`` or
                    ``analyze.cleanup(path)``.
        """
        chosen = list(axes) if axes else list(_AXES)
        chosen = [a for a in chosen if a in _AXES]
        analysis_id = self.ctx.record_and_serve("Analysis", {
            "path": path,
            "axes": ",".join(chosen),
            "started_at": int(time.time()),
        })
        totals: dict[str, dict[str, int]] = {}
        for axis in chosen:
            if axis == "paths":
                # paths takes (memory, root_intent_id) — operate over the
                # graph, not a filesystem path. v1: scan all user roots.
                findings = _paths.scan(self.ctx.memory)
            elif lang != "py" and axis in {"quality", "security", "performance", "architecture"}:
                # File-based axes only support Python today; honor the
                # caller's lang hint here so non-Python scans don't
                # silently record Python-Finding nodes (PR review
                # r3343808295 follow-up).
                findings = []
            else:
                scanner = {
                    "quality": _quality.scan,
                    "security": _security.scan,
                    "performance": _performance.scan,
                    "architecture": _architecture.scan,
                }[axis]
                findings = scanner(path)
            # Spec 354 — enrich decidable findings with the risk code + Iron Law
            # fields they evidence before recording (a no-op for rules in no
            # risk's decidable list), so the graph nodes carry the decay
            # diagnosis the judgment pass (355) later enriches in place.
            findings = _decay.tag(findings)
            totals[axis] = _findings.count_by_severity(findings)
            for fnd in findings:
                fid = self.ctx.record("Finding", fnd.to_dict())
                self.ctx.link(analysis_id, fid, "HAS_FINDING")
                self.ctx.link(fid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"analysis_id": analysis_id, "totals": totals}

    @verb(role="act")
    def improve(self, analysis_id: str, axes: list = None,
                apply: bool = False) -> dict:
        """Read prior Analysis findings, draft an improvement plan as a Reflection.

        Inputs: analysis_id (str — from a prior ``analyze.run``),
                axes (list[str] — filter findings to these axes),
                apply (bool — v1: planning only; apply path is v2).
        Returns: ``{improvement_plan_id, item_count, summary}``.
        chain_next: ``gate.check`` per cluster before applying (v2).
        """
        findings = self._findings_of(analysis_id, axes)
        items = [{"rule": f["rule"], "file": f["file"], "line": f["line"],
                  "message": f["message"], "severity": f["severity"]}
                 for f in findings]
        plan_id = self.ctx.record_and_serve("Reflection", {
            "scope": "technical",
            "kind": "improvement-plan",
            "analysis_id": analysis_id,
            "text": f"improvement plan for {analysis_id}: {len(items)} items",
        })
        self.ctx.link(plan_id, self.ctx.intent_id, "OBSERVED_DURING")  # Spec 058 — intent-scoped view
        self.ctx.link(plan_id, analysis_id, "IMPROVES")
        # v1 apply path: NOT IMPLEMENTED (Open Question 3). Refusing
        # apply=True is the safer default — record the request in the
        # plan, surface it in the result.
        summary = (
            f"{len(items)} findings clustered for improvement; "
            f"apply=False (v1 planning-only)."
            if not apply else
            f"{len(items)} findings; apply=True NOT YET IMPLEMENTED in v1 "
            f"(gate.check per cluster — Open Question 3)."
        )
        return {
            "improvement_plan_id": plan_id,
            "item_count": len(items),
            "summary": summary,
        }

    @verb(role="act")
    def cleanup(self, path: str = ".", dry_run: bool = True) -> dict:
        """Focused mode: analyse for dead-code findings only, draft a patch plan.

        Inputs: path (str), dry_run (bool — v1: dry-run only; apply is v2).
        Returns: ``{improvement_plan_id, item_count, summary}``.
        chain_next: ``gate.check`` before writes (v2).
        """
        findings = [f for f in _quality.scan(path) if f.rule == "Q001"]
        plan_id = self.ctx.record_and_serve("Reflection", {
            "scope": "technical",
            "kind": "improvement-plan",
            "text": f"cleanup plan for {path}: {len(findings)} dead-code items",
        })
        self.ctx.link(plan_id, self.ctx.intent_id, "OBSERVED_DURING")  # Spec 058 — intent-scoped view
        summary = (
            f"{len(findings)} dead-code findings; dry_run=True (v1)."
            if dry_run else
            f"{len(findings)} findings; dry_run=False NOT YET IMPLEMENTED in v1."
        )
        return {
            "improvement_plan_id": plan_id,
            "item_count": len(findings),
            "summary": summary,
        }

    # ---------------------------------------------------------------
    # Internals.
    # ---------------------------------------------------------------

    def _findings_of(self, analysis_id: str, axes) -> list[dict]:
        """Reconstruct findings of an Analysis from its HAS_FINDING edges."""
        out = self.ctx.neighbors(analysis_id, "HAS_FINDING", direction="out")
        if axes:
            allow = set(axes)
            # Spec 057 — filter by the rule-axis registry (each analyzer module
            # owns its prefixes via AXIS_PREFIXES; longest-prefix-first lookup).
            out = [f for f in out if _rule_axis(f["rule"]) in allow]
        return out
