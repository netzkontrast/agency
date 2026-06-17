<!-- agency-generated: no — authored guidance; the canonical rules for skilldoc paragraphs (Spec 306). -->
# Rules for writing a skilldoc paragraph

> An instruction prompt for any agent (human or model) authoring or optimizing a
> capability docstring, SkillDoc, or tool description. Created with the `prompt`
> capability (the `skilldoc` functional framework, Spec 306) and evaluated with
> `prompt.evaluate(target="skilldoc")`. A skilldoc is a **functional** prompt:
> its job is correct **routing + invocation**, not persuasion.

## The one rule that governs the rest

**A function does not need a Role — it needs actionable insight.** Never open a
skilldoc with `You are a/an <role>`, `Act as …`, or `As a senior <expert>`. That
is `role_padding` — the load-bearing anti-pattern. Roles are for *agents doing
work* (that is `persona`, Spec 297); a skilldoc *exposes a capability*, so it
states **what it does** and **when to call it**, in plain second-or-third person.

## The grammar (fill every slot; leave none as a guess)

```
USE_WHEN:   the single situation that should trigger this skill
TRIGGERS:   concrete signals that should invoke it (one bullet each)
RED_FLAGS:  anti-patterns that mean "reach for a sibling instead" (→ name the sibling)
ACTIONABLE_IMPERATIVE: what to DO — verb-first, no Role
SIBLING_DISAMBIGUATION: how this differs from the nearest sibling skill
TOKEN_BUDGET: keep the whole doc lean (≤ 600 tokens)
```

## The rules

1. **Lead with what it does, then when to use it.** The first sentence is a
   verb-first summary of the capability's job ("Author research dossiers, route a
   draft to the right framework, score prompts for clarity…"); the `Use when:`
   line follows. The skill selector shows this composed paragraph — so the first
   sentence must stand alone as "what this is."
2. **No Role, no persuasion.** Strip `you are`, `act as`, tone, audience, and
   adjectives. State the mechanism, not a personality. (Fires `role_padding`.)
3. **Triggers are observable signals, not restated purpose.** Each trigger is a
   condition an agent can detect in its own situation ("a draft prompt needs the
   right framework picked"), not "use this to do X."
4. **Every red flag names the sibling to use instead.** A red flag without a
   `→ call <sibling>` is half a rule. This is what prevents misrouting.
5. **Disambiguate from the nearest sibling.** State the one distinction that
   tells an agent to pick this over the closest alternative.
6. **Be verb-first and specific.** Replace "helps with", "tries to", "various",
   "stuff" with the concrete action and object. (Fires `vague_imperative`.)
7. **Stay within budget (≤ 600 tokens).** A skilldoc is a routing aid, not an
   essay. Implementation detail belongs in the body/verbs, not the trigger
   paragraph. (Fires `over_budget`.)
8. **Derive, don't duplicate.** The overview, triggers, and red flags ARE the
   doc — do not maintain a second hand-written description that drifts.

## Worked example (before → after)

**Before** (weak overview → the selector falls back to the bare trigger):
```
prompt — prompt-engineering capability.

Two-lineage capability:
...
Use when: authoring research dossiers, engineering structured prompts …
```

**After** (leads with what it does; role-clean; under budget):
```
prompt — prompt-engineering substrate (Spec 109 · 129 · 304-306).

Author research dossiers, engineer token-budgeted prompts, route a draft to the
right one of 27 research-backed frameworks, and score prompts — and agency's own
functional docs — for clarity and anti-patterns. …

Use when: authoring a research dossier, engineering a token-budgeted prompt,
picking the right framework for a goal (route_framework), or scoring a prompt or
functional doc for clarity / anti-patterns (evaluate).
Triggers:
- A draft prompt needs the right framework picked, then filled to a token budget
Red flags:
- Reading all 27 frameworks to pick one → `prompt.route_framework` returns the one
- Adding a Role to a function's doc → that is `role_padding`; functions need actionable insight
```

## Self-check before you ship

Run the doc through the capability you just documented:

```python
prompt.evaluate(prompt_body=<the docstring>, target="skilldoc")
# expect: status "passed", flags == []   (no role_padding / missing_trigger /
#         no_red_flags / vague_imperative / over_budget)
develop.optimize_skilldoc(target_ref="<capability>", kind="skilldoc")
# returns flags + an optimized candidate; writes no source — you apply it.
develop.validate_skill(name="<capability>")   # the Spec 080 gate
```

If any flag fires, fix the named goal (not a generic "make it nicer"): the flag
tells you which rule above you broke.
