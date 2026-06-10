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
      Invocations (graph), ranks by frequency, and proposes template
      definitions (Spec 147 names + parameterizes them).
- [ ] **Accepted suggestions call `shell.define`** — provenance: the
      template PRODUCES-from the Invocations it generalizes.
- [ ] **Suggestions inherit the safety gate** (Spec 192) — a suggested
      template wrapping an irreversible command carries the gate.
- [ ] **Degrades** (no suggestions) without `[anthropic]`.
- [ ] Test: a 5×-repeated bash sequence surfaces a template suggestion
      (mocked Driver); accepting defines it.
- [ ] TODO row + drift clean.

## Interconnects

- **dogfood-loop chain** (150) · **LLM-driver chain** (147).
- Spec 183 (verb opportunity) is the verb-side sibling.
- Spec 192 (safety gate) governs suggested templates.

## Open questions

1. Auto-define or always suggest? **Recommend**: always suggest
   (definitions are user vocabulary); never auto-define.
