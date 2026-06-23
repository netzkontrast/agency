# The Fresh-Agent Onboarding Proof Loop

> **Status:** ACTIVE — running "until no progress" (resumable).
> **Provenance intent:** `intent:771b09a6` (agency graph, `.agency/session.db`).
> **Output target:** PR #296 MERGED (Pass 1–4 doc fixes landed in `main`). Pass 5+
> folds into a NEW PR from branch `claude/fresh-agent-onboarding-proof-t8ecjb`.
> **Last checkpoint:** Pass 5 COMPLETE — **live MCP refresh ACHIEVED + VERIFY
> ACCEPTED** (the lone open item is CLOSED). Root-caused the stale server to a
> non-editable pipx COPY, synced from repo, restarted → live `agency_welcome` = **36**
> caps incl. workflow/adr/frugal/loop. Shipped Spec 302 Slice 4: `reload()` self-heals
> the installed copy every reload (mirror source→install; restart-signal on core drift).
> An INDEPENDENT fresh subagent onboarded through the live MCP and exercised
> workflow.board + adr.catalogue under `intent:7b359a01`; graph provenance
> (`Invocation SERVES intent`) confirms the plugin was driven, not bypassed.
> **Next (optional, future pass):** the minor bare-vs-prefixed tool-name doc note; or
> pick up Spec 389 (derived-fence generator for reference docs).

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

### Pass 1 — VERIFY: deferred (live MCP VERIFY blocked on server reload; CLI lane used instead).

### Pass 2 — ACT (CLI/MCP lane; owner directive: "improve the plugin autonomously")

1. **Code-mode chaining proven on the stale MCP** — one `mcp__agency__execute` block
   chained 5 `call_tool` calls (`intent_bootstrap` → `manage_provenance` →
   `thinking.tradeoffs` → `reflect.note` → `manage_provenance`), returning a single
   delta; the final provenance read saw the write made earlier in the same chain
   (typed join: invocations · agents · artefacts · lifecycle · counts). Demonstrates
   the "uses code-mode, does not circumvent the plugin" pillar.
2. **Registry-drift guard shipped** (the durable fix for the Pass-1 hazard) — new
   acceptance scenario *"welcome surfaces every discoverable capability (no registry
   drift)"* in `tests/acceptance/features/welcome.feature` +
   `tests/acceptance/test_welcome.py`. Asserts (rule 8, computed from live source, no
   magic number) that a fresh engine's `agency_welcome` capability set **equals**
   `discover_capabilities()`. Verified: full welcome suite **10 passed**. This guards
   against any future hidden filter / failed registration / welcome dropping a
   discovered capability.
3. **Fixed this checkpoint's own `doc-source` marker** — it was malformed (prose +
   brace-glob), so `scripts/check-doc-drift` flagged the file STALE. Re-pointed to real
   space-separated source paths + computed `doc-hash` via the script's own
   `_hash_sources`. Now in-sync (did **not** blanket `--update`, which would have
   silently re-stamped 10 other genuinely-stale docs).

### Pass 3 — tooling investigation (owner directive: "find tooling that generates those docs and why they aren't autogenerated correctly")

**Finding:** the 9 stale reference/vision docs are **hand-authored by design — there is no
generator for them.** Doc tooling targets a *different* set: `gen-capability-docs` →
`docs/guide/capabilities.md`; `gen-spec-index` → `docs/specs/index.md`; `gen-living-spec.py`
→ `Plan/living/`; `derive_docs.py` → spec.md test-count fences; `optimize-verb-docs` → a
hand-applied report. **Nothing writes to `docs/vision/reference/`.** `check-doc-drift` is a
*detector* (hashes `doc-source` files, flags change), not a generator. So the docs aren't
mis-generating; hand-maintenance lapsed (confirmed drift: `overview.md` says "eight
`SUBSTRATE_TOOLS`" but code has **11** after Spec 339's LifecycleOpen/Move/Close).
- Verified mechanical drift in `loop.md` path (fixed) + `overview.md` count (8→11, pending).
- **Opportunity:** extend the `<!-- derived:… -->` fence pattern to reference docs so the
  mechanically-derivable fragments (substrate-tool list, verb rosters) regenerate — leaving
  only true prose hand-maintained. New spec, not a same-pass edit. → owner decision pending.

### Pass 4 — ACT (all stale docs reviewed + fixed)

Dispatched 4 parallel read-only drift reviewers over the 8 remaining stale docs (each
claim verified against current source via codegraph), then applied fixes centrally and
re-stamped only after genuine review (no blind hash bumps):
- **cookbook.md** — `agency doctor` field is `hooks.plugin_enabled`, not top-level.
- **SKILL-CONTRACT.md** — the 39 disciplines now **block** (Spec 378 complete), not "warn".
- **intent-lifecycle-gate.md** — added `gate.verdict` (Spec 382 read-only CI reader).
- **skills.md** — `develop` ships **18** authored skills, not 11.
- **drivers.md** / **install-cli.md** — marker fixes to track the real source
  (`agency/capabilities/music/drivers.py`; `agency/_install_adapters.py`).
- **README.md** / **frugal.md** — prose verified current, re-stamped only.
- **loop.md** — corrected the overstated "NOT YET ACTIVATED" header to "W1 ACTIVATED;
  W2 IN PROGRESS" (the `loop` capability now ships 15 verbs with MCP reach + Invocation
  provenance; generative `ctx.sample` advance + elicit still pending), inserted the
  missing doc-hash.

