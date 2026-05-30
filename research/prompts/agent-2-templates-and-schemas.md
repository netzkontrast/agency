# Agent 2 — Templates & Schemas expansion

**Output dir:** `research/templates-and-schemas/`
**Critical-thinking method:** completeness/gap analysis + SCAMPER.

Read `research/JULES_RESEARCH_PROTOCOL.md` and `research/SOURCES.md` first and obey
them. Satisfy Gate 1 (full recursive ingestion + `_ingest.md` ledger) before any
finding.

## Scope to ingest (read every file)

- **Work repo (PR1):** `agency/templates.py`, `agency/ontology.py`, every
  capability in `agency/capabilities/**` and its `OntologyExtension`, every verb
  that returns an artefact, the `validate`/`validate_schema` paths in
  `agency/memory.py`, and the tests that exercise templates/schemas.
- **Sources (read-only):** `the-agency-system` → `templates/`,
  `Plan/harness/VOCABULARY.md`, any spec defining artefact shapes;
  `bitwize-music` → its handler/skill artefact shapes. Use what you can clone.

## Method

Build the **artefact×capability matrix**: every artefact kind PR1 produces and
every verb that emits one. For each, mark whether it has (a) a named Template and
(b) a strict Schema. The gaps are the work. Then SCAMPER the template library
(Substitute/Combine/Adapt/…) against the richer prior art in the sources.

## Deliverables (concrete artifacts, every claim cited)

- `research/templates-and-schemas/_ingest.md` — the ingestion ledger.
- `research/templates-and-schemas/FINDINGS.md` — the gap matrix (artefact kind ·
  has template? · has schema? · cited `path:line`).
- `research/templates-and-schemas/templates-catalogue.md` — concrete proposed
  Templates for the uncovered artefacts (e.g. review-findings, plan, debug-report,
  baseline-report, branch-outcome, delegation-reduction, gate-evidence,
  reflection-digest). Each: field list, the `string.Template`-style body, and one
  rendered example.
- `research/templates-and-schemas/schemas-catalogue.md` — a strict **Schema** per
  artefact kind (required fields) AND enriched **input schemas** for verbs
  (param descriptions / enums / examples) to make `get_schema` self-documenting.
  Show how each pairs with its Template (the generate↔validate loop).

Publish one ready PR into `claude/extract-agency-plugin-o4JRc` per the protocol.
