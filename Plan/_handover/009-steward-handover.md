# Steward Handover 009 — 2026-06-21

## What shipped this run

**Spec 322 Slice 3 / Spec 323 — `guided-discovery` authored discipline**

The clarity gate (`discover.clarity_gate`, Spec 322 Slice 2) is now wired as a
structural property of the discovery walk, not a reviewer's hope.

### Key changes

- `agency/capabilities/discover/ontology.py`: Added `GUIDED_DISCOVERY_SKILL`
  (7-phase authored discipline dict) registered in `discover_ontology` via
  `skills={"guided-discovery": GUIDED_DISCOVERY_SKILL}`.
  - Phase 7 ("decide") carries `gate="computed"` + `gate_verb="clarity_gate"`.
  - Per Spec 081: authored `ontology.skills` suppresses the derived
    `discover-usage` walk — the discipline is the only registered skill.
- `tests/acceptance/features/guided_discovery_skill.feature` (new, 6 scenarios):
  parse-clean · kind=discipline · 7 phases with produces · contiguous indices ·
  decide/computed/clarity_gate gate · engine ontology registration.
- `tests/acceptance/test_guided_discovery_skill.py` (new): pytest-bdd steps.
- `tests/acceptance/features/discover.feature` + `test_discover.py`: `_usage_walk`
  now asserts `"guided-discovery"` (authored) not `"discover-usage"` (suppressed).
- `skills/discover/SKILL.md`: auto-regenerated (`python -m agency.install`).
- `TODO.md` + `Plan/322-intent-clarity-score-gate/spec.md`: updated per rule 4.

### Test results (local)

- 13/13 Spec 322 acceptance scenarios green
- 31/31 discover acceptance scenarios green (regression fix included)
- `scripts/check-drift`: NO DRIFT
- `scripts/check-doc-drift`: NO DOC DRIFT

### PR

**PR #263**: https://github.com/netzkontrast/agency/pull/263
Branch: `claude/affectionate-fermi-un98lf`

## Lessons

1. **Spec 081 authored-override silences the derived walk** — when `ontology.skills`
   is non-empty, `capability.py:784` skips generating `<cap>-usage`. This is the
   correct contract, but tests asserting the derived skill name regress immediately
   when an authored discipline is added. Update the expectation alongside the
   implementation (not after CI catches it).
2. **`gate: "computed"` requires `gate_verb`** — `_skill_parse.py` validates this
   pair. The discipline dict must carry both fields on the final phase or
   `parse_skill` returns a failure.
3. **`applies_when` goes in `extras`** — the `Skill` dataclass stores it there;
   `parse_skill` doesn't fail on unknown top-level keys but they land in extras.
   Verified: the skill parses clean with `applies_when` as a top-level key.

## Next candidates

In priority order:

1. **Spec 350 Slice 3** — graph FilterProfile override: a user-authored
   `FilterProfile` node in the graph overrides the config-registry defaults
   (Spec 350 Slice 2 shipped the config registry). This completes the filter
   personalisation loop.
2. **Spec 311 Slice 2** — `discover.clarify` wet Driver `ClarifySpec` +
   grounding-sharp options. Depends on Spec 147 Slice 2 (Managed-Agents
   dispatch_session bridge) for the AnthropicDriver wet path.
3. **Spec 147 Slice 2** — Managed-Agents `dispatch_session` bridge. The
   prerequisite for all wet-driver (real LLM) slices (311 Slice 2, 317 Slice 2,
   etc.). High-leverage unblock.
4. **Spec 146 Slice 2.3** — reachability analysis: restrict the prefix lint
   scan to functions reachable from substrate-tool prefix builders. Re-promoted
   gate (2026-06-20).

## Intent

Active intent: `intent:6541264e`
