<!-- agency steward handover — read this first next run -->
# Steward Handover 005 — 2026-06-19

## What shipped this run

**Spec 153 Slice 4 — engine-load intersection gate (dormant_schemas).**

Closed the recurring trap: a schema file present on disk but whose owning
capability never declared `artefact_schemas` was previously counted as
`covered` — the glob found the file, but the engine never loaded it.
This has bitten three consecutive Slice 6 batches (develop, document, skills
caps). The gate makes it mechanical:

- **`engine_loaded_schema_titles(merged_schemas) → set[str]`** — new function
  in `agency/_schema_coverage.py`. Extracts PascalCase labels for every schema
  the engine actually loaded from `e.ontology.schemas` (handles all three
  value forms: dict-with-title, dict-without-title fallback to key, list-form
  inline declared with `OntologyExtension.schemas = {"foo-bar": ["field"...]}`).
  Mirrors `schema_labels()` extraction logic for symmetry.

- **`audit_schemas()` gains `engine_loaded_titles: set[str] | None = None`** —
  when supplied: `covered = schemas ∩ ontology ∩ engine_loaded`;
  `dormant_schemas = (schemas ∩ ontology) − engine_loaded`. Backwards-compatible
  (old callers without the param see `dormant_schemas = set()`).

- **`CoverageReport.dormant_schemas: set[str]`** — new field; empty = clean;
  non-empty = schema on disk matching ontology label but cap undeclared.

- **`agency_doctor.schema_coverage.dormant_schemas`** — live sorted list now
  included in the doctor payload. The gate is surfaced at runtime without
  running the CLI.

- **2 new Gherkin acceptance scenarios** (total 24 in `template_schema.feature`):
  (1) unit trap test — a fabricated cap with schema file but no
  `artefact_schemas` → "Dormant" appears in `dormant_schemas`, not in `covered`;
  (2) live zero-dormant assertion — boots Engine, calls
  `engine_loaded_schema_titles()`, passes to `audit_schemas()`, asserts
  `dormant_schemas == set()`.

- **`scripts/check_schema_coverage.py`** (re-export shim) updated to include
  `engine_loaded_schema_titles` in the `from agency._schema_coverage import`
  surface.

- **`agency/_substrate_tools.py`** (doctor) updated to call the new extraction
  path and surface `dormant_schemas` in the `schema_coverage` health block.

- **Pre-existing doc drift** (6 reference docs) re-stamped via
  `scripts/check-doc-drift --update` (not caused by this run).

## Evidence

- RED→GREEN: 2 new scenarios, all 24 `test_template_schema` scenarios green.
- Invariant: 36 acceptance scenarios across touched files (template_schema +
  doctor) passed.
- `scripts/check-drift` → **NO DRIFT**.
- `scripts/check-doc-drift` → **NO DOC DRIFT**.
- TODO.md Spec 153 row updated (Slice 4 SHIPPED); spec.md Followup appended.
- Reflections: `reflection:d9230733` (engine_loaded extraction approach),
  `reflection:57c117de` (three-form symmetry invariant).
- PR #182 created — https://github.com/netzkontrast/agency/pull/182
  (CI in_progress at handover write time).

## Pre-existing debt noted (NOT caused this run)

- 6 reference docs went stale prior to this run
  (`docs/README.md`, `docs/examples/cookbook.md`,
  `docs/vision/reference/{README,drivers,engine,overview}.md`).
  All re-stamped; debt closed in this commit.

## Next 3 candidates (ranked)

1. **Schema backfill — discover wave + 2 substrate (Spec 153 Slice 6 cont.)**
   Current coverage: 33/89 = 0.371. Next highest-impact uncovered labels
   from `priority_uncovered` (run `agency_doctor schema_coverage` to confirm
   live ranking before starting):
   - `FeasibilitySignal`, `IntentRefinement`, `ScopeBoundary` — discover cap
     (already has `artefact_schemas`; just need the JSON files).
   - `PromptFramework` — prompt cap (already has `artefact_schemas`).
   - `Template` — document cap (already has `artefact_schemas`).
   Pattern: derive required fields from the cap module, add `schemas/NAME.json`
   with `title`, add 2 Gherkin scenarios (unit + live), update baseline file.
   **Lowest risk; highest cumulative coverage gain.**

2. **Spec 153 Slice 5 — deferred-tag gate (auto-trim baseline)**
   The baseline file (`Plan/_planning/schema-coverage-baseline.txt`) is
   manually trimmed when labels graduate from uncovered → covered. Slice 5
   automates: `check_schema_coverage --strict --baseline` already flags
   `fixed_uncovered`, but there's no CI auto-trim. Add a `--fix-baseline`
   flag that rewrites the baseline in-place (remove fixed, warn on new).
   Medium effort. Would eliminate the manual "trim 5 entries each batch" step.

3. **FastAPI typed-read surface (Goal 5/7, Spec 330 follow-up)**
   Architecturally significant capstone; needs a human-reviewed spec for
   server boundary, auth model, and lifecycle integration before implementation
   begins. Still the right long-term direction the typed-entity program points
   at. Do NOT start without explicit human sign-off on the design.

## Proposed amendment

**Add the `dormant_schemas` check to `scripts/check-drift`** so the gate
fires on every PR even when the CLI isn't invoked. Current state: the gate
runs only when the user calls the doctor or the schema CLI. Proposed addition
to `scripts/check-drift`:

```python
from agency.engine import Engine
from agency._schema_coverage import (
    audit_schemas, truly_inline_schemas, engine_loaded_schema_titles)

e = Engine(":memory:")
merged = dict(e.ontology.schemas)
e.memory.close()
inline = truly_inline_schemas(root, merged)
loaded = engine_loaded_schema_titles(merged)
rep = audit_schemas(root, ontology_labels=set(e.ontology.nodes),
                    ontology_schemas=inline, engine_loaded_titles=loaded)
if rep.dormant_schemas:
    print(f"DRIFT: {len(rep.dormant_schemas)} dormant schemas: "
          f"{sorted(rep.dormant_schemas)}")
    sys.exit(1)
```

This would have caught the develop/document/skills trap automatically on
each PR, before the backfill CI run exposed it.

## Pillar gate (held — unchanged from run 004)

Intent (intent.json/invocation.json covered) · Capability (skill.json/phase.json
covered) · Lifecycle (lifecycle.json covered) · Memory (session.json/event.json
covered).

Schema coverage: 33/89 = 0.371. Dormant schemas: 0 (gate enforced).
Drift: clean. Doc-drift: clean. 24 acceptance scenarios green.
