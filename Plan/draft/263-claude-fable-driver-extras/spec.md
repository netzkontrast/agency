---
spec_id: "263"
slug: claude-fable-driver-extras
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "147"
depends_on: ["147", "256", "201", "170", "146", "257"]
vision_goals: [3]
affects:
  - agency/_drivers/_anthropic.py
  - tests/test_fable_driver.py
---

# Spec 263 — Claude Fable 5 driver extras

## Why

Per `claude-api` skill, Claude Fable 5 (`claude-fable-5`) is
Anthropic's most capable widely-released model and the natural target
for high-leverage classifier + planning loops in the agency. Its
request surface differs sharply from the Opus family:

- protected thinking is ALWAYS ON (omit `thinking` entirely;
  `{type:"disabled"}` → 400)
- no `temperature`, `top_p`, `top_k` (sampling params return 400)
- 30-day data retention REQUIRED (ZDR orgs are rejected at request
  time with a typed retention error)
- ~30% more tokens than the Opus tokenizer (re-count via Spec 201)
- `task_budget` available via beta `task-budgets-2026-03-13` for
  agentic loops
- assistant prefill is REJECTED

Without explicit Fable 5 support, every verb that opts into Fable gets
silent 400s the first time it's invoked. This spec lands the typed
surface so opt-in is one config flag, not a debug session.

## Done When

- [ ] **Model selector includes `claude-fable-5`** + `claude-mythos-5`
      (Project Glasswing) as first-class options in
      `AnthropicDriver(model=...)`. Default remains
      `claude-opus-4-8`; Fable 5 is opt-in.
- [ ] **Fable-specific request shape enforced** — when
      `model.startswith("claude-fable")` or `model.startswith("claude-mythos")`:
      - omit `thinking` from the request payload (never send
        `{"type":"disabled"}`)
      - strip `temperature`, `top_p`, `top_k` from any caller-passed
        kwargs (warn once; the params silently work nowhere on Fable)
      - reject `messages[-1].role == "assistant"` (no prefill) with
        a typed `DriverError.BAD_REQUEST{detail:"prefill_rejected"}`
- [ ] **Retention pre-flight** — before any Fable 5 request, check
      `agency_doctor.anthropic_driver.retention_meets_fable_5`. If
      False, return `DriverError.BAD_REQUEST{detail:"retention"}`
      WITHOUT calling the SDK.
- [ ] **Task Budgets (beta `task-budgets-2026-03-13`)** — for agentic
      loops on Fable, the driver accepts `task_budget={...}` and
      forwards via the beta header; `agency_doctor` reports
      task-budget readiness.
- [ ] **`agency_doctor` (Spec 170) reports Fable readiness**:
      `{fable_available: bool, retention_meets_fable_5: bool,
      task_budgets_enabled: bool, model_ids_resolved: [...]}`.
- [ ] **Refusal fallback to Opus 4.8 by default (Spec 256 path)** —
      the Fable default fallback chain is `["claude-opus-4-8"]`;
      callers override via config.
- [ ] **Token re-baselining via Spec 201** — Fable usage values are
      re-counted with the Fable tokenizer (~30% delta vs Opus); both
      counts stored so the cost delta is observable.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - any request with `model.startswith("claude-fable")` MUST NOT
        contain `thinking`, `temperature`, `top_p`, `top_k`,
        `assistant_prefill`
      - Fable token count `>= 1.20 * Opus token count` for the same
        message text (rough ~30% delta; relationship not snapshot)
      - `fable_available == False ⇒ Fable requests rejected pre-flight`
      - first Fable refusal in a session routes through Spec 256
        fallback; if `fallback_used` event fires, the wrapping verb
        sees a successful completion, not an error
- [ ] Test: Fable request shape correct (mocked) — no forbidden
      params, no `thinking` block; ZDR org refused cleanly with
      typed retention error; assistant prefill rejected; task_budget
      header forwarded when set.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  agency_doctor reports {fable_available:True,
        retention_meets_fable_5:True, task_budgets_enabled:True}
        and caller invokes driver.complete(model="claude-fable-5",
        temperature=0.7, top_p=0.9, messages=[...], task_budget={...})
