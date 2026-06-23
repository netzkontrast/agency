---
name: adr
description: "Use when an architectural decision must be RECORDED as a first-class,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# adr capability



## When to use

- A spec or design makes a choice whose rationale would otherwise be lost
- "Why did we decide X (and not Y)?" needs a durable, traversable answer
- An ADR must be validated against the WH(Y) format before approval

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `approve` | act | APPROVE — the DoD hinge (SPEC-001-E pre-approval gate). | [details](references/approve.md) |
| `architecture` | act | ARCHITECTURE — rebuild the shorthand architecture digest: every recorded WH(Y) decision as a ONE-LINER, grouped by architecture layer, rolled up from the durable thematic ADRs (``docs/adr/<layer>.md``). | [details](references/architecture.md) |
| `catalogue` | transform | CATALOGUE — the "handful of ADRs" index (SPEC-001-B minimalism): every theme + its `PART_OF` decision counts grouped by status. | [details](references/catalogue.md) |
| `dod_check` | transform | DOD_CHECK — run the ported SPEC-001-E Definition-of-Done criteria over a Decision (pure compute; never flips status). | [details](references/dod_check.md) |
| `draft` | act | DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF`` the theme, SERVING the intent (SPEC-001-A). | [details](references/draft.md) |
| `extract_decisions` | act | EXTRACT_DECISIONS — surface a spec's key decisions as WH(Y) candidates and (``apply=True``) draft them as ``proposed`` ``Decision``s that ``REFINES`` the spec. **Decidable-first** (no API key): a canonical WH(Y) statement is parsed verbatim (SPEC-001-A), else the ``## Design`` cue sentences + ``## Why``/``## Failure modes`` sections are mined. | [details](references/extract_decisions.md) |
| `hints` | transform | HINTS — the payoff: at implementation start, project the spec's **approved** decisions (+ their depth-1 ``DEPENDS_ON`` neighbours) into a compact, token-BOUNDED architecture-hint block — *decisions and their consequences*, not the spec re-stated (the minimum an implementer needs to not contradict an approved decision). | [details](references/hints.md) |
| `impact` | transform | IMPACT — what ``DEPENDS_ON`` / ``REFINES`` / ``PART_OF`` this decision, to ``depth`` hops (SPEC-001-C ``adr impact``). | [details](references/impact.md) |
| `link` | act | LINK — add a typed SPEC-001-C dependency edge between two Decisions. | [details](references/link.md) |
| `publish` | effect | PUBLISH — project a theme to its ``docs/adr/<layer>.md`` FILE: the keep-both file side of `render`. | [details](references/publish.md) |
| `read` | act | READ a ``Decision``'s current WH(Y) fields + status (the domain read — no need to reach into the generic `manage` tool for an ADR). | [details](references/read.md) |
| `render` | act | RENDER — project a theme's **live** decisions into a markdown body and stamp the theme ``Document``'s ``content_sha`` (graph-side projection; the file round-trip is `document.sync`'s job, keep-both — Spec 292). | [details](references/render.md) |
| `review_sweep` | effect | REVIEW_SWEEP — cadence governance (Spec 355 S2, SPEC-001-A): flip every live ``approved``/``implemented`` decision whose ``next_review`` date has lapsed (< today) to ``expired`` — a legal `decision`-machine transition. | [details](references/review_sweep.md) |
| `spec_decisions_ready` | transform | SPEC_DECISIONS_READY — the /open→/inprogress predicate (358). | [details](references/spec_decisions_ready.md) |
| `supersede` | act | SUPERSEDE — the SPEC-001-C automatic actions: mint a replacement ``Decision`` (status ``proposed``) ``PART_OF`` the same theme, flip the old one to ``superseded``, and write the forward reference (the core ``SUPERSEDED_BY`` edge). | [details](references/supersede.md) |
| `theme` | act | THEME — get-or-create a thematic-living ADR for one architecture ``layer`` (the ported Master ADR). | [details](references/theme.md) |
| `theme_status` | transform | THEME_STATUS — the SPEC-001-D aggregate status DERIVED from the theme's ``PART_OF`` children (never stored — rule 8). | [details](references/theme_status.md) |
| `update` | act | UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y) elements + governance incrementally (the DOMAIN mutator; never reach into `manage` for an ADR). | [details](references/update.md) |
| `validate` | transform | VALIDATE — run the decidable WH(Y) rules over a Decision; return findings + an ``ok`` flag. | [details](references/validate.md) |

## Example

```bash
await call_tool('capability_adr_approve', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Burying a decision in spec prose where it is lost at implementation time → draft it
- Hand-writing a Decision via `manage.create` without the WH(Y) discipline → use adr.draft
- Putting implementation detail in the decision → that belongs in the spec it REFINES

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`adr-usage`** (usage): use-transform → use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'adr-usage', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_adr_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_adr_approve", {"intent_id": iid})
await call_tool("capability_adr_architecture", {"intent_id": iid})
await call_tool("capability_adr_catalogue", {"intent_id": iid})
await call_tool("capability_adr_dod_check", {"intent_id": iid})
await call_tool("capability_adr_draft", {"intent_id": iid})
await call_tool("capability_adr_extract_decisions", {"intent_id": iid})
```

More verbs: `capability_adr_hints`, `capability_adr_impact`, `capability_adr_link`, `capability_adr_publish`, `capability_adr_read`, `capability_adr_render`, `capability_adr_review_sweep`, `capability_adr_spec_decisions_ready` …
