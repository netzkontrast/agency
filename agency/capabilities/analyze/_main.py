# agency-scaffold: v1
"""analyze — multi-axis decidable code analysis (Spec 042).

Four transform verbs (one per axis) + two act verbs (improve, cleanup)
+ one Lifecycle skill (`code-analysis`, 5-phase hard-gated walker).

Every axis emits the canonical Finding shape (see ``_findings.py``).
Composition (run / improve / cleanup) records findings as graph nodes
— the wire payload stays a compact summary; detail lives in the graph.

Doctrine: NO LLM judgement inline (Spec 042 §"Why decidable-only").
Heuristic judgement happens at the skill's review phase via explicit
dispatch, not as part of the transform.
"""
from __future__ import annotations

import time

from agency.capability import CapabilityBase, verb
from agency.ontology import OntologyExtension

from . import (_architecture, _findings, _paths, _performance, _quality,
                _security)


_AXES = ("quality", "security", "performance", "architecture", "paths")


def _phase(idx: int, name: str, produces: list[str], gate: str = "") -> dict:
    p: dict = {"index": idx, "name": name, "produces": produces}
    if gate:
        p["gate"] = gate
    return p


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
        return {"findings": findings,
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
        return {"findings": findings,
                "counts": _findings.count_by_severity(findings)}

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
        return {"findings": findings,
                "counts": _findings.count_by_severity(findings)}

    @verb(role="transform")
    def architecture(self, path: str = ".") -> dict:
        """Dependency-graph + structural checks: import cycles, file LOC thresholds.

        Inputs: path (str — file or package root).
        Returns: ``{findings: [...], counts: {info, warn, fail}}``.
        chain_next: ``analyze.run``.
        """
        findings = _architecture.scan(path)
        return {"findings": findings,
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
        return {"findings": findings,
                "counts": _findings.count_by_severity(findings)}

    # ---------------------------------------------------------------
    # Two act verbs — compose + record provenance.
    # ---------------------------------------------------------------

    @verb(role="act")
    def run(self, path: str = ".", axes: list = None, lang: str = "py") -> dict:
        """Run the requested axes; record an Analysis + per-Finding nodes.

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
        analysis_id = self.ctx.record("Analysis", {
            "path": path,
            "axes": ",".join(chosen),
            "started_at": int(time.time()),
        })
        self.ctx.link(analysis_id, self.ctx.intent_id, "SERVES")
        totals: dict[str, dict[str, int]] = {}
        for axis in chosen:
            if axis == "paths":
                # paths takes (memory, root_intent_id) — operate over the
                # graph, not a filesystem path. v1: scan all user roots.
                findings = _paths.scan(self.ctx.memory)
            else:
                scanner = {
                    "quality": _quality.scan,
                    "security": _security.scan,
                    "performance": _performance.scan,
                    "architecture": _architecture.scan,
                }[axis]
                findings = scanner(path)
            totals[axis] = _findings.count_by_severity(findings)
            for fnd in findings:
                fid = self.ctx.record("Finding", dict(fnd))
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
        plan_id = self.ctx.record("Reflection", {
            "scope": "technical",
            "kind": "improvement-plan",
            "analysis_id": analysis_id,
            "text": f"improvement plan for {analysis_id}: {len(items)} items",
        })
        self.ctx.link(plan_id, self.ctx.intent_id, "SERVES")
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
        findings = [f for f in _quality.scan(path) if f["rule"] == "Q001"]
        plan_id = self.ctx.record("Reflection", {
            "scope": "technical",
            "kind": "improvement-plan",
            "text": f"cleanup plan for {path}: {len(findings)} dead-code items",
        })
        self.ctx.link(plan_id, self.ctx.intent_id, "SERVES")
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
        rows = self.ctx.memory.g.query(
            "MATCH (a:Analysis)-[:HAS_FINDING]->(f:Finding) "
            "WHERE a.id = $id RETURN f",
            {"id": analysis_id})
        out = [r["f"]["properties"] for r in rows]
        if axes:
            allow = set(axes)
            # Filter by rule prefix → axis. Spec 048 added a `paths` axis
            # whose findings use the `IP` two-letter prefix; check the
            # two-letter prefix first, then fall back to the single
            # letter for Q/S/P/A.
            two_letter_to_axis = {"IP": "paths"}
            one_letter_to_axis = {"Q": "quality", "S": "security",
                                  "P": "performance", "A": "architecture"}

            def _rule_axis(rule: str) -> str:
                if rule[:2] in two_letter_to_axis:
                    return two_letter_to_axis[rule[:2]]
                return one_letter_to_axis.get(rule[:1], "")

            out = [f for f in out if _rule_axis(f["rule"]) in allow]
        return out
