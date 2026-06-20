# agency infrastructure audit — for the ponytail-port + event-registration build

Read-only audit (2026-06-20). Maps the EXISTING substrate a "ponytail port +
event-registration system" builds on. Code cited `file:line`; spec status
cross-checked against each `Followup` section + the `TODO.md` grouping rows.

> **Naming note:** "ponytail" is the upstream MIT skill that agency redeveloped
> natively as **frugal** (Spec 332). There is no vendored ponytail source — the
> reference pointer lives at `.claude/skills/ponytail/`; the engine implementation
> is `agency/_frugal.py`. A "ponytail port" in this repo means *extending the
> native frugal discipline*, not importing anything.

---

## 1. Shipped vs in-flight — every target spec

| Spec | Title | Status (verdict) | Grounding | What is real on disk |
|---|---|---|---|---|
| **076** | unified-event-hook | **SHIPPED (v1)** | frontmatter `status: shipped`; Followup "Shipped (v1)" (076 spec.md:118) | The dispatcher + open-set handler surface + capture wiring all live (`engine.dispatch_hook`, `register_hook_handler`, `_default_hook_handler`, `hooks/dispatch`, `hooks.json`, CLI `agency hook`). *(Predates the current TODO Shipped-count line; it is a wave-5 substrate spec, fully landed.)* |
| **195** | unified-hook-event-replay + boundary-use | **PARTIAL → Slices 1+2+"Slice 2 MCP-suggestion" SHIPPED; Slice 3 NOT started** | In TODO **Shipped** count line; frontmatter `status: partial` (195 spec.md:4) | Shipped: `BoundaryUse` capture in `_default_hook_handler`/`_record_boundary_use`; `dogfood.replay_events` + `boundary_use_audit`; the PreToolUse→MCP-suggestion (`_pre_tool_use_handler`, `_suggest_mcp_calls`, `_resolve_mcp_suggestion`, `_verb_input_schema`, shared `_RAW_ROUTES`). **Still (Slice 3+):** live `verb_shadow` via Spec 188; `LoopEvent` in replay; PII summarization+gate; monotonic/clock-skew invariant; cross-session replay; blocking `permissionDecision:"ask"`. |
| **329** | typed-lifecycle-memory-spine | **SHIPPED** | In TODO Shipped count line; Followup "SHIPPED 2026-06-19" (329 spec.md:112) | `agency/_entity_store.py`: `TypedLifecycleState`, `TypedArtefact`, `TypedEdge` spine; `memory.link` projects every edge onto the typed spine (one-way, failure-isolated). 6 acceptance scenarios. *(Note: lands the typed TABLE for lifecycle state — not the state-machine behaviour; that is 338/340.)* |
| **332** | frugal-core-discipline | **SHIPPED (all 5 slices)** | TODO row 102 "**332 SHIPPED**"; Followup "Shipped (all 5 slices)" (332 spec.md:186) | `agency/_frugal.py` (ladder + floor + `render`/`frugal_level`/`frugal_prefix`/`safety_floor_intact`). M1 inject via `engine._append_frugal` on SessionStart+UserPromptSubmit; M2 stamp via `engine._shape_wire_result`; doctor `frugal` block. *(Frontmatter `spec_id:"326"` is a pre-renumber artifact; folder is 332.)* |
| **333** | multi-agent-installer (the "setup" being ported) | **SHIPPED (Wave 1, all 5 slices)** | TODO row 102 "**333 SHIPPED**"; Followup "Shipped (Wave 1)" (333 spec.md:183) | `agency/_install_adapters.py`: `surface_card(engine)` single source → Cursor/Windsurf/Cline/Kiro/Copilot/AGENTS adapters; compact projection + pipx bootstrap + fenced-block merge; `agency install --agent`/`uninstall --agent`; MCP `agency_install(agent=)`; `agency_doctor.installed_agents`. **Wave 2 MCP runtimes deferred → Spec 335.** |
| **338** | lifecycle-pillar-deep-program (master) | **DRAFT — design only; 339a IMPL STARTED** | frontmatter `status: draft`; TODO row 54 "All drafted, no code yet… IMPL STARTED — 339a TDD cycle 1 SHIPPED" | Master spec governs children 339–347 until each is promoted. Only **339a** has code: `agency/lifecycle.py` hardened (`open→submitted`, sole-writer state-shaped `move`, `close`). PR #215. Reframed: lifecycle is a **pillar** (`agency/lifecycle.py` + `ctx.lifecycle` + `lifecycle_*` tools), **NOT** an `agency/capabilities/lifecycle/` folder. |
| **340** | lifecycle-state-machine-transitions (enforced A2A table) | **DRAFT — NOT started** | frontmatter `status: draft`; Followup "Not started" (340 spec.md:129) | Designed: `agency/_lifecycle_data/transitions.json` (data registry) + `_assert_transition` guard behind `move`, typed `IllegalTransition`, monotone `extend_table` + terminal/orphan floor. **Confirmed absent on disk** (no `_lifecycle_data/`). |
| **344** | lifecycle-transition-events ("lifecycle Events" gap) | **DRAFT — NOT started** | frontmatter `status: draft`; Followup "Not started" (344 spec.md:166) | Designed: `agency/_lifecycle_events.py` (pure `LifecycleEvent` dataclass) + emission folded into `move`. **Panel B4 split:** terminal/blocked → durable graph `Event{name:"lifecycle_transition"}` (REUSES Spec 076 node + `OBSERVED_DURING`); intermediate churn → Spec 021 `MonitorEvent` only. **Confirmed absent** (no `_lifecycle_events.py`). Build-order: after 340, before 341. |
| **345** | lifecycle-generic-state-machine | **DRAFT — NOT started** | frontmatter `status: draft`; Followup "Not started" (345 spec.md:134) | Designed: `agency/_lifecycle_data/machines.json` machine registry; A2A = default machine; `open(machine=)`; per-machine `move` validation; ontology `(Lifecycle,state)` enum relaxes to union of registered machines' states; 342 parameterizations re-express as derived machines. **Confirmed absent.** |
| **347** | frugal-embedded-lifecycle | *(read separately — quoting TODO row only)* | TODO row 54: **"347** frugal embedded (Spec 332 floor = non-removable cross-machine invariant; transitions carry the frugal stamp; `frugal` is a drivable machine)." Followup "Not started" (347 spec.md:111). | DRAFT — NOT started. Depends on 332+338+340+344+345. |

