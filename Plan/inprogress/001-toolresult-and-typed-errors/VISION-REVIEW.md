# Vision-Alignment Review — Spec 001 (Unified `ToolResult` Envelope + Typed Errors)

> Reviewer: vision-alignment pass against the Agency CANON (`docs/vision/CORE.md`
> authoritative; `specs/engine.md`, `specs/memory.md`, `VOCABULARY.md`).
> Method: `sc:sc-spec-panel` critique mode, four-concepts lens
> (Intent · Capability · Lifecycle · Memory + the Engine substrate; no new concepts).

---

## Alignment verdict

**ALIGNED — needs one reframe.**

The spec introduces **no new concept**. `ToolResult`/`TypedError` are an *Engine-substrate
serialization detail* (the shape a verb returns through the `Registry.invoke` → `_wire`
reflection seam), exactly the category CORE.md reserves for "a serializer detail, not a
top-level concern" (CORE.md:90). It strengthens three of the four concepts (Capability return
contract, Memory provenance join via `trace_id`, Lifecycle outcome typing) and contradicts
none.

The **single reframe required** is the framing of the load-bearing Open Q-2. The spec frames
"full envelope on the wire" as *"a real breaking change for existing `execute()` scripts"*
(spec.md:470-475) — which silently conflates **the in-sandbox `call_tool` return boundary**
with **the context boundary**. Under the canon these are two different boundaries. Once
disentangled, the envelope is fully canon-compliant and the "breaking change" is far narrower
than the spec fears (it touches `cli.py` and any code that treats `execute`'s *own* return as
pre-unwrapped — not "every `execute()` script").

---

## Canon citations

- **Code-mode IS the contract (lean):** "the public surface is exactly `search` · `get_schema`
  · `execute`. The agent writes code in `execute` that chains tools (`await call_tool(...)`);
  **intermediate results stay in-sandbox, only deltas cross into context.**" — CORE.md:10-13
  (echoed `specs/engine.md:16-34`, `:50-55`; `VOCABULARY.md:31`).
- **Three isomorphic renderings:** "exposed three isomorphic ways — MCP · Skills · a bash CLI"
  — CORE.md:13-17; `specs/engine.md:33-34`.
- **Schema as isomorphism glue (the stated NEXT STEP):** "one schema per verb renders three
  ways (MCP `inputSchema`, the Skill's frontmatter, the bash CLI's arg parser) — the
  *isomorphism glue*. *(Not yet wired … making the ontology schema the single source is the
  next step.)*" — CORE.md:69-73.
- **Serializer details are demoted, not concepts:** "Three name renderers → a serializer
  detail, not a top-level concern." — CORE.md:90.
- **Memory / provenance moat:** every node + edge in one bi-temporal graph; `Invocation`
  records `SERVES → intent` (+ `PRODUCES → artefact`) — CORE.md:38-45; `specs/memory.md:53-67`;
  `VOCABULARY.md:25,29`.
- **`PRODUCES` from an artefact, not a side-channel:** Artefact node + `PRODUCES` edge —
  `specs/memory.md:54-56`, `:74-80`.
- **Lifecycle A2A states:** `submitted · working · input-required · completed · failed ·
  canceled`; `COMPLETED ≠ done` — CORE.md:30-35; `VOCABULARY.md:35`.
- **Gates are `elicit` steps, not error returns:** a gate pauses at `input-required`; its
  outcome is a `Gate` node `PASSED`/blocked — CORE.md:56-62; `VOCABULARY.md:22`.
- **Naming:** tool names `<concept>_<capability>_<verb>`, underscores, ≤64, no dots —
  CORE.md:98-102; `specs/engine.md:63-65`.
- **Engine guards are middleware, not concepts:** quality-score, loop-detection, compaction,
  `Slot`/quota — CORE.md:17-18; `specs/engine.md:67-75`.

---

## The three alignment questions, judged

### Q1 — Does wrapping every verb return in a `ToolResult` envelope at `_wire` HONOR or VIOLATE the lean contract? (CORE.md:9-18)

**HONORS it — once the boundary is named correctly.**

CORE.md:10-13 specifies *two distinct boundaries*:

1. The **in-sandbox `call_tool` boundary** — what a verb returns to the Python the agent runs
   inside `execute`. The canon places no minimalism constraint here; it is "intermediate
   results [that] stay in-sandbox."
2. The **context boundary** — what `execute` *itself* returns; only here does the canon's
   "only deltas cross into context" apply.

`_wire` (`agency/engine.py:69-74`) builds the function the model reaches **only as
`await call_tool(capability_<cap>_<verb>, …)` from inside `execute`** (`specs/engine.md:30-31`).
Its return value is therefore an *in-sandbox* value (boundary 1), not a context value
(boundary 2). Serializing the full `ToolResult` there does **not** push the envelope into
context — the agent's own code reads `r["ok"]`/`r["data"]`, joins/filters in-sandbox, and
returns a delta. The envelope is exactly the kind of "intermediate result [that] stays
in-sandbox" the canon protects.

