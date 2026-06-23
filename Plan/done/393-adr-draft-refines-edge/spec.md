<!-- agency-node: spec-393 -->
---
spec_id: "393"
slug: adr-draft-refines-edge
status: done
state: done
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [4, 9]
depends_on: ["354", "356", "358"]
affects:
  - agency/capabilities/adr/_main.py    # draft(): create the REFINES edge when a spec is named
domain: adr / workflow / dormant-edge
wave: agency-self-teaching
---

# Spec 393 — adr.draft creates the REFINES edge (close the ADR-hinge gap)

> Found by the Agency Self-Teaching Loop's DEEP-chain verifier (Pass 3, Chain 3).

## Problem — the FK-prop vs idle-edge anti-pattern

`adr.spec_decisions_ready` (the `/open→/inprogress` hinge, Spec 358) is contractually
"≥1 `Decision` **REFINES** the spec AND every such decision is `approved`" — it traverses
the **`REFINES` edge**. But `adr.draft(spec=<doc id>)` only stored `spec` as a node
**PROPERTY** and linked `PART_OF` the theme; it never created the `REFINES` edge. So a
decision drafted+approved by hand was **invisible to the gate**: `spec_decisions_ready`
returned `{ready: false, reason: "no-decisions"}` and `workflow.begin_impl` stayed blocked,
even with an approved decision present. The two ADR-hinge lanes never converged — only
`extract_decisions(apply=True)` created the edge, and it requires an ingested spec body.

This is exactly the repo's documented **"declare an edge ⇒ traverse it; FK-prop +
Python-filter is the anti-pattern"** dormant-surface rule (CLAUDE.md field-tested
heuristics) — written on one side, read on the other.

## Approach (one edge, mirroring extract_decisions)

In `adr.draft`, after recording the Decision and linking `PART_OF`, when `spec` is given
and resolves (via the existing `_resolve_spec`, which accepts a Document id OR a
frontmatter `spec_id`), create `link(decision, doc_id, "REFINES")` — the same edge
`extract_decisions` writes. Return the resolved `refines` target. No other change; the
`spec` FK property stays (it renders the Source link in the ADR body).

## Acceptance

```gherkin
Scenario: a manually drafted+approved decision satisfies the ADR hinge
  Given a spec Document and a theme
  When I adr.draft a decision with spec set to that Document
  Then the decision REFINES the spec (an edge, not just a property)
  And adr.spec_decisions_ready no longer reports "no-decisions"
  And after owner approval the hinge reports ready: true
```

## Decisions (WH(Y))

- **D1 — Write the REFINES edge at draft time, not only via extract.** The hinge reads the
  edge; the manual lane must write it for the two lanes to converge. WHY: a gate that an
  approved decision cannot satisfy is a dead gate (the dormant-surface anti-pattern).
- **D2 — Keep the `spec` FK property too.** It renders the ADR Source link + central
  sentence. The edge is for traversal, the property for rendering — both, not either.
