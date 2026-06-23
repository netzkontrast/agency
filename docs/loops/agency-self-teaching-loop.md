# The Agency Self-Teaching Loop (spec-governed, single-PR)

> **Status:** ACTIVE — running "until no progress" (resumable).
> **Provenance intent:** `intent:6771acf8` (agency graph, `.agency/session.db`).
> **Output target:** ONE PR from branch `claude/fresh-agent-onboarding-proof-t8ecjb`.
> **Secondary goal (owner directive):** MAXIMIZE agency-MCP use to surface real
> plugin caveats and fix them through the workflow (dogfooding is the point).
> **Owner gates (pause + ask):** ADR-approval, "this spec is done", final PR merge.

Each pass drives one improvement to agency's **automatic documentation
generation**, `README.md`, and the **`using-agency` skill** (+ its references)
through the **complete `develop-spec` → implement → ADR workflow**, accumulating
onto one PR, until a fresh independent subagent can chain **every capability
cluster** in code-mode error-free (including a chain where the agency MCP
correctly uses **elicit + sample** to interact mid-chain) — then it stops.

---

## The loop

A spec-governed instance of the fresh-clone (#025) + Loop-Harness-verification
(#020) family: every change is routed through the repo's own 14-phase
`develop-spec` lifecycle (`workflow` + `adr` capabilities, Spec 353–359) with its
three hard gates (improve · ADR-approve · done), and a *separate* fresh agent
then proves — via graph provenance — that the resulting docs/skill let a cold
agent chain agency's capabilities through the plugin without mistakes.

**Prompt:**

> Work on the `agency` repo on ONE branch / ONE PR for the whole run. Each pass,
> pick the single worst gap that stops an AI from using and chaining agency
> capabilities in code-mode, and drive that change through the **complete
> `develop-spec` lifecycle** (`workflow` + `adr`): intent → triage → brainstorm →
> research (use **codegraph** over what exists) → acceptance → spec into
> `Plan/draft/` → spec-panel → brooks-lint → improve gate → `to_open` (extract
> decisions) → **pause for owner ADR-approval** (never self-approve) →
> `begin_impl` → TDD build that improves the **automatic documentation
> generation**, regenerates `README.md` + the reference docs, and extends the
> `using-agency` skill + references to teach capability-chaining per the Vision
> and GOALS → **pause for owner "done"** → done-cascade (`adr.render`,
> `move_spec` to done, rebuild `architecture.md`); keep `TODO.md` current. Then
> dispatch a **separate fresh subagent** given ONLY the committed `using-agency`
> skill + references; it must complete one representative code-mode chain for
> **each capability cluster**, including one chain where the agency MCP correctly
> uses **elicit and sample** to interact with you mid-chain. Accept the pass only
> if the graph's `Invocation SERVES intent` provenance shows every chain ran with
> **zero errors** — never the subagent's self-report. Commit each spec's work to
> the same PR. Discard subagent state and retry. **Stop** when one independent
> fresh run completes a clean, error-free chain for every cluster (elicit +
> sample included), or when passes stop making measurable progress. Ask before
> editing canonical docs (CORE / AGENTS / AGENCY_PROTOCOL), installing skills, or
> merging the PR.

---

## Run configuration (chosen by owner)

| Parameter | Value |
|---|---|
| **Change process** | EVERY change runs the full `develop-spec` lifecycle (intent→…→done) — no ad-hoc edits. |
| **Success gate** | One representative code-mode chain **per capability cluster**, run by an independent fresh subagent, accepted on graph `Invocation SERVES intent` provenance with **zero errors**. At least one chain must exercise the MCP's **elicit + sample** mid-chain round-trip. |
| **Budget / stop** | Run **until no progress** — keep fix→verify until one clean independent run across all clusters, or no measurable progress between passes. |
| **Output** | All specs + ADRs + `architecture.md` rebuilds + doc/skill changes land on **one PR**. |
| **Verifier** | A *separate* fresh subagent (no shared context) — the fixer is never the judge. |
| **Owner gates** | ADR-approval, "this spec is done", PR merge — owner-only; the loop pauses and asks. |
| **Anti-circumvention** | Acceptance = graph provenance, not self-report. MCP and CLI both count as "through the plugin." |
| **Dogfood directive** | Maximize agency-MCP use; record every caveat via `reflect.note(scope="observation")` and fix it through the workflow. |

---

## Caveats ledger (dogfooding finds → workflow fixes)

Surfaced while driving the loop through the live agency MCP. Each becomes (or
feeds) a spec.

- _(populated as the loop runs — see Run log + `reflect.note` observations.)_

---

## Run log

### Pass 1 — OBSERVE (in progress)

- Anchored provenance intent `intent:6771acf8` via `intent_bootstrap` (MCP, 36
  caps live after the Spec 302 Slice 4 reload fix).
- Next: dispatch a fresh subagent to attempt one code-mode chain per capability
  cluster against the CURRENT `using-agency` skill, maximizing MCP use, to
  surface the worst capability-chaining gap + plugin caveats.

---

## How to resume

1. Re-read this file and the provenance intent `intent:6771acf8`
   (`memory_graph_provenance('intent:6771acf8')` if the graph DB survived).
2. Continue from the latest **Run log** entry.
3. Honor the run configuration — especially the per-change `develop-spec`
   lifecycle, the owner gates, the independent verifier, and the provenance gate.
4. Keep this file's Run log + Caveats ledger current each pass (durable
   checkpoint; the graph DB is ephemeral in remote sessions).
