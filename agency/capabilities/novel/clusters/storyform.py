"""novel.storyform — Storyform cluster — Dramatica NCP decidable checks + coherence (Spec 103/120).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

import json
from agency.capability import verb
from agency.toolresult import ToolResult
from .._main import (
    _CANONICAL_SIGNPOST_ORDER,
    _canonical_appreciations,
    _canonical_narrative_functions,
    _resolve_term,
    _walk_field,
)


class StoryformMixin:
    """Storyform cluster — Dramatica NCP decidable checks + coherence (Spec 103/120)."""

    @verb(role="effect")
    def create_storyform(self, novel_id: str, body: dict | None = None) -> ToolResult:
        """Mint the Storyform node for a novel + STORYFORM_OF edge (effect).

        Spec 103 Slice 2 (Workstream D) — closes the documented ENGINE GAP:
        the storyform gates + checks read a ``Storyform`` node, but no verb
        minted one (it had to be inserted surgically). This verb records it
        properly, carrying the NCP payload as a JSON ``body`` and wiring the
        STORYFORM_OF edge to the parent Novel. Idempotent per novel: a second
        call updates the existing Storyform's body rather than minting a
        duplicate.

        Inputs: novel_id (parent Novel), body (the NCP v1.3.0 storyform dict —
                stored JSON-serialised; optional, defaults to empty).
        Returns: ``{storyform_id, novel_id, has_body}``.
        chain_next: ``novel.pre_draft_gate`` (now satisfiable) or the
                    ``storyform-build`` skill which fills the body.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        body_json = json.dumps(body, sort_keys=True) if body else ""
        # Idempotent: one Storyform per novel — update the existing body.
        existing = next((s for s in self.ctx.find("Storyform")
                         if s.get("novel") == novel_id), None)
        if existing is not None:
            sid = existing["id"]
            if body_json:
                self.ctx.memory.update(sid, {"body": body_json})
            return ToolResult.success(data={
                "storyform_id": sid, "novel_id": novel_id,
                "has_body": bool(body_json or existing.get("body")),
            })
        sid = self.ctx.record("Storyform", {"novel": novel_id, "body": body_json})
        self.ctx.link(sid, novel_id, "STORYFORM_OF")
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "storyform_id": sid, "novel_id": novel_id, "has_body": bool(body_json),
        })

    @verb(role="transform")
    def get_storyform(self, novel_id: str) -> ToolResult:
        """Return a novel's Storyform node + parsed NCP body (transform).

        Inputs: novel_id (parent Novel).
        Returns: ``{storyform_id, novel_id, body}`` (``body`` is the parsed
                 NCP dict, or ``{}`` when unset); ``found=False`` when the
                 novel has no Storyform yet.
        chain_next: feed ``body`` into ``novel.novel_coherence_check`` or any
                    decidable ``check_*`` verb.
        """
        sf = next((s for s in self.ctx.find("Storyform")
                   if s.get("novel") == novel_id), None)
        if sf is None:
            return ToolResult.success(data={"found": False, "novel_id": novel_id})
        raw = sf.get("body") or ""
        try:
            body = json.loads(raw) if raw else {}
        except (ValueError, TypeError):
            body = {}
        return ToolResult.success(data={
            "found": True, "storyform_id": sf["id"],
            "novel_id": novel_id, "body": body,
        })

    @verb(role="transform")
    def check_throughline_partition(self, ncp: dict) -> ToolResult:
        """Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform).

        Inputs: ncp (the NCP v1.3.0 storyform payload — top-level dict
                with ``storyform.throughlines.{mc,os,ic,rs}.class_id``).
        Returns: ``{passed, violations}`` — violations is a list of
                 short codes (≤120 chars each per the report-shape
                 budget in Spec 103 §"Done When").
        chain_next: ``novel.check_quad_completeness`` then the composite
                    ``novel_coherence_check`` (Slice 2).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        throughlines = story.get("throughlines") or {}
        # H1: exactly the four named throughlines (mc, os, ic, rs)
        expected = {"mc", "os", "ic", "rs"}
        actual = set(throughlines)
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            if missing:
                violations.append(f"H1: missing throughlines {sorted(missing)}")
            if extra:
                violations.append(f"H1: unexpected throughlines {sorted(extra)}")
        # H2: each Class used exactly once across the 4 throughlines.
        # Post Round-1 sc-analyze F3: the missing-class_id branch must
        # not be suppressed when other H2 violations fire. Report
        # missing-class_id IFF the throughline count is correct (H1 passed)
        # but some throughline omits `class_id` — that's a separate H2
        # facet from class-reuse.
        classes = [t.get("class_id") for t in throughlines.values()
                   if t.get("class_id")]
        from collections import Counter
        counts = Counter(classes)
        dupes = [c for c, n in counts.items() if n > 1]
        if dupes:
            violations.append(f"H2: class reuse {sorted(dupes)}")
        if len(throughlines) == 4 and len(classes) < 4:
            violations.append("H2: missing class_id on some throughlines")
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
        })

    @verb(role="transform")
    def check_slot_fill(self, ncp: dict) -> ToolResult:
        """Decidable check (row 4): no null required slots (transform).

        Each throughline must carry non-null `class_id`, `concern_id`,
        `approach`, `mental_sex`, `resolve` slots (or omit the slot
        entirely — explicit null is a fill error, not absence).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_throughline_partition`` for H1+H2.
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        throughlines = story.get("throughlines") or {}
        for tname, tbody in throughlines.items():
            for slot in ("class_id", "concern_id", "approach",
                         "mental_sex", "resolve"):
                if slot in tbody and tbody.get(slot) is None:
                    violations.append(
                        f"row4: {tname}.{slot} is null (use omission, not null)")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_storybeat_moment_refs(self, ncp: dict) -> ToolResult:
        """Decidable check (row 11): every moment.storybeat_ref resolves (transform).

        Each `moments[*].storybeat_ref` must point to an existing
        `storybeats[*].id`. A dangling ref is a NCP-referential break.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_slot_fill`` for row 4 audit.
        """
        violations: list[str] = []
        storybeats = ncp.get("storybeats") or []
        moments = ncp.get("moments") or []
        beat_ids = {sb.get("id") for sb in storybeats if sb.get("id")}
        for i, m in enumerate(moments):
            ref = m.get("storybeat_ref")
            if ref and ref not in beat_ids:
                violations.append(
                    f"row11: moments[{i}].storybeat_ref={ref!r} dangling")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_dynamic_pair_reciprocity(self, ncp: dict) -> ToolResult:
        """Decidable check (row 1): mc.dynamic and os.dynamic must differ.

        In Dramatica, the mc/os throughline pair shares a binary dynamic axis
        (`thought` ↔ `knowledge`) — the same value on both sides collapses
        the pair. Same for ic/rs.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_throughline_partition`` (row 5).
        """
        violations: list[str] = []
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for a, b in (("mc", "os"), ("ic", "rs")):
            da = (tls.get(a) or {}).get("dynamic")
            db = (tls.get(b) or {}).get("dynamic")
            if da and db and da == db:
                violations.append(
                    f"row1: {a}.dynamic == {b}.dynamic ({da!r}); "
                    f"pair must be antipodes")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_ktad_coverage(self, ncp: dict) -> ToolResult:
        """Decidable check (row 2): concern_id == signposts[0] (K-position).

        The first signpost is the concern's KTAD-K anchor for that
        throughline. A mismatch means the concern wandered from its K slot.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 10 in the composite — only runs when
                    signposts are in a canonical permutation.
        """
        violations: list[str] = []
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for tname, tbody in tls.items():
            concern = tbody.get("concern_id")
            signposts = tbody.get("signposts") or []
            if concern and signposts and signposts[0] != concern:
                violations.append(
                    f"row2: {tname}.concern_id={concern!r} != "
                    f"signposts[0]={signposts[0]!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_quad_completeness(self, ncp: dict) -> ToolResult:
        """Decidable check (row 3): mc problem and solution are paired.

        Resolves each via ``_resolve_term`` (kind-agnostic; tolerates
        ``el.*`` vs ``var.*``), then asserts the resolved problem's
        ``dynamic_pair_id`` slug matches the resolved solution's slug.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 5 in the composite (per Slice-2 lesson).
        """
        violations: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        problem = mc.get("problem_id")
        solution = mc.get("solution_id")
        if problem and solution:
            p_entry, _ = _resolve_term(problem)
            s_entry, _ = _resolve_term(solution)
            if p_entry and s_entry:
                p_pair = (p_entry.get("dynamic_pair_id") or "").split(".", 1)
                s_slug = (s_entry.get("id") or "").split(".", 1)
                p_pair_slug = p_pair[1] if len(p_pair) == 2 else ""
                s_slug_only = s_slug[1] if len(s_slug) == 2 else ""
                if p_pair_slug and s_slug_only and p_pair_slug != s_slug_only:
                    violations.append(
                        f"row3: mc.problem={problem!r}'s dynamic_pair_id is "
                        f"{p_entry.get('dynamic_pair_id')!r}, not solution={solution!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_crucial_element_placement(self, ncp: dict) -> ToolResult:
        """Decidable check (row 6): storyform.crucial_element_id == mc.problem_id.

        The crucial element is the storyform-level pivot point — by
        Dramatica convention it sits on mc.problem. Mismatch means the
        storyform's center of gravity moved without the throughline
        following it.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_resolve_outcome_judgment`` (row 7).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        crucial = story.get("crucial_element_id")
        mc_problem = ((story.get("throughlines") or {}).get("mc") or {}
                      ).get("problem_id")
        if crucial and mc_problem:
            c_slug = crucial.split(".", 1)[-1]
            p_slug = mc_problem.split(".", 1)[-1]
            if c_slug != p_slug:
                violations.append(
                    f"row6: crucial_element_id={crucial!r} != "
                    f"mc.problem_id={mc_problem!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_resolve_outcome_judgment(self, ncp: dict) -> ToolResult:
        """Decidable check (row 7): resolve/outcome/judgment triple is legal.

        4 canonical Dramatica endings encode the legal triples:
            Triumph         = (change,    success, good)
            Tragedy         = (steadfast, failure, bad)
            Personal Triumph= (steadfast, failure, good)
            Personal Tragedy= (change,    success, bad)
        Other 4 combos are inconsistent (e.g. change+failure+good has the
        protagonist abandon their drive for a happy result — not a
        canonical Dramatica ending). Cap at the documented table.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_approach_concern`` (row 8).
        """
        violations: list[str] = []
        story = ncp.get("storyform") or {}
        mc = (story.get("throughlines") or {}).get("mc") or {}
        os_tl = (story.get("throughlines") or {}).get("os") or {}
        resolve = mc.get("resolve")
        outcome = os_tl.get("outcome")
        judgment = os_tl.get("judgment")
        if resolve and outcome and judgment:
            valid = {
                ("change", "success", "good"),
                ("steadfast", "failure", "bad"),
                ("steadfast", "failure", "good"),
                ("change", "success", "bad"),
            }
            if (resolve, outcome, judgment) not in valid:
                violations.append(
                    f"row7: triple (resolve={resolve!r}, outcome={outcome!r}, "
                    f"judgment={judgment!r}) is not a canonical Dramatica ending")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_approach_concern(self, ncp: dict) -> ToolResult:
        """Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity).

        Per Dramatica theory: Do-er approach pairs with Universe/Physics
        classes; Be-er pairs with Mind/Psychology. Mismatch is a soft
        signal — emits ``warnings``, not ``violations``, so the composite
        passes-with-note instead of blocking.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed: True, violations: [], warnings: [str]}``.
        chain_next: ``novel.check_mental_sex_problem_solving`` (row 9).
        """
        warnings: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        approach = mc.get("approach")
        klass = mc.get("class_id")
        if approach and klass:
            doer_classes = {"class.universe", "class.physics"}
            beer_classes = {"class.mind", "class.psychology"}
            if approach == "do-er" and klass not in doer_classes:
                warnings.append(
                    f"row8: approach=do-er but class={klass!r} "
                    f"(expected universe/physics)")
            elif approach == "be-er" and klass not in beer_classes:
                warnings.append(
                    f"row8: approach=be-er but class={klass!r} "
                    f"(expected mind/psychology)")
        return ToolResult.success(data={
            "passed": True,           # WARN-severity: never blocks
            "violations": [],
            "warnings": warnings,
        })

    @verb(role="transform")
    def check_mental_sex_problem_solving(self, ncp: dict) -> ToolResult:
        """Decidable check (row 9): mental_sex ↔ class compatibility.

        Parallel rule to row 8 but on the mental_sex axis. Universe /
        Physics classes pair with ``linear`` problem-solving (sequential,
        cause→effect); Mind / Psychology pair with ``holistic`` (gestalt,
        whole-system). Mismatch is a structural violation.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: ``novel.check_signpost_permutation`` (row 10).
        """
        violations: list[str] = []
        mc = ((ncp.get("storyform") or {}).get("throughlines") or {}
              ).get("mc") or {}
        ms = mc.get("mental_sex")
        klass = mc.get("class_id")
        if ms and klass:
            linear_classes = {"class.universe", "class.physics"}
            holistic_classes = {"class.mind", "class.psychology"}
            if ms == "linear" and klass not in linear_classes:
                violations.append(
                    f"row9: mental_sex=linear but class={klass!r}")
            elif ms == "holistic" and klass not in holistic_classes:
                violations.append(
                    f"row9: mental_sex=holistic but class={klass!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="transform")
    def check_signpost_permutation(self, ncp: dict) -> ToolResult:
        """Decidable check (row 10): signposts in canonical order per class.

        Each class has a canonical ordering of its 4 types (the Dramatica
        signpost sequence). A reordering signals an authoring drift.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations}``.
        chain_next: gated behind row 5 in the composite.
        """
        violations: list[str] = []
        canonical = _CANONICAL_SIGNPOST_ORDER
        tls = (ncp.get("storyform") or {}).get("throughlines") or {}
        for tname, tbody in tls.items():
            klass = tbody.get("class_id")
            signposts = tbody.get("signposts") or []
            expected = canonical.get(klass)
            if expected and signposts and list(signposts) != list(expected):
                violations.append(
                    f"row10: {tname}.signposts={signposts!r} not canonical "
                    f"order for {klass!r}")
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
        })

    @verb(role="effect")
    def novel_coherence_check(self, ncp: dict) -> ToolResult:
        """Composite gate (Spec 120): runs all 11 storyform checks with chaining.

        Chain order (Rec 2 exact-fail contract):
            row 5 (throughline_partition) →
              if pass → rows 3 (quad_completeness) + 10 (signpost_permutation)
              if row 10 pass → row 2 (ktad_coverage)
            rows 1, 4, 6, 7, 8 (WARN), 9, 11 always run.

        Records a ``gate.check(name="storyform-coherent")`` Gate node and
        a ``dogfood.record_decision`` for traceability.

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{check, message}], warnings: [{check, message}]}``.
        chain_next: terminal — orchestrator gates on ``passed``.
        """
        violations: list[dict] = []
        warnings: list[dict] = []

        def _record(check_name: str, result: dict) -> bool:
            for msg in result.get("violations", []):
                violations.append({"check": check_name, "message": msg})
            for msg in result.get("warnings", []):
                warnings.append({"check": check_name, "message": msg})
            return result.get("passed", True)

        # Always-run checks.
        for verb_name, check_name in (
            ("check_dynamic_pair_reciprocity", "dynamic_pair_reciprocity"),
            ("check_slot_fill", "slot_fill"),
            ("check_crucial_element_placement", "crucial_element_placement"),
            ("check_resolve_outcome_judgment", "resolve_outcome_judgment"),
            ("check_approach_concern", "approach_concern"),
            ("check_mental_sex_problem_solving", "mental_sex_problem_solving"),
            ("check_storybeat_moment_refs", "storybeat_moment_refs"),
        ):
            r = self.ctx.call("novel", verb_name, ncp=ncp)
            _record(check_name, r)

        # Chain: row 5 gates 3 and 10; 10 gates 2.
        r5 = self.ctx.call("novel", "check_throughline_partition", ncp=ncp)
        if _record("throughline_partition", r5):
            r3 = self.ctx.call("novel", "check_quad_completeness", ncp=ncp)
            _record("quad_completeness", r3)
            r10 = self.ctx.call(
                "novel", "check_signpost_permutation", ncp=ncp)
            if _record("signpost_permutation", r10):
                r2 = self.ctx.call("novel", "check_ktad_coverage", ncp=ncp)
                _record("ktad_coverage", r2)

        passed = not violations
        # Record the verdict as an Artefact (provenance moat) — composite
        # doesn't bind to a Lifecycle (caller may not have one yet); the
        # walkable storyform-build skill's final phase carries the gate.
        aid = self.ctx.record("Artefact", {
            "kind": "storyform-coherence-report",
            "passed": passed,
            "violations_count": len(violations),
            "warnings_count": len(warnings),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "report_id": aid,
        })

    @verb(role="transform")
    def validate_appreciations(self, ncp: dict) -> ToolResult:
        """Row 12 hybrid: NCP appreciations ∈ canonical 463 (transform).

        Walks every ``appreciation`` field across the NCP body
        recursively; each string must belong to the
        ``canonical_appreciation`` enum from the vendored NCP v1.3.0
        schema (463 values).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{path, value}], canonical_size}``.
        chain_next: ``novel.validate_narrative_functions`` for row 13.
        """
        canonical = _canonical_appreciations()
        violations: list[dict] = []
        for path, value in _walk_field(ncp, "appreciation"):
            if value not in canonical:
                violations.append({"path": path, "value": value})
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
            "canonical_size": len(canonical),
        })

    @verb(role="transform")
    def validate_narrative_functions(self, ncp: dict) -> ToolResult:
        """Row 13 hybrid: NCP narrative_functions ∈ canonical 144 (transform).

        Walks every ``narrative_function`` field; each string must
        belong to the ``canonical_narrative_function`` enum (144 values).

        Inputs: ncp (NCP v1.3.0 payload).
        Returns: ``{passed, violations: [{path, value}], canonical_size}``.
        chain_next: ``novel.check_throughline_partition`` for structural row 5.
        """
        canonical = _canonical_narrative_functions()
        violations: list[dict] = []
        for path, value in _walk_field(ncp, "narrative_function"):
            if value not in canonical:
                violations.append({"path": path, "value": value})
        return ToolResult.success(data={
            "passed": not violations,
            "violations": violations,
            "canonical_size": len(canonical),
        })
