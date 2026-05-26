# agency — Claude Code plugin

This repo **is** the `agency` plugin: **ONE FastMCP engine + ONE GraphQLite
graph**, designed as the **5W1H decomposition** of work. At this stage the repo
is the **Concept, Vision canon, and Plan** — all documentation; implementation
follows on this branch. The canon in `docs/vision/` is authoritative — **the
Vision wins; code serves it.**

## The model (detail: docs/vision/OVERVIEW.md)

- The human owns **Why / What = INTENT**, captured via `why.capture` →
  `why.confirm`, pinned once as an **Intent node**; every action edges back via
  `SERVES_INTENT`.
- The engine executes the other four as **four isomorphic domains**:
  - **who** — agent-session lifecycle (dispatch, handoff, supervision,
    harness-in-harness).
  - **how** — the craft: skills/tools/actions. OPEN domain; verbs are
    capability-specific and discoverable via a mandatory `how.<capability>.help`.
  - **when** — task / process lifecycle (order, gates, scheduling, triggers).
  - **where** — memory: a bi-temporal, append-only GraphQLite graph + artefacts.
- **who ↔ when boundary**: `when` owns the TASK lifecycle; `who` owns the
  AGENT-SESSION lifecycle; a `DRIVES` edge links a who-session to the when-task
  it advances. Never duplicate state across them.

## The two-axis canonical verb frame (closed domains: who / when / where)

- Lifecycle (write): `open · move · close`
- Observe (read): `read · find · check` (plus `watch` for live/subscribe)

| Domain | open | move | close | read | find | check |
|---|---|---|---|---|---|---|
| who | dispatch | handoff | release | poll | roster | verify |
| when | start | advance | complete | status | list | check (gate) |
| where | record | link | supersede | recall | find | validate |

`how` is OPEN — capability verbs (music: write / master / mix; jules: patch /
bulk), each TAGGED with the frame role it fills. A specialist verb may live in
any closed domain but MUST declare its frame role and surface it as a call-site
ALIAS (e.g. `where.music.supersede` ≡ `where.music.close`).

## Capabilities, home domains, aspects

A **capability** (jules, music, novel, meta-development) is authored in ONE
**home domain** and expressed across the four as **aspects**, each materialized
**lazily** only when needed (**lazy-domaining**). The holding domain owns the
aspect, whether lazy graph data or an authored folder. No eager 4×
triplication.

## Naming (self-describing)

- MCP tool: `mcp__<domain>_<capability>_<verb>`
- Skill: `/agency:<domain>:<capability>:<verb>`
- code-mode: `domain.capability.verb()`

## Where to look

| Task | Open |
|---|---|
| The model | `docs/vision/OVERVIEW.md` |
| The runtime + context-engineering commitments | `docs/vision/ARCHITECTURE.md` |
| A worked walkthrough | `docs/vision/EXAMPLE.md` |
| The engine meta-contract | `docs/vision/specs/engine.md` |
| A domain contract | `docs/vision/specs/{who,how,when,where,intent}.md` |
| Lazy-domaining | `docs/vision/specs/capability-and-aspects.md` |
| Terms | `docs/vision/VOCABULARY.md` |
| Durable lessons | `docs/vision/LESSONS.md` |
| What's next | `docs/ROADMAP.md` |

## Scope discipline

Everything here is documentation. The Vision describes the entire four-domain
model; the buildable slice is MINIMAL — `jules` anchored in `who`, one authored
aspect, the rest lazy, plus the worked example. EVERYTHING else is **"specced —
not built."** Do not claim code is implemented. Do not author eager folders for
all four domains.

## How to work

- Design before code: `superpowers:brainstorming` → `superpowers:writing-plans`
  → `superpowers:executing-plans`. New skills via `superpowers:writing-skills`.
- Analysis / design / spec review: the `sc:` (superclaude) skills.
- Claude Code plugin / MCP / hook mechanics: the
  `superpowers-developing-for-claude-code` plugin.
- Add a capability = author its **home aspect** in one domain; let the other
  aspects stay lazy until needed. No eager cross-domain scaffolding.

## Dev

- Keep `docs/vision/` authoritative; develop on the active feature branch.
- Additive commits only — never rewrite history or force-push.
