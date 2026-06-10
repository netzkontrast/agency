# agency-scaffold: v1
# agency-accept-warn: surface_size — Spec 109 ships 9 founding verbs (research-dossier + engineering lineages); Spec 129 adds 3 fragment verbs (fragment/fragments_for/register_fragment) for the Dramatica-as-prompts substrate; Spec 127 adds assemble_scene_brief for graph-driven brief assembly. 13 total > 12 budget by design — each verb pulls a distinct primitive; consolidating would re-grow the function signatures (kw-arg explosion). Tier discovery via Spec 068 not warranted while the cluster is still landing.
"""prompt — prompt-engineering capability (Spec 109 Slice 1).

Two-lineage capability:

1. **Research-dossier lineage**: intent_capture → catalog_list → brief_render
   → brief_audit → brief_finalize. Produces dossier-shaped research
   deliverables.
2. **Prompt-engineering lineage**: engineer (renders a PromptInstance inside
   a token budget) + audit (general-case reader-test simulation) +
   token_budget_gate (composite gate verb).

Slice 1 ships 7 user verbs + 1 gate verb + 2 walkable skills + 2
templates. Slice 2 adds the 7 builder/optimizer/variant verbs + 3 more
skills + the bundled module catalog YAML.

Use when: authoring research dossiers, engineering structured prompts that honor a token budget, auditing prompts for clarity / anti-patterns.
Triggers:
- A research intent needs a dossier authored before generation begins
- A prompt is being constructed and needs token-budget gating
- An LLM output flagged for anti-patterns needs an optimization pass
Red flags:
- Hand-rolling prompts outside the engineering pipeline → call `prompt.engineer`
- Skipping the audit gate → call `prompt.audit` (general-case) or `prompt.brief_audit` (dossier-case)
"""
from __future__ import annotations

from agency.capability import CapabilityBase, RenderTemplates, verb
from agency.toolresult import ToolResult

from .ontology import (
    ANTI_PATTERN_KIND,
    AUDIT_STATUS,
    CATALOG_CATEGORY,
    DELIVERABLE_KIND,
    OPTIMIZATION_KIND,
    prompt_ontology,
)

# Doctrine-tunable budgets (CLAUDE.md rule 8).
_DEFAULT_TOKEN_BUDGET: int = 4000          # default prompt-budget ceiling
_DEFAULT_AUDIT_MIN_SCORE: int = 70         # below → audit_gate blocks
_CLARITY_PENALTY_VAGUE: int = 15           # docstring-vague-words penalty
_CLARITY_PENALTY_NO_CONSTRAINTS: int = 20  # no [bracketed] markers penalty
_CLARITY_PENALTY_OVER_BUDGET: int = 40     # over-budget penalty

# Token approximation — 4 chars/token is the cl100k-band heuristic when
# tiktoken isn't installed. Spec 082's TokenCounter boundary would replace
# this on caps that opt into the `[tokens]` extra.
_CHARS_PER_TOKEN: int = 4


def _approx_tokens(text: str) -> int:
    return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


# Minimal seed catalog for Slice 1 — the full YAML-loaded catalog lands in
# Slice 2. These 6 modules cover the load-bearing dossier-author phases:
# discovery / sources / synthesis (A); structure / framing (B); audit /
# anti-pattern checks (C).
_SEED_CATALOG: list[dict] = [
    {"category": "A", "identifier": "M01",
     "name": "discovery", "summary": "primary-source identification"},
    {"category": "A", "identifier": "M02",
     "name": "source-curation", "summary": "weight + lineage tagging"},
    {"category": "A", "identifier": "M03",
     "name": "synthesis", "summary": "cross-source distillation"},
    {"category": "B", "identifier": "M04",
     "name": "structure", "summary": "deliverable shape selection"},
    {"category": "B", "identifier": "M05",
     "name": "framing", "summary": "audience + voice alignment"},
    {"category": "C", "identifier": "M06",
     "name": "audit", "summary": "clarity + completeness review"},
]