When:   driver builds the SDK request
Then:   payload contains model="claude-fable-5", messages, task_budget
        AND payload does NOT contain temperature, top_p, top_k, thinking
        AND a one-time WARN reflection records "stripped sampling
        params on Fable 5"
        AND beta header includes task-budgets-2026-03-13

Given:  ZDR org (retention_meets_fable_5: False)
When:   any caller requests model="claude-fable-5"
Then:   driver returns Result.failure(DriverError.BAD_REQUEST{
        detail:"retention", model:"claude-fable-5"}) BEFORE any
        SDK call — never burns a request to discover the org constraint
        AND agency_doctor's report is the canonical diagnostic source

Given:  Fable 5 returns stop_reason: "refusal", category: "cyber",
        billed_tokens: 0 (pre-output)
When:   Spec 256 fallback chain ["claude-opus-4-8"] runs
Then:   Opus 4.8 serves the request; response.model == "claude-opus-4-8"
        AND DriverEvent("fallback_used", requested="claude-fable-5",
        served="claude-opus-4-8") recorded
        AND token counts include both Fable estimate + Opus actual so
        the ~30% delta is observable
```

## Failure modes (Nygard)

| Failure | Driver response |
|---|---|
| Caller passes `temperature` on Fable 5 | Strip silently after one-time WARN reflection; never forward (avoids 400) |
| Caller passes `thinking={"type":"disabled"}` on Fable 5 | Strip the thinking block entirely; record reflection (Fable always-on protected thinking) |
| ZDR org tries Fable 5 | Pre-flight `BAD_REQUEST{detail:"retention"}` — never reaches SDK |
| Assistant prefill in messages on Fable 5 | Pre-flight `BAD_REQUEST{detail:"prefill_rejected"}` |
| `task-budgets-2026-03-13` beta unavailable | Forward without the header; record reflection; the budget becomes advisory |
| Fable 5 refuses → Opus 4.8 also refuses | Spec 256 `REFUSAL_EXHAUSTED`; observability records the full chain |
| Token count diverges from API count by > 35% | Spec 201 alarm — tokenizer estimate has regressed |
| Model deprecation (Fable 5 → Fable 6) | Single-config-constant default model; opt-in `pin_model_version=True` keeps reproducibility per Spec 147 §open-question 3 |

## Interconnects

- Spec 147 (parent driver) — this extends with Fable-specific surface.
- Spec 256 (refusal/fallbacks) — Fable's default fallback chain lives
  here; refusal handling is shared.
- Spec 201 (token counter API) — Fable usage re-counted authoritatively.
- Spec 170 (doctor) — Fable readiness report consumer.
- Spec 146 (output-prefix) — prefix discipline is model-agnostic;
  Fable's larger tokenizer is a body concern, not a prefix concern.
- Spec 257 (managed cache proof) — Fable composes with Managed-Agents;
  prefix stability across the model swap is verified.
- **LLM-driver chain** — Fable surface completion.

## Open questions

1. **Default model — Fable 5 or Opus 4.8?** **Recommend**: keep Opus
   4.8 as default; Fable 5 is opt-in via `model="claude-fable-5"` or
   config flag. Cost + retention requirements make Fable inappropriate
   as a quiet default.
2. **Should `claude-mythos-5` share the Fable request shape?**
   **Recommend**: yes — same `claude-fable-*`/`claude-mythos-*` detection
   gates the request normalization; Glasswing inherits the same
   constraints per the `claude-api` skill.
3. **How is task_budget reported back to the orchestrator?**
   **Recommend**: as a `DriverEvent("task_budget_consumed",
   budget_remaining=...)` after each Fable response, so the wrapping
   verb can decide whether to continue an agentic loop or stop.
