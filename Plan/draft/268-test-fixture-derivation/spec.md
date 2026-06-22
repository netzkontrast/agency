---
spec_id: "268"
slug: test-fixture-derivation
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "169"
depends_on: ["169", "196", "147", "149", "259", "269"]
vision_goals: [4]
affects:
  - tests/conftest.py
  - tests/fixtures/
  - tests/test_fixture_derivation.py
---

# Spec 268 — test fixture derivation

## Why

Spec 169 ships CI coverage + flake gates. Test fixtures today are
hand-authored (a fresh Engine + ad-hoc node inserts per test). As the
graph schema grows (Spec 158 schema sweeps, new node kinds per
capability), fixtures rot: a new node kind ships with zero coverage
until someone writes a fixture by hand; meanwhile every existing
fixture interpolates fields that may no longer be required. The
derivation discipline: a canonical fixture set is DERIVED from the
live ontology — every Schema gets a min-fixture (smallest valid
instance) plus an edge-fixture (source + target + edge) — so a new
node kind auto-gets coverage on the same commit that ships it.
Spec 196 BDD scenarios populate from the same derived set, so the
two layers stay in lock-step.

## Done When

- [ ] **`tests/fixtures/derived.py`** generated from ontology Schemas
      on every test session (`conftest.py` autouse fixture).
- [ ] **Per-Schema min-fixture** = smallest valid instance — required
      fields populated from Schema defaults, optional fields omitted.
- [ ] **Per-edge fixture** = source-node + target-node + edge instance
      with realistic ids.
- [ ] **Typed `DerivedFixture` shape**:
      ```python
      class DerivedFixture(TypedDict):
          node_kind: str
          min_instance: dict
          edge_fixtures: list[dict]
          generator_source: str       # ontology spec_id that produced it
          generated_at: str           # body, not prefix
      ```
- [ ] **Spec 196 BDD scenarios use derived fixtures by default** —
      Given/When/Then steps reference `DerivedFixture.min_instance`
      rather than hand-crafted dicts.
- [ ] **CI fails when a Schema lacks a derived fixture** (rule 8) —
      every node kind in the live ontology MUST appear in the derived
      set; missing entries fail the audit.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `set(derived_fixtures.keys()) == set(ontology.node_kinds)`
        (set equality — every Schema covered)
      - every `min_instance` validates against its Schema
        (round-trip — derive → validate must pass)
      - `len(edge_fixtures) >= 1` for every node kind that has
        outbound edges in the ontology
      - re-running the derivation twice produces identical output
        (deterministic) — diff == 0
- [ ] Test: a synthetic new Schema added to the fixture ontology
      auto-gets a min-fixture in the next derive; deleting a Schema
      removes its fixture; round-trip validation passes for all.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ontology adds a new node kind `MusicTrack` with required
        fields {id, title, album_id} and an edge MusicTrack -> Album
When:   pytest session starts and conftest.py runs the derive step
Then:   tests/fixtures/derived.py now contains DerivedFixture{
            node_kind:"MusicTrack",
            min_instance:{id:"t-min", title:"min", album_id:"a-min"},
            edge_fixtures:[{source:"t-min", target:"a-min",
                edge:"BELONGS_TO"}],
            generator_source:"ontology@<sha>"
        }
        AND every existing test that takes `derived_fixture("MusicTrack")`
        works without modification

Given:  PR removes a required field from an existing Schema without
        updating dependent tests
When:   the derive runs and round-trip validation executes
Then:   round-trip succeeds (the min-fixture now needs fewer fields)
        AND tests that hand-set the removed field fail loudly with
        "field X is not in Schema" — caught at fixture build time,
        not at deep-test time

Given:  derive runs twice in the same CI job (cold + warm)
When:   compared
Then:   bit-identical output (deterministic invariant); ordering
        canonicalized by node-kind name
```

## Failure modes (Nygard)

| Failure | Fixture response |
|---|---|
| Schema added without fixture coverage | Audit fails — set equality invariant trips; CI blocks |
| Schema's required field cannot be defaulted | Generator emits `Codes.FIXTURE_GEN_FAILED` with the field named; operator picks a sensible default in a `fixture_defaults` config |
| Edge fixture has no valid source/target | Skip with a recorded warning; the audit reports `edge_uncoverable: [...]` |
| Derive output non-deterministic (timestamp / random in min_instance) | Generator uses deterministic placeholders (`"<kind>-min"`); explicit list of `non_deterministic_fields` per Schema if needed |
| BDD scenario (Spec 196) references a fixture that derived away | Scenario fails fast with a name resolution error |
| Schema changes mid-test-run (rare; concurrent migration) | Derive snapshot taken at session start; per-session immutable |
| LLM-authored Schema doesn't deserialize | Generator rejects with `Codes.SCHEMA_INVALID`; the LLM author re-runs Spec 147 with the validation error feedback |

## Interconnects

- Spec 169 (parent CI gates) — fixture derivation is the per-Schema
  coverage layer the gates enforce.
- Spec 196 (BDD driver impl) — consumes the derived set as scenario
  inputs.
- Spec 149 (derive-doc discipline) — fixtures are a derived surface;
  same discipline.
- Spec 147 (driver) — when an LLM authors a Schema, it ships through
  the driver; the round-trip validation catches bad shapes.
- Spec 259 (derived-doc self-test) — the self-test exercises the
  fixture derivation end-to-end.
- Spec 269 (per-spec Followup derived) — Followup test counts read
  derived fixture counts to stay accurate.
- Drift-derivation extended to test data.

## Open questions

1. **Where do non-derivable fixture details live (e.g. realistic
   business-logic content)?** **Recommend**: `fixture_overrides/<kind>.py`
   — explicit, named, opt-in extensions to the min-fixture; never
   hand-edits to the derived file.
2. **Should derivation run on every pytest invocation, or be
   committed?** **Recommend**: regenerate at session start
   (autouse fixture) AND commit the file (so diffs are reviewable +
   CI sees the artifact); a session-start mismatch trips CI.
3. **Schema versioning across derivation?** **Recommend**: include
   `ontology_schema_version` in `DerivedFixture`; old fixtures
   discarded when the version bumps; per-version snapshots in the
   graph for historical replay.
