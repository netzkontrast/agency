# The Fresh-Agent Onboarding Proof Loop

> **Status:** ACTIVE — running "until no progress" (resumable).
> **Provenance intent:** `intent:771b09a6` (agency graph, `.agency/session.db`).
> **Output target:** fold fixes into PR [#296](https://github.com/netzkontrast/agency/pull/296)
> on branch `claude/docs-agent-onboarding-up91ym`.
> **Last checkpoint:** Pass 1 OBSERVE + root-cause confirmed (stale MCP server).
> **Blocked on:** harness/owner MCP-server reload before VERIFY can run.

A copy-ready Loop Library loop that interconnects three published loops
(#039 easy-onboarding, #001 docs-sweep, #010 full-product-evaluation) plus the
`find-skills` skill, designed to make agency onboarding easy for humans **and**
agents and to *prove* the plugin is used rather than circumvented.

---

## The loop

A cold, no-memory agent repeatedly fixes the single worst onboarding or
docs-vs-reality gap — using `find-skills` only to source a genuinely missing
capability — and a *separate* fresh agent then proves, via graph provenance,
that onboarding succeeds end-to-end *through* the plugin rather than around it;
it stops at one independently-verified clean run with every capability
reachable, or at no progress.

**Prompt:**

> Act as a cold-start agent with no prior session memory in the agency repo.
> Using only the committed onboarding docs and the plugin's MCP/CLI surface,
> inventory every live capability (`mcp__agency__search`) and record where
> onboarding stumbles or docs diverge from behaviour (cross-check the repo's
> doc-drift check). Fix the single worst gap with the smallest reversible
> change — update the doc, or when a capability is genuinely missing, use
> **find-skills** to surface candidate skills and ask before installing. Then
> have a **separate** fresh agent, given only the committed docs, reach the
> ready state and exercise the fixed capability through `mcp__agency__execute`;
> accept it only if the graph's provenance edges show the plugin was used, not
> bypassed. Discard all session state and retry. Stop when one independent
> fresh run onboards uninterrupted and every inventoried capability is
> documented and reachable through the plugin, or at no safe fix / blocked /
> no progress. Ask before touching canonical docs, installing skills, editing
> public copy, or merging.

---

## Run configuration (chosen by owner)

| Parameter | Value |
|---|---|
| **Ready state** | Fresh agent completes the documented session-start protocol (`agency_welcome` → `intent_bootstrap` → walk a skill) **AND** successfully exercises ≥1 capability through `mcp__agency__execute`. |
| **Budget / stop** | Run **until no progress** — keep iterating fix→verify until one clean independent run AND every capability reachable, or no measurable progress between passes. |
| **Output** | Fold doc fixes into PR #296. |
| **Verifier** | A *separate* fresh subagent (no shared context) judges onboarding — never the agent that authored the fix. |
| **Anti-circumvention gate** | Acceptance requires graph provenance (`Invocation SERVES intent` edges), not the agent's self-report. MCP **and** CLI both count as "through the plugin"; bypassing the substrate (raw edits that skip provenance) does not. |

---

## Critical-thinking improvements applied (agency `thinking.apply_full_review`, 8 methods)

- **Independent verification** — the fixer is not the judge (defeats overfit + self-approval).
- **Provenance-gated, not self-reported** — "didn't circumvent" proven by graph edges.
- **Clean room defined + state discarded between retries** — carry nothing between attempts.
- **MCP-or-CLI both valid** — circumvention = bypassing the substrate, not choosing a lane.
- **`find-skills` = discover/triage only** — install is approval-gated; repo prefers native re-dev.
- **Reproducible doc-truth check** — reuse `scripts/check-doc-drift` + `scripts/check-drift`.
- **Both humans and agents** — verify covers a human README path and an agent MCP path.
- **Bounded** — one gap per pass; the capability inventory is the finite checklist.

---

## Run log

### Pass 1 — OBSERVE (complete)

**Cold-start surface (`agency_welcome`):** 30 capabilities exposed —
analyze, branch, delegate, develop, discover, doctrine, document, dogfood,
gate, intent, jules, manage, mode, music, novel, panel, persona, plugin,
prompt, recommend, reflect, research, select, shell, skill_generator, skills,
subagent, symbols, thinking, workspace.

**Gap found (HIGH severity — the worst onboarding obstacle):**
`CLAUDE.md` documents `workflow` + `adr` as the *primary* repo-development
surface (entire "repo-development workflow (Spec 353–359)" section) and lists
`frugal.review` in the verb-routing table — but **none of `adr`, `workflow`,
`frugal`, `loop` appear in the live registry** (`agency_welcome` or `search`).

**Root cause — CONFIRMED (codegraph-led, primary-source verified):**
- Codegraph (`codegraph explore` → `codegraph node discover_capabilities`) located
  the discovery entry point `discover_capabilities()` at
  `agency/capabilities/__init__.py:24`. It registers **every** top-level
  `Capability` / `CapabilityBase` in every non-private module — **no filter**
  excludes adr/workflow/frugal/loop.
- Decisive test: a **fresh** `discover_capabilities()` returns **36 capabilities
  including all four** (adr, workflow, frugal, loop). The four also import cleanly.
- Yet the live MCP server's `agency_welcome` exposes only **30** (missing those four
  + the infra modules clusters/config/migrations/toolcalls).
- ∴ **The running agency MCP server is STALE** — its in-memory registry predates the
  current source tree. The code is correct, discovery is correct, and `CLAUDE.md` is
  accurate. This is an **operational reload/restart**, NOT a code or doc edit.
- Impact while stale: a cold agent following `CLAUDE.md` cannot discover
  workflow/adr/frugal/loop through the live MCP → forced to improvise →
  **circumvents the plugin** (the exact failure this loop exists to prevent).

**CHOOSE / ACT decision:** The fix is to **reload/restart the agency MCP server**
so its registry matches source (`Engine.reload` at `engine.py:1164` re-runs
`discover_capabilities`; in practice the harness restarts the server / new session).
This is operational and **owner/harness-gated** — the agent cannot restart the
managed MCP server itself.

→ **NEXT ACTION (resume here):** (a) reload the MCP server (new session or harness
reload) and re-run OBSERVE — confirm `agency_welcome` then lists 36 caps incl.
workflow/adr/frugal/loop; (b) once the four are live, VERIFY with a *separate*
fresh agent that it can walk the documented session-start protocol AND exercise
one of the previously-missing capabilities through `mcp__agency__execute`, with
graph provenance proving the plugin path. Secondary hardening (optional, owner
approval): add a drift guard so `agency_welcome`'s live cap set is checked against
`discover_capabilities()` — a stale-server smoke test.

### Pass 1 — VERIFY: not yet run (blocked on the CHOOSE/ACT decision above).

---

## How to resume

1. Re-read this file and the provenance intent `intent:771b09a6`
   (`memory_graph_provenance('intent:771b09a6')` if the graph DB survived;
   otherwise this file is the source of truth).
2. Continue from **NEXT ACTION** in the Pass 1 log.
3. Honor the run configuration above — especially the independent verifier and
   the provenance-based anti-circumvention gate.
4. Keep this file's Run Log + Status updated each pass (it is the durable
   checkpoint; the graph DB is ephemeral in remote sessions).

<!-- doc-source: agency_welcome registry vs CLAUDE.md repo-development-workflow section; agency/capabilities/{adr,workflow,frugal,loop} -->