**One-line rollup:** the hook substrate (076) + replay/boundary capture (195
S1-2) + frugal core (332) + the self-installer (333) + the typed lifecycle table
(329) are **all shipped and on disk**. The entire lifecycle **state-machine /
transition-event** program (338 master + 340/344/345/347) is **design-only** —
only 339a (the `lifecycle.py` hardening) has code.

---

## 2. Hook system — registration mechanism + open-vs-closed verdict

### VERDICT: the handler set is an **OPEN SET** — a capability/caller can register into it.

It is **not** a hardcoded if/elif. Handlers live in a per-engine **dict** keyed by
event name, with a public registration method:

- The map: `engine.py:704-708` —
  ```python
  self._hook_handlers = {"*": _default_hook_handler,
                         "PreToolUse": _pre_tool_use_handler,
                         "UserPromptSubmit": _user_prompt_submit_handler,
                         "SessionStart": _session_start_handler,   # Spec 332 M1
                         "SessionEnd": _session_end_handler}
  ```
- The open-set API: `engine.register_hook_handler(event_name, fn)` —
  `engine.py:764-768`. Docstring: *"register a per-event hook handler (open set).
  `fn(engine, event) -> dict`. Overrides the default for `event_name`; use `*` to
  replace the catch-all."*
- The dispatcher: `engine.dispatch_hook(event)` — `engine.py:770-779`. Routes by
  `hook_event_name`: **exact handler wins, else the `*` catch-all**; never raises
  on a malformed event (`handler = self._hook_handlers.get(name) or
  self._hook_handlers.get("*")`).
