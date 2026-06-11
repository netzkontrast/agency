---
spec_id: "177"
slug: plugin-reference-continuous-audit
status: draft
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

- [ ] **Typed audit finding: `RefFinding{file, invariant: str,
      observed: str, expected: str, severity: Literal["error",
      "warn"], doc_source: str}`** — every finding cites both the
      offending file and the reference doc it violates.
- [ ] **Invariant: `set(audited_invariants) ⊇ {plugin_json_shape,
      hooks_matcher_async, mcp_cwd_env, run_hook_polyglot,
      command_frontmatter, marketplace_entry_shape}`** — the set is
      open (new invariants can join as the reference evolves).
- [ ] **Invariant: every audited file resolves a `doc-source`
      marker** (Spec 054 family) — a finding points at a versioned
      reference, never an opinion.
- [ ] **Invariant: the audit is idempotent** — same plugin tree +
      same reference version ⇒ byte-identical findings list across
      runs.
- [ ] **Invariant: derived install-surface files (Spec 175 — slash
      commands, marketplace.json) pass the audit on every install** —
      the regen path satisfies the audit by construction; a divergence
      proves a bug in either side.
- [ ] **Relationship: a malformed `/agency-<skill>.md` (Spec 148)
      trips `command_frontmatter` with severity=error** — proves
      the gate; not pinned to a specific skill.
- [ ] **Failure mode (reference drift):** the
      `working-with-claude-code` skill (the reference source) updates
      → `doc-source` marker hash changes → audit re-runs against the
      new shape; if the plugin lags, audit fails with `severity=warn`
      one cycle (Spec 056 promotion pattern), then `error`.
- [ ] TODO row + drift clean.

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
