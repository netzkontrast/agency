---
spec_id: "177"
slug: plugin-reference-continuous-audit
status: done
state: done
last_updated: 2026-06-10
owner: "@agency"
enhances: "064"
depends_on: ["064", "148", "175", "149"]
vision_goals: [5, 4]
affects:
  - scripts/check-plugin-reference
  - tests/test_plugin_reference_audit.py
---

# Spec 177 — plugin-reference continuous-compliance audit

## Why

Spec 064 (plugin-reference-compliance) brought the plugin to the
superpowers 5.1.0 + episodic-memory 1.4.2 reference patterns
(cross-platform hooks, `hooks.json` matcher, `.mcp.json` cwd, the
`using-agency` meta-skill). But it was a POINT-IN-TIME alignment.
Per the `working-with-claude-code` skill, the plugin reference evolves;
the alignment should be a STANDING audit so the plugin doesn't drift
from current Claude Code conventions as new slash commands (Spec 148)
and a derived install surface (Spec 175) land.

## Done When (measurable invariants — rule 8)

- [x] **Typed audit finding: `RefFinding{file, invariant, observed,
      expected, severity, doc_source}`** — `doc_source` added (additive);
      every finding cites the offending file AND the reference doc.
      `audit_plugin_refs` produces them.
- [x] **Invariant: `set(audited_invariants) ⊇ {plugin_json_shape,
      hooks_matcher_async, mcp_cwd_env, run_hook_polyglot,
      command_frontmatter, marketplace_entry_shape}`** — the OPEN
      `AUDITED_INVARIANTS` tuple registers all six.
      `test_audited_invariants_superset_of_the_baseline_six`.
- [x] **Invariant: every finding cites a `doc-source`** — each
      `RefFinding.doc_source` names the reference doc (never an opinion).
      `test_findings_are_typed_and_cite_a_doc_source`.
- [x] **Invariant: the audit is idempotent** — invariants iterated in
      `AUDITED_INVARIANTS` order, files sorted ⇒ byte-identical findings
      across runs. `test_audit_is_idempotent`.
- [x] **Invariant: derived install-surface files (Spec 175) pass the
      audit** — the live plugin tree audits clean (0 errors, ready).
      `test_live_plugin_tree_passes_the_audit`.
- [x] **Relationship: a malformed command file trips
      `command_frontmatter` with severity=error** —
      `test_findings_are_typed_and_cite_a_doc_source`.
- [ ] **Failure mode (reference drift):** REFINEMENT — the temporal
      `doc-source` hash tracking + warn→error promotion-over-cycles
      (Spec 054/056) is deferred; the audit currently flags at each
      check's assigned severity.
- [x] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  plugin in reference-compliant state; PR adds a new walkable
        skill `develop.estimate` — Spec 175 regenerates
        `/agency-develop-estimate.md` but the template forgot the
        `description` frontmatter field
When:   `scripts/check-plugin-reference` runs in CI
Then:   RefFinding{file=".../agency-develop-estimate.md",
        invariant="command_frontmatter", observed="missing
        `description`", expected="description: required",
        severity="error", doc_source="working-with-claude-code#commands"};
        CI fails the PR

Given:  the `working-with-claude-code` skill is updated upstream
        (a new `hooks.json` field becomes required); the doc-source
        marker hash changes
When:   the next CI run audits
Then:   findings flip `hooks_matcher_async` to severity="warn" for one
        cycle (Spec 056 pattern); the next cycle promotes to "error";
        the plugin's hooks.json must update in between

Given:  malformed `.mcp.json` (missing `env` passthrough block)
When:   audit runs
Then:   RefFinding{invariant="mcp_cwd_env", severity="error"};
        the doc-source pointer names the exact skill section
```

## Failure modes

| Failure | Audit response |
|---|---|
| Malformed command frontmatter | `command_frontmatter` error |
| `.mcp.json` missing env passthrough | `mcp_cwd_env` error |
| `run-hook.cmd` missing platform branch | `run_hook_polyglot` error |
| marketplace.json shape diverges from reference | `marketplace_entry_shape` error |
| Reference upstream updates (skill bumped) | new finding at `warn` one cycle → `error` |
| `doc-source` marker missing on an audited file | Spec 054 hand-off — drift gate fails BEFORE this audit |
| Two reference versions disagree (mid-migration) | audit pins to the doc-source marker; never blends |

## Interconnects

- **UX-onboarding chain** (148/176): audits the new command surface
  + the SessionStart hook shape.
- **Drift-derivation chain** (149/175): audits the derived install
  surface; the regen path satisfies the audit by construction.
- Spec 064 is the parent alignment.
- Spec 170 (doctor) reports `plugin_reference.live_compliance_score`
  (% of invariants passing).
- Spec 175 (install surface derived) is the primary producer of files
  audited here.
- Spec 169 (CI coverage + flake gate) — the audit job participates in
  the standing CI gate.
- Spec 151 (Codes coverage) supplies finding-shape codes if any
  invariant promotes to a typed error.

## Open questions

1. Pin to a Claude Code reference version? **Recommend**: track the
   `working-with-claude-code` skill's documented shape; re-run the
   audit when that skill's doc-source marker hash changes (Spec 054
   family). A pinned version ages immediately; the marker keeps it
   live.
2. Audit cadence — every PR or merge to main only? **Recommend**:
   every PR (the audit is cheap; catches regressions before merge).
3. Reference-update grace period? **Recommend**: one full WARN cycle
   (Spec 056/058 pattern) before promoting a new reference-required
   invariant to error — gives the plugin time to update on each
   upstream change.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Done — Slice 2 (2026-06-26)

The plugin-reference continuous-audit is built and consumed:

- `agency/_plugin_ref_audit.py`:
  - `AUDITED_INVARIANTS` — the OPEN reference-invariant set (the baseline six +
    room to grow).
  - `audit_plugin_refs(root=".")` — a deterministic, idempotent sweep over the
    committed plugin files (`.claude-plugin/plugin.json`, `marketplace.json`,
    `commands/*.md`) producing typed `RefFinding`s, each citing its `doc_source`.
  - `ref_audit_summary(root=".")` — `{audited_invariants, findings, errors,
    warns, ready}`; `ready` iff zero error findings. Live tree: 0 findings.
- `RefFinding` gained `doc_source` (additive default).
- `agency_doctor.plugin_ref_audit` consumes the summary.
- 5 invariant tests in `tests/test_plugin_ref_audit.py` (all green): superset
  of the six, live tree passes, idempotent, malformed command trips error +
  cites doc_source, missing plugin.json field flagged.

**Verdict:** Slice 2 SHIPPED — the audit + all six structural invariants +
doc_source citations + idempotency + doctor consumer; check-drift clean. The
temporal reference-drift warn→error promotion (doc-source hash tracking) is a
noted refinement.