class PromptCapability(CapabilityBase):
    name = "prompt"
    home = "capability"
    ontology = prompt_ontology
    render_templates = RenderTemplates.from_module(__file__)

    # ════════════════════════════════════════════════════════════════════════
    # Research-dossier lineage (verbs 1-5)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def intent_capture(self, seed_query: str, topic: str,
                        deliverable: str = "dossier",
                        success_criteria: str = "") -> ToolResult:
        """Record a structured ResearchIntent SERVING the intent (act).

        Inputs: seed_query, topic, deliverable (one of DELIVERABLE_KIND),
                success_criteria (multi-line).
        Returns: ``{intent_id, deliverable}``.
        chain_next: ``prompt.catalog_list`` then ``prompt.brief_render``.
        """
        if deliverable not in DELIVERABLE_KIND:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"deliverable={deliverable!r} not in {sorted(DELIVERABLE_KIND)}")
        rid = self.ctx.record("ResearchIntent", {
            "seed_query": seed_query, "topic": topic,
            "deliverable": deliverable,
            "success_criteria": success_criteria,
        })
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "intent_id": rid, "deliverable": deliverable,
        })

    @verb(role="transform")
    def catalog_list(self, category: str = "") -> ToolResult:
        """List bundled CatalogModule entries optionally filtered by category (transform).

        Slice 1 ships a 6-module seed (M01-M06 across categories A/B/C);
        Slice 2 loads the full catalog from ``data/reference/research-module-catalog.yaml``.

        Inputs: category (one of CATALOG_CATEGORY or ``""`` for all).
        Returns: ``{modules: [{category, identifier, name, summary}], count}``.
        chain_next: ``prompt.brief_render`` with the selected module identifiers.
        """
        if category and category not in CATALOG_CATEGORY:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"category={category!r} not in {sorted(CATALOG_CATEGORY)}")
        modules = [m for m in _SEED_CATALOG
                   if not category or m["category"] == category]
        return ToolResult.success(data={
            "modules": modules, "count": len(modules),
        })

    @verb(role="act")
    def brief_render(self, research_intent_id: str,
                      module_ids: str = "") -> ToolResult:
        """Render a ResearchBrief body from the dossier-skeleton template (act).

        Records a ResearchBrief node + body; edges to the source
        ResearchIntent via RENDERS_FROM.

        Inputs: research_intent_id (the ResearchIntent node id from
                ``prompt.intent_capture``; the reserved ``intent_id`` is the
                serving Intent so this verb's input is namespaced), module_ids
                (comma-separated CatalogModule identifiers, e.g. ``"M01,M03,M06"``).
        Returns: ``{result, artefact}`` research-dossier artefact.
        chain_next: ``prompt.brief_audit`` to gate.
        """
        intent_node = self.ctx.recall(research_intent_id)
        if intent_node is None:
            return ToolResult.failure(
                "NOT_FOUND",
                f"research_intent_id={research_intent_id!r} not found")
        skeleton = self.ctx.template("dossier-skeleton")
        body = skeleton.template if skeleton is not None else ""
        # Substitute intent fields
        body = body.replace("[topic]", intent_node.get("topic", ""))
        body = body.replace("[deliverable]",
                            intent_node.get("deliverable", "dossier"))
        body = body.replace(
            "[criteria]", intent_node.get("success_criteria", ""))
        if module_ids:
            body = body.replace(
                "- [Catalog modules drawn from `prompt.catalog_list`]",
                "\n".join(f"- {m.strip()}" for m in module_ids.split(",")))
        brief_id = self.ctx.record("ResearchBrief", {
            "intent": research_intent_id, "body": body,
        })
        self.ctx.link(brief_id, research_intent_id, "RENDERS_FROM")
        self.ctx.link(brief_id, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "research-dossier",
                         "intent_ref": research_intent_id,
                         "brief_id": brief_id,
                         "body": body},
        })

    @verb(role="effect")
    def brief_audit(self, brief_id: str,
                     min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """Rule-based clarity audit of a ResearchBrief (effect).

        Scores 0-100 on heuristics: vague words → penalty; missing bracket
        markers → penalty; over default token budget → penalty. Below
        ``min_score`` records a BriefAudit with ``status='failed'``;
        else ``passed``.

        Inputs: brief_id, min_score (default 70).
        Returns: ``{audit_id, clarity_score, status, missing_sections}``.
        chain_next: revise + re-audit OR ``prompt.brief_finalize``.
        """
        brief_node = self.ctx.recall(brief_id)
        if brief_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"brief_id={brief_id!r} not found")
        body = brief_node.get("body", "")
        score, findings = _score_brief(body)
        status = "passed" if score >= min_score else "failed"
        audit_id = self.ctx.record("BriefAudit", {
            "brief": brief_id, "clarity_score": score, "status": status,
        })
        self.ctx.link(audit_id, brief_id, "AUDITS")
        self.ctx.link(audit_id, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "audit_id": audit_id, "clarity_score": score,
            "status": status,
            "missing_sections": findings.get("missing", []),
        })

    @verb(role="effect")
    def brief_finalize(self, brief_id: str) -> ToolResult:
        """Finalize a ResearchBrief — flips its status (effect).

        Inputs: brief_id.
        Returns: ``{brief_id, finalized}``.
        chain_next: deliver the dossier downstream.
        """
        brief_node = self.ctx.recall(brief_id)
        if brief_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"brief_id={brief_id!r} not found")
        self.ctx.update(brief_id, {"finalized": True})
        return ToolResult.success(data={
            "brief_id": brief_id, "finalized": True,
        })

    # ════════════════════════════════════════════════════════════════════════
    # Prompt-engineering lineage (verbs 6-7 + 1 gate)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def engineer(self, builder_kind: str, context: str,
                  constraints: str = "",
                  max_tokens: int = _DEFAULT_TOKEN_BUDGET) -> ToolResult:
        """Render a PromptInstance inside a token budget (act).

        Composes context + constraints into a structured prompt body using
        the canonical layout:

            # <builder_kind> prompt
            ## Context
            <context>
            ## Constraints
            <constraints>

        Records a PromptInstance node + body. Refuses to produce a body that
        exceeds ``max_tokens`` (returns INVALID_ARGUMENT instead — the
        caller revises before re-engineering).

        Inputs: builder_kind (free-form slug), context, constraints,
                max_tokens.
        Returns: ``{result, artefact}`` prompt-instance artefact.
        chain_next: ``prompt.token_budget_gate`` to gate the lifecycle.
        """
        body = (f"# {builder_kind} prompt\n\n"
                f"## Context\n{context.strip()}\n\n"
                f"## Constraints\n{(constraints or 'none').strip()}\n")
        tokens = _approx_tokens(body)
        if tokens > max_tokens:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"engineered prompt {tokens} tokens > budget {max_tokens}; "
                f"reduce context or relax constraints")
        instance_id = self.ctx.record("PromptInstance", {
            "builder_kind": builder_kind, "rendered_body": body,
        })
        self.ctx.link(instance_id, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "prompt-instance",
                         "builder_kind": builder_kind,
                         "rendered_body": body,
                         "instance_id": instance_id,
                         "approx_tokens": tokens},
        })

    @verb(role="effect")
    def audit(self, prompt_body: str,
               min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """General-case reader-test simulation for any prompt (effect).

        Inputs: prompt_body, min_score.
        Returns: ``{clarity_score, status, findings}``.
        chain_next: revise + re-audit; or ``prompt.audit_gate`` to gate.
        """
        score, findings = _score_brief(prompt_body)
        status = "passed" if score >= min_score else "failed"
        return ToolResult.success(data={
            "clarity_score": score, "status": status,
            "findings": findings,
        })

    # ── 2 composite gate verbs — called by walkable skills ──

    @verb(role="effect")
    def token_budget_gate(self, lifecycle_id: str,
                           prompt_body: str,
                           max_tokens: int = _DEFAULT_TOKEN_BUDGET) -> ToolResult:
        """Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect).

        Inputs: lifecycle_id, prompt_body, max_tokens.
        Returns: ``{gate, passed, tokens, max_tokens}`` or typed GATE_FAILED.
        chain_next: on failure, revise + re-engineer + re-gate.
        """
        tokens = _approx_tokens(prompt_body)
        passed = tokens <= max_tokens
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="token-budget", passed=passed,
                      evidence=f"approx_tokens={tokens}, max={max_tokens}")
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"token-budget: {tokens} > {max_tokens}")
        return ToolResult.success(data={
            "gate": "token-budget", "passed": True,
            "tokens": tokens, "max_tokens": max_tokens,
        })

    # ════════════════════════════════════════════════════════════════════════
    # Spec 127 — Dynamic prompt assembly
    # ════════════════════════════════════════════════════════════════════════
    # Walks the graph for a Scene (or Chapter) and composes a bounded
    # prompt with sourced provenance. Pure transform; no LLM call; no
    # driver dep — fake-friendly for CI.

    @verb(role="act")
    def assemble_scene_brief(self, scene_id: str,
                              max_tokens: int = 4000,
                              section_budget: int = 320) -> ToolResult:
        """Compose a Novelcrafter-style scene brief from graph state (act).

        Walks Scene → Chapter → Novel → Storyform, then for each section
        (storyform / pov_card / scene_cast / world_rules / continuity /
        foreshadowing / voice_constraints) calls a private composer that
        truncates to ``section_budget``. Sections render in priority order
        (storyform highest, voice_constraints lowest); when ``max_tokens``
        binds, lower-priority sections drop with a ``truncated`` flag.

        Inputs: scene_id (graph id of a Scene node), max_tokens (total cap),
                section_budget (per-section cap).
        Returns: ``{prompt, sections, token_count, sources, truncated,
                  brief_id}`` — ``brief_id`` is the Artefact node id
                  recorded for provenance. ``{error: 'NOT_FOUND', ...}``
                  when scene_id doesn't resolve.
        chain_next: hand ``prompt`` to a generation driver; on return,
                    record the scene body back to the graph (Spec 130
                    scene-writer skill phase 5).
        """
        ctx = _BriefContext.from_scene(self.ctx, scene_id)
        if ctx.error:
            return ToolResult.success(data={
                "error": ctx.error, "scene_id": scene_id,
            })

        sections: dict[str, str] = {}
        sources: list[dict] = []
        truncated: list[str] = []
        running_total = 0

        # Section composition order — earlier = higher priority on budget bind.
        composers = [
            ("storyform", _compose_storyform),
            ("pov_card", _compose_pov_card),
            ("scene_cast", _compose_scene_cast),
            ("world_rules", _compose_world_rules),
            ("continuity", _compose_continuity),
            ("foreshadowing", _compose_foreshadowing),
            ("voice_constraints", _compose_voice_constraints),
        ]
        for name, composer in composers:
            text, src = composer(ctx, self)
            tokens = _approx_tokens(text)
            if tokens > section_budget:
                text = _truncate_to_tokens(text, section_budget)
                tokens = _approx_tokens(text)
                truncated.append(name)
            if running_total + tokens > max_tokens:
                truncated.append(name)
                continue
            sections[name] = text
            for s in src:
                sources.append({**s, "contributed": name})
            running_total += tokens

        prompt_body = _render_brief(sections)
        # Provenance: record the brief Artefact + SERVES intent.
        aid = self.ctx.record("Artefact", {
            "kind": "scene-brief",
            "scene_id": scene_id,
            "token_count": running_total,
            "section_count": len(sections),
            "truncated_count": len(truncated),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "prompt": prompt_body,
            "sections": sections,
            "token_count": running_total,
            "sources": sources,
            "truncated": truncated,
            "brief_id": aid,
        })

    # ════════════════════════════════════════════════════════════════════════
    # Spec 129 — Dramatica-as-prompt-fragments
    # ════════════════════════════════════════════════════════════════════════
    # Each Dramatica ontology entry can carry a guidance fragment
    # (second-person agent imperative). Storage is hybrid: a vendored
    # `fragments.json` ships the bootstrap set; a per-project overlay
    # (`.agency/dramatica-fragments-overlay.yaml`) lets a workflow add or
    # override without editing the vendored file. `register_fragment`
    # writes to the overlay.

    @verb(role="transform")
    def fragment(self, slug: str) -> ToolResult:
        """Look up a single Dramatica prompt fragment (transform).

        Inputs: slug (str — ontology id like ``th.main-character`` or any
                kind-prefix alias the novel cap's ``_resolve_term`` recognises).
        Returns: ``{slug, canonical_id, kind, text, tokens}`` OR
                 ``{slug, error: 'NO_FRAGMENT'}`` when no fragment is
                 authored for that entry yet.
        chain_next: ``prompt.fragments_for(scope)`` for multi-entry composition.
        """
        canonical_id, kind = _resolve_to_canonical(slug)
        if canonical_id is None:
            return ToolResult.success(data={
                "slug": slug, "error": "UNKNOWN_SLUG",
            })
        text = _load_fragments().get(canonical_id)
        if not text:
            return ToolResult.success(data={
                "slug": slug, "canonical_id": canonical_id, "kind": kind,
                "error": "NO_FRAGMENT",
            })
        return ToolResult.success(data={
            "slug": slug, "canonical_id": canonical_id, "kind": kind,
            "text": text, "tokens": _approx_tokens(text),
        })

    @verb(role="transform")
    def fragments_for(self, scope: dict,
                       max_tokens: int = 2000) -> ToolResult:
        """Compose multiple fragments for a storyform scope (transform).

        ``scope`` describes a slice of a storyform — any of these keys
        contributes a fragment lookup (order matters; earlier = higher
        priority when budget binds):
            throughline      → th.{mc|os|ic|rs}
            class_id         → class.{universe|physics|mind|psychology}
            concern_id       → type.{slug}
            problem_id       → element/variation lookup
            solution_id      → element/variation lookup
            crucial_element_id → element/variation lookup
            archetypes       → list[arc.*]; included in order

        Inputs: scope (dict), max_tokens (int — total budget).
        Returns: ``{fragments: [{slug, kind, text, tokens}], total_tokens,
                 truncated_at: int|None, skipped_no_fragment: [slug]}``.
        chain_next: feed ``fragments`` into the assembled brief
                    (Spec 127 ``prompt.assemble_scene_brief``).
        """
        order = [
            ("throughline", _throughline_slug),
            ("class_id", lambda v: v),
            ("concern_id", lambda v: v),
            ("crucial_element_id", lambda v: v),
            ("problem_id", lambda v: v),
            ("solution_id", lambda v: v),
        ]
        looked_up: list[tuple[str, str]] = []
        for key, transform in order:
            raw = scope.get(key)
            if raw:
                looked_up.append((key, transform(raw)))
        for arc in scope.get("archetypes") or []:
            looked_up.append(("archetype", arc))

        fragments: list[dict] = []
        skipped: list[str] = []
        total = 0
        truncated_at: int | None = None
        store = _load_fragments()
        for _key, slug in looked_up:
            canonical_id, kind = _resolve_to_canonical(slug)
            if canonical_id is None:
                skipped.append(slug)
                continue
            text = store.get(canonical_id)
            if not text:
                skipped.append(slug)
                continue
            tokens = _approx_tokens(text)
            if total + tokens > max_tokens:
                truncated_at = len(fragments)
                break
            fragments.append({
                "slug": slug, "canonical_id": canonical_id,
                "kind": kind, "text": text, "tokens": tokens,
            })
            total += tokens
        return ToolResult.success(data={
            "fragments": fragments,
            "total_tokens": total,
            "truncated_at": truncated_at,
            "skipped_no_fragment": skipped,
        })

    @verb(role="effect")
    def register_fragment(self, slug: str, text: str,
                           overlay_path: str = "") -> ToolResult:
        """Write a fragment to the project overlay (effect; runtime-extensible).

        Inputs: slug (str — canonical or alias id), text (str — guidance
                body, ≤300 tokens recommended), overlay_path (str — defaults
                to ``.agency/dramatica-fragments-overlay.yaml``).
        Returns: ``{slug, canonical_id, kind, tokens, overlay_path}`` OR
                 ``{slug, error: 'UNKNOWN_SLUG'}``.
        chain_next: ``prompt.fragment(slug)`` to verify the round-trip.
        """
        canonical_id, kind = _resolve_to_canonical(slug)
        if canonical_id is None:
            return ToolResult.success(data={
                "slug": slug,
                "error": "UNKNOWN_SLUG",
            })
        path = overlay_path or _DEFAULT_OVERLAY_PATH
        _write_overlay_fragment(path, canonical_id, text)
        # Invalidate the loader cache so the next read sees the write.
        _load_fragments.cache_clear()
        return ToolResult.success(data={
            "slug": slug, "canonical_id": canonical_id, "kind": kind,
            "tokens": _approx_tokens(text),
            "overlay_path": path,
        })

    @verb(role="effect")
    def audit_gate(self, lifecycle_id: str, prompt_body: str,
                    min_score: int = _DEFAULT_AUDIT_MIN_SCORE) -> ToolResult:
        """Computed audit gate — passes iff clarity_score ≥ min_score (effect).

        Inputs: lifecycle_id, prompt_body, min_score.
        Returns: ``{gate, passed, score, status}`` or typed GATE_FAILED.
        chain_next: on failure, revise + re-audit.
        """
        score, _ = _score_brief(prompt_body)
        passed = score >= min_score
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="audit", passed=passed,
                      evidence=f"clarity_score={score}, min={min_score}")
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"audit: clarity_score={score} < {min_score}")
        return ToolResult.success(data={
            "gate": "audit", "passed": True,
            "score": score, "status": "passed",
        })