So spec Q2's "full envelope on the wire, callers read `data`" (spec.md:459-475) is the
*canon-faithful* resolution — but the spec's own justification (ADR-0005's "does not change
the MCP wire format") is the **weaker** argument, and its phrasing "a real breaking change for
existing `execute()` scripts" (spec.md:470) is the **misalignment**: it implies the envelope
crosses into context. It does not. The break is confined to (a) `agency/cli.py`'s own
result-printing and (b) any in-sandbox snippet that today assumes `call_tool` returns the
*unwrapped inner dict*. That is a real but **narrow** migration, not a context-surface break.

**Verdict on Q1: HONORS.** The envelope lives on the in-sandbox side of the code-mode boundary
and never auto-crosses into context. The reframe is to say so, and to stop describing it as a
context-surface break.

### Q2 — THE CANON'S ANSWER: does the envelope cross the code-mode boundary?

**No.** The `_wire` return is the value `await call_tool(...)` yields *inside* the sandbox
(CORE.md:11-13). Only `execute`'s own return crosses into context, and that is whatever delta
the agent's code chooses to return. The full `ToolResult` envelope is an intermediate,
in-sandbox value by construction — it crosses the **`call_tool` boundary** (which has no
leanness constraint) but **not the context boundary**. The lean-contract invariant is about
the *surface* (`search`/`get_schema`/`execute`) and the *context delta*, neither of which the
envelope touches.

### Q3 — Does `ToolResult`/typed-errors connect to the schema-isomorphism NEXT STEP, or pull away? (CORE.md:64-76)

**Neutral-to-supportive; orthogonal axis.** The CORE.md:69-73 NEXT STEP is about the **input**
schema (verb params → MCP `inputSchema` / SKILL frontmatter / bash arg parser, one ontology
schema as the single source). `ToolResult` is the **output/return** contract. They are
different axes and do not collide.

It mildly *supports* the isomorphism: a uniform return envelope makes the **bash↔MCP
isomorphism test** (CORE.md:16) cleaner — `cli.py` and the MCP path now serialize the *same*
shape, so the bash-only agent (Jules) reads `data`/`ok` identically. But the spec does not
claim — and must not claim — to advance the input-schema-single-source work. Risk: a future
reader could mistake `ToolResult.to_dict()` for "the schema." It is not; it is a return
serializer. **Add a one-line scope note** so the envelope is not later conflated with the
ontology-schema-as-single-source effort.

### Naming / role-tags / vocabulary (CORE.md:98-102; VOCABULARY.md)

- Tool names are untouched — still `capability_<cap>_<verb>` (`engine.py:85`). **Compliant.**
- Error `code` is a free string (`"unsupported"`, `"internal"`, …) — these are *not* tool
  names and the canon's `<concept>_<capability>_<verb>` rule does not apply to them. **No
  conflict.**
- `artefacts_written` + the derived `PRODUCES` edge map cleanly onto Memory's `Artefact` node
  / `PRODUCES` edge (`specs/memory.md:54-56`; `VOCABULARY.md:25,29`). Replacing the
  `result["artefact"]` dict-sniff (`capability.py:177-179`) with a first-class wire field is a
  **canon improvement** — provenance derives from a declared contract, not a smuggled key.
- `trace_id` = the `Invocation` id (spec.md:135-137) is a **strong** canon fit: it makes a
  failure joinable to its `SERVES`/`PERFORMED_BY` provenance in one traversal — directly
  serving "the moat" (CORE.md:43-45; `specs/memory.md:58-67`).

---

## Misalignments (each with the CORE.md / spec line)

1. **[REFRAME — load-bearing] Q-2 conflates the `call_tool` boundary with the context boundary.**
   - Spec: *"This is a real breaking change for existing `execute()` scripts and
     `agency/cli.py`"* — spec.md:470-475; resolution at spec.md:164-169.
   - Canon: "intermediate results stay in-sandbox, only deltas cross into context" —
     CORE.md:11-13.
   - The envelope crosses the in-sandbox `call_tool` boundary (unconstrained), **not** the
     context boundary. The break is `cli.py` + in-sandbox snippets that assumed pre-unwrapped
     `call_tool` returns — not "every `execute()` script." Reframe the risk accordingly.

2. **[CLARIFY] No explicit statement that `ToolResult` is NOT a fifth concept / not the schema.**
   - Canon: serializer details are demoted, "not a top-level concern" — CORE.md:90; concepts
     are exactly four — CORE.md:7.
   - Spec never states this guard, leaving room for a later reader to treat `ToolResult` as a
     concept or as the isomorphism schema (CORE.md:64-76). Add a one-line scope note.

