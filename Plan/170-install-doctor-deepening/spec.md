---
spec_id: "170"
slug: install-doctor-deepening
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "055"
depends_on: ["055", "065", "147", "148"]
vision_goals: [5, 3]
affects:
  - agency/_doctor.py
  - tests/test_doctor_deepening.py
---

# Spec 170 — agency_doctor deepening

## Why

Spec 055 (pipx-only-install) + Spec 065 (pipx-direct-doctrine) settled
the install path and gave `agency_doctor` install_method reporting. But
as the enhancement waves add capabilities (AnthropicDriver, server-side
tools, Managed Agents), `doctor` needs to report their readiness so a
user/agent knows what's wired BEFORE invoking. A deep doctor is the
first-touch diagnostic the UX chain (Spec 148) leans on.

## Done When (measurable invariants — rule 8)

- [ ] **Typed report shape: `DoctorReport{sections: list[Section]};
      Section{name, fields: list[Field]}; Field{key, value, ready: bool,
      hint: str | None, source: Literal["env", "extra", "graph",
      "registry"]}`** — uniform across every section.
- [ ] **Invariant: every `ready=False` field carries a non-empty
      `hint`** — the pipx-HINT pattern from Spec 065 generalizes.
- [ ] **Invariant: every field's `source` resolves** — `extra` →
      `pyproject.toml`; `env` → the named env var; `graph` → a live
      node label; `registry` → a live capability/verb. A stale source
      fails `Codes.DOCTOR_SOURCE_STALE`.
- [ ] **Invariant: report regen is idempotent** — same DB hash + same
      env ⇒ byte-identical report (Spec 146 prefix discipline applies
      to doctor's response).
- [ ] **Relationship: `set(doctor.sections.keys()) ⊇ {anthropic_driver,
      managed_agents_capable, prefix_stability, codes_coverage,
      schema_coverage, analyze_extras, drift}`** — the enhancement-era
      surface is reported; new sections can be added without breaking
      consumers (open-set discipline).
- [ ] **`/agency-doctor` slash command** (Spec 148 family) renders the
      report in a single-screen brief (≤ 1024 tokens for the brief
      tier; full available on demand).
- [ ] **Failure mode (doctor itself):** a section that raises during
      probe (e.g. graph query timeout) yields `ready=False,
      value=None, hint="probe failed; rerun with --verbose"` + a
      `Codes.DOCTOR_PROBE_FAILED` Reflection — never crashes the
      whole report.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  fresh install via pipx; ANTHROPIC_API_KEY not set;
        `[analyze]` extra installed; networkx missing from
        `[analyze]` (Spec 167 not yet shipped)
When:   `agency_doctor` runs (or `/agency-doctor`)
Then:   DoctorReport.sections includes:
          anthropic_driver: ready=False, hint="set ANTHROPIC_API_KEY"
          analyze_extras: ready=True, value={ruff, bandit, radon}
          analyze_extras.networkx: ready=False, hint="pipx inject
             agency networkx"
          prefix_stability: ready=True, drift_bytes=0
        AND envelope.prefix is byte-identical to a prior doctor call
        (cache held)

Given:  same env, graph DB locked by another process
When:   doctor runs
Then:   the drift section returns ready=False + hint="another agency
        process is holding .agency/session.db" + DOCTOR_PROBE_FAILED
        Reflection; OTHER sections still report (no crash)
```

## Failure modes

| Failure | Doctor response |
|---|---|
| Probe section raises | `ready=False` + hint + Reflection; other sections still report |
| Source resolves to a stale name | `DOCTOR_SOURCE_STALE`; drift gate fails |
| ANTHROPIC_API_KEY set but org has Fable 5 ZDR | `managed_agents_capable.ready=False` + hint per claude-api skill |
| Schema/Codes coverage < live registry | `ready=False` + pointer at the missing entries (Spec 151 sibling) |
| Slash command renders > brief budget | doctor truncates body, keeps prefix — Spec 146 envelope guarantees no partial-cache |

## Interconnects

- **UX-onboarding chain** (148/176): doctor is the first-touch
  diagnostic; SessionStart can call it during onboarding.
- **LLM-driver chain** (147): reports `anthropic_driver` +
  `managed_agents_capable` (the Driver readiness consumer).
- **Output-budget chain** (146): doctor's report itself honors the
  envelope; brief-tier ≤ 1024 tokens.
- **Drift-derivation chain** (149/175): every field derived; the
  install surface consumes the same source set.
- Spec 169 (CI coverage gate) — doctor reports `coverage.live` per
  capability.
- Spec 161 (discovery rank) reports `rerank_available` here.
- Spec 162 (skills llm_select) reports `llm_select_available` here.
- Spec 151 (Codes coverage) supplies `DOCTOR_SOURCE_STALE` +
  `DOCTOR_PROBE_FAILED`.
- Spec 177 (plugin-reference audit) gates the `/agency-doctor`
  command's frontmatter shape.

## Open questions

1. One doctor or per-extra doctors? **Recommend**: one, sectioned —
   matches the single `agency_doctor` surface users already know;
   sections are open-set (rule 5).
2. Render format — JSON, markdown, or both? **Recommend**: JSON is the
   wire shape (machine-readable); the slash command renders markdown
   on demand from the same JSON (Spec 060 template pattern).
3. Cache doctor result? **Recommend**: 60s session-scoped TTL keyed on
   (DB hash + env hash + pyproject hash); a re-call within the TTL
   returns the cached report (Spec 146 prefix stability).
