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
rules DERIVED from the `decision` Schema — never an LLM gate).

Slice 2 adds the dependency + lifecycle surface: `read`/`update` (the domain
read + in-place mutator — never reach into `manage` for an ADR), `link` (typed
SPEC-001-C edges, enforcing DEP-001 no-cycle + DEP-003 no-depend-on-rejected),
`supersede` (the SPEC-001-C automatic actions over the core `SUPERSEDED_BY`
edge), `theme_status` (the SPEC-001-D aggregate, derived), `impact` (incoming
dependents to depth), and `render` (live decisions → the theme Document, with a
collapsed superseded-history appendix — panel B3).

Spec 355 Slice 1 adds the Definition-of-Done hinge: `dod_check` (the eight
SPEC-001-E criteria as decidable findings — DOCUMENTATION reuses 354 `validate`)
and `approve` (the gate — blocks on a failed automated criterion, pauses at the
human criteria via `ctx.elicit`, records a `Gate` node, and only the intent
OWNER may confirm or override; an agent may not self-approve). The full
status-as-a-Lifecycle model + cadence sweep are 355 Slice 2.

Spec 356 Slice 1 adds the ADR-central hinge: `extract_decisions` (decidable,
evidence-anchored extraction of a spec's WH(Y) decisions — a canonical WH(Y)
statement is parsed verbatim per SPEC-001-A, else `## Design` cue sentences are
mined; `apply=True` drafts `proposed` Decisions that `REFINES` the spec,
idempotent on `evidence_span`) and `spec_decisions_ready` (the /open→/inprogress
predicate — true iff ≥1 decision REFINES the spec AND all are `approved`; a
zero-decision spec never vacuously passes). `hints` (context loading) is Slice 2.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

from agency.capability import CapabilityBase, verb
from agency.memory import OPEN as _OPEN
from agency.toolresult import ToolResult
from agency._overflow import budget_take   # Spec 286 P3 — shared token-budget split
from agency._tokens import count_tokens     # Spec 082 — the one TokenCounter boundary
# The shared body parsers (one ## slicer, one keep-both latest-revision rule).
from agency.capabilities.document._interconnect import (
    latest_revision_text, parse_frontmatter, section_after as _section_after)

from .ontology import DECISION_SCHEMA, DECISION_STATUS, adr_ontology

# Tokens that mean "no real alternative" — a `neglected` of one of these fails
# WHY-003 (at least one alternative must be documented). The ontology cannot
# catch this (the field is non-empty), so it is `validate`'s job.
_EMPTY_ALTERNATIVES = {"", "none", "n/a", "na", "-", "nil"}
# A tradeoffs statement shorter than this reads as a flimsy acknowledgement
# (WHY-005, SPEC-001-A — tunable budget, not a magic snapshot; rule 8).
_MIN_SUBSTANTIVE = 15

# Dependency edges `adr.link` accepts (SPEC-001-C). SUPERSEDES is NOT here — it
# is the `supersede` verb's job (it reuses the core `SUPERSEDED_BY` edge).
_LINK_TYPES = {"DEPENDS_ON", "RELATES_TO", "REFINES", "PART_OF"}
# Acyclic-by-intent edges — a cycle in these is the SPEC-001-C DEP-001 error.
_ACYCLIC = {"DEPENDS_ON", "REFINES"}

# Spec 356 — the canonical WH(Y) statement (SPEC-001-A): six ordered marker
# phrases that, when ALL present, are parsed verbatim into a complete Decision
# (the highest-fidelity extraction layer — the format the ADR repo IS about).
_WHY_MARKERS = [
    ("context", "in the context of"),
    ("facing", "facing"),
    ("decision", "we decided for"),
    ("neglected", "and neglected"),
    ("benefits", "to achieve"),
    ("tradeoffs", "accepting that"),
]
# Decidable decision cues (Layer 3 fallback) — sentences that announce a choice.
_DECISION_CUES = ("we decided", "we chose", "we will use", "decided to",
                  "decided for", "chose ", "instead of", "rather than",
                  "trade-off", "accepting that", "neglected")
# Markers that introduce the neglected alternative within a cue sentence.
_NEGLECT_MARKERS = ("instead of", "rather than", "neglected", " over ")


def _theme_slug(layer: str) -> str:
    return "adr-" + "".join(c if c.isalnum() else "-" for c in layer.lower()).strip("-")


def _sentences(text: str) -> list[str]:
    """Split prose into sentences (period/!/? or newline boundaries)."""
    parts = re.split(r"(?<=[.!?])\s+|\n", str(text))
    return [p.strip() for p in parts if p.strip()]


def _clean(text: str) -> str:
    return text.strip(" ,.\n*_:").replace("**", "").strip()


def _spec_path(spec_id: str) -> str:
    """Resolve a spec_id to its repo-root-relative ``spec.md`` path across the
    physical ``Plan/<state>/`` folders (Spec 357), with a legacy flat fallback.
    Returns "" when no spec matches. Resolved LIVE so the link tracks the spec
    as it moves toward ``done`` (the digest is rebuilt on spec-done)."""
    import glob
    sid = str(spec_id).strip()
    if not sid:
        return ""
    matches = sorted(glob.glob(f"Plan/*/{sid}-*/spec.md")
                     + glob.glob(f"Plan/{sid}-*/spec.md"))
    return matches[0] if matches else ""