3. **[VERIFY against canon] `gate.check(passed=False)` as `ok=True`** (spec.md:418-423, Q-6).
   - Canon: a gate is an `elicit`/Lifecycle step whose outcome is a `Gate` node
     `PASSED`/`BLOCKED_ON`, pausing at `input-required` — CORE.md:56-62; `engine.py:118-122`.
   - The spec's decision (domain "fail" = `ok=True`, record `BLOCKED_ON`) is **canon-correct**:
     a failed gate is a Lifecycle transition (`input-required`), not a verb *error*. But the
     spec sources this from `the-agency-system` (`handlers/novel/status.py`) rather than from
     the canon. **Re-anchor the justification to CORE.md:56-62** so the rule survives if the
     vendor source is dropped.

4. **[GUARD-RAIL] `next_suggested_tools` must not become a tool-router concept.**
   - Canon: routing/halting is engine *middleware*, not a concept — CORE.md:17-18;
     `specs/engine.md:67-75`.
   - Spec keeps it top-level + empty (spec.md:392, 454) — fine. Note it is reserved for a
     future *guard* (middleware), so it is never promoted to a concept.

5. **[MEMORY FIDELITY] Warnings-only soft failure recording.** (spec.md:154-159, 332-335)
   - Canon: every Invocation is auditable; a failed run "must be auditable too"
     (`capability.py:164-165`); Lifecycle states include `failed` — CORE.md:30-35.
   - Recording `ok=False` with `error_code="unspecified"` as `outcome:"failed"` keyed off
     `not result.ok` (not off `result.error`) is **canon-faithful** (no silent success). Keep
     it; it is correctly aligned — listed here only to affirm the invariant is met.

---

## Recommended aligned framing

Adopt the spec **as designed**, with the boundary language corrected:

- `ToolResult`/`TypedError` are an **Engine-substrate return serializer** (CORE.md:90
  category), not a concept. The four concepts are unchanged.
- The envelope is the **in-sandbox `call_tool` return shape** (boundary 1). It is, by the
  canon's own words, an "intermediate result [that] stays in-sandbox" (CORE.md:11-13). It does
  **not** auto-cross into context; only `execute`'s chosen delta does (boundary 2). The lean
  surface (`search`/`get_schema`/`execute`) is untouched.
- Resolve Q-2 to **(a) accept the documented break** — it is the canon-faithful shape and the
  blast radius is `cli.py` + in-sandbox-unwrap assumptions, **not** the context surface. Pin
  both success and failure *in-sandbox* wire shapes in tests, plus one **bash↔MCP isomorphism**
  test proving `cli.py` and the MCP path emit byte-identical envelopes (CORE.md:16).
- Strengthen the Memory tie explicitly: `trace_id = Invocation id` and `PRODUCES`-from-
  `artefacts_written` are presented as **moat reinforcements** (CORE.md:43-45), the spec's
  most canon-positive contributions.

---

## Must-change list for the design pass

1. **Rewrite Open Q-2's risk framing** to separate the **in-sandbox `call_tool` boundary**
   from the **context boundary** (CORE.md:11-13). State that the envelope stays in-sandbox and
   does not cross into context; scope the "break" to `cli.py` + in-sandbox unwrap assumptions,
   not "every `execute()` script." *(load-bearing — this is the spec's central reframe.)*

2. **Add a one-line scope guard:** "`ToolResult` is an Engine-substrate return serializer
   (CORE.md:90), NOT a fifth concept and NOT the verb input-schema; the schema-isomorphism
   single-source work (CORE.md:64-73) is a separate, untouched axis." Prevents future
   conflation.

3. **Add a bash↔MCP isomorphism test** to the Done-When list: `agency/cli.py` and the MCP
   `_wire` path must emit the identical `ToolResult.to_dict()` envelope for the same call
   (CORE.md:13-17; `specs/engine.md:33-34`). This is the canon's litmus for "exposed three
   isomorphic ways" and is currently only implied.

4. **Re-anchor Q-6 (`gate.check` → `ok=True`) to CORE.md:56-62** (gate = Lifecycle
   `elicit`/state transition, not a verb error), not only to the vendor `handlers/novel/`
   precedent — so the rule is canon-derived and survives dropping the source.

5. **Annotate `next_suggested_tools` as reserved for future engine *middleware* (a guard),
   not a concept** (CORE.md:17-18) — keep it top-level, empty, and un-promoted.

6. **State the Memory wins as canon reinforcements:** call out `trace_id = Invocation id` and
   `PRODUCES` derived from the declared `artefacts_written` field as direct moat strengthening
   (CORE.md:43-45; `specs/memory.md:54-56`), replacing the smuggled `result["artefact"]`
   side-channel (`capability.py:177-179`).