- `_default_hook_handler` itself documents the contract: *"The handler surface is
  an OPEN SET; register a per-event override via `engine.register_hook_handler`."*
  (`engine.py:319-321`).

**Caveat for the design — registration is in-process only.** `_hook_handlers` is
seeded in `Engine.__init__`; there is **no capability-side hook to populate it at
discovery time** (capabilities self-register *verbs* via reflection, but nothing
walks them for hook handlers). So a new `frugal`-style event subscription today
means either (a) calling `register_hook_handler` after the engine is built, or (b)
adding a key to the `engine.py:704` literal. An "event-registration system" that
lets a capability *declare* its event subscriptions (the natural ponytail-port
shape) is **net-new wiring** — the open-set primitive exists, but the
auto-discovery loop that reads capability-declared subscriptions does not.

### Events handled today
- `SessionStart` → `_session_start_handler` (full frugal inject + config repair).
- `UserPromptSubmit` → `_user_prompt_submit_handler` (assumption-guard + intent
  context + frugal inject).
- `PreToolUse` → `_pre_tool_use_handler` (Event/BoundaryUse capture + advisory
  MCP-suggestion).
- `PostToolUse` → falls to `*` → `_default_hook_handler` (routed to the **ephemeral
  toolcall store**, NOT the graph — Spec 336 S2, `engine.py:314-316,345-384`).
- `SessionEnd` → `_session_end_handler`.
- Everything else (Stop, SubagentStop, …) → `*` catch-all `_default_hook_handler`.

The plugin wires these via `hooks/hooks.json` (one block per event, all → the
shared `hooks/dispatch` script EXCEPT SessionStart, which routes to the
specialized `hooks/session-start` script). `hooks/dispatch` pipes stdin JSON to
`agency hook` (CLI `cli.py:449-478`), which calls the `hook_event` substrate tool
→ `engine.dispatch_hook`, and prints any returned `inject` / `hookSpecificOutput`
to stdout.

### Where the SessionStart payload is assembled + does it call frugal `render()`?
**Yes.** `_session_start_handler` (`engine.py:494-501`):
```python
def _session_start_handler(engine, event):
    base = _default_hook_handler(engine, event)   # records the Event
    _maybe_repair_config()                         # Spec 334 S3 non-destructive repair
    return {**base, "inject": _append_frugal("", prompt=False)}
```
`_append_frugal(inject, prompt=False)` (`engine.py:476-491`) imports `_frugal`,
reads `frugal_level()`, and calls `_frugal.render(level, mode="full")` (full
ladder+floor at session start; `off` → nothing; **degrades silently** — any
exception returns the unchanged inject). So the SessionStart inject **is** the
frugal full render. This is the precise seam a mandatory ponytail/event-setup
injection would extend (see §5).

---

## 3. Event / replay model (node types, edges, replay verb)

**Live today (Spec 076 + 195 + 336):**
- **`Event` node** — `{name, session}` (+ optional `tool`), recorded for
  **lifecycle/low-volume** events only (UserPromptSubmit/Stop/SubagentStop/
  SessionStart/SessionEnd). Linked `IN_SESSION` → `Session{session_id,status}`
  (Spec 292) and `OBSERVED_DURING` → the active Intent (`AGENCY_INTENT`).
  `engine.py:386-400`.
- **High-volume tool events are OFF the graph** — `PreToolUse`/`PostToolUse`
  (`_TOOLCALL_EVENTS`, `engine.py:316`) are captured in FULL into the **ephemeral
  `engine.toolcalls` store** (`agency/_toolcalls.py`), not as `Event` nodes (Spec
  336 S2 — Events were ~95% of `session.db` bloat). `keep_full` warns instead of
  truncating (`engine.py:331-332,376-379`). **This B4-style split (durable vs
  ephemeral by volume) is the precedent Spec 344 reuses.**