def _truncate_words(text: str, limit: int) -> str:
    """Truncate to ``limit`` chars on a WORD boundary (never mid-word), adding an
    ellipsis when cut — a central sentence sliced mid-word reads as a defect."""
    s = text.strip()
    if len(s) <= limit:
        return s
    return s[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def _central_sentence(spec_path: str, limit: int = 200) -> str:
    """Derive ONE central sentence from a spec file — the frontmatter
    ``summary`` if present, else the first SUBSTANTIVE sentence of its ``## Why``
    section (skipping headings, list items and short label fragments), else the
    H1 title. Read LIVE from the spec so the quote is always a real, current
    sentence of that spec, never a hand-copied (driftable) anchor — rule 8:
    derive, don't pin. ``limit`` caps display width only."""
    import pathlib
    p = pathlib.Path(spec_path)
    if not p.exists():
        return ""
    body = p.read_text(encoding="utf-8")
    fm = parse_frontmatter(body)
    for key in ("summary", "one_liner", "oneliner"):
        s = str(fm.get(key, "")).strip().strip('"').strip()
        if s:
            return _truncate_words(s, limit)
    # Flatten the Why section to one line first so a sentence spanning several
    # physical lines is captured whole, then split on sentence boundaries only
    # (not newlines, unlike _sentences) so we never quote a mid-line fragment.
    flat = re.sub(r"\s+", " ", _section_after(body, "why")).strip()
    for raw in re.split(r"(?<=[.!?])\s+", flat):
        c = _clean(raw)
        # Substantive = a real sentence, not a sub-heading / list item / short
        # label fragment (e.g. a parenthetical like "(evidence + doctrine)").
        if len(c) >= 40 and " " in c and not c.startswith(("#", "-", "*", "|", ">")) \
                and not c.endswith(":"):
            return _truncate_words(c, limit)
    m = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    return _truncate_words(_clean(m.group(1)), limit) if m else ""


def _parse_why_block(body: str) -> dict | None:
    """LAYER 1 (highest fidelity) — parse an explicit WH(Y) 6-part statement
    (SPEC-001-A) into a complete candidate. Marker-anchored + order-tolerant;
    returns ``None`` unless ALL six markers are present (so it never fires on
    prose that merely contains the word "facing")."""
    low = body.lower()
    positions = []
    for field, marker in _WHY_MARKERS:
        idx = low.find(marker)
        if idx == -1:
            return None
        positions.append((idx, field, marker))
    positions.sort()
    cand: dict = {}
    for i, (idx, field, marker) in enumerate(positions):
        start = idx + len(marker)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        cand[field] = _clean(body[start:end])
    cand["evidence_span"] = "why-statement"
    return cand


def _split_neglected(sentence: str) -> str:
    low = sentence.lower()
    for marker in _NEGLECT_MARKERS:
        if marker in low:
            return _clean(sentence[low.index(marker) + len(marker):])
    return ""


def _extract_candidates(body: str, theme_layer: str) -> list[dict]:
    """Decidable, evidence-anchored extraction (no LLM). When the body carries a
    canonical WH(Y) statement, parse it verbatim (Layer 1); else mine the
    structured sections + decision-cue sentences (Layer 3). Each candidate keeps
    an ``evidence_span`` pointing back into the body (the idempotency key + the
    anti-hallucination anchor — SPEC-001-A/B fidelity)."""
    why = _parse_why_block(body)
    if why:
        why["theme"] = theme_layer
        return [why]

    why_sec = _section_after(body, "why")
    design = _section_after(body, "design")
    failure = _section_after(body, "failure modes") or _section_after(body, "failure")
    context = _sentences(why_sec)[0] if _sentences(why_sec) else ""
    tradeoffs = _sentences(failure)[0] if _sentences(failure) else ""

    cands: list[dict] = []
    for sentence in _sentences(design):
        if any(cue in sentence.lower() for cue in _DECISION_CUES):
            cands.append({
                "theme": theme_layer, "context": context, "facing": "",
                "decision": _clean(sentence), "neglected": _split_neglected(sentence),
                "benefits": "", "tradeoffs": tradeoffs,
                "evidence_span": _clean(sentence)[:200],
            })
    return cands


def _aggregate_status(statuses: list[str]) -> str:

    """The SPEC-001-D Master-ADR aggregate-status calculation, ported verbatim
    (agency's lowercase enum). The theme's status is DERIVED from its children's
    statuses, never stored (rule 8)."""
    if any(s == "rejected" for s in statuses):
        return "blocked"
    if statuses and all(s in ("implemented", "retired") for s in statuses):
        return "completed"
    if any(s == "implemented" for s in statuses):
        return "partially-implemented"
    if statuses and all(s == "approved" for s in statuses):
        return "approved"
    if any(s == "approved" for s in statuses):
        return "in-progress"
    return "proposed"


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
              tradeoffs: str = "", proposed_by: str = "agent",
              spec: str = "") -> ToolResult:
        """DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF``
        the theme, SERVING the intent (SPEC-001-A). Only ``decision`` (what was
        decided) is required to record; the rest of the WH(Y) justification may
        be filled incrementally (a ``proposed`` skeleton — Spec 356) and is gated
        for completeness at approval by `adr.validate` + the DoD gate (355).

        Inputs: theme_id (str), decision (str — the chosen course; required),
                context/facing/neglected/benefits/tradeoffs (str — optional at
                draft), proposed_by (str), spec (str — the source spec_id this
                decision derives from; renders a Source link + a derived central
                sentence in the ADR body and the architecture digest).
        Returns: ``{id, status, theme_id}`` or ``{error}`` on an ontology violation.
        chain_next: adr.validate(id) to check the WHY rules; adr.approve (355).
        """
        props = {"decision": decision, "context": context, "facing": facing,
                 "neglected": neglected, "benefits": benefits,
                 "tradeoffs": tradeoffs, "status": "proposed",
                 "proposed_by": proposed_by}
        if spec:
            props["spec"] = str(spec).strip()
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
        # WHY-005 (warn) — tradeoffs must be SUBSTANTIVE, not an empty
        # acknowledgement (SPEC-001-A). Fires only when non-empty-but-flimsy
        # (an empty tradeoffs is already a WHY-001 error).
        tradeoffs = str(props.get("tradeoffs", "")).strip()
        if tradeoffs and (tradeoffs.lower() in _EMPTY_ALTERNATIVES
                          or len(tradeoffs) < _MIN_SUBSTANTIVE):
            findings.append({"rule": "WHY-005", "severity": "warn",
                             "msg": "tradeoffs look insubstantial — state a real cost/risk"})
        # MIN-005 (info) — a decision should reference ≥1 spec (SPEC-001-B
        # separation): a REFINES/RELATES_TO edge to a Document/Spec. Traversed,
        # not a foreign-key scan (dormant-edge rule).
        refs = (self.ctx.neighbors(decision_id, "REFINES", direction="out")
                + self.ctx.neighbors(decision_id, "RELATES_TO", direction="out"))
        if not refs:
            findings.append({"rule": "MIN-005", "severity": "info",
                             "msg": "no referenced spec — REFINES/RELATES_TO a spec Document"})
        ok = not any(f["severity"] == "error" for f in findings)
        return ToolResult.success(data={"decision_id": decision_id,
                                        "findings": findings, "ok": ok})

    # ── Slice 2 — read / update / link / supersede / theme_status / impact / render

    def _why_fields(self) -> list[str]:
        return [f for f in self._decision_schema().get("properties", {})
                if f != "status"]

    def _status_transition_error(self, current: str, new: str) -> str:
        """'' if ``current``→``new`` is a legal decision-status transition (the
        ``decision`` machine in machines.json — Spec 355 S2), else a typed error
        message. A no-op or a fresh decision (no current) is allowed. NOTE: a
        Decision's status is governed by the ``decision`` MACHINE'S transition
        table (enforced here in the domain writers), NOT by a separate Lifecycle
        node — the Decision IS the bi-temporally-versioned tracked entity, so a
        second tracking node would be the parallel-system smell `brooks_lint`
        flags. The machine is the single source of legal transitions."""
        if not current or current == new:
            return ""
        from agency._lifecycle_machines import resolve_machine
        from agency._lifecycle_transitions import assert_transition, IllegalTransition
        try:
            assert_transition(current, new, resolve_machine("decision")["transitions"])
        except IllegalTransition as exc:
            return str(exc)
        return ""

    def _reaches(self, start: str, target: str, edge: str) -> bool:
        """True iff ``target`` is reachable from ``start`` following ``edge``
        outward (the cycle probe behind DEP-001). Traverses via
        ``ctx.neighbors`` — declare an edge ⇒ traverse it (dormant-surface rule)."""
        seen: set[str] = set()
        stack = [start]
        while stack:
            nid = stack.pop()
            if nid == target:
                return True
            if nid in seen:
                continue
            seen.add(nid)
            for nb in self.ctx.neighbors(nid, edge, direction="out"):
                nxt = nb.get("id")
                if nxt:
                    stack.append(nxt)
        return False

    @verb(role="act")
    def read(self, decision_id: str) -> ToolResult:
        """READ a ``Decision``'s current WH(Y) fields + status (the domain read —
        no need to reach into the generic `manage` tool for an ADR).

        Inputs: decision_id (str).
        Returns: ``{id, status, <WH(Y) fields>}`` or ``{error}`` if absent / not a
                 Decision.
        chain_next: adr.validate(id) / adr.update(id, status=…).
        """
        props = self.ctx.recall_typed(decision_id, "Decision")
        if not props:
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id})
        data = {"id": decision_id, "status": props.get("status"),
                "proposed_by": props.get("proposed_by", "")}
        data.update({f: props.get(f, "") for f in self._why_fields()})
        return ToolResult.success(data=data)

    @verb(role="act", param_enums={"status": DECISION_STATUS})
    def update(self, decision_id: str, status: str = "", context: str = "",
               facing: str = "", decision: str = "", neglected: str = "",
               benefits: str = "", tradeoffs: str = "", proposed_by: str = "",
               next_review: str = "", review_cadence: str = "") -> ToolResult:
        """UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y)
        elements + governance incrementally (the DOMAIN mutator; never reach into
        `manage` for an ADR). Only the NON-empty args are written. A ``status``
        change is GOVERNED by the ``decision`` machine (Spec 355 S2): an illegal
        transition (e.g. ``proposed→retired``, or any move off a terminal state)
        is REJECTED with ``DEC-001`` — status no longer poked arbitrarily.

        Inputs: decision_id (str), status (the decision_status enum — transition
                must be legal), any WH(Y) element, next_review (ISO date — the
                cadence `review_sweep` reads), review_cadence (str). Empty = unchanged.
        Returns: ``{id, updated: [field…]}`` or ``{error, rule}``.
        chain_next: adr.validate(id); adr.review_sweep() for the cadence sweep.
        """
        props = self.ctx.recall_typed(decision_id, "Decision")
        if not props:
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id})
        changes = {k: v for k, v in {
            "status": status, "context": context, "facing": facing,
            "decision": decision, "neglected": neglected, "benefits": benefits,
            "tradeoffs": tradeoffs, "proposed_by": proposed_by,
            "next_review": next_review, "review_cadence": review_cadence}.items() if v}
        if not changes:
            return ToolResult.success(data={"id": decision_id, "updated": []})
        if "status" in changes:                                   # DEC-001 — legal transition
            err = self._status_transition_error(str(props.get("status", "")),
                                                changes["status"])
            if err:
                return ToolResult.success(data={"error": err, "rule": "DEC-001",
                                                "decision_id": decision_id})
        try:
            self.ctx.update(decision_id, changes)
        except (KeyError, ValueError) as exc:
            return ToolResult.success(data={"error": str(exc),
                                            "decision_id": decision_id})
        return ToolResult.success(data={"id": decision_id, "updated": sorted(changes)})

    @verb(role="act", param_enums={"dependency_type": _LINK_TYPES})
    def link(self, source_id: str, dependency_type: str, target_id: str,
             note: str = "") -> ToolResult:
        """LINK — add a typed SPEC-001-C dependency edge between two Decisions.
        Enforced at write time (a rejected edge is NEVER created):
        - **DEP-003** (error): no ``DEPENDS_ON`` a ``rejected`` decision.
        - **DEP-001** (error): no cycle in the acyclic edges (``DEPENDS_ON`` /
          ``REFINES``).

        Inputs: source_id, dependency_type (one of DEPENDS_ON · RELATES_TO ·
                REFINES · PART_OF), target_id, note (the DEP-004 rationale).
        Returns: ``{linked: True, source_id, target_id, dependency_type}`` or
                 ``{error, rule, linked: False}``.
        chain_next: adr.impact(target_id) to see what now depends on it.
        """
        dt = dependency_type.upper()
        if dt not in _LINK_TYPES:
            return ToolResult.success(data={
                "error": f"unknown dependency_type {dependency_type!r}",
                "rule": "DEP-000", "linked": False})
        src = self.ctx.recall_typed(source_id, "Decision")
        tgt = self.ctx.recall_typed(target_id, "Decision")
        if not src or not tgt:
            missing = source_id if not src else target_id
            return ToolResult.success(data={"error": f"no decision {missing!r}",
                                            "linked": False})
        if dt == "DEPENDS_ON" and str(tgt.get("status")) == "rejected":   # DEP-003
            return ToolResult.success(data={
                "error": "cannot depend on a rejected decision",
                "rule": "DEP-003", "linked": False})
        if dt in _ACYCLIC and self._reaches(target_id, source_id, dt):    # DEP-001
            return ToolResult.success(data={
                "error": f"circular {dt} dependency",
                "rule": "DEP-001", "linked": False})
        self.ctx.link(source_id, target_id, dt, {"note": note} if note else None)
        return ToolResult.success(data={"linked": True, "source_id": source_id,
                                        "target_id": target_id,
                                        "dependency_type": dt})

    @verb(role="act")
    def supersede(self, old_id: str, decision: str, context: str = "",
                  facing: str = "", neglected: str = "", benefits: str = "",
                  tradeoffs: str = "", proposed_by: str = "agent") -> ToolResult:
        """SUPERSEDE — the SPEC-001-C automatic actions: mint a replacement
        ``Decision`` (status ``proposed``) ``PART_OF`` the same theme, flip the old
        one to ``superseded``, and write the forward reference (the core
        ``SUPERSEDED_BY`` edge). The old node stays queryable (its status is now
        ``superseded``; the render appendix lists it).

        Inputs: old_id (the decision being replaced), plus the new WH(Y) fields
                (same shape as `draft`).
        Returns: ``{old_id, new_id, status: "superseded", theme_id}`` or ``{error}``.
        chain_next: adr.validate(new_id); adr.render(theme_id).
        """
        old = self.ctx.recall_typed(old_id, "Decision")
        if not old:
            return ToolResult.success(data={"error": f"no decision {old_id!r}",
                                            "old_id": old_id})
        terr = self._status_transition_error(str(old.get("status", "")), "superseded")
        if terr:                                                  # DEC-001 — can't supersede a terminal decision
            return ToolResult.success(data={"error": terr, "rule": "DEC-001",
                                            "old_id": old_id})
        themes = self.ctx.neighbors(old_id, "PART_OF", direction="out")
        theme_id = themes[0].get("id") if themes else ""
        props = {"decision": decision, "context": context, "facing": facing,
                 "neglected": neglected, "benefits": benefits,
                 "tradeoffs": tradeoffs, "status": "proposed",
                 "proposed_by": proposed_by}
        try:
            new_id = self.ctx.record_and_serve("Decision", props)
        except ValueError as exc:
            return ToolResult.success(data={"error": str(exc), "old_id": old_id})
        if theme_id:
            self.ctx.link(new_id, theme_id, "PART_OF")
        self.ctx.update(old_id, {"status": "superseded"})       # SPEC-001-C action 1
        self.ctx.link(old_id, new_id, "SUPERSEDED_BY")          # action 2 (forward ref)
        return ToolResult.success(data={"old_id": old_id, "new_id": new_id,
                                        "status": "superseded", "theme_id": theme_id})

    @verb(role="transform")
    def theme_status(self, theme_id: str) -> ToolResult:
        """THEME_STATUS — the SPEC-001-D aggregate status DERIVED from the theme's
        ``PART_OF`` children (never stored — rule 8).

        Inputs: theme_id (str).
        Returns: ``{theme_id, status, counts: {status: n}, children}``.
        chain_next: adr.render(theme_id) to project the live decisions.
        """
        children = self.ctx.neighbors(theme_id, "PART_OF", direction="in")
        statuses = [str(c.get("status")) for c in children]
        counts = dict(Counter(statuses))
        return ToolResult.success(data={"theme_id": theme_id,
                                        "status": _aggregate_status(statuses),
                                        "counts": counts, "children": len(children)})

    @verb(role="transform")
    def impact(self, decision_id: str, depth: int = 1) -> ToolResult:
        """IMPACT — what ``DEPENDS_ON`` / ``REFINES`` / ``PART_OF`` this decision,
        to ``depth`` hops (SPEC-001-C ``adr impact``). Traverses INCOMING edges.

        Inputs: decision_id (str), depth (int — transitive hops; ≥ 1).
        Returns: ``{decision_id, depth, dependents: [{id, via, status, depth}], total}``.
        chain_next: review each dependent before changing this decision.
        """
        edges = ("DEPENDS_ON", "REFINES", "PART_OF")
        seen: dict[str, dict] = {}
        frontier = [decision_id]
        d = 0
        while frontier and d < max(1, depth):
            nxt: list[str] = []
            for nid in frontier:
                for edge in edges:
                    for nb in self.ctx.neighbors(nid, edge, direction="in"):
                        dep = nb.get("id")
                        if dep and dep != decision_id and dep not in seen:
                            seen[dep] = {"id": dep, "via": edge,
                                         "status": nb.get("status"), "depth": d + 1}
                            nxt.append(dep)
            frontier = nxt
            d += 1
        deps = list(seen.values())
        return ToolResult.success(data={"decision_id": decision_id, "depth": depth,
                                        "dependents": deps, "total": len(deps)})

    @verb(role="act")
    def render(self, theme_id: str) -> ToolResult:
        """RENDER — project a theme's **live** decisions into a markdown body and
        stamp the theme ``Document``'s ``content_sha`` (graph-side projection; the
        file round-trip is `document.sync`'s job, keep-both — Spec 292). Per panel
        B3, superseded decisions are NOT re-inflated — they collapse to a one-line
        "Superseded / history" appendix, so the active section stays a handful.
        Deterministic (children sorted by id, no timestamps) ⇒ re-render is
        idempotent (same ``content_sha``).

        Inputs: theme_id (str).
        Returns: ``{id, path, content_sha, active, superseded, body}`` or ``{error}``.
        chain_next: document.sync(path) to round-trip the body to disk.
        """
        theme = self.ctx.recall_typed(theme_id, "Document")
        if not theme:
            return ToolResult.success(data={"error": f"no theme {theme_id!r}",
                                            "theme_id": theme_id})
        children = self.ctx.neighbors(theme_id, "PART_OF", direction="in")
        # Sort by the decision TEXT (stable across sessions) — NOT the graph id
        # (a fresh UUID each session would churn the committed file every render).
        active = sorted((c for c in children
                         if str(c.get("status")) != "superseded"),
                        key=lambda c: str(c.get("decision", "")))
        superseded = sorted((c for c in children
                             if str(c.get("status")) == "superseded"),
                            key=lambda c: str(c.get("decision", "")))
        body = self._render_body(theme, active, superseded)
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.ctx.update(theme_id, {"content_sha": sha})
        return ToolResult.success(data={"id": theme_id, "path": theme.get("path"),
                                        "content_sha": sha, "active": len(active),
                                        "superseded": len(superseded), "body": body})

    # The five WH(Y) connectors, in canonical order (SPEC-001-A / adr ADR-001):
    # rendered as a bolded six-part block, one line per element.
    _WHY_BLOCK = (("In the context of", "context"), ("facing", "facing"),
                  ("we decided for", "decision"), ("and neglected", "neglected"),
                  ("to achieve", "benefits"), ("accepting that", "tradeoffs"))
    # Typed dependency edges surfaced per decision (SPEC-001-C; SUPERSEDED_BY is
    # the history appendix, and PART_OF — membership in this very theme — is
    # implied by the file, not a dependency).
    _DEP_EDGES = (("DEPENDS_ON", "Depends On"), ("REFINES", "Refines"),
                  ("RELATES_TO", "Relates To"))

    def _render_body(self, theme: dict, active: list[dict],
                     superseded: list[dict]) -> str:
        """Project a theme (a Master ADR — SPEC-001-D) to the canonical enhanced
        WH(Y) markdown of the `adr` repo: an aggregate-status header, then each
        live decision as a metadata table + a bolded six-part WH(Y) statement
        (SPEC-001-A) + a typed Dependencies table, and a collapsed superseded
        appendix. Deterministic (children pre-sorted by id, no timestamps)."""
        title = theme.get("title") or f"{theme.get('layer', '')} decisions"
        agg = _aggregate_status([str(d.get("status")) for d in active + superseded])
        lines = [f"# {title}", ""]
        if theme.get("scope"):
            lines += [f"> {theme.get('scope')}", ""]
        # Master-ADR aggregate status (SPEC-001-D — status over the children).
        lines += ["| Master ADR | Layer | Aggregate Status | Decisions |",
                  "|---|---|---|---|",
                  f"| {title} | {theme.get('layer', '—')} | {agg} | "
                  f"{len(active)} live · {len(superseded)} superseded |", ""]
        layer_id = (theme.get("layer") or "adr").upper()
        for i, d in enumerate(active, start=1):
            did = d.get("id", "—")              # graph id — for edge traversal only
            disp = f"{layer_id}-{i:02d}"         # stable human Decision ID (SPEC-001-A)
            lines += [
                f"## {d.get('decision')}", "",
                "| Decision ID | Status | Proposed By |",
                "|---|---|---|",
                f"| {disp} | {d.get('status')} | {d.get('proposed_by', '—')} |", "",
            ]
            # The WH(Y) statement — bolded connectors, one element per line
            # (markdown hard breaks via trailing two spaces), the canonical shape.
            why = [f"**{conn}** {str(d.get(field, '')).strip()}"
                   for conn, field in self._WHY_BLOCK]
            lines.append(",  \n".join(why) + ".")
            lines.append("")
            # Source: link to the spec that established this decision + ONE central
            # sentence derived live from it (the evidence anchor). The link is
            # ../../-relative so it resolves from docs/adr/; the architecture digest
            # re-parses this line back to a root-relative link.
            spec_path = _spec_path(d.get("spec", ""))
            if spec_path:
                sent = _central_sentence(spec_path)
                src = f"**Source:** [`{spec_path}`](../../{spec_path})"
                if sent:
                    src += f' — "{sent}"'
                lines += [src, ""]
            # Typed dependencies (only when present — ADR-minimalism, SPEC-001-B).
            deprows: list[str] = []
            for edge, label in self._DEP_EDGES:
                # Sort + reference by the target's TEXT (decision/title/path), never
                # its graph id — a fresh UUID each session would churn the file.
                for nb in sorted(self.ctx.neighbors(did, edge, direction="out"),
                                 key=lambda n: str(n.get("decision") or n.get("title")
                                                    or n.get("path") or n.get("id", ""))):
                    ref = (nb.get("decision") or nb.get("title")
                           or nb.get("path") or nb.get("id", "—"))
                    deprows.append(f"| {label} | {ref} |")
            if deprows:
                lines += ["| Relationship | Decision / Spec |", "|---|---|",
                          *deprows, ""]
        if superseded:
            lines += ["## Superseded / history", ""]
            for d in superseded:
                fwd = self.ctx.neighbors(d.get("id"), "SUPERSEDED_BY",
                                         direction="out")
                by = fwd[0].get("id") if fwd else "—"
                lines.append(
                    f"- {d.get('id')} · {d.get('decision')} · superseded-by {by}")
        return "\n".join(lines)

    # ── Spec 355 Slice 1 — the Definition-of-Done gate ───────────────────────

    @staticmethod
    def _is_owner(approver: str) -> bool:
        """The approver is a human owner iff it is a non-empty identity that is
        not the reserved agent marker (panel B2.1 — an agent may NOT self-approve
        or self-override; only the intent owner clears the hinge)."""
        return bool(approver) and approver.strip().lower() != "agent"

    def _count_alternatives(self, neglected: str) -> int:
        """Count the distinct alternatives a `neglected` field documents —
        comma / semicolon / 'and' / slash separated, dropping the empty tokens."""
        import re
        parts = re.split(r"[;,/]|\band\b", str(neglected))
        return sum(1 for p in parts if p.strip().lower() not in _EMPTY_ALTERNATIVES)

    def _has_cycle(self, decision_id: str) -> bool:
        for nb in self.ctx.neighbors(decision_id, "DEPENDS_ON", direction="out"):
            t = nb.get("id")
            # _reaches(t, …) already returns True when t IS decision_id (the start
            # node is checked against the target first) — no separate self-edge term.
            if t and self._reaches(t, decision_id, "DEPENDS_ON"):
                return True
        return False

    def _dod_criteria(self, decision_id: str, props: dict) -> list[dict]:
        """The eight SPEC-001-E criteria as decidable findings. The DOCUMENTATION
        check reuses 354 `validate` (no duplicated WH(Y) rule logic — rule 2)."""
        val_ok = bool(self.validate(decision_id).data.get("ok"))
        alts = self._count_alternatives(props.get("neglected", ""))
        part_of_theme = bool(self.ctx.neighbors(decision_id, "PART_OF", direction="out"))
        refs = (self.ctx.neighbors(decision_id, "REFINES", direction="out")
                + self.ctx.neighbors(decision_id, "RELATES_TO", direction="out"))
        depends = self.ctx.neighbors(decision_id, "DEPENDS_ON", direction="out")
        evidence = bool(str(props.get("context", "")).strip()
                        and str(props.get("facing", "")).strip())
        gov = bool(str(props.get("review_board", "")).strip())
        cadence = bool(str(props.get("review_cadence", "")).strip())

        def c(cid, criterion, mode, severity, passed, msg):
            return {"id": cid, "criterion": criterion, "mode": mode,
                    "severity": severity, "passed": bool(passed), "msg": msg}

        return [
            c("DOD-E01", "Evidence", "partial", "warn", evidence,
              "context+facing reference prior art (human confirm)"),
            c("DOD-C01", "Criteria", "auto", "error", alts >= 2,
              f"{alts} neglected alternative(s); need ≥2"),
            c("DOD-A01", "Agreement", "partial", "warn", gov,
              "governance populated (human confirm)"),
            c("DOD-D01", "Documentation", "auto", "error", val_ok,
              "WH(Y) validate passes"),
            c("DOD-D02", "Documentation", "auto", "error", part_of_theme,
              "PART_OF a theme Document"),
            c("DOD-R01", "Review", "auto", "warn", cadence,
              "review_cadence set"),
            c("DOD-DP01", "Dependencies", "auto", "warn", bool(depends),
              "has dependency edges"),
            c("DOD-DP02", "Dependencies", "auto", "error", not self._has_cycle(decision_id),
              "no DEP-001 cycle"),
            c("DOD-RF01", "References", "auto", "warn", all(r.get("id") for r in refs),
              "REFINES/RELATES_TO targets resolve"),
            c("DOD-M01", "Master", "auto", "error", part_of_theme,
              "PART_OF an AdrTheme"),
        ]

    @verb(role="transform")
    def dod_check(self, decision_id: str) -> ToolResult:
        """DOD_CHECK — run the ported SPEC-001-E Definition-of-Done criteria over a
        Decision (pure compute; never flips status). Each criterion is **auto**,
        **partial**, or **human**; the auto checks are decidable (no LLM/key).

        Inputs: decision_id (str).
        Returns: ``{decision_id, criteria: [{id, criterion, mode, passed, severity,
                 msg}], auto_passed, human_pending: [id…], score}`` — ``auto_passed``
                 is True iff every ``error``-severity auto/partial check passes;
                 ``score`` is the SPEC-001-E weighted fraction (surfaced, NOT gating
                 — rule 8). Or ``{error}`` if absent.
        chain_next: adr.approve(decision_id, approver=…) to clear the gate.
        """
        props = self.ctx.recall_typed(decision_id, "Decision")
        if not props:
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id})
        criteria = self._dod_criteria(decision_id, props)
        auto_passed = all(c["passed"] for c in criteria
                          if c["mode"] in ("auto", "partial") and c["severity"] == "error")
        human_pending = [c["id"] for c in criteria if c["mode"] in ("partial", "human")]
        decidable = [c for c in criteria if c["mode"] != "human"]
        score = round(sum(1 for c in decidable if c["passed"]) / len(decidable), 3) \
            if decidable else 0.0
        return ToolResult.success(data={"decision_id": decision_id, "criteria": criteria,
                                        "auto_passed": auto_passed,
                                        "human_pending": human_pending, "score": score})

    def _record_gate(self, decision_id: str, name: str, passed: bool,
                     evidence: str, approver: str) -> str:
        gid = self.ctx.record_and_serve("Gate", {
            "name": name, "passed": bool(passed),
            "evidence": evidence, "approver": approver})
        self.ctx.link(decision_id, gid, "GATED_BY")
        return gid

    @verb(role="act")
    def approve(self, decision_id: str, approver: str = "",
                override: bool = False) -> ToolResult:
        """APPROVE — the DoD hinge (SPEC-001-E pre-approval gate). Runs `dod_check`;
        a decision advances to ``approved`` ONLY when the automated criteria pass
        AND a human OWNER confirms. Records a ``Gate`` node (passed/blocked) either
        way; never silently passes, never lets the agent self-approve (panel B2.1).

        - automated criterion fails → ``{blocked: True, failing}`` (no approval),
          unless a provenance-stamped OWNER ``override`` is supplied.
        - automated pass, no ``approver`` → tries `ctx.elicit`; with no host bound
          it returns ``{input_required: True, pending}`` (the owner resumes later).
        - OWNER ``approver`` given → advances to ``approved``.

        Inputs: decision_id (str), approver (str — the human owner's identity;
                ``"agent"`` is rejected), override (bool — owner-only escape hatch).
        Returns: ``{decision_id, approved, …}`` — see the branches above.
        chain_next: adr.render(theme_id); the spec's /open→/inprogress gate (356).
        """
        props = self.ctx.recall_typed(decision_id, "Decision")
        if not props:
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id, "approved": False})
        terr = self._status_transition_error(str(props.get("status", "")), "approved")
        if terr:                                                  # DEC-001 — e.g. a rejected/superseded decision
            return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                            "error": terr, "rule": "DEC-001"})
        chk = self.dod_check(decision_id).data
        owner = self._is_owner(approver)

        if not chk["auto_passed"]:
            failing = [c["id"] for c in chk["criteria"]
                       if c["mode"] == "auto" and c["severity"] == "error" and not c["passed"]]
            if override and owner:
                gate = self._record_gate(decision_id, "dod-override", True,
                                         f"owner override by {approver}; failing={failing}",
                                         approver)
                self.ctx.update(decision_id, {"status": "approved"})
                return ToolResult.success(data={"decision_id": decision_id, "approved": True,
                                                "override": True, "approver": approver,
                                                "failing": failing, "gate": gate,
                                                "status": "approved"})
            if override:                                   # override by a non-owner / agent
                return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                                "error": "an agent may not self-approve; "
                                                "override requires an owner identity",
                                                "approver": approver})
            gate = self._record_gate(decision_id, "dod", False,
                                     f"blocked: {failing}", approver)
            return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                            "blocked": True, "failing": failing, "gate": gate})

        # automated checks pass → require a human OWNER confirmation
        if approver and not owner:                         # an explicit "agent"
            return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                            "error": "an agent may not self-approve"})
        if owner:
            gate = self._record_gate(decision_id, "dod", True,
                                     f"approved by {approver}; pending={chk['human_pending']}",
                                     approver)
            self.ctx.update(decision_id, {"status": "approved"})
            return ToolResult.success(data={"decision_id": decision_id, "approved": True,
                                            "approver": approver, "gate": gate,
                                            "status": "approved", "override": bool(override)})

        # no approver supplied → ask the owner in the flow, else pause for resume
        from agency._host_bridge import HostUnavailable
        msg = f"Approve decision {decision_id}? Human-pending: {chk['human_pending']}"
        try:
            outcome = self.ctx.host.elicit(msg, options=["approve", "reject"])
        except HostUnavailable:
            gate = self._record_gate(decision_id, "dod", False,
                                     f"awaiting human approval; pending={chk['human_pending']}", "")
            return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                            "input_required": True,
                                            "pending": chk["human_pending"], "gate": gate})
        if outcome.accepted and str(getattr(outcome, "data", "")).lower() != "reject":
            gate = self._record_gate(decision_id, "dod", True, "approved via elicit", "owner")
            self.ctx.update(decision_id, {"status": "approved"})
            return ToolResult.success(data={"decision_id": decision_id, "approved": True,
                                            "approver": "owner", "gate": gate,
                                            "status": "approved"})
        return ToolResult.success(data={"decision_id": decision_id, "approved": False,
                                        "declined": True})

    # ── Spec 356 Slice 1 — spec→decision extraction + the /open gate predicate ──

    def _spec_body(self, doc_id: str) -> str:
        """The latest revision body of an ingested spec Document (Spec 292 — the
        text lives on the DocRevision, not the Document node)."""
        return latest_revision_text(
            self.ctx.neighbors(doc_id, "REVISION_OF", direction="in"))

    def _resolve_spec(self, spec_id: str) -> tuple[str, str]:
        """Resolve ``spec_id`` to ``(document_id, body)``. It may be EITHER a
        Document node id OR a frontmatter ``spec_id`` (owner directive: "the
        document id can also be a Spec id") — try the node id first, then match
        the frontmatter ``spec_id`` across ingested spec Documents."""
        doc = self.ctx.recall_typed(spec_id, "Document")
        if doc:
            return spec_id, self._spec_body(spec_id)
        seen: set[str] = set()
        for d in self.ctx.query_nodes("Document"):
            did = d.get("id")
            if not did or did in seen:
                continue
            seen.add(did)
            body = self._spec_body(did)
            fm = parse_frontmatter(body)
            if str(fm.get("spec_id", "")).strip().strip('"') == str(spec_id).strip():
                return did, body
        return "", ""

    @verb(role="act")
    def extract_decisions(self, spec_id: str, theme_id: str = "",
                          apply: bool = False) -> ToolResult:
        """EXTRACT_DECISIONS — surface a spec's key decisions as WH(Y) candidates
        and (``apply=True``) draft them as ``proposed`` ``Decision``s that
        ``REFINES`` the spec. **Decidable-first** (no API key): a canonical WH(Y)
        statement is parsed verbatim (SPEC-001-A), else the ``## Design`` cue
        sentences + ``## Why``/``## Failure modes`` sections are mined. Every
        candidate keeps an ``evidence_span`` (anti-hallucination anchor +
        idempotency key — re-apply never duplicates).

        Inputs: spec_id (a Document id OR a frontmatter spec_id), theme_id (the
                AdrTheme to file decisions under; inferred/get-or-created when
                empty), apply (False = preview only; True = draft the Decisions).
        Returns: ``{spec_id, theme_id, candidates: [...], drafted: [ids]}`` or
                 ``{error}``.
        chain_next: human edits the candidates → apply=True → adr.approve (355) →
                    adr.spec_decisions_ready gates /open→/inprogress (358).
        """
        doc_id, body = self._resolve_spec(spec_id)
        if not doc_id:
            return ToolResult.success(data={"error": f"no spec {spec_id!r} (Document "
                                            "id or frontmatter spec_id)", "spec_id": spec_id})
        if not body:
            return ToolResult.success(data={"error": f"spec {spec_id!r} has no ingested "
                                            "body (document.ingest it first)",
                                            "spec_id": spec_id, "candidates": []})
        # Theme: explicit, else INFER the architecture layer from the spec's
        # frontmatter `domain` (Spec 356 theme-inference) and get-or-create that
        # theme (default "core"). Per-candidate multi-theme routing (one spec's
        # decisions spanning several themes) needs a classifier — deferred.
        theme_layer = "core"
        if not theme_id:
            # Newline-agnostic (the graph store flattens the DocRevision body, so
            # `## ` parsing + frontmatter both go by substring/regex, not lines).
            m = re.search(r'\bdomain:\s*"?([A-Za-z][\w-]*)"?', body)
            theme_layer = m.group(1) if m else "core"
            theme_id = self.theme(layer=theme_layer).data["id"]
        else:
            t = self.ctx.recall_typed(theme_id, "Document")
            theme_layer = (t or {}).get("layer", "") if t else ""
        candidates = _extract_candidates(body, theme_layer)
        if not apply:
            return ToolResult.success(data={"spec_id": doc_id, "theme_id": theme_id,
                                            "candidates": candidates, "drafted": []})
        # apply=True — draft each NEW candidate (idempotent on evidence_span).
        existing = self.ctx.sources_via_edge("REFINES", doc_id, "Document",
                                             label="Decision")
        seen_spans = {d.get("evidence_span") for d in existing}
        drafted: list[str] = []
        for c in candidates:
            if c["evidence_span"] in seen_spans:
                continue
            try:
                did = self.ctx.record_and_serve("Decision", {
                    "decision": c["decision"], "context": c.get("context", ""),
                    "facing": c.get("facing", ""), "neglected": c.get("neglected", ""),
                    "benefits": c.get("benefits", ""), "tradeoffs": c.get("tradeoffs", ""),
                    "status": "proposed", "proposed_by": "extractor",
                    "evidence_span": c["evidence_span"]})
            except ValueError as exc:
                return ToolResult.success(data={"error": str(exc), "spec_id": doc_id})
            self.ctx.link(did, theme_id, "PART_OF")
            self.ctx.link(did, doc_id, "REFINES")
            seen_spans.add(c["evidence_span"])
            drafted.append(did)
        return ToolResult.success(data={"spec_id": doc_id, "theme_id": theme_id,
                                        "candidates": candidates, "drafted": drafted})

    @verb(role="transform")
    def spec_decisions_ready(self, spec_id: str) -> ToolResult:
        """SPEC_DECISIONS_READY — the /open→/inprogress predicate (358). ``ready``
        is True iff **≥1** ``Decision`` ``REFINES`` the spec AND every such
        decision is ``approved`` (the 355 gate). A zero-decision spec returns
        ``{ready: False, reason: "no-decisions"}`` — it does NOT vacuously pass
        (panel B2.2); the owner clears it with an explicit override (357).

        Inputs: spec_id (a Document id OR a frontmatter spec_id).
        Returns: ``{spec_id, ready, decisions: [{id, status}], blocking: [ids],
                 reason?}``.
        chain_next: workflow.move_spec(spec, "inprogress") guards on ``ready``.
        """
        doc_id, _ = self._resolve_spec(spec_id)
        if not doc_id:
            return ToolResult.success(data={"error": f"no spec {spec_id!r}",
                                            "spec_id": spec_id, "ready": False})
        decisions = self.ctx.sources_via_edge("REFINES", doc_id, "Document",
                                              label="Decision")
        rows = [{"id": d.get("id"), "status": d.get("status")} for d in decisions]
        if not rows:
            return ToolResult.success(data={"spec_id": doc_id, "ready": False,
                                            "reason": "no-decisions", "decisions": [],
                                            "blocking": []})
        blocking = [r["id"] for r in rows if r["status"] != "approved"]
        return ToolResult.success(data={"spec_id": doc_id, "ready": not blocking,
                                        "decisions": rows, "blocking": blocking})

    # ── Spec 356 Slice 2 — architecture-hint loading (the payoff) ────────────

    @verb(role="transform")
    def hints(self, spec_id: str, budget: int = 2000) -> ToolResult:
        """HINTS — the payoff: at implementation start, project the spec's
        **approved** decisions (+ their depth-1 ``DEPENDS_ON`` neighbours) into a
        compact, token-BOUNDED architecture-hint block — *decisions and their
        consequences*, not the spec re-stated (the minimum an implementer needs to
        not contradict an approved decision). Owner's vision: "ADRs exist primarily
        to extract code + architecture hints loaded into context at implementation
        start." Only `approved` decisions appear (a `proposed` draft is not yet a
        constraint). Reuses the shared ``budget_take`` split (rule 2); the stored
        Decision nodes remain FULL — the budget governs only this projection (rule 9).

        Inputs: spec_id (a Document id OR a frontmatter spec_id), budget (int —
                max tokens of returned hints).
        Returns: ``{spec_id, themes, hints: [{decision_id, theme, decision, why,
                 constraints, touches, related}], budget, returned_tokens,
                 truncated}`` or ``{error}``.
        chain_next: load the block into the implementer's context (workflow 358).
        """
        doc_id, _ = self._resolve_spec(spec_id)
        if not doc_id:
            return ToolResult.success(data={"error": f"no spec {spec_id!r}",
                                            "spec_id": spec_id, "hints": []})
        decisions = self.ctx.sources_via_edge("REFINES", doc_id, "Document",
                                              label="Decision")
        approved = [d for d in decisions if str(d.get("status")) == "approved"]
        hints: list[dict] = []
        for d in approved:
            did = d.get("id")
            facing, benefits = d.get("facing", ""), d.get("benefits", "")
            why = " → ".join(p for p in (facing, benefits) if str(p).strip()) or d.get("context", "")
            related = [nb.get("id") for nb in self.ctx.neighbors(did, "DEPENDS_ON",
                       direction="out") if nb.get("id")]
            themes = self.ctx.neighbors(did, "PART_OF", direction="out")
            touches = themes[0].get("layer", "") if themes else ""
            hints.append({"decision_id": did, "theme": touches,
                          "decision": d.get("decision", ""), "why": why,
                          "constraints": d.get("tradeoffs", ""), "touches": touches,
                          "related": related})

        def _cost(h: dict) -> int:
            return count_tokens(json.dumps(h, default=str, sort_keys=True))

        kept, skipped = budget_take(hints, _cost, budget)
        return ToolResult.success(data={
            "spec_id": doc_id,
            "themes": sorted({h["theme"] for h in kept if h["theme"]}),
            "hints": kept, "budget": budget,
            "returned_tokens": sum(_cost(h) for h in kept),
            "truncated": bool(skipped)})

    # ── Spec 354 Slice 3 — the "handful of ADRs" index ───────────────────────

    @verb(role="transform")
    def catalogue(self, status: str = "", layer: str = "") -> ToolResult:
        """CATALOGUE — the "handful of ADRs" index (SPEC-001-B minimalism): every
        theme + its `PART_OF` decision counts grouped by status. Optionally filter
        to one architecture ``layer`` and/or count only one ``status``.

        (Named `catalogue`, not `list`, to avoid a bare-name collision with
        `manage.list` — Spec 074 collision discipline.)

        Inputs: status (str — count only this decision status), layer (str — only
                this theme's layer).
        Returns: ``{themes: [{id, layer, title, decisions, by_status}],
                 total_themes, total_decisions}``.
        chain_next: adr.theme_status(theme_id) for one theme's aggregate;
                    adr.render(theme_id) to project its live decisions.
        """
        themes = [t for t in self.ctx.query_nodes("Document", where={"kind": "adr-theme"})
                  if t.get("vto", _OPEN) >= _OPEN]
        if layer:
            themes = [t for t in themes if t.get("layer") == layer]
        rows: list[dict] = []
        total_decisions = 0
        for t in themes:
            children = self.ctx.neighbors(t.get("id"), "PART_OF", direction="in")
            statuses = (str(c.get("status")) for c in children)
            by_status = dict(Counter(s for s in statuses if not status or s == status))
            count = sum(by_status.values())
            total_decisions += count
            rows.append({"id": t.get("id"), "layer": t.get("layer", ""),
                         "title": t.get("title", ""), "decisions": count,
                         "by_status": by_status})
        rows.sort(key=lambda r: r["layer"])
        return ToolResult.success(data={"themes": rows, "total_themes": len(rows),
                                        "total_decisions": total_decisions})

    @verb(role="effect")
    def review_sweep(self, today: str = "") -> ToolResult:
        """REVIEW_SWEEP — cadence governance (Spec 355 S2, SPEC-001-A): flip every
        live ``approved``/``implemented`` decision whose ``next_review`` date has
        lapsed (< today) to ``expired`` — a legal `decision`-machine transition.
        Makes governance LIVE rather than a table that rots. Decidable (no key):
        an ISO-date string compare.

        Inputs: today (ISO 'YYYY-MM-DD'; default = the system date).
        Returns: ``{swept: [decision_ids], count, as_of}``.
        chain_next: adr.catalogue(status="expired") to review what lapsed.
        """
        import datetime
        as_of = today or datetime.date.today().isoformat()
        swept: list[str] = []
        for d in self.ctx.find("Decision"):
            if str(d.get("status")) in ("approved", "implemented"):
                nr = str(d.get("next_review", "")).strip()
                if nr and nr < as_of:
                    self.ctx.update(d.get("id"), {"status": "expired"})
                    swept.append(d.get("id"))
        return ToolResult.success(data={"swept": swept, "count": len(swept),
                                        "as_of": as_of})

    # The architecture layers in canonical order (the reserved theme set, Spec
    # 353); unknown layers sort after, alphabetically. AGENCY-DRIFT: adr-layers.
    _LAYER_ORDER = ("datalayer", "substrate", "capabilities", "lifecycle", "workflow")

    @verb(role="act")
    def architecture(self, adr_dir: str = "docs/adr", out: str = "architecture.md",
                     apply: bool = False) -> ToolResult:
        """ARCHITECTURE — rebuild the shorthand architecture digest: every recorded
        WH(Y) decision as a ONE-LINER, grouped by architecture layer, rolled up from
        the durable thematic ADRs (``docs/adr/<layer>.md``). The digest is the
        token-cheap, high-signal artefact the SessionStart hook emits so every
        session opens knowing the load-bearing decisions; the full rationale lives in
        the ADRs. "Code is the final decision" — this is derived from the shipped
        ADRs, never authored ahead of them. Rebuilt when a spec is marked done (the
        owner's word is the approval) and its ADR is appended/updated.

        Inputs: adr_dir (where the thematic ADRs live), out (the digest path,
                repo-root-relative), apply (write the file; else preview only).
        Returns: ``{path, layers, decisions, body, written}``.
        chain_next: the SessionStart hook emits ``out``; `adr.hints` for the
                    per-spec deep cut at implementation start.
        """
        import pathlib
        base = pathlib.Path(adr_dir)
        layers: dict[str, dict] = {}
        for md in sorted(base.glob("*.md")):
            if md.name == "README.md":
                continue
            raw = md.read_text(encoding="utf-8")
            _anchor, fm_body = self._strip_anchor(raw)
            fm = parse_frontmatter(fm_body)
            if fm.get("kind") != "adr-theme":
                continue
            layer = str(fm.get("layer", md.stem)).strip()
            # Per-decision blocks (split on `## ` headings), minus the superseded
            # appendix. Each carries its source-spec link + central sentence,
            # parsed back from the ADR's `**Source:**` line.
            decisions = []
            for blk in re.split(r"(?m)^##\s+", fm_body)[1:]:
                head, _, rest = blk.partition("\n")
                head = head.strip()
                if head.lower().startswith("superseded"):
                    continue
                spec_path = sentence = ""
                m = re.search(r"\*\*Source:\*\*\s+\[[^\]]*\]\(([^)]+)\)", rest)
                if m:
                    spec_path = re.sub(r"^(\.\./)+", "", m.group(1).strip())
                    # Derive the central sentence straight from the spec (not by
                    # re-parsing the ADR's quoted text — a sentence containing a
                    # double-quote would break that, and a live read stays fresh).
                    sentence = _central_sentence(spec_path)
                decisions.append({"title": head, "spec": spec_path,
                                  "sentence": sentence})
            layers[layer] = {"title": str(fm.get("title", layer)).strip().strip('"'),
                             "scope": str(fm.get("scope", "")).strip().strip('"'),
                             "decisions": decisions}
        order = sorted(layers, key=lambda l: (self._LAYER_ORDER.index(l)
                       if l in self._LAYER_ORDER else len(self._LAYER_ORDER), l))
        total = sum(len(layers[l]["decisions"]) for l in order)
        lines = ["# agency — architecture digest", "",
                 f"Every recorded WH(Y) decision as a one-liner ({total} across "
                 f"{len(order)} layers), grouped by architecture layer — each links "
                 "to the spec that established it with one central sentence from that "
                 "spec. Linked specs are **approved**: a spec reaches `/inprogress` "
                 "(and later `/done`) only once its decisions clear the ADR hinge, so "
                 "an `/inprogress` spec is an approved one still shipping its last "
                 "slices. The decision IS what ships — **code is the final "
                 "decision**; the full rationale, neglected alternatives and "
                 "trade-offs live in [`docs/adr/`](docs/adr/). Refreshed on spec-done "
                 "via `adr.architecture(apply=True)`; emitted by the SessionStart "
                 "hook.", ""]
        for layer in order:
            t = layers[layer]
            lines.append(f"## {layer.title()}")
            if t["scope"]:
                lines.append(f"_{t['scope']}_")
            lines.append("")
            if not t["decisions"]:
                lines.append("- (no decisions yet)")
            for d in t["decisions"]:
                if d["spec"]:
                    lines.append(f"- {d['title']} — [`{d['spec']}`]({d['spec']})")
                    if d["sentence"]:
                        lines.append(f'  > "{d["sentence"]}"')
                else:
                    lines.append(f"- {d['title']}")
            lines.append("")
        from agency.capabilities.document._interconnect import stamp_anchor
        body = stamp_anchor("\n".join(lines).rstrip() + "\n", "architecture-digest")
        written = False
        if apply:
            pathlib.Path(out).write_text(body, encoding="utf-8")
            written = True
        return ToolResult.success(data={"path": out, "layers": order,
                                        "decisions": total, "body": body,
                                        "written": written})

    @verb(role="effect")
    def publish(self, theme_id: str, out: str = "", apply: bool = True) -> ToolResult:
        """PUBLISH — project a theme to its ``docs/adr/<layer>.md`` FILE: the
        keep-both file side of `render`. The full file = a Spec-292 anchor +
        DETERMINISTIC frontmatter (kind/layer/title/scope/aggregate-status, no
        timestamp — git history is the clock, so re-publish is byte-idempotent)
        + the rendered canonical WH(Y) body. This is the "append/update the ADR"
        step of the done-cascade; `workflow.mark_done` calls it per affected theme.

        Inputs: theme_id, out (override the theme's path — for tests), apply
                (write the file; else preview the body).
        Returns: ``{theme_id, path, written, content_sha, body}`` or ``{error}``.
        chain_next: adr.architecture(apply=True) to roll the published ADRs up.
        """
        theme = self.ctx.recall_typed(theme_id, "Document")
        if not theme:
            return ToolResult.success(data={"error": f"no theme {theme_id!r}",
                                            "theme_id": theme_id})
        r = self.render(theme_id).data
        if "error" in r:
            return ToolResult.success(data=r)
        layer = theme.get("layer", "")
        children = self.ctx.neighbors(theme_id, "PART_OF", direction="in")
        agg = _aggregate_status([str(c.get("status")) for c in children])
        title = theme.get("title") or f"{layer} decisions"
        fm = ["---", "kind: adr-theme", f"layer: {layer}", f'title: "{title}"']
        if theme.get("scope"):
            fm.append(f'scope: "{theme.get("scope")}"')
        fm += [f"status: {agg}", "---", ""]
        from agency.capabilities.document._interconnect import stamp_anchor
        body = stamp_anchor("\n".join(fm) + "\n" + r["body"] + "\n",
                            f"adr-theme-{layer}")
        path = out or theme.get("path") or f"docs/adr/{_theme_slug(layer)}.md"
        written = False
        if apply:
            import pathlib
            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(path).write_text(body, encoding="utf-8")
            written = True
        return ToolResult.success(data={"theme_id": theme_id, "path": path,
                                        "written": written,
                                        "content_sha": r["content_sha"],
                                        "body": body})

    @staticmethod
    def _strip_anchor(raw: str):
        """Split a leading Spec-292 anchor off a doc body (delegates to the one
        interconnect helper — rule 2) so frontmatter still parses."""
        from agency.capabilities.document._interconnect import extract_anchor
        return extract_anchor(raw)
