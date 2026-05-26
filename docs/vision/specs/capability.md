---
slug: spec-capability
type: spec
status: ready
summary: Capability — the craft, the OPEN set. An invokable action whose verbs are capability-defined and role-tagged act (craft write) / transform (stateless compute) / effect (external side-effect). Discover via <capability>.help. Invoking one records an Invocation in Memory edged SERVES->intent. 5W1H cross-sections are an optional observation, not a total function. Proven.
---

# Capability

> **Status: specced; proven where noted.** The engine ships two genuinely
> different capabilities — a stateless `transform` and an agent.

## Concept

A **Capability** is the craft — the OPEN concept. An invokable action whose verbs
are capability-defined and **role-tagged**:

| Role | Meaning | Example |
|---|---|---|
| `act` | a craft write | write lyrics; apply a patch |
| `transform` | stateless compute, no side-effect | count syllables; analyze rhyme |
| `effect` | an external side-effect | master audio; upload; web search |

Discovery is via **`<capability>.help`** (progressive disclosure ↔ a SKILL.md).
Capabilities are an open set; the engine cannot enumerate them by a fixed frame,
but every verb declares its role so the open concept stays legible against the
others.

## Interface

```
<capability>.help()        -> { verbs: [ {name, role, args}, ... ] }
<capability>.<verb>(...)   -> result   (records an Invocation in Memory)
```

A capability registers its name, a `home` concept, and a verb map
(`verb -> {role, fn}`). Invoking it records an **Invocation** node in Memory and
edges it:

- `SERVES → intent` (always),
- `PERFORMED_BY → agent` (when an agent ran it),
- `PRODUCES → artefact` (when it produced one).

**Proven:** `plugin` (`lint_skill`, role `transform`) and `jules` (`dispatch`,
role `effect`; `verify`, role `transform`) register, invoke, and record
Invocations that `SERVE` the Intent; provenance recovers both verbs and roles.

## 5W1H cross-sections are an observation, not a structure

A capability has ONE faceted **home** concept. Its cross-section in another
concept (e.g. its Lifecycle aspect, its Memory aspect) is an optional
`(home, target)` **observation** — useful for explanation, but NOT a total
function. Total decomposition always leaks (Cyc / RDF / Ranganathan), so there is
**no generating function** and no eager triplication. For genuinely cross-cutting
capabilities (`verify`/QC, observability) with no natural home, the **AOP escape
hatch** models them across concepts rather than forcing a home.

## Interactions

- Capability verbs are invoked inside a Lifecycle (often as steps of a skill
  step-graph); their outputs are recorded in Memory.
- An advisory capability (e.g. a voice/AI-pattern check) is a `transform` whose
  output is explicitly NOT wired to a Lifecycle `check` — it emits Info/Warning,
  never gates.
- A capability spanning two roles (e.g. web-search `effect` + phrase-match
  `transform`) is split by role.