# ─────────────────────────── private scoring helpers ───────────────────────────
_VAGUE_WORDS = (
    "something", "thing", "stuff", "kind of", "sort of",
    "really", "very", "just", "maybe", "probably",
)


def _score_brief(body: str) -> tuple[int, dict]:
    """Score the body 0-100 + return findings dict.

    Heuristics (Spec 109 Slice 1):
      - vague words → -15 per kind
      - no [bracketed] markers (suggests no constraints declared) → -20
      - over default budget → -40

    Returns (score, {"missing": [...], "warnings": [...]})
    """
    body_lower = body.lower()
    score = 100
    findings = {"missing": [], "warnings": []}
    vague_hits = [w for w in _VAGUE_WORDS if w in body_lower]
    if vague_hits:
        score -= _CLARITY_PENALTY_VAGUE
        findings["warnings"].append({"kind": "vague_words",
                                      "hits": vague_hits[:5]})
    has_constraints = "[" in body and "]" in body
    if not has_constraints:
        score -= _CLARITY_PENALTY_NO_CONSTRAINTS
        findings["missing"].append("constraint-markers")
    if _approx_tokens(body) > _DEFAULT_TOKEN_BUDGET:
        score -= _CLARITY_PENALTY_OVER_BUDGET
        findings["warnings"].append({"kind": "over_budget",
                                      "tokens": _approx_tokens(body)})
    return max(0, score), findings


