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
collapsed superseded-history appendix — panel B3). The Definition-of-Done gate
(355) and spec→decision extraction + hints (356) build on this.
"""
from __future__ import annotations

import hashlib

from agency.capability import CapabilityBase, verb
from agency.toolresult import ToolResult

from .ontology import DECISION_SCHEMA, DECISION_STATUS, adr_ontology

# Tokens that mean "no real alternative" — a `neglected` of one of these fails
# WHY-003 (at least one alternative must be documented). The ontology cannot
# catch this (the field is non-empty), so it is `validate`'s job.
_EMPTY_ALTERNATIVES = {"", "none", "n/a", "na", "-", "nil"}

# Dependency edges `adr.link` accepts (SPEC-001-C). SUPERSEDES is NOT here — it
# is the `supersede` verb's job (it reuses the core `SUPERSEDED_BY` edge).
_LINK_TYPES = {"DEPENDS_ON", "RELATES_TO", "REFINES", "PART_OF"}
# Acyclic-by-intent edges — a cycle in these is the SPEC-001-C DEP-001 error.
_ACYCLIC = {"DEPENDS_ON", "REFINES"}


def _theme_slug(layer: str) -> str:
    return "adr-" + "".join(c if c.isalnum() else "-" for c in layer.lower()).strip("-")


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

    # ── Slice 2 — read / update / link / supersede / theme_status / impact / render

    def _why_fields(self) -> list[str]:
        return [f for f in self._decision_schema().get("properties", {})
                if f != "status"]

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
               benefits: str = "", tradeoffs: str = "",
               proposed_by: str = "") -> ToolResult:
        """UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y)
        elements incrementally (the DOMAIN mutator; never reach into `manage` for
        an ADR). Only the NON-empty args are written, so a partial completion
        leaves the rest untouched (the draft→complete→approve lifecycle, Spec 356).
        Bi-temporal: a revision with a stable id — append-only revision history is
        `supersede`'s job, not a status flip.

        Inputs: decision_id (str), status (the decision_status enum), and any WH(Y)
                element to (over)write; empty = leave unchanged.
        Returns: ``{id, updated: [field…]}`` or ``{error}`` (e.g. an out-of-enum
                 status the ontology rejects).
        chain_next: adr.validate(id); adr.theme_status(theme_id) to see the roll-up.
        """
        if not self.ctx.recall_typed(decision_id, "Decision"):
            return ToolResult.success(data={"error": f"no decision {decision_id!r}",
                                            "decision_id": decision_id})
        changes = {k: v for k, v in {
            "status": status, "context": context, "facing": facing,
            "decision": decision, "neglected": neglected, "benefits": benefits,
            "tradeoffs": tradeoffs, "proposed_by": proposed_by}.items() if v}
        if not changes:
            return ToolResult.success(data={"id": decision_id, "updated": []})
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
        counts: dict[str, int] = {}
        for s in statuses:
            counts[s] = counts.get(s, 0) + 1
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
        active = sorted((c for c in children
                         if str(c.get("status")) != "superseded"),
                        key=lambda c: c.get("id", ""))
        superseded = sorted((c for c in children
                             if str(c.get("status")) == "superseded"),
                            key=lambda c: c.get("id", ""))
        body = self._render_body(theme, active, superseded)
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.ctx.update(theme_id, {"content_sha": sha})
        return ToolResult.success(data={"id": theme_id, "path": theme.get("path"),
                                        "content_sha": sha, "active": len(active),
                                        "superseded": len(superseded), "body": body})

    def _render_body(self, theme: dict, active: list[dict],
                     superseded: list[dict]) -> str:
        title = theme.get("title") or f"{theme.get('layer', '')} decisions"
        lines = [f"# {title}", ""]
        for d in active:
            lines += [
                f"## {d.get('decision')}", "",
                f"In the context of {d.get('context')}, facing {d.get('facing')}, "
                f"we decided for {d.get('decision')} and neglected "
                f"{d.get('neglected')}, to achieve {d.get('benefits')}, accepting "
                f"that {d.get('tradeoffs')}.",
                f"_status: {d.get('status')}_", "",
            ]
        if superseded:
            lines += ["## Superseded / history", ""]
            for d in superseded:
                fwd = self.ctx.neighbors(d.get("id"), "SUPERSEDED_BY",
                                         direction="out")
                by = fwd[0].get("id") if fwd else "—"
                lines.append(
                    f"- {d.get('id')} · {d.get('decision')} · superseded-by {by}")
        return "\n".join(lines)