- **`BoundaryUse` node** — `{tool, argument_summary, target, verb_shadow,
  intent_id, session}`, recorded for raw mutating PreToolUse (Write/Edit/Bash)
  under an active intent. `SERVES` → Intent; `RECORDED_BY` → Event.
  `_record_boundary_use` (`engine.py:403-424`).
- **`LoopEvent`** (`agency/_loop_events.py`, Spec 156) + **`MonitorEvent`**
  (`agency/_monitor.py`, Spec 021, the SLOG channel) — typed, pure dataclasses.
- **Replay verb:** `dogfood.replay_events(for_intent_id, tool="", limit=100)` —
  walks Events `OBSERVED_DURING` the intent, joins each to its BoundaryUse via
  `RECORDED_BY`, returns `{intent_id, events:[{event_id, prior_event_id, name,
  tool, session, target, verb_shadow, summary}], count}`. The monotonic-chain /
  clock-skew / cross-session invariants are **Slice 3 (not built)**.

**Designed-not-built (Spec 344):** `agency/_lifecycle_events.py` with a pure
`LifecycleEvent{event_id, lifecycle_id, from_state, to_state, intent_id, at,
evidence}` dataclass; emission folded into `lifecycle.move` only. It **reuses** the
Spec 076 `Event` node (`name:"lifecycle_transition"`) + `OBSERVED_DURING` edge for
terminal/blocked transitions, and the Spec 021 monitor channel for churn — **no
new node type, no new emit call sites.** This is the direct model for any
event-registration work touching lifecycle.

---

## 4. Config system — how to add an event-subscription config section

`agency/_config.py` is the single `.agency/config.yaml` home (Spec 334).

- **Resolution precedence:** env var → `.agency/config.yaml` → built-in default.
  `config_get(dotted)` / `config_resolve` (`_config.py:115-138`).
- **File location:** `_resolve_config_path()` = `$AGENCY_CONFIG` env, else
  `$CWD/.agency/config.yaml` (`_config.py:81-84`).
- **Persist:** `config_set(dotted, value)` deep-copies, writes YAML, busts the
  mtime-keyed read cache; refuses to persist `secret=True` keys (`_config.py:141-159`).
- **Section registration (the open set):** `register_config_section(name, keys)`
  (`_config.py:40-43`) — core + each capability call it; `registered_keys()` is the
  union, **no frozen audit**. Sections register via **import side-effect**, pulled
  in lazily by `_ensure_all_registered()` which globs `capabilities/*/config.py`
  (`_config.py:205-227`) so a new drop-in capability's config is picked up with no
  edit here.
- **The `ConfigKey` shape:** `name, env, default, doc, enum, secret`
  (`_config.py:24-34`). There is a `register_dataclass_section(name, dc)` helper
  that derives keys from a dataclass's scalar-default fields (`_config.py:57-70`).

**The frugal precedent to copy verbatim** — `_frugal.py:133-138` registers its
section at import time:
```python
_config.register_config_section("frugal", [
    _config.ConfigKey("level", "AGENCY_FRUGAL_LEVEL", DEFAULT_LEVEL,
                      "minimal-code discipline level", enum=LEVELS),
    _config.ConfigKey("stamp_every_verb", "AGENCY_FRUGAL_STAMP", True, "..."),
])
```

**Is there existing list-valued / event-subscription config? NO.** Every
registered `ConfigKey` default in the repo is a scalar (str/bool/enum) —
`core.db_path/embedder/token_backend`, `secrets.*`, `frugal.level/stamp_every_verb`,
plus per-cap dataclass-derived scalars. `register_dataclass_section` **explicitly
filters to `isinstance(f.default, (str,int,float,bool))`** (`_config.py:66-67`), and
the scaffold's `_yaml_scalar` (`_config.py:171-184`) only renders scalars — a
**list-valued default would not round-trip through the scaffold today.**

