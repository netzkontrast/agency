# Capability authoring — the unified guide

> **Scope.** When you sit down to add a new capability to the agency
> engine, this page is what you read first. It synthesizes four external
> bodies of knowledge into the doctrine the engine ENFORCES via `develop.scaffold_capability`
> + `develop.lint_capability` (Spec 024 v2). Authored once with all four
> source skills loaded; do not regress by reading only one of them.
>
> **Sources synthesized:**
> - `superpowers:writing-skills` — TDD for documentation; RED→GREEN→REFACTOR; rationalization tables; CSO descriptions.
> - `superpowers-developing-for-claude-code:developing-claude-code-plugins` — the 6 plugin patterns; MCP+Skill = capability+judgment.
> - `superpowers-developing-for-claude-code:working-with-claude-code` — skills are model-invoked; `allowed-tools`; progressive disclosure.
> - `claude-api` — token-efficient agentic loops; prescriptive "call when X" tool descriptions; prompt caching invariants; adaptive thinking.
> - Internal: `Plan/016` (the 11 hints), `Plan/023` (render-slice contract), `Plan/025` (skill-first discovery foundation).

---

## The four-line summary

1. **A capability is a single file** (`agency/capabilities/<name>.py`)
   unless it owns templates/schemas/ontologies as data or has ≥3 sibling
   helpers — then folder form (Spec 016 Hint #1).
2. **Every verb has a Spec-023-compliant docstring** with `Inputs:` /
   `Returns:` / `chain_next:` markers and a first sentence ≤120 chars.
3. **Verbs are role-tagged** `act` / `transform` / `effect` —
   load-bearing for provenance + auto-wiring (Spec 016 Hint #3).
4. **Tests exercise verbs through `engine.registry.invoke`**, NEVER by
   direct method call (Spec 016 Hint #11).

If you follow those four lines, the engine takes care of the rest. The
sections below are the WHY — when it gets non-obvious, come back.

---

## Decision tree (what shape does this capability need?)

```
Adding a new capability?
├── Does it own templates / schemas / ontologies as data files?
│       ├── YES → folder form: agency/capabilities/<name>/
│       └── NO  → next question
├── Does it have any underscore-prefixed sibling that exists ONLY to support it?
│       ├── ≥2 siblings → folder form
│       └── 0-1 siblings → single-file: agency/capabilities/<name>.py
└── Re-evaluate at every commit; promote to folder when the second sibling lands.
```

Light precedent: `reflect.py` (3 verbs, 80 LOC). Medium: `plugin.py`
(scaffold + lint + author_skill + author_command, 273 LOC). Heavy:
`jules` + 5 sibling files (target for the folder migration).

---

## The verb docstring contract (Spec 023, enforced by `develop.lint_capability`)

Every `@verb` docstring follows this shape:

```python
@verb(role="effect")
def dispatch(self, source: str, starting_branch: str, prompt: str, ...) -> dict:
    """Spawn a remote Jules session.

    Inputs: source (owner/repo), starting_branch, prompt, title?,
            require_plan_approval=True, alias?, automation_mode='|AUTO_CREATE_PR',
            protocol_preset='agency-default'.
    Returns: {status, session, url, alias, artefact: {kind, session, url}}.
    chain_next: jules.status(session=) once dispatched;
                jules.approve_plan if state in AWAITING_PLAN_APPROVAL.

    Free-text body explaining nuances — this is the T3 (deep) tier.
    Use sparingly; most verbs need only the markers above.
    """
```

**Why the structure matters** — every marker has a runtime consumer:

| Marker | Used by | At which tier |
|---|---|---|
| First sentence (≤120 chars) | `parse_slices(doc)["brief"]` → FastMCP Tool description → `search` output | T1 (brief) |
| `Inputs:` line | render at depth=standard; snippet rendering parses names for `call_tool` args | T2 (standard) |
| `Returns:` line | render at depth=standard; orchestrator learns return shape without executing | T2 (standard) |
| `chain_next:` line | render at depth=deep; pointer for downstream chain construction | T3 (deep) |
| Free-text body | render at depth=deep (`body` slice) | T3 (deep) |

**The first-sentence rule is load-bearing.** A 521-char `search` result
is 130 tiktoken-cl100k tokens; with first-sentence-only briefs the same
result is 86 tokens — a 35% reduction, **directly proportional to
context cost on every search call**. Spec 023 measured this; the Spec
025 Phase-1 tests assert it stays under 120 tokens for typical queries.

**Common docstring mistakes** (caught by lint):

| Mistake | Why it breaks | Fix |
|---|---|---|
| First sentence is two clauses joined by `;` or em-dash | brief stays long; search bloats | Split into two sentences; second goes in body |
| `Returns id/url/state.` (legacy prose) | no marker → falls back to first sentence at standard depth | Add `Returns: {id, url, state}.` |
| `Inputs:` on its own line with prose below | the regex captures the line only; prose drifts to body | Put the input list on the same line as `Inputs:` |
| `chain_next:` missing on a verb that chains | orchestrator must guess what to call next | Add it; it's free |

---

## Role tags (Spec 016 Hint #3 — load-bearing for provenance)

| Role | What it does | Records |
|---|---|---|
| **`act`** | Writes an artefact / a node / a reflection | Invocation + SERVES edge + PRODUCES (when `artefact` returned) |
| **`transform`** | Pure compute over inputs (or read-only graph query) | Invocation + SERVES edge — no side effects |
| **`effect`** | Touches the outside world (network, GitHub, filesystem, subprocess) | Invocation + SERVES edge — observable cost; the provenance moat |

**Mis-tagging is silent and dangerous.** A verb that calls a remote API
tagged as `transform` produces a provenance graph that says no
external action occurred — the moat lies. Spec 016 Hint #3 gives
concrete examples; the lint should flag obvious mismatches (`requests`
or `httpx` imports in a `transform` body, etc.).

---

## Capability skeleton (the minimum that registers cleanly)

Two equivalent forms — both supported by `discover()`:

### Class form (recommended for ≥2 verbs)

```python
"""<name> — one-line description.

What this capability owns; which concepts it serves. Cite the spec it
implements if there is one.
"""
from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension


class MyCapability(CapabilityBase):
    name = "my-cap"
    home = "capability"  # or "memory", "lifecycle", "intent" — its primary concept

    ontology = OntologyExtension(
        nodes={"MyArtefact": ["kind", "data"]},
        edges={"DERIVED_FROM"},
        # enums, schemas, templates, skills — all optional, declared here
    )

    @verb(role="act")
    def do_thing(self, scope: str, text: str) -> dict:
        """Record a thing.

        Inputs: scope (str), text (str).
        Returns: {result: <id>}.
        chain_next: my-cap.recall(scope=).
        """
        nid = self.ctx.record("MyArtefact", {"kind": scope, "data": text})
        return {"result": nid}
```

### Functional form (light capabilities, no class state)

```python
from ..capability import Capability
from ..ontology import OntologyExtension


def _do_thing(ctx, scope: str, text: str) -> dict:
    """Record a thing.

    Inputs: scope (str), text (str).
    Returns: {result: <id>}.
    """
    nid = ctx.record("MyArtefact", {"kind": scope, "data": text})
    return {"result": nid}


CAP = Capability(
    name="my-cap", home="capability",
    verbs={
        "do_thing": {"role": "act", "fn": _do_thing, "inject": ["ctx"]},
    },
    ontology=OntologyExtension(nodes={"MyArtefact": ["kind", "data"]}),
)
```

The class form auto-injects `ctx`; the functional form names it
explicitly. Choose by feel — class form scales further.

---

## Ontology ownership rule (Spec 016 Hint #4)

A capability owns its ontology fragment; **never reaches into others'
fragments**. If two capabilities need the same node type, neither owns
it — it gets promoted to core via a `CORE.md` amendment (rare,
high-cost). The `OntologyExtension` merge enforces this:

| Field | Merge rule | What collision does |
|---|---|---|
| `nodes` | strict, no redefinition | raises at engine build |
| `edges` | unioned | no collision possible |
| `enums` | WIDEN never clobber | collisions widen |
| `skills` | unique-name | raises at engine build |
| `schemas` | unique-name | raises at engine build |
| `templates` | unique-name | raises at engine build |

If your capability needs a node type another already declares — that
other capability should expose a verb that records it for you. Never
duplicate the declaration.

---

## Returns must be deltas, not dumps (Spec 016 Hint #6)

```python
# ❌ Don't do this:
@verb(role="transform")
def recall(self, scope: str) -> dict:
    return {"reflections": all_reflections_in_scope}  # ~1MB on a busy DB

# ✅ Do this:
@verb(role="transform")
def recall(self, scope: str, limit: int = 20, cursor: str = "") -> dict:
    """...
    Returns: {result: [reflection_id, ...], total, cursor}.
    """
    return {"result": ids[:limit], "total": len(ids), "cursor": next_cursor}
```

**Rules:**
- Every `transform` verb returning >20 items takes a `limit: int` and
  returns `{result, total, cursor}`.
- Every verb returning a string body (`patch_body`, etc.) takes
  `max_bytes: int`.
- `act` verbs return `{result: <id>}` or `{result: <id>, metadata:
  <≤100 chars>}` — never the recorded node verbatim.

The orchestrator's context cost scales linearly with what crosses the
sandbox boundary. Inside the sandbox is free; across is expensive.

---

## Wire shape vs internal wrap (Spec 019)

The engine's `_wire` impl (`agency/engine.py`) strips a `{"result":
<inner>}` envelope IFF `<inner>` is itself a dict. The motivation: verbs
return `{"result": <delta>}` internally so the engine can detect ok-path
vs error-path uniformly (Spec 001 envelope discipline); the wire shape
that crosses to the code-mode caller is the bare `<delta>` (the lean
code-mode contract per CORE.md + GOALS.md goal #5).

The corollary the docstring sweep must observe:

```python
# ❌ Don't document the internal envelope:
@verb(role="transform")
def assess(self, branch: str) -> dict:
    """...
    Returns: {result: {ahead, behind, dirty, recommended}}.  # leaks the wrap
    """
    return {"result": {"ahead": 0, "behind": 0, "dirty": False, "recommended": "discard"}}

# ✅ Document the WIRE shape (what the caller actually receives):
@verb(role="transform")
def assess(self, branch: str) -> dict:
    """...
    Returns: {ahead, behind, dirty, recommended}.   # the wire shape
    """
    return {"result": {"ahead": 0, "behind": 0, "dirty": False, "recommended": "discard"}}
```

Scalar wraps are the exception. The engine re-wraps non-dict returns
into `{"result": <scalar>}` because MCP tool responses must be JSON
objects. So `reflect.note` returning `{"result": "reflection:abc"}`
internally produces the SAME shape on the wire — its docstring
correctly says `Returns: {result: <reflection_id>}`.

`plugin.lint_capability` enforces this via the `wire_shape` rule:
verbs whose source returns `{"result": {dict_literal}}` are flagged
when their docstring's `Returns:` line includes the `result` envelope.
Rich-dict verbs (no envelope, like `jules.dispatch`) are unaffected.

**Rule of thumb:** describe what `await call_tool('capability_<x>_<y>',
{...})` returns at the wire, not what your verb's `return` statement
holds.

---

## Universal `input-required` convention (Spec 016 Hint #8)

Verbs that can block on human/agent input return:

```python
{
    "status": "input-required",
    "reason": "<one-liner why>",
    "blocked_on": "<Gate id>",        # the persisted blocker for audit
    "resume_with": ["<input keys>"],  # what the caller must supply on retry
}
```

The caller resumes by re-invoking with the resume-with keys + a
`confirmed=True` flag. This is the chain-pattern at scale — applies to
skills, long-running effects, elicit-driven gates.

---

## Graph is the store; files are a rendered view (Spec 016 Hint #10 + GOALS.md #7)

If your capability writes a markdown file that downstream code parses,
you have it backwards. Write to the graph
(`Reflection` / `Artefact` / your-own-node-type); render markdown on
demand via a separate `<cap>.render(...)` verb when humans need it.

**Exceptions:** canon/doctrine docs (CORE.md, AGENTS.md, AGENCY_PROTOCOL.md,
this file) — those serve external readers and stay as files.

`reflect.note` is the canonical example: it writes to the graph; you
recall it via `reflect.recall` (transform); markdown lives in your head
or in this doc, not in `.md` files keyed to scope.

---

## Skills your capability owns (the Lifecycle templates)

A skill is a Lifecycle template — an ordered phase-graph ending in a
hard gate that the engine's `SkillRun` walker walks one phase at a
time. Declare them on your `OntologyExtension.skills`:

```python
ontology = OntologyExtension(
    skills={
        "my-discipline": {
            "name": "my-discipline",
            "kind": "discipline",  # or "authoring", "workflow"
            "phases": [
                {"index": 1, "name": "gather", "produces": ["evidence"]},
                {"index": 2, "name": "decide", "produces": ["decision"]},
                {"index": 3, "name": "confirm", "produces": ["confirmed"], "gate": "hard"},
            ],
        },
    },
)
```

**Phase shape today** (survey of 17 existing skills): every phase
carries `{index, name, produces}` plus optional `{gate, invoke,
inputs}`. Spec 025 Phase-1 added optional `cue` for T1 rendering.

**When a phase calls a verb** (verb-bound phase), add `invoke`:

```python
{"index": 2, "name": "fan-out", "produces": ["children"],
 "invoke": {"capability": "delegate", "verb": "fan_out"},
 "inputs": ["driver", "driver_verb", "items"]}
```

Verb-bound phases inherit the bound verb's Spec-023 slice — never
author a duplicate cue. The `_wire_skill_tags` at engine build adds
`skill:<name>` to the bound verb's tags automatically.

---

## Writing the SKILL.md (when your capability ships a Claude-Code skill)

A SKILL.md is what Claude reads when it decides the capability applies
to the current task. **Skills are model-invoked**, not user-invoked —
the `description` field is the entire discovery surface. Get it wrong
and Claude never finds your skill.

### Description = WHEN, not WHAT (CSO rule from writing-skills)

```yaml
# ❌ BAD — describes the workflow; Claude follows the description and skips the body
description: Use when developing — runs scaffold then lint then commits.

# ❌ BAD — first person
description: I help you author new capabilities.

# ✅ GOOD — triggering conditions only, third person, "Use when..."
description: Use when authoring a new capability or extending an existing one — before writing the file.
```

**Why this matters** (from writing-skills): when the description
summarizes the workflow, Claude reads ONLY the description and skips
the body. Empirically validated: a description saying "code review
between tasks" caused Claude to do one review even though the body
specified two. Description = triggering conditions, body = the
process.

### Naming — gerund form (anthropic-best-practices)

`authoring-capabilities` > `capability-authoring` > `capability_author`.
Active voice, verb-first, hyphens (no underscores in skill names).

### `allowed-tools` — list what the skill ACTUALLY uses

```yaml
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Read
  - Write
  - Bash
```

A skill whose `allowed-tools` lists `Read/Write/Edit` but whose body
teaches `await call_tool(...)` is broken — the agent can't execute
what the body teaches. Phase 1 of Spec 023 caught this exact bug.

### Token efficiency targets

- getting-started workflows: <150 words each
- Frequently-loaded skills: <200 words
- Other skills: <500 words

The skill shares the context window with everything else Claude needs
to know. Be ruthless.

### Progressive disclosure

SKILL.md is the high-level guide; details go in `references/`:

```
skills/authoring-capabilities/
├── SKILL.md              # ≤200 words, the WHEN + the index
└── references/
    ├── matcher-modes.md  # heavy reference, loaded on demand
    └── examples.md
```

Claude reads SKILL.md once; references only when the body links them.

---

## Testing the capability (Spec 016 Hint #11)

```python
# ✅ Correct: through engine.registry.invoke
def test_my_verb_records_a_reflection():
    e = Engine(":memory:")
    iid = e.intent.capture(purpose="...", deliverable="...", acceptance="...")
    try:
        result, _ = e.registry.invoke(e.memory, iid, "my-cap", "do_thing",
                                       scope="x", text="y")
        assert result["result"].startswith("mycap_")
    finally:
        e.memory.close()

# ❌ Wrong: direct method call — skips provenance, skips ToolResult unwrap,
# skips C5 intent-id validation. The unit test passes but the integration
# is broken.
def test_my_verb_direct():
    cap = MyCapability(ctx=...)
    assert cap.do_thing(scope="x", text="y")["result"]  # silently wrong
```

The `engine`/`iid` fixtures live in `tests/conftest.py` (Spec 016 Phase
5) — your test file gets them by parameter name.

**Three test classes you should always have:**

1. **The happy path** — invoke through engine, assert the artefact lands.
2. **The render contract** — `parse_slices(verb.__doc__)["brief"]` is
   non-empty and ≤120 chars; `search` on a representative query lands
   under budget. (Spec 023 + Spec 025 Phase-1 expose this surface; use
   it.)
3. **A pressure scenario** — when authoring a discipline-enforcing
   skill or when adding lint rules, run a subagent under pressure
   without the discipline and document the rationalizations
   verbatim. Then add it with the discipline and confirm compliance.
   (writing-skills RED-GREEN-REFACTOR.)

---

## What the engine does for free (don't re-implement)

| What you might write | What the engine already provides |
|---|---|
| `try: tool_call() except: log_error()` retry loop | The Anthropic SDK retries 429+5xx automatically |
| `if "429" in str(e):` | `anthropic.RateLimitError` (typed exception) |
| Custom token-counting heuristic | `tiktoken.encoding_for_model("gpt-4").encode(...)` — already in `[dev]` deps |
| Hand-rolled JSON serialization of tool results | `Anthropic.MessageParam`, `Tool`, `Message` types |
| Custom retry-with-exponential-backoff | SDK's `max_retries=2` default |
| Multi-step state across `execute` calls | The graph is the state — `reflect.note` it |
| Skill-step state across orchestrator sessions | `SkillRun(memory, intent_id, schema)` with `skill_id` resume |
| Verb-result decoration for "what to call next" | `chain_next:` docstring marker (static); Spec 026 `intent.suggests_skill` (dynamic, when shipped) |

---

## Token economics of agentic loops (claude-api distilled)

Three savings, all confirmed in primary sources:

1. **Progressive tool discovery** — tool defs live behind `search`,
   read on-demand. A 200-tool server otherwise dumps two hundred
   schemas into the context window before the LLM reads a single
   word (~tens of thousands of tokens).

2. **Intermediate results stay in the sandbox** — filter 10k rows in
   code so the agent sees 5; the multi-step transcript never
   round-trips the model.

3. **Control flow in code** — loops/conditionals/error-handling
   replace N round-trips ("every tool call is a round-trip").

**Numbers from the primary sources:**
- Anthropic engineering: 150,000 → 2,000 tokens (98.7% reduction).
- FastMCP code-mode: ~34K upfront → ~600/workflow.
- Agent Skills: ~40% reduction vs full-content prompts.

**Threshold heuristic** (gofastmcp + jlowin.dev): under ~20 tools, show
everything upfront (one fewer round-trip beats searching); larger
catalogs → staged discovery.

**Implications for verb authoring:**
- Default to `transform`/`act` returns ≤500 chars unless caller asks for
  more (limit/cursor pattern).
- A verb whose return regularly exceeds 2KB is a smell — split it or
  add `max_bytes`.
- Tool descriptions are prescriptive ("call this when X") not
  descriptive ("does X") — informs Claude's invocation triggering.

---

## Prompt caching invariants (when your capability calls Claude API)

If your capability calls `client.messages.create` (e.g. a future
`llm_select` matcher in Spec 026), respect the **prefix-match
invariant**: any byte change anywhere in the prefix invalidates
everything after it.

**Silent invalidators to avoid:**
- `datetime.now()` / `uuid4()` in system prompt
- `json.dumps(d)` without `sort_keys=True`
- Per-user IDs interpolated into system prompt
- Conditional system sections (`if flag: system += ...`)
- Adding/removing tools mid-conversation

**Verify with `response.usage.cache_read_input_tokens`** — if it stays
zero across identical-prefix requests, a silent invalidator is at work.

---

## The 11 hints (Spec 016 distilled into one table)

| # | Hint | Where enforced |
|---|---|---|
| 1 | Folder form when ≥3 sibling files | `discover()` accepts both module + subpackage |
| 2 | Single-file for light capabilities | doctrine — `reflect.py` is the precedent |
| 3 | Role tags are load-bearing | lint flags obvious mismatches |
| 4 | Capability owns ITS ontology fragment | `OntologyExtension` merge raises on collision |
| 5 | `CapabilityContext` fields documented | `agency/capability.py:36-60` |
| 6 | Returns are deltas, not dumps | lint checks for `limit:int` on transform >20 returns |
| 7 | Docstring contract (Inputs/Returns/chain_next) | `parse_slices` + `lint_capability` |
| 8 | Universal `input-required` return convention | `agency/skill.py:71-95` |
| 9 | Skills compose by intersection at hard gates | doctrine — don't introduce meta-skills |
| 10 | Graph is the store; markdown is rendered | doctrine + `reflect.note` pattern |
| 11 | Verbs go through `engine.registry.invoke` in tests | `tests/conftest.py` fixtures (Spec 016 Phase 5) |

---

## Where this guide is enforced

`develop.lint_capability(name)` (Spec 024 v2) runs every rule above as
a structured check. `develop.scaffold_capability(name, kind=light|medium|heavy)`
emits a skeleton that lint-clean by construction. `develop.reference("authoring")`
returns slices of this page at T1/T2/T3 depth (Spec 023 progressive
disclosure applied to this doc itself).

The discipline that walks you through it: `authoring-capabilities`
(skill on the develop capability). Walk it via `SkillRun` and the lint
fires at the gate.

---

## Rationalization table (when the discipline feels heavy)

| Excuse | Reality |
|---|---|
| "This capability is too simple for the contract" | Then it's a 30-second scaffold — do it anyway. The contract pays back on every search call. |
| "The docstring is self-evident from the code" | `parse_slices` doesn't read code; it reads docstrings. No marker = no chain hint = orchestrator guesses. |
| "I'll add markers later" | You won't. Add them while the call shape is in your head. |
| "Lint is overkill for the first version" | Lint is 2ms; the bug it prevents is hours. |
| "My verb returns a string body so the contract doesn't apply" | Then add `max_bytes:int`. Don't ship unbounded returns. |
| "Skills are scattered across capabilities anyway" | That's the current state; this doc + Spec 026 are the convergence. Don't make it worse. |
| "I'm just dogfooding the engine; rules don't apply to internal capabilities" | The engine IS the plugin (`CLAUDE.md` line 1). Internal capabilities are external capabilities from the user's perspective. |

---

## Red flags — STOP and reconsider

- You're about to write a `.md` file that downstream code parses → graph it instead.
- You're about to write a verb that returns >2KB by default → add `max_bytes` or `limit/cursor`.
- You're about to add `import requests` to a `transform` verb → re-tag `effect`.
- You're about to test a verb by calling its method directly → use `engine.registry.invoke`.
- You're about to write a skill whose description summarizes the body → rewrite as "Use when…" trigger conditions only.
- You're about to copy a node type declaration from another capability → that means someone else owns it; call their verb.
- You're about to write `temperature=0.7` for an LLM call → Opus 4.7/4.8 removed sampling params; use adaptive thinking + `effort`.
