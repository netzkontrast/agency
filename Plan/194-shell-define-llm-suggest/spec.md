---
spec_id: "194"
slug: shell-define-llm-suggest
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "075"
depends_on: ["075", "192", "147", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/shell.py
  - tests/test_shell_define_suggest.py
---

# Spec 194 — shell.define LLM-suggested templates

## Why

Spec 075 ships `shell.define` + `shell.templates(query)` + a
graph-first command registry with common-bash seeds. The registry
grows by hand. When the Spec 147 Driver is present + the dogfood loop
(Spec 150) observes a raw bash sequence repeated across sessions, the
shell cap should SUGGEST a template definition — "you ran this 5×;
define it as `<name>`?" — closing the same observe→promote loop the
intent-opportunity detector (Spec 183) runs for verbs, but for bash.

## Done When

- [ ] **`shell.suggest_templates()`** reads recurring `shell.run`
      Invocations (graph), ranks by frequency, and proposes typed
      `TemplateSuggestion{name:str, body:str, params:list[Param],
      frequency:int, evidence_invocations:list[str], safety_verdict:
      ReversibilityVerdict, confidence:float}` records. The Driver
      (Spec 147) generates the `name` + `params` from the observed
      command shape.
- [ ] **Frequency threshold is tunable, not hand-pinned** — default
      `SUGGEST_MIN_FREQUENCY = 3` (documented, overridable); the
      lint asserts the constant exists with a rationale comment.
- [ ] **Accepted suggestions call `shell.define`** — provenance: the
      template PRODUCES-from the Invocations it generalizes (graph
      edge `Template PRODUCES_FROM Invocation[]`).
- [ ] **Suggestions inherit the safety gate** (Spec 192) — every
      suggestion carries its `safety_verdict`; if the verdict is
      `irreversible`, the suggested template defaults to
      `requires_confirm=True` and the human reviewer sees it.
- [ ] **Degrades** (no suggestions) without `[anthropic]` — the verb
      returns `TemplateSuggestion[]` empty with `reason:
      "driver_unavailable"`; no synthesis attempted.
- [ ] **No-PII invariant** (rule 8): suggestions strip literal
      paths/secrets/IDs from the proposed body and surface them as
      params; the original Invocations stay in evidence but the
      proposed template does not leak them into the template registry.
- [ ] **Failure-mode coverage** for false-positive patterns, Driver
      hallucination, and safety regression.
- [ ] Test: a 5×-repeated bash sequence surfaces a template suggestion
      (mocked Driver); accepting defines it; an irreversible-wrapped
      suggestion defaults to `requires_confirm=True`; PII-bearing
      invocations parameterize out the secret.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  the graph contains 5 Invocations of shell.run with bodies like
        `pytest -q -k test_foo`, `pytest -q -k test_bar`, ...
        AND [anthropic] extra installed
        AND SUGGEST_MIN_FREQUENCY = 3
When:   shell.suggest_templates() runs
Then:   returns [TemplateSuggestion{name:"pytest_k", body:"pytest -q -k {target}",
        params:[Param("target", str)], frequency:5, safety_verdict:
        ReversibilityVerdict{level:"safe"}, confidence:0.92,
        evidence_invocations:[<5 ids>]}]; the agent shows the user;
        on accept, shell.define is called and Template PRODUCES_FROM
        the 5 Invocations is written

Given:  5 invocations of `rm -rf ./build-<commit>`
When:   suggest_templates() runs
Then:   the suggestion has safety_verdict.level == "irreversible";
        proposed template has requires_confirm=True; the user MUST
        opt-in to ship without confirm; safety gate (Spec 192) runs
        on every future use

Given:  invocations contain literal AWS keys
When:   the Driver synthesizes the template
Then:   the synthesized body parameterizes the secret as a Param
        (not a literal); a no-PII assertion verifies the template body
        contains no recognizable secret pattern before define

Given:  [anthropic] not installed
When:   shell.suggest_templates() runs
Then:   returns [] with metadata {reason: "driver_unavailable"};
        no synthesis attempted; no graph mutation
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| False-positive pattern | 5 similar but semantically different commands grouped | Driver confidence threshold; human review | `confidence < 0.7` suppresses suggestion; user always confirms |
| Driver hallucination | suggested template body doesn't match the evidence | replay test: each evidence Invocation must match the template-with-params | reject suggestions that fail replay |
| PII leak | secret/path baked into template body | no-PII regex + Driver instructed to parameterize | block define if literal PII pattern remains |
| Safety regression | suggested template wrapping irreversible loses the gate | inherited `safety_verdict` propagates to `requires_confirm` | gate inheritance is unconditional |
| Suggestion spam | every Invocation pattern becomes a suggestion | `SUGGEST_MIN_FREQUENCY` floor + dedup by template-body hash | tune floor; rate-limit per session |
| Driver cost runaway | every shell.run triggers a Driver call | suggestion runs on-demand, not on every Invocation | batched, not per-call |

## Interconnects

- **dogfood-loop chain** (150) · **LLM-driver chain** (147).
- Spec 183 (verb opportunity) is the verb-side sibling.
- Spec 192 (safety gate) governs suggested templates.
- Spec 075 (shell.define) is what accepted suggestions call.
- Spec 195 (event replay) provides the Invocation stream
  `suggest_templates` reads.
- Spec 150 (amendment classifier) shares the observe-then-promote pattern.
- Spec 187 (output lints) ensures TemplateSuggestion is field-projectable.

## Open questions

1. Auto-define or always suggest? **Recommend**: always suggest
   (definitions are user vocabulary); never auto-define. The graph
   captures the suggestion so the human can revisit.
2. Where does PII detection live? **Recommend**: a single
   `_pii_patterns.py` shared with Spec 150's amendment classifier
   and Spec 195's event replay — derive, don't duplicate.
3. What about commands suggested by the Driver but with novel
   params the user has never used? **Recommend**: mark with
   `unverified_params:bool`; require the first use to confirm
   even on safe-classified templates.
