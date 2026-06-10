# Vision Enhancement Charter — 2026-06-10

> **Drives the planning session autonomously.** Every enhancement spec in
> Plan/146+ answers ONE existing spec with a measurable improvement,
> deeply interconnected via `depends_on`. Stop only when no further
> improvement spec is possible.

## Goal paragraph (≤4000 chars)

The agency plugin already proves the four-concept canon — Intent ·
Capability · Lifecycle · Memory on one FastMCP + bi-temporal graph
substrate, wire surface `search · get_schema · execute`. The remaining
work is to deepen, simplify, and integrate every existing spec so the
eight Vision goals are uniformly strong rather than unevenly proven,
and so the plugin is genuinely *usable* by an agent like Claude and
*welcoming* to a creative user. The enhancement waves close five named
gaps the alignment matrix surfaces: (1) **token-economy on the OUTPUT
side** — Spec 067 budgets names, nothing budgets the bytes returned
through `mcp__agency__{search,get_schema,execute}` to an LLM driver;
each substrate-tool response needs a frozen-prefix discipline that the
Claude API's prompt-caching prefix-match rule rewards (Anthropic SDK
`cache_control`, ~1024-token minimum, byte-stable prefix), with a lint
that fails when a verb interpolates `datetime.now()`/UUIDs into a
cacheable prefix; (2) **dogfood-loop closure** — Goal 6's critical gap:
Reflections accumulate but no automated path turns "observed pattern"
into "spec amendment proposal"; a Claude-API-mediated
`dogfood.parse_amendment` classifier (managed-agents Outcome with a
gradeable rubric — see `claude-api` skill) finishes Spec 014 and lights
the loop GOALS.md promises; (3) **agent-uniform Lifecycle for LLM
drivers** — Spec 002 ships the Boundary/Driver protocol but no
typed `AnthropicDriver` exists, so every verb that "should call an
LLM" either does it lossy-in-chat (Spec 110's `thinking.*`) or ships
a one-off shim (Spec 026's `llm_select` Matcher still pending);
one canonical Driver with adaptive thinking, `output_config.format`
structured outputs, `stop_reason` handling, and Managed-Agents
session bridging makes every existing verb LLM-aware additively, and
makes the harness-in-harness recursion (Goal 8) explicit: an agency
walk can dispatch to a Managed Agent whose tools execute on Anthropic
sandboxes and whose events stream back as `MonitorEvent`s (Spec 021);
(4) **plugin-distribution + first-touch UX** — the plugin manifest is
minimal, the `/help` command is the only slash command, there is no
SessionStart-driven Intent capture, no marketplace.json layered on
top of the engine's bare install; per the plugin-development skill an
agency-user should be able to type `/agency` and be onboarded
conversationally (the managed-agents-onboarding pattern: describe →
configure → environment → session) with each interview turn captured
as a graph Artefact `PRODUCES` edge, so the user feels creative and
the AI captures everything; (5) **derivability + drift** — Specs 054,
080, 081 ship drift guardrails but every existing spec carries
hand-authored test counts, hand-authored verb lists in its row, and
hand-authored cross-references that rot the first time anything
moves; the enhancement layer derives each of these from the live
registry + graph and lints the rendered docs against the source, so
TODO.md, the alignment matrix, the SkillDoc set, and every spec's
"Followup — Implementation Status" section update themselves on every
spec-touching commit. The enhancement specs are intentionally
**interconnected**: each new spec lists ≥ 3 peer enhancements in
`depends_on`, every enhancement that touches the LLM driver chains to
the Anthropic-SDK spec, every enhancement that touches discovery
chains to the tiered-discovery + output-budget specs, every
enhancement that touches user UX chains to the SessionStart + slash-
command + interview-capture specs. The result is a single ribbon of
follow-up work that strengthens each Vision goal at every existing
spec's surface without breaking the lean three-verb contract.

## Wave map

| Wave | Existing specs covered | New numbers | Theme |
|---|---|---|---|
| 1 | 001–006, 011, 015–023 | 146–160 | Substrate foundation enhancements |
| 2 | 024–026, 031–032, 041, 046, 050–058 | 161–177 | Authoring discipline + lint depth |
| 3 | 042–045, 047–048 | 178–183 | Capability surface depth |
| 4 | 049, 052–055, 061–065 | 184–193 | Distribution + token-economy execution |
| 5 | 056–060, 066–076 | 194–209 | Token economy + naming closure |
| 6 | 077–092 | 210–225 | Substrate hardening continuation |
| 7 | 093–100, 115 | 226–234 | Music cluster depth |
| 8 | 101–108, 117 | 235–243 | Novel cluster depth |
| 9 | 109–112, 114, 119 | 244–249 | Substrate-adjacent capabilities |
| 10 | 120–132 | 250–262 | Novel post-shipped depth |
| 11 | 133–145 | 263–275 | KP wave depth + closure |

Total enhancement specs targeted: **128** (one per existing spec). Each
carries `depends_on: [<original>, <≥3 peer enhancements>]`,
`enhances: <original-id>`, a Why pinned to a measurable gap, a Done
When list, and an Interconnects section naming the cross-wave chains
it participates in.

## Stop condition

A wave halts when every existing spec in its range has an enhancement
spec, OR when an existing spec genuinely needs none (already at
Vision-strength on every Goal it serves, with no derivable surface
left un-derived, no drift sites un-tagged, no LLM-leverage left
un-applied). The session as a whole stops only when no existing spec
has a remaining enhancement on any of the five gap axes.

## Cross-wave chains (the interconnect spine)

- **LLM-driver chain** — every wave touches Spec 147 (the canonical
  `AnthropicDriver` enhancement to Spec 002): research, analyze,
  thinking, prompt, dogfood, intent-bootstrap, scene-writer, deep
  research, sensitivity reader, voice-locked drafting all chain here.
- **Output-budget chain** — every wave touches Spec 146 (the
  response-prefix-discipline enhancement to Spec 023 + 067): every
  substrate-tool response, every capability search payload, every
  skill-walk phase output budgets through the same lint.
- **Dogfood-loop chain** — every wave touches Spec 150 (the
  classifier-mediated enhancement to Spec 014 + 017 + 045): every
  Reflection-emitting verb is upgraded to an amendment-aware shape.
- **UX-onboarding chain** — every wave touches Spec 148 (the
  SessionStart + `/agency` slash-family enhancement to Spec 029 + 062
  + 064): every walkable skill gets a one-line `/agency <skill>`
  shortcut.
- **Drift-derivation chain** — every wave touches Spec 149 (the
  derived-doc enhancement to Spec 054 + 080 + 081): TODO.md rows,
  spec-followup sections, and SkillDoc bodies re-derive on every
  spec-touching commit.

## Doctrine (binding)

1. Each enhancement spec is **additive** — never breaks the wire
   contract, never renames a shipped verb, never forces an upgrade.
2. Each enhancement spec lists **at least one measurable test** that
   proves the gap it closes (token delta, cache-hit rate, derived-doc
   parity, etc.).
3. Each enhancement spec **derives, doesn't duplicate** — if it
   computes a number that already lives somewhere, it reads, doesn't
   re-pin.
4. Each enhancement spec is **tagged with the Vision goal(s)** it
   advances in frontmatter (`vision_goals: [1, 6]` etc.).
5. Each enhancement spec **declares the peer enhancements it depends
   on**, so the cross-wave spine is queryable from the graph.

Charter signature: this file lives at `Plan/_planning/charter.md` and
is the binding driver of every enhancement spec 146 onward. Future
review compares each shipped enhancement against the gap axis it was
spec'd to close.