# ─────────────────────────── Spec 129 fragment loader ───────────────────────────

import json
import os
from functools import lru_cache
from pathlib import Path

_FRAGMENTS_FILE = (Path(__file__).parent.parent / "novel"
                   / "data" / "dramatica" / "fragments.json")
_DEFAULT_OVERLAY_PATH = ".agency/dramatica-fragments-overlay.yaml"


@lru_cache(maxsize=1)
def _load_fragments() -> dict:
    """Merged store: vendored bootstrap + per-project overlay (overlay wins)."""
    base: dict = {}
    if _FRAGMENTS_FILE.is_file():
        raw = json.loads(_FRAGMENTS_FILE.read_text())
        base = dict(raw.get("fragments") or {})
    overlay = _load_overlay(_DEFAULT_OVERLAY_PATH)
    base.update(overlay)
    return base


def _load_overlay(path: str) -> dict:
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        return {}
    text = p.read_text()
    # Tiny YAML subset: top-level `id: "text"` lines (one per line) OR
    # full PyYAML when available.
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
        return {k: str(v) for k, v in loaded.items()
                if isinstance(k, str) and v is not None}
    except ImportError:
        pass
    out: dict = {}
    for ln in text.splitlines():
        ln = ln.split("#", 1)[0].rstrip()
        if not ln or ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if val:
            out[key.strip()] = val
    return out


