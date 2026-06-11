---
spec_id: "260"
slug: slash-family-natural-language
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "148"
depends_on: ["148", "176", "147", "188", "256", "266"]
vision_goals: [5, 3]
affects:
  - commands/agency.md
  - tests/test_slash_natural_language.py
---

# Spec 260 — slash family: natural-language routing

## Why

Spec 148 anchors the UX-onboarding chain — `/agency [query]` routes to
search today. With Spec 147 (AnthropicDriver) + Spec 188 (tiered
discovery LLM drill) in place, `/agency <free text>` can route to the
right verb OR skill directly via ONE structured-output call — the
natural extension of `/agency-onboard`'s conversational pattern. The
user types intent in natural language; the engine disambiguates,
confirms before mutating, executes. Without this, the slash family is
a hand-curated menu; with it, the engine becomes welcoming to
non-expert users (the charter's "welcoming to a creative user").

## Done When

- [ ] **`/agency <free text>`** dispatches via the Spec 188 LLM-drill
      with `output_schema` enforcing the typed return:
      ```python
      class SlashRouteResult(TypedDict):
          intent_kind: Literal["verb", "skill", "onboard", "ambiguous"]
          target: str | None             # verb name or skill name
          confidence: float              # [0.0, 1.0]
          alternatives: list[str]        # top-3 runner-ups
          requires_confirmation: bool    # mutating verb gate
          arguments: dict[str, Any]      # extracted args
      ```
- [ ] **Confirmation gate** before mutating verbs run — Spec 192 safety
      gate. The orchestrator shows the user the resolved target +
      arguments BEFORE executing; user confirms or edits.
- [ ] **Onboarding (Spec 148/176) for unmatched queries** — when
      `intent_kind == "ambiguous"` OR `confidence < 0.5`, route to
      `intent.managed_onboard` (Spec 262) instead of failing, so a
      vague query becomes a capture opportunity.
- [ ] **Output budget (Spec 146)** on the dispatch payload — the
      route result is small (< 500 tokens); the prefix discipline
      applies so repeat queries cache.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `confidence in [0.0, 1.0]` AND `len(alternatives) <= 3`
      - `requires_confirmation == True` whenever `target` resolves to
        a verb whose ontology declares `mutating=True`
      - `intent_kind == "ambiguous" ⇒ target is None`
      - top-1 accuracy on a derived test set (built from current
        capability docstrings) reported as a metric, not asserted to
        a specific value — regression alarm on > 10% drop
- [ ] Test: free-text query "show me what changed" routes to
      `analyze.graph` (mocked); free-text "fix the broken build" with
      mutating verbs gates for confirmation; ambiguous query routes
      to onboarding.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  user types "/agency what specs are still partial?"
When:   slash dispatch runs the LLM drill with the verb catalogue
        cached prefix (Spec 146)
Then:   SlashRouteResult{intent_kind:"verb", target:"analyze.graph",
        confidence:0.92, arguments:{"query":"status='partial'"},
        requires_confirmation:False}
        AND the orchestrator executes immediately (read-only verb)
        AND second identical query hits the cache (~0 prefix tokens billed)

Given:  user types "/agency delete the demo capability"
When:   drill resolves to a mutating verb
Then:   SlashRouteResult{target:"<destructive_verb>",
        requires_confirmation:True}
        AND the orchestrator shows a confirmation prompt with the
        resolved arguments; nothing executes until the user confirms

Given:  user types "/agency I want to make a record about cool stuff"
When:   drill cannot disambiguate (confidence 0.31 across 4 candidates)
Then:   SlashRouteResult{intent_kind:"ambiguous", target:None,
        confidence:0.31, alternatives:["music.album_new", ...]}
        AND control hands off to intent.managed_onboard with the
        original text as the seed describe-beat
```

## Failure modes (Nygard)

| Failure | Slash response |
|---|---|
| LLM drill refuses (`stop_reason: "refusal"`) | Route through Spec 256 fallback; on exhaustion, route to onboarding rather than crashing |
| Drill returns malformed structured output | Schema validation catches it; retry once with explicit format reminder; on second failure, route to onboarding |
| Confidence high but target nonexistent (hallucinated verb) | Cross-check against live registry; treat as ambiguous; record reflection (drill regression signal) |
| Mutating verb routed without confirmation gate | Spec 192 safety gate is a hard block — the verb cannot dispatch without the user's explicit confirm token |
| Token budget exceeded on the route payload | Spec 146 envelope rejects with `Codes.PREFIX_BUDGET_EXCEEDED`; the slash command falls back to the static `/agency search` form |
| User types `/agency` with no text | Show the slash family menu (Spec 148) — onboarding entry is one of the items |

## Interconnects

- Spec 148 (parent slash family) — this spec adds the NL routing layer.
- Spec 176 (sessionstart capture) — unmatched queries become Intent
  capture artefacts.
- Spec 147 (AnthropicDriver) — the drill ships through the canonical
  driver with structured outputs.
- Spec 188 (tiered discovery LLM drill) — the routing primitive this
  spec layers a UX onto.
- Spec 256 (refusal fallback) — required for the drill to survive
  safety classifier hits.
- Spec 266 (code-mode error boundary) — slash routing reuses the same
  typed-error envelope so failure stays observable.
- Spec 262 (managed-agents onboarding cap) — the destination for
  ambiguous queries.
- Spec 146 (output-prefix) — verb catalogue is the cached prefix.
- **UX-onboarding chain** completion.

## Open questions

1. **Confidence threshold for auto-execute vs confirmation.**
   **Recommend**: read-only verbs auto-execute at `confidence >= 0.7`;
   mutating verbs ALWAYS require confirmation regardless of confidence
   (safety > efficiency).
2. **Should ambiguous routing capture intent even without consent?**
   **Recommend**: capture as an ephemeral candidate Artefact; promote
   to Intent only when the user proceeds through onboarding (avoids
   silent capture).
3. **How are arguments extracted from free text?** **Recommend**: the
   drill's structured-output `arguments` field carries them; verbs
   with required args missing from the extraction trigger
   `requires_confirmation=True` with the missing args highlighted in
   the prompt.
