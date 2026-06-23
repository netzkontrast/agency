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

**Pass 1 OBSERVE (fresh subagent `intent:372e7740`, 13 invocations / 11 verbs, MCP lane):**

- **C1 — wire-naming is silently inconsistent (WORST gap).** Bare substrate tools
  (`agency_welcome`, `intent_bootstrap`, `agency_doctor`, `memory_graph_provenance`)
  vs prefixed `capability_<cap>_<verb>` — a fresh agent can't predict which, and the
  `using-agency` skill never teaches the rule. A guessed `manage.provenance` (doesn't
  exist) burns a call. → Spec A.
- **C2 — `get_schema` hides nested object shapes.** `detailed` shows `context: any[]`
  but the verb needs `[{id, text}]`; `gate_check`'s `blocked_on` is an OUTPUT field,
  not input — passing it raised `unexpected_keyword_argument` and **aborted the whole
  execute block** (partial-write hazard). → Spec A (enrich schema output).
- **C3 — elicit/sample advertised live but unreachable from the walker (BUG).**
  `agency_doctor` reports host `sampling:true, elicitation:true`, yet
  `skill_walk("brainstorm")` still returned the client-side `input-required` pause
  (`blocked_on: 'sample:questions'`) instead of round-tripping inline. The live host
  Context that direct substrate calls see is likely NOT threaded into the walker's
  nested verb-invoke path. → **Spec B (owner-critical).**
- **C4 — `manage_list(label="Intent")` returns count 0** though `manage_read` confirms
  the node is `live` with `labels:['Intent']` → list label-filter / index disagreement
  with the read path. Likely a real bug. → queued.
- **C5 — inconsistent result-envelope keys** across caps (`rows` vs `result`) →
  standardize or document. → queued.
- **C6 — `research_lead(depth="shallow")` echoed `depth='standard'`** → enum silently
  normalized/ignored. → queued.
- **C7 — thinking/intent verbs return prompt scaffolds, not executed analysis**
  (they're `transform` templates) → document so a fresh agent expects to reason through
  them. → Spec A (doc).
- **C8 — `workflow_board`/`adr_catalogue` empty while `workflow_index` finds 381 specs**
  → board/catalogue read the GRAPH (`SpecLifecycle` unpopulated in this DB); index reads
  the FILESYSTEM. → queued.

**FEATURE (owner directive 2026-06-23) — not a caveat:** `document.session` writing
`.agency/sessions/intent_<id>.md` is **wanted**. Extend it so the file **auto-appends
with each capability call** — a live, grow/append per-intent session log (rule-9
never-truncate doctrine). → **Spec C.**

### Candidate specs (one per pass, all on the single PR)

- **Spec A — skills teach the call (loop's core deliverable + owner "MCP examples"
  directive).** Autogenerate richer **code-mode call examples** into every skill
  (per-verb + one chaining example), make `using-agency` carry the **bare-vs-prefixed
  naming rule** + bare-tool list + a "`get_schema` before first call" rule, and
  **enrich `get_schema`** so object/`any[]` params show their required nested shape.
  Extend the GENERATOR (`disclosure.parse_module_skill` / `skill_emit.emit_skill` /
  `install.generate`'s static `_USING_AGENCY_SKILL_MD`) — no hand-editing per skill.
- **Spec B — elicit/sample reachable from the walker (C3).** Thread the
  sample/elicit-capable host Context through `skill_walk`'s nested invoke so
  server-initiated `ctx.sample`/`ctx.elicit` round-trip inline.
- **Spec C — session auto-append (owner directive).** `document.session` appends each
  invocation to `.agency/sessions/intent_<id>.md` (grow/append, never truncate).
- **Queued:** C4 · C5 · C6 · C8.

**Pass 1 BUILD — caveats found while driving the `develop-spec` workflow via the MCP
(dogfooding the workflow itself):**

- **C9 — `document.ingest` re-anchors a spec, breaking the `spec-<id>` convention.**
  Ingesting `Plan/draft/390-…/spec.md` (which carried `<!-- agency-node: spec-390 -->`)
  minted a content-hash Document `document:24de285e` and **rewrote the anchor** to it,
  rather than honoring the `spec-390` anchor. → ingest should respect a pre-existing
  `spec-<id>` anchor (keep-both). → queued.
- **C10 — `workflow.open_spec(spec_id=…)` is misleadingly named.** The `spec_id` param
  is actually the **Document id** (`recall_typed(spec_id, "Document")`), NOT the spec
  number. Passing `"390"` returns `no spec Document '390'`; you must pass
  `document:24de285e`. → rename/alias the param or accept the spec number. → queued.
- **C11 — `adr.extract_decisions` mines only specific headers.** It parses a canonical
  WH(Y) statement, else `## Design` / `## Why` / `## Failure modes`. A spec with a clear
  `## Decisions (WH(Y))` + `## Approach` yielded **0 candidates** — the ADR hinge can't
  populate. → teach the extractor the `## Decisions` header (or document the required
  shape in `develop.write_spec`). → **blocks the clean ADR-gate path; Spec D candidate.**
- **C12 — graph-state vs folder-state can diverge.** `workflow.to_open` moved the
  SpecLifecycle node `draft→open` but left the physical folder at `Plan/draft/390-…`
  (folder move is `finish_spec`'s job, not `move_spec`'s). Ephemeral here (fresh CI
  graph has no node), but a live session shows `node-drift`. → confirm/​document which
  verb owns the folder move. → queued.

---

## Run log

### Pass 1 — OBSERVE (complete)

- Anchored provenance intent `intent:6771acf8` (MCP, 36 caps after the Spec 302
  Slice 4 reload fix).
- Fresh subagent (own `intent:372e7740`) attempted one code-mode chain per cluster
  through the MCP, recording the caveats ledger above + a cluster-coverage table
  (8/11 chained-OK; workflow+adr and the gate cluster partial; elicit/sample
  characterized). Provenance: `memory_graph_provenance('intent:372e7740')`.
- **Worst gap chosen → Spec A** (skills teach the call). Spec B (elicit/sample) +
  Spec C (session auto-append) queued; all land on ONE PR.

→ **NEXT:** open Spec A through the `workflow` lifecycle, drive to the ADR hinge,
   then PAUSE for owner ADR-approval.

---

## How to resume

1. Re-read this file and the provenance intent `intent:6771acf8`
   (`memory_graph_provenance('intent:6771acf8')` if the graph DB survived).
2. Continue from the latest **Run log** entry.
3. Honor the run configuration — especially the per-change `develop-spec`
   lifecycle, the owner gates, the independent verifier, and the provenance gate.
4. Keep this file's Run log + Caveats ledger current each pass (durable
   checkpoint; the graph DB is ephemeral in remote sessions).
