"""adr — architecture decision records on the substrate (Spec 354, Slice 1).

Use when: an architectural decision must be RECORDED as a first-class,
queryable, gate-able artefact — its WH(Y) rationale, the alternatives neglected,
the trade-offs accepted — separate from the spec that implements it.
Triggers:
- A spec or design makes a choice whose rationale would otherwise be lost
- "Why did we decide X (and not Y)?" needs a durable, traversable answer
- An ADR must be validated against the WH(Y) format before approval
Red flags:
- Burying a decision in spec prose where it is lost at implementation time → draft it
- Hand-writing a Decision via `manage.create` without the WH(Y) discipline → use adr.draft
- Putting implementation detail in the decision → that belongs in the spec it REFINES

Slice 1 lands the decision-record primitive: `theme` (a thematic-living ADR =
a Document), `draft` (a WH(Y) `Decision` PART_OF a theme — recordable as a
`proposed` skeleton, completed incrementally), and `validate` (decidable WHY
rules DERIVED from the `decision` Schema — never an LLM gate). The
Definition-of-Done gate (355), dependency `link`/`supersede`/`render`/`impact`
(354 Slice 2), and spec→decision extraction + hints (356) build on this.
"""
from __future__ import annotations

import hashlib

from agency.capability import CapabilityBase, verb
from agency.toolresult import ToolResult

from .ontology import DECISION_SCHEMA, adr_ontology

# Tokens that mean "no real alternative" — a `neglected` of one of these fails
# WHY-003 (at least one alternative must be documented). The ontology cannot
# catch this (the field is non-empty), so it is `validate`'s job.
_EMPTY_ALTERNATIVES = {"", "none", "n/a", "na", "-", "nil"}


def _theme_slug(layer: str) -> str:
    return "adr-" + "".join(c if c.isalnum() else "-" for c in layer.lower()).strip("-")


class AdrCapability(CapabilityBase):
    name = "adr"
    home = "memory"          # reads/writes graph nodes; no new substrate
    ontology = adr_ontology

    def _decision_schema(self) -> dict:
        """The authoritative `decision` Schema (the merged ontology's copy, with
        the module default as a fallback) — `validate` derives WHY-001 + WHY-LEN
        from it so there is ONE contract (rule 2)."""
        return self.ctx.ontology.schemas.get("decision") or DECISION_SCHEMA

    @verb(role="act")
    def theme(self, layer: str, title: str = "", scope: str = "") -> ToolResult:
        """THEME — get-or-create a thematic-living ADR for one architecture
        ``layer`` (the ported Master ADR). A theme is a ``Document`` with
        ``kind="adr-theme"`` (panel B1 — not a new node label); decisions are
        ``PART_OF`` it and `adr.render` (Slice 2) projects its live decisions to
        ``docs/adr/<id>.md``.

        Inputs: layer (str — e.g. "datalayer"), title (str), scope (str — the
                Master-ADR scope boundary).
        Returns: ``{id, layer, created}``.
        chain_next: adr.draft(theme_id, decision=…) to record a decision under it.
        """
        slug = _theme_slug(layer)
        existing = self.ctx.query_nodes(
            "Document", where={"kind": "adr-theme", "layer": layer})
        if existing:
            return ToolResult.success(data={"id": existing[0]["id"], "layer": layer,
                                            "created": False})
        did = self.ctx.record_and_serve("Document", {
            "path": f"docs/adr/{slug}.md",
            # the content_sha of the (empty) unrendered body; render (Slice 2)
            # updates it to the projected file's hash.
            "content_sha": hashlib.sha256(b"").hexdigest(),
            "kind": "adr-theme", "layer": layer,
            "title": title or f"{layer} decisions", "scope": scope,
        })
        return ToolResult.success(data={"id": did, "layer": layer, "created": True})

    @verb(role="act")
    def draft(self, theme_id: str, decision: str, context: str = "",
              facing: str = "", neglected: str = "", benefits: str = "",
              tradeoffs: str = "", proposed_by: str = "agent") -> ToolResult:
        """DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF``
        the theme, SERVING the intent (SPEC-001-A). Only ``decision`` (what was
        decided) is required to record; the rest of the WH(Y) justification may
        be filled incrementally (a ``proposed`` skeleton — Spec 356) and is gated
        for completeness at approval by `adr.validate` + the DoD gate (355).

        Inputs: theme_id (str), decision (str — the chosen course; required),
                context/facing/neglected/benefits/tradeoffs (str — optional at
                draft), proposed_by (str).
        Returns: ``{id, status, theme_id}`` or ``{error}`` on an ontology violation.
        chain_next: adr.validate(id) to check the WHY rules; adr.approve (355).
        """
        props = {"decision": decision, "context": context, "facing": facing,
                 "neglected": neglected, "benefits": benefits,
                 "tradeoffs": tradeoffs, "status": "proposed",
                 "proposed_by": proposed_by}
        try:
            did = self.ctx.record_and_serve("Decision", props)
        except ValueError as exc:
            return ToolResult.success(data={"error": str(exc)})
        self.ctx.link(did, theme_id, "PART_OF")
        return ToolResult.success(data={"id": did, "status": "proposed",
                                        "theme_id": theme_id})

    @verb(role="transform")
    def validate(self, decision_id: str) -> ToolResult:
        """VALIDATE — run the decidable WH(Y) rules over a Decision; return
        findings + an ``ok`` flag. Pure compute — never flips status, never an
        LLM gate (a human/owner approves via adr.approve, 355). WHY-001 + WHY-LEN
        are DERIVED from the ``decision`` Schema (one contract — rule 2).

        Findings:
        - **WHY-001** (error): every WH(Y) element the Schema requires is present
          and non-empty (the approval-gating completeness check).
        - **WHY-003** (error): ``neglected`` documents at least one real alternative
          (semantic — the ontology cannot catch a non-empty "none").
        - **WHY-LEN** (warn): an element exceeds its Schema ``maxLength`` budget.

        Inputs: decision_id (str).
        Returns: ``{decision_id, findings: [{rule, severity, msg}], ok}`` —
                 ``ok`` is False iff any ``error`` finding fires.
        chain_next: adr.approve(decision_id) once ok (355, Slice 2).
        """
        props = self.ctx.recall(decision_id)
        if not props:
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id})
        schema = self._decision_schema()
        why_elements = [f for f in schema.get("required", []) if f != "status"]
        properties = schema.get("properties", {})

        findings: list[dict] = []
        for elem in why_elements:                                   # WHY-001
            if not str(props.get(elem, "")).strip():
                findings.append({"rule": "WHY-001", "severity": "error",
                                 "msg": f"WH(Y) element '{elem}' is empty"})
        if str(props.get("neglected", "")).strip().lower() in _EMPTY_ALTERNATIVES:
            findings.append({"rule": "WHY-003", "severity": "error",   # WHY-003
                             "msg": "no neglected alternative documented"})
        for elem, spec in properties.items():                       # WHY-LEN
            cap = spec.get("maxLength")
            if cap and len(str(props.get(elem, ""))) > cap:
                findings.append({"rule": "WHY-LEN", "severity": "warn",
                                 "msg": f"'{elem}' exceeds the {cap}-char budget"})
        ok = not any(f["severity"] == "error" for f in findings)
        return ToolResult.success(data={"decision_id": decision_id,
                                        "findings": findings, "ok": ok})