**Result: `scripts/check-doc-drift` exits 0 — 20 in sync, 0 stale.** The "improve all
documentation" objective is met. (34 docs remain unmarked — not a failure; they carry no
`doc-source` and are out of the drift gate's scope unless `--strict`.)

**Remaining gap (the loop's one open item):**
- Live MCP VERIFY still pending a server reload (new session / harness) to confirm a
  cold agent sees 36 caps and can exercise a previously-missing capability (e.g.
  `workflow`/`adr`) through the live MCP with provenance. Everything fixable from the
  CLI lane this session is done.

### Pass 5 — the live MCP refresh (the lone open item) + reload self-heal

**Confirmed the blocker was real in a fresh session.** `agency_welcome` via the
live MCP still showed **30** caps; the CLI lane (fresh Engine) showed **36**. So
the stale-server hypothesis held across sessions — the managed MCP process
outlives the session.

**Root-caused it properly (codegraph + `/proc`, not guesswork).** The user asked
to "try to reload the mcp server", so I escalated:
1. `agency_reload` (Spec 302 in-process reload) — ran but stayed at 30 (`added:
   []`). So not an in-memory cache; the on-disk source it scans is itself stale.
2. The execute sandbox blocks `import agency`, so I found the server via `ps`:
   pid 802 = `/root/.local/share/pipx/venvs/agency/bin/python -E agency-mcp`.
3. That pipx venv holds a **non-editable COPY** of `agency` (`agency-0.1.0.dist-
   info` + a real `agency/` dir, no `__editable__` `.pth`) frozen at the 30-cap
   snapshot — while the server's **cwd is the repo** (`/home/user/agency`, the
   36-cap source). The marketplace clone + plugin cache are *also* stale (stuck at
   PR #194), but the actual import path is the pipx copy.

**Fixed it (what unblocked the loop).** Backed up + mirrored the repo `agency/`
onto the pipx copy (`fresh discover count: 36`), then `agency_reload` — which now
hit `phase() got an unexpected keyword argument 'goal'`: reimporting newer
capability code against the cached OLD core `skill.phase` skews. In-process reload
**cannot** bridge a core-module version gap. Sent `SIGTERM` to the server; the
harness respawned it fresh from the synced disk → live `agency_welcome` = **36**
caps incl. workflow/adr/frugal/loop, and `capability_workflow_board` /
`capability_adr_catalogue` are live + intent-gated (the substrate enforcing
provenance, as designed).

**Made it not recur — Spec 302 Slice 4 (`reload` self-heals the install).** Per
the user directive ("update the reload functionality to properly update the
installed version every time"): new `agency/_reload_sync.py` mirrors the source
checkout onto the installed package on every `reload()`; core-module drift returns
`restart_required` (disk updated, restart applies cleanly) instead of skewing the
live process; capability-only edits hot-reload as before; no-op for editable
installs. 4 new acceptance scenarios; `check-drift` clean. (Full rationale: Spec
302 `## Followup — Slice 4`.)

**Activated Slice 4 live.** Re-synced the pipx copy (now carrying Slice 4),
restarted once → live `agency_welcome` = 36 caps and `agency_reload` now reports
`installed_sync` (reason `already-current`, `synced=False` — no spurious restart).
The self-heal is active: future repo drift auto-mirrors; core drift signals
restart instead of skewing the process.

### Pass 5 — VERIFY: **ACCEPTED** (independent verifier + graph provenance)

Dispatched a SEPARATE fresh subagent (`agent:onboarding-verifier`, no shared
context — the fixer is not the judge) given only the committed onboarding docs. It
walked the documented session-start protocol through the **live MCP** (`mcp__agency__
execute`, no CLI fallback needed): `agency_welcome` → 36 caps incl. workflow/adr/
frugal/loop; `intent_bootstrap` → `intent:7b359a01`; then exercised TWO
previously-missing caps under that intent — `workflow.board` and `adr.catalogue` —
plus a `reflect.note`.

**Judged independently by the graph (not self-report).** I read
`memory_graph_provenance('intent:7b359a01')` myself; it holds 4 `SERVES` edges:
`invocation:76412c5a`→**workflow.board**, `invocation:ba27428e`→**adr.catalogue**,
`invocation:caba0563`→reflect.note, `reflection:508948e8` (observation), under
`agent:onboarding-verifier`. Both previously-missing caps have live `Invocation
SERVES intent` provenance ⇒ the plugin was DRIVEN, not bypassed. **Anti-
circumvention gate satisfied.**

**Stop condition met for this open item:** one independent fresh run onboarded
uninterrupted AND all 36 inventoried caps are reachable through the live plugin.

**One minor, non-blocking doc-vs-behavior note (candidate for a future pass):**
CLAUDE.md's discovery example shows bare names (`call_tool("agency_welcome", …)`,
`call_tool("intent_bootstrap", …)`) while externally-loaded capability tools are
`capability_<cap>_<verb>`. Inside `execute`, `call_tool` accepts BOTH the
unprefixed substrate names and the prefixed capability-verb names; the welcome
payload's `_prefix_keys` documents this, so it's discoverable — a fresh agent
following the table literally could briefly trip on the naming but is not blocked.

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

<!-- doc-source: agency/capabilities/__init__.py agency/_substrate_tools.py tests/acceptance/test_welcome.py -->
<!-- doc-hash: f71f0b91a27922ad -->
