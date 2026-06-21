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
            # Spec 381 §3 — a review run recorded as a graph node (history is a
            # query, not a .brooks-lint-history.json sidecar).
            "QualityRun": ["mode", "score", "status"],
        },
        enums={
            ("Finding", "severity"): {"info", "warn", "fail"},
            # Spec 048: 'paths' joins the axis set as a graph-walking
            # analyzer; the others are file-tree walkers.
            ("Analysis", "axis"): set(_AXES),
            # Spec 381 §3 — an incomplete (crashed) walk is recorded but excluded
            # from the trend (Nygard).
            ("QualityRun", "status"): {"complete", "incomplete"},
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
            # Spec 360 — enrich decidable findings with the risk code + Iron Law
            # fields they evidence before recording (a no-op for rules in no
            # risk's decidable list), so the graph nodes carry the decay
            # diagnosis the judgment pass (380) later enriches in place.
            findings = _decay.tag(findings)
            totals[axis] = _findings.count_by_severity(findings)
            for fnd in findings:
                fid = self.ctx.record("Finding", fnd.to_dict())
                self.ctx.link(analysis_id, fid, "HAS_FINDING")
                self.ctx.link(fid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"analysis_id": analysis_id, "totals": totals}

    @verb(role="act")
    def review(self, path: str = ".", mode: str = "review", scope: str = "") -> dict:
        """Headless code-quality review for CI — never pauses; risky remedies auto-declined.

        The CI actor's entry point (Spec 380 §3a, Cockburn + Hightower fix).
        Shares the same decidable engine as develop.review but NEVER blocks on a
        gate or confirmation prompt: risky remedies are reported in gated:[] and
        auto-declined, not applied. Decidable-only output when no LLM key
        (Hightower fix — the CI degradation path).

        Inputs: path (str — filesystem scope; '' = current dir),
                mode (one of review/audit/debt/test/health/sweep),
                scope (str — informational scope description; '' = auto-detect).
        Returns: {scope_line, findings:[...], iron_law_passed, mode, headless:True, gated:[...]}.
        chain_next: analyze.sarif(...) for SARIF / code-scanning upload (Spec 382).

        Use when: running code-quality diagnosis in CI or any non-interactive context
            where blocking for confirmation is forbidden.
        Do NOT use when: interactive triage or remedy is needed — use develop.review +
            develop.remediate instead.
        """
        from . import _decay, _quality, _architecture, _performance, _security
        from ._review import scope_detect, iron_law_passed, classify_remedy

        scope_line = scope_detect(scope)
        scan_path = path or "."

        _AXES_FOR_MODE: dict = {
            "review":  [_quality.scan, _architecture.scan],
            "audit":   [_architecture.scan, _quality.scan],
            "debt":    [_quality.scan, _performance.scan],
            "test":    [_quality.scan, _security.scan],
            "health":  [_quality.scan, _security.scan,
                        _performance.scan, _architecture.scan],
            "sweep":   [_quality.scan, _security.scan,
                        _performance.scan, _architecture.scan],
        }
        scanners = _AXES_FOR_MODE.get(mode, [_quality.scan])
        raw: list = []
        for scan_fn in scanners:
            raw.extend(scan_fn(scan_path))

        findings = _decay.tag(raw)
        iron_law = iron_law_passed(findings)
        gated = [f.to_dict() for f in findings if classify_remedy(f) == "risky"]

        return {
            "scope_line": scope_line,
            "findings": [f.to_dict() for f in findings[:20]],
            "iron_law_passed": iron_law,
            "mode": mode,
            "headless": True,
            "gated": gated,
        }

    @verb(role="transform")
    def score(self, findings: list = None, preset: str = "",
              config: dict = None) -> dict:
        """Compute the Health Score (Spec 381) from findings × preset/config — READ-ONLY.

        ``score = max(0, 100 - Σ deduction(tier, preset))`` — the per-tier
        deductions are a documented tunable budget (strict/balanced/legacy-friendly,
        ``data/score-presets.json``), computed live every run, never pinned
        (rule 8). ``top_leverage`` names the highest-impact fixes
        (deduction_weight × occurrence_count — Wiegers). An unknown preset falls
        back to balanced.

        §2 config: an optional ``quality:`` block tunes the bar — ``disable``
        (drop risks), ``focus`` (keep ONLY these), ``ignore`` (glob-exclude files),
        ``severity`` (override a risk's tier), ``strictness`` (the preset when
        ``preset`` is not given explicitly). Validation is surfaced in
        ``config_notes``, never fatal (focus+disable → both ignored; bad
        strictness → balanced). Pure transform — no graph write; the QualityRun
        history node is a later slice.

        Inputs: findings (list of wire-shape finding dicts — severity + risk_code),
                preset (strict|balanced|legacy-friendly; '' → config strictness),
                config (dict — the quality: block; optional).
        Returns: {score, preset, top_leverage, deductions, config_notes,
                  scored_findings}.
        chain_next: analyze.sarif / document.render the report (Spec 382).

        Use when: turning a finding set into a tunable Health Score + the
            highest-leverage fixes (CI gate, report Summary).
        """
        from ._score import (score as _score, top_leverage as _top, load_presets,
                             weights, parse_quality_config, apply_quality_config,
                             apply_suppressions)
        findings = findings or []
        presets = load_presets()
        cfg, notes = parse_quality_config(config, set(presets))
        findings = apply_quality_config(findings, cfg)
        # Spec 381 §4 — read live Suppressions cross-capability (written by
        # intent.triage) and drop matching findings from the score; an expired
        # suppression lets its finding resurface (keep-both).
        findings, suppressed, expired = apply_suppressions(
            findings, self.ctx.find("Suppression"))
        eff_preset = preset or cfg["strictness"]
        return {
            "score": _score(findings, eff_preset, presets),
            "preset": eff_preset,
            "top_leverage": _top(findings, eff_preset, 3, presets),
            "deductions": weights(eff_preset, presets),
            "config_notes": notes,
            "scored_findings": len(findings),
            "suppressed": len(suppressed),
            "expired_suppressions": expired,
        }

    @verb(role="act")
    def record_run(self, mode: str = "review", scope: str = "", findings: list = None,
                   preset: str = "", status: str = "complete",
                   config: dict = None) -> dict:
        """Record a QualityRun history node + return the trend (Spec 381 §3).

        History is a GRAPH QUERY, never a ``.brooks-lint-history.json`` sidecar
        (Goal 2; survives ephemeral containers). Computes the Health Score + tier
        counts from the findings (honouring the quality: config), records a
        ``QualityRun{mode, scope, score, critical, warning, suggestion, status}``
        SERVING the intent (vfrom IS the recorded-at), then derives the trend: the delta from
        the most recent prior **complete** same-mode run. An incomplete/crashed
        walk is recorded but EXCLUDED from the delta (Nygard); a first run reports
        ``first=True``.

        Inputs: mode, scope (str), findings (wire dicts), preset ('' → config
                strictness), status (complete|incomplete), config (quality: block).
        Returns: {run_id, mode, score, counts, status, trend:{first, prior, delta}}.
        chain_next: manage.timeline(intent_id) / analyze.graph('QualityRun') for the series.

        Use when: persisting a review run so its score trend survives across
            sessions/CI as a durable, queryable node.
        """
        from ._score import (score as _score, load_presets, parse_quality_config,
                             apply_quality_config, _tier_of)
        findings = findings or []
        presets = load_presets()
        cfg, _notes = parse_quality_config(config, set(presets))
        findings = apply_quality_config(findings, cfg)
        eff_preset = preset or cfg["strictness"]
        sc = _score(findings, eff_preset, presets)
        counts = {"critical": 0, "warning": 0, "suggestion": 0}
        for f in findings:
            counts[_tier_of(f)] = counts.get(_tier_of(f), 0) + 1
        # trend BEFORE recording this run — prior COMPLETE same-mode runs only
        prior = [r for r in self.ctx.find("QualityRun")
                 if r.get("mode") == mode and r.get("status") == "complete"]
        if prior:
            prior.sort(key=lambda r: r.get("vfrom", 0))
            last = prior[-1].get("score")
            trend = {"first": False, "prior": last, "delta": sc - last}
        else:
            trend = {"first": True, "prior": None, "delta": None}
        # recorded_at is the substrate's vfrom tick (rule 2 — don't duplicate the
        # temporal stamp); the trend orders by it.
        run_id = self.ctx.record_and_serve("QualityRun", {
            "mode": mode, "scope": scope, "score": sc,
            "critical": counts["critical"], "warning": counts["warning"],
            "suggestion": counts["suggestion"], "status": status})
        return {"run_id": run_id, "mode": mode, "score": sc, "counts": counts,
                "status": status, "trend": trend}

    @verb(role="transform")
    def sarif(self, findings: list = None, max_results: int = 0) -> dict:
        """Render Findings as SARIF 2.1.0 for code-scanning — READ-ONLY (Spec 382 §1).

        Straight from the structured findings, NO parsing (brooks' report-parse is
        dropped — findings are born structured). The ``rules`` set is DERIVED from
        the live decay-risk registry (``decay-risks.json`` + any custom ``Cx``), so
        it never drifts (rule 8); ``level`` maps from the finding's tier
        (critical→error, warning→warning, suggestion→note); the ``message`` is the
        Iron Law (Symptom + Consequence + Remedy). ``max_results`` caps the emit
        with a truncation locator ("N of M shown") — never a silent drop (#9); the
        full set stays in the graph.

        Inputs: findings (list of wire-shape finding dicts), max_results (int — 0 =
                uncapped).
        Returns: {sarif, rule_count, result_count, total, truncated}.
        chain_next: upload `sarif` to GitHub code-scanning in CI (Spec 382 §3).

        Use when: emitting code-quality findings for GitHub code-scanning / a CI
            SARIF artefact.
        """
        from . import _decay
        from ._sarif import to_sarif
        findings = findings or []
        risks = _decay.load_risks()
        doc, total, truncated = to_sarif(findings, risks, max_results or None)
        return {
            "sarif": doc,
            "rule_count": len(doc["runs"][0]["tool"]["driver"]["rules"]),
            "result_count": len(doc["runs"][0]["results"]),
            "total": total,
            "truncated": truncated,
        }

    @verb(role="act")
    def gate(self, score: int = 100, critical: int = 0, min_score: int = 70,
             max_critical: int = 0, mode: str = "review") -> dict:
        """Record the quality gate verdict as an auditable Gate node (Spec 382 §2).

        PASSED iff ``score >= min_score`` AND ``critical <= max_critical`` —
        documented tunable budgets (rule 8). Records a ``Gate{name:"quality:<mode>",
        passed, evidence}`` SERVING the intent — auditable provenance, unlike
        brooks' bare ``ci-gate.mjs`` exit code. The headless CI twin computes the
        score (analyze.score) then calls this; ``gate.verdict`` reads it back.

        Inputs: score (int), critical (int — critical-tier finding count),
                min_score / max_critical (int — tunable budgets), mode (str).
        Returns: {passed, blocked, evidence, gate, name}.
        chain_next: gate.verdict("quality:<mode>") — non-zero exit on a block in CI.

        Use when: gating a PR/commit on the Health Score + critical count.
        """
        from ._review import quality_gate
        passed, evidence = quality_gate(score, critical, min_score, max_critical)
        name = f"quality:{mode}"
        gid = self.ctx.record_and_serve(
            "Gate", {"name": name, "passed": passed, "evidence": evidence})
        return {"passed": passed, "blocked": not passed, "evidence": evidence,
                "gate": gid, "name": name}

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