**To add an event-subscription config section** (e.g.
`events.subscriptions: [PreToolUse, Stop]`): the resolver (`config_get`) already
returns whatever YAML parses, so a list **reads** fine; but (a) the annotated
**scaffold generator** needs a list-aware `_yaml_scalar` branch, and (b) a list
default cannot come through `register_dataclass_section`. Recommended shape: a new
`events` section registered like frugal's, with the subscription list read by a
discovery loop that calls `register_hook_handler` per subscribed event. The config
plumbing is open; the only code change is teaching the scaffold to render a list.

---

## 5. Welcome / SessionStart assembly — where to inject mandatory ponytail setup

- **`agency_welcome`** is defined at `agency/_substrate_tools.py:595-752` (a
  substrate tool, NOT a capability verb — lives in `_substrate_tools.py` alongside
  `agency_doctor`/`agency_install`). It returns a cache-split envelope:
  `prefix` (byte-stable: `wire_contract`, `capability_tier`, `discipline_skills`,
  `sandbox_constraints`, hashes, **and the frugal stamp** via
  `prefix.update(_frugal.frugal_prefix())` at `:732-736`) + `body` (per-call: state,
  intents_count, last_intent, db_path, next steps). It is pure introspection (no
  graph writes) and lists capabilities by name only (budget discipline).
- **Does SessionStart reuse `agency_welcome`? NO.** They are **separate paths**.
  `_session_start_handler` (`engine.py:494-501`) does **not** call
  `agency_welcome`; it records the Event, repairs config, and injects the frugal
  full render via `_append_frugal`. `agency_welcome` is the *MCP first-call*
  onboarding payload (Spec 114 protocol step 1), invoked explicitly by a client —
  not fired by the SessionStart hook. The only thing they share is that **both pull
  the frugal text from `_frugal.py`** (welcome via `frugal_prefix()`, SessionStart
  via `render()`).

**Where to inject mandatory ponytail/event setup — two precise seams:**
1. **The SessionStart inject** — `_session_start_handler` → `_append_frugal("",
   prompt=False)` (`engine.py:501`). To make ponytail setup *mandatory at every
   session*, extend this return's `inject` (compose alongside the frugal render),
   exactly as Spec 332 M1 did. This is the canonical "governs every session" seam
   and it already degrades silently.
2. **The `agency_welcome` prefix** — `_substrate_tools.py:732-736`. For setup that
   should ride the *first MCP call's* onboarding payload (and stay cache-stable),
   add to the `prefix` dict the same way `frugal_prefix()` is merged in.

For a **mandatory installer/setup gate**, note the existing zero-manual-step
pattern: the `hooks/session-start` script (`hooks/session-start`) already runs
`agency install --scaffold-only` every session and pipx-installs the MCP server —
that shell hook is the place a *filesystem* setup step belongs; the engine
`_session_start_handler` is the place a *prompt-injected* mandatory instruction
belongs.

---

## 6. Capability authoring template — the drop-in bar (file cites)

Reference: the small `gate` capability, `agency/capabilities/gate/`.

**The drop-in bar (CLAUDE.md):** add a folder under `agency/capabilities/<name>/`
— verbs + ontology + a docstring that *derives* its Agent Skill — and **nothing
else**, and agency gains a complete, discoverable, walkable, CLI-exposed,
MCP-wired, emittable capability. If adding one needs an edit elsewhere, that
coupling is the bug.

Folder anatomy (`agency/capabilities/gate/`):
- **`__init__.py`** (`gate/__init__.py:1-6`) — one re-export: `from ._main import
  GateCapability`. Folder-form per Spec 060.