def _write_overlay_fragment(path: str, canonical_id: str, text: str) -> None:
    """Append-or-replace a single fragment in the overlay file."""
    p = Path(os.path.expanduser(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_overlay(path)
    existing[canonical_id] = text
    # Write back as one-line-per-entry; PyYAML when available for safety.
    try:
        import yaml  # type: ignore
        p.write_text(yaml.safe_dump(existing, allow_unicode=True))
    except ImportError:
        lines = []
        for k, v in existing.items():
            safe = str(v).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{k}: "{safe}"')
        p.write_text("\n".join(lines) + "\n")


# ────────────── ontology resolution (re-uses novel cap's helper) ──────────────

def _resolve_to_canonical(slug: str) -> tuple[str | None, str | None]:
    """Resolve a slug to (canonical_ontology_id, kind) via the novel cap's
    ``_resolve_term``. Returns ``(None, None)`` when no entry matches.
    Cross-cap import is acceptable: the Dramatica ontology IS the substrate
    Spec 129 composes against (novel owns the data; prompt presents it)."""
    from agency.capabilities.novel._main import _resolve_term
    entry, _exact = _resolve_term(slug)
    if entry is None:
        return None, None
    return entry.get("id"), entry.get("kind")


def _throughline_slug(value: str) -> str:
    """Normalise common throughline aliases to canonical ontology ids.

    Caller short forms (``mc``, ``os``, ``ic``, ``rs``) map to the
    Dramatica canonical ids (``throughline.main``, ``throughline.objective``,
    ``throughline.influence``, ``throughline.relationship``). Pass-through
    for values that already look canonical."""
    alias = {
        "mc": "throughline.main",
        "os": "throughline.objective",
        "ic": "throughline.influence",
        "rs": "throughline.relationship",
    }
    return alias.get(value.lower(), value)


# ─────────────────────────── Spec 127 brief assembly ───────────────────────────
# Pure helpers — graph walk + fragment composition; no driver, no LLM,
# no filesystem; runs in CI on a bare graph.

from dataclasses import dataclass, field as _dataclass_field
from typing import Any


@dataclass
class _BriefContext:
    """Graph-resolved context for an assemble_scene_brief call.

    Holds the Scene + Chapter + Novel + (optional) Storyform property dicts
    + a parsed NCP scope when the Storyform's body carries one. Composers
    read from this dataclass; errors short-circuit at the entry verb.
    """
    scene: dict
    chapter: dict
    novel: dict
    storyform_scope: dict
    error: str | None = None

    @classmethod
    def from_scene(cls, ctx, scene_id: str) -> "_BriefContext":
        scene = ctx.recall(scene_id)
        if scene is None or "chapter" not in scene:
            return cls(scene={}, chapter={}, novel={}, storyform_scope={},
                       error="NOT_FOUND")
        chapter_id = scene.get("chapter")
        chapter = ctx.recall(chapter_id) or {}
        novel_id = chapter.get("novel")
        novel = ctx.recall(novel_id) if novel_id else {}
        storyform_scope: dict = {}
        if novel_id:
            # Find a Storyform for this novel; pick the most-recent body.
            for sf in ctx.find("Storyform"):
                if sf.get("novel") == novel_id and sf.get("body"):
                    try:
                        import json as _json
                        ncp = _json.loads(sf["body"])
                        storyform_scope = _ncp_to_scope(ncp)
                    except (ValueError, TypeError):
                        pass
                    break
        return cls(scene=scene, chapter=chapter, novel=novel or {},
                   storyform_scope=storyform_scope)


def _ncp_to_scope(ncp: dict) -> dict:
    """Flatten the relevant NCP storyform fields into a fragments_for scope."""
    story = ncp.get("storyform") or {}
    mc = (story.get("throughlines") or {}).get("mc") or {}
    return {
        "throughline": "mc",      # default: scene serves MC
        "class_id": mc.get("class_id"),
        "concern_id": mc.get("concern_id"),
        "problem_id": mc.get("problem_id"),
        "solution_id": mc.get("solution_id"),
        "crucial_element_id": story.get("crucial_element_id"),
    }


def _compose_storyform(bctx: _BriefContext, cap) -> tuple[str, list[dict]]:
    """Compose the storyform section via prompt.fragments_for (Spec 129)."""
    scope = dict(bctx.storyform_scope)
    # Drop None values — `fragments_for` treats them as "skip this key".
    scope = {k: v for k, v in scope.items() if v}
    if not scope:
        return ("(no storyform on this novel yet — Spec 103/120 surface unused)",
                [])
    tool_result = cap.fragments_for(scope=scope, max_tokens=1500)
    data = getattr(tool_result, "data", tool_result) or {}
    fragments = data.get("fragments", []) if isinstance(data, dict) else []
    parts: list[str] = []
    sources: list[dict] = []
    for f in fragments:
        parts.append(f"- **{f['canonical_id']}** ({f['kind']}): {f['text']}")
        sources.append({"node_id": f["canonical_id"], "kind": f["kind"]})
    body = "\n".join(parts) if parts else "(no fragments authored for this scope)"
    return body, sources


def _compose_pov_card(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    pov = bctx.scene.get("pov") or "unset"
    lines = [
        f"POV: {pov}",
        f"Scene slug: {bctx.scene.get('slug', '')}",
    ]
    return "\n".join(lines), [{"node_id": bctx.scene.get("id", ""),
                                "kind": "Scene"}]


def _compose_scene_cast(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    cast = bctx.scene.get("cast") or ""
    if not cast:
        return ("(no scene_cast tracked yet — Spec 123 PsychProfile/Character "
                "ontology pending)", [])
    return f"Cast in scene: {cast}", [
        {"node_id": bctx.scene.get("id", ""), "kind": "Scene"}]


def _compose_world_rules(_bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    return ("(world rules — Spec 132 codex parity pending; "
            "no world facts injected)", [])


def _compose_continuity(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    chapter_n = bctx.chapter.get("number", "?")
    return (f"Story-time anchor: chapter {chapter_n}. "
            f"(StoryTimeEvent graph — Spec 128 — pending; "
            f"narrative-order continuity only)",
            [{"node_id": bctx.chapter.get("id", ""), "kind": "Chapter"}])


def _compose_foreshadowing(_bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    return ("(foreshadowing obligations — Spec 123 PlantedElement pending; "
            "no Chekhov's-gun report)", [])


def _compose_voice_constraints(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    pov = bctx.scene.get("pov") or ""
    tense_hint = {
        "first": "first-person past unless the chapter outline says otherwise",
        "second": "second-person — carry the unsettling intimacy",
        "third-limited": "third-limited, deep, anchored to the POV's interiority",
        "third-omniscient": "third-omniscient — knowing-narrator distance",
    }.get(pov, "match the established novel voice")
    return f"Voice: {tense_hint}.", [
        {"node_id": bctx.scene.get("id", ""), "kind": "Scene"}]


def _truncate_to_tokens(text: str, budget: int) -> str:
    """Cut to ≈ budget cl100k tokens (4-chars/token heuristic) + ellipsis."""
    max_chars = max(0, budget * _CHARS_PER_TOKEN - 3)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


_SECTION_TITLES = {
    "storyform": "Storyform position",
    "pov_card": "POV card",
    "scene_cast": "Scene cast",
    "world_rules": "World rules in scope",
    "continuity": "Continuity / story-time",
    "foreshadowing": "Foreshadowing obligations",
    "voice_constraints": "Voice + craft constraints",
}


def _render_brief(sections: dict) -> str:
    """Render the SceneBrief as structured markdown (per Open Q1)."""
    parts: list[str] = ["# Scene brief\n"]
    for name in _SECTION_TITLES:
        if name in sections:
            parts.append(f"## {_SECTION_TITLES[name]}\n\n{sections[name]}\n")
    return "\n".join(parts)