- **`_main.py`** (`gate/_main.py`) — the capability:
  - Module docstring (`:1-10`) opens `# agency-scaffold: v1` and carries
    `Use when:` / `Triggers:` lines — the **SkillDoc derives from this docstring**
    (no separately-authored skill metadata; the derivability audit).
  - `class GateCapability(CapabilityBase)` with `name = "gate"`,
    `home = "lifecycle"` (declares which pillar it belongs to — `home="lifecycle"`
    member caps are how the lifecycle pillar gains verbs without a `lifecycle/`
    folder), and `artefact_schemas = ArtefactSchemas.from_module(__file__)` (auto-
    loads `schemas/*.json`). `gate/_main.py:18-21`.
  - Verbs via the **`@verb(role="act")`** decorator (imported from
    `...capability`, `gate/_main.py:13`). The engine reflects each `@verb` method
    and AUTO-WIRES one MCP tool from its signature (`inspect.signature`); params in
    the verb's `inject` list are engine-supplied. `intent_id`/`agent_id` are
    auto-injected at the wire. Inside a verb, work goes through `self.ctx`
    (`ctx.record`, `ctx.link`, `ctx.call`, `ctx.has_edge`, `ctx.memory`) — see
    `check` (`:23-54`) and `adjudicate` (`:56-92`).
- **`schemas/`** — JSON-schema artefacts: `gate.json` (the `Gate` node shape) +
  `gate-outcome.json` (the wire-payload shape). `from_module(__file__)` binds them.

Ontology: `gate` reuses the **core** `Gate` node + `PASSED`/`BLOCKED_ON` edges
(`home="lifecycle"` comment, `gate/_main.py:20`) — a capability that needs new
node/edge types declares them on its `.ontology` instead (per the dormant-surface
rule: *declare an edge ⇒ traverse it*).

**For a new `frugal` capability:** confirmed **there is NO
`agency/capabilities/frugal/` folder** — frugal is deliberately **core**
(`agency/_frugal.py` + the engine hook handlers + the M2 envelope stamp), exactly
because Spec 332 argues a discipline that must govern *every* verb cannot be an
opt-in capability (the assumption-guard precedent). If the ponytail-port adds an
event-registration *capability*, the gate folder is the template; but the *frugal
discipline itself* stays core by design.

---

## 7. The single most-important constraint each place imposes on the design

- **Hook system (076):** handlers are an open set, **but seeded once in
  `Engine.__init__` with no capability-discovery loop** — registering an event
  subscription is in-process wiring, not a declared-and-auto-discovered fact.
  Build the discovery loop if you want capabilities to *declare* subscriptions.
- **Event/replay (195/336/344):** **do not graph-record high-volume events.** Spec
  336 moved tool capture off the graph (95% bloat); Spec 344 splits transitions
  terminal→graph / churn→monitor. Any new event stream must pick its sink by
  volume, and **capture in FULL** (`keep_full`, never truncate — CLAUDE.md #9/#76).
- **Config (334):** the registry is open and scalar-proven; **no list-valued
  config round-trips through the scaffold today** — an event-subscription list
  needs a list-aware `_yaml_scalar` branch, and won't come via
  `register_dataclass_section`.
- **Welcome/SessionStart:** they are **separate paths that share only `_frugal`**;
  the SessionStart inject (`_append_frugal`, engine.py:501) is the one seam that
  governs *every* session and **must degrade silently** (a render failure can never
  break the turn).
- **Capability template (drop-in bar):** adding a capability must be **adding a
  folder and nothing else** — if your event-registration feature forces an edit to
  `engine.py`/`_config.py`/install, that coupling is the bug to design out (or it
  belongs in *core*, like frugal, not in a capability).
- **Lifecycle program (338 + 340/344/345/347):** **design-only — only 339a has
  code.** The transition table (340), `LifecycleEvent` emitter (344), and machine
  registry (345) do **not** exist yet; `lifecycle.move` is the sole guarded state
  writer (`agency/lifecycle.py:60`, `AGENCY-DRIFT: lifecycle-state-writer`) and is
  the single chokepoint everything downstream hangs off. Building event-on-
  transition means implementing 344 against that chokepoint (it is currently a
  spec, not a hook you can subscribe to).
