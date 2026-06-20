---
spec_id: "348"
slug: frugal-capability-port
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3]
depends_on: ["076", "114", "195", "332", "333", "347", "349"]
domain: frugal
wave: program-master
parent_spec: "332"
---

# Spec 348 — Frugal capability port (ponytail's full surface, native + mandatory)

> Owner directive: *"Port ponytail completely over to agency — all skills and
> commands, the setup and the docs — and it should be mandatory; integrate setup
> into the SessionStart template."* Spec 332 redeveloped ponytail's **core
> discipline** as `frugal` (the ladder + the safety floor, `agency/_frugal.py`).
> This spec ports the **rest of ponytail's surface** — the five sub-commands, the
> MCP, the always-on activation, the setup, the docs — by graduating `frugal` from
> a core module into a first-class **capability cluster**, where the substrate
> gives discovery, CLI mirroring, MCP wiring, and *provenance* for free.

## Why

Ponytail (`/home/user/ponytail`, MIT, indexed this session) ships **six** surfaces;
agency today has **one** of them:

| Ponytail surface | Agency today | This spec |
|---|---|---|
| `ponytail` core mode (ladder + floor, lite/full/ultra) | ✅ `_frugal.py` (Spec 332), hook-injected + verb-stamped | keep as the single source |
| `/ponytail` level switch | partial — `frugal_level`/`set_frugal_level` exist, no verb | `frugal.level` / `frugal.set_level` verbs |
| `/ponytail-review` (diff over-engineering) | ❌ | `frugal.review` |
| `/ponytail-audit` (repo-wide) | ❌ | `frugal.audit` |
| `/ponytail-debt` (harvest `ponytail:` comments) | ❌ | `frugal.debt` |
| `/ponytail-gain` (impact scoreboard) | ❌ | `frugal.gain` |
| `/ponytail-help` (reference card) | ❌ | `frugal.help` |
| `ponytail-mcp` (instructions as prompt + tool) | ❌ | `frugal.instructions` (auto-MCP-wired) |
| always-on activation (SessionStart hook) | partial — `_session_start_handler` injects `_append_frugal` | make it mandatory + surface in `agency_welcome` |
| setup (install the hooks) | partial — Spec 333 installer | fold the SessionStart inject into the canonical install |
| docs (README, agent-portability) | ❌ | a generated `frugal` capability page |

The research backing this is in `research/ponytail-port/scenario-analysis.md`
(462 lines, 36+ usage scenarios) and `research/ponytail-port/agency-infra.md`
(308 lines, the extension points). Two findings from that analysis set the shape:

1. **Ponytail is two layers in one** (`scenario-analysis.md` §4): a *persistent
   MODE* (`ponytail` itself — injected every turn) and *five stateless one-shot
   skills* (review/audit/debt/gain/help — no runtime state; the per-turn tracker
   only branches on `ponytail` and the vestigial `ponytail-review` flag,
   `hooks/ponytail-mode-tracker.js:24-32`). The native shape mirrors that seam
   exactly: **one always-on `frugal` discipline + five stateless verbs.**
2. **The substrate beats the original on provenance** (`scenario-analysis.md`
   §"Provenance upside"): in ponytail every run is ephemeral terminal output. In
   agency each run becomes a **graph artefact** — review/audit findings, a debt
   *ledger node*, typed `DEBT` edges from `frugal:` comments — so "what did we
   defer" is a query, not a re-grep.

This is also the **drop-in-capability bar** (CLAUDE.md): adding the folder should
buy a complete, discoverable, walkable, CLI-exposed, MCP-wired, emittable
capability — *and nothing else*. If the port needs an edit anywhere outside
`agency/capabilities/frugal/` + the documented wiring seams, that coupling is the
bug to fix.

## Design

### 1. The capability cluster wraps the core (single source preserved)

`agency/capabilities/frugal/` follows the `gate/` template
(`agency-infra.md` §6): `__init__.py` (re-export) + `_main.py` (`@verb`s +
docstring-derived SkillDoc) + `schemas/` + ontology registration. It **wraps
`agency/_frugal.py`** — the ladder/floor content stays single-sourced there
(Spec 332 owns it; Spec 347's rule: *read the floor from Spec 332's module, never
a copy*). The capability adds verbs and provenance; it never re-defines the
discipline text.

> **Tension resolved (owner Q2 = "dedicated frugal capability"):** the verbs live
> in `frugal`, not `develop`. `develop` *cross-links* them (§7) — honoring the
> "wire the MCP verb with the develop skill" directive without scattering a
> cohesive cluster across two homes. `frugal.review`/`audit` stay distinct from
> the existing multi-axis `analyze` capability: frugal hunts **over-engineering
> only** (delete/stdlib/native/yagni/shrink), `analyze` covers quality/security/
> performance/architecture. Two different lenses, no overlap.

### 2. The verb surface (the port)

| Verb | Role | Ponytail origin | Behaviour |
|---|---|---|---|
| `frugal.level` | read | `/ponytail` (no-arg) | report the active level (env `AGENCY_FRUGAL_LEVEL` → `.agency/config.yaml` → `full`). |
| `frugal.set_level` | effect | `/ponytail lite\|full\|ultra\|off` | persist the level (wraps `set_frugal_level`). |
| `frugal.instructions` | read | `ponytail-mcp` prompt+tool | return the ruleset text at a level (wraps `render`). **The MCP port** (§4). |
| `frugal.review` | transform | `/ponytail-review` + `/ponytail-audit` | over-engineering review at `scope="diff"` (default — working-tree `git diff`) or `scope="repo"` (ranked, within `paths`); emit `Finding` artefacts + `net: -N`. **One verb, not two** (B1) — `audit` IS `review(scope="repo")`. |
| `frugal.debt` | transform | `/ponytail-debt` | harvest `frugal:`/`ponytail:` comments → a `DebtLedger` node + typed `DEBT` edges. |
| `frugal.gain` | read | `/ponytail-gain` | impact scoreboard, **sourced from a data file** (§6), plus a live pointer to `frugal.debt`. |
| `frugal.help` | read | `/ponytail-help` | reference card, **derived from the live verb registry** (§6). |

Skills derive from the `_main.py` docstring (the SkillDoc pattern): a walkable
`frugal` discipline (the ladder as a phase walk — aligns with Spec 347 depth 3's
drivable `frugal` machine), plus `frugal-review` / `frugal-audit` walks. No
hand-authored skill metadata (derivability audit, CLAUDE.md).

### 3. Mandatory always-on wiring (owner Q3 = "always-on, level overridable")

"Mandatory" = **always present in every session**, not un-disableable.

- **SessionStart.** `_session_start_handler` (engine.py:494-501) already returns
  `inject = _append_frugal("", prompt=False)`, and `_append_frugal`
  (engine.py:476-491) calls frugal `render(level, mode="full")`. This spec makes
  that injection **canonical and non-optional**: the discipline at the active
  level is always in the SessionStart payload, plus a one-line pointer that the
  `frugal` *capability* (review/audit/debt/gain/help) is available. `off` →
  the discipline text is empty but the capability pointer still ships (the floor
  is never injected as removable — Spec 347 makes the floor a non-removable
  cross-machine invariant; this spec does not weaken that).
- **`agency_welcome`** (`_substrate_tools.py:595-752`). The onboarding payload —
  the canonical first call, owner's "starting with the Agency-Welcome" — gains a
  `frugal` block: the active level + the frugal verb list. SessionStart and
  welcome share `_frugal` today but not the payload (`agency-infra.md` §5); this
  spec adds the frugal surface to **both** so the first call and every session
  start both announce it.
- **Level stays overridable** end-to-end: `frugal.set_level("off")` quiets the
  discipline; the capability and its verbs remain callable.

### 4. The MCP port (ponytail-mcp, natively)

Ponytail's MCP (`ponytail-mcp/index.js`) serves the ruleset two ways: a `ponytail`
**prompt** and a `ponytail_instructions` **tool** (both call one
`buildInstructions(mode)`). Agency ports this with **zero new MCP machinery**:

- Every `capability_frugal_*` verb is **auto-exposed on the agency MCP wire**
  (`search`/`get_schema`/`execute`) by the drop-in bar — that *is* the tool
  surface ponytail's MCP provided, generalized.
- `frugal.instructions(level)` is the direct analogue of `ponytail_instructions`:
  same input (the level), same output (the ruleset text). It is the one verb a
  host pulls when its only injection point is a tool/prompt call.

So "port the ponytail MCP over and wire the agency MCP verb with the develop
skill" = ship `frugal.instructions` (auto-MCP-wired) + reference it from
`develop` (§7). No second server.

### 5. Provenance upside (where the substrate wins)

The five sub-commands stop being ephemeral terminal text and become graph nodes:

- `frugal.review` / `frugal.audit` → one `Finding` artefact per cut
  (`{tag, location, what, replacement}`), `PRODUCES`-linked to the invocation and
  `OBSERVED_DURING` the intent. The `net: -N` line is computed from the findings,
  not asserted.
- `frugal.debt` → a `DebtLedger` node + one `DEBT` edge per `frugal:` marker
  (`{file, line, ceiling, upgrade, has_trigger}`). "What did we defer" becomes
  `manage.timeline` / a graph query; a marker with no upgrade-path is a queryable
  `has_trigger=false` row (ponytail's `no-trigger` tag, now durable).
- Capture is **full** (CLAUDE.md #76 / Spec 336) — findings and markers are
  stored verbatim, never truncated to a budget.

### 6. Doctrine-hazard fixes (port forward, not faithfully)

The scenario analysis flagged three places where a faithful port would import a
defect (`scenario-analysis.md` §8):

- **`gain` hardcodes benchmark medians in prose** → violates CLAUDE.md #8
  (no frozen snapshots). Fix: the published medians live in a committed data file
  (`agency/capabilities/frugal/data/benchmark.json`, cited to the ponytail
  benchmark), and `gain` renders *from the data*; the only per-repo number it
  prints is the live `frugal.debt` count (never an invented "you saved X here" —
  the unbuilt version was never written).
- **`debt` greps only `#`/`//`** → misses `<!-- -->`, `--`, `;`, `%` comments —
  including ponytail's *own* `<!-- ponytail: -->` example. Fix: `frugal.debt`
  scans the full comment-prefix set.
- **`help` omits `audit`+`debt`** (the card drifted from the README). Fix:
  `frugal.help` is **derived from the live verb registry**, so it cannot drift.

### 7. `develop` integration (the cross-link)

- `develop.reference("frugal")` surfaces the heavy how-to on demand (T3
  disclosure), exactly as `develop.reference("codegraph")` does today.
- A `develop`/`tdd` walk's implementation phase may `open(machine="frugal")`
  (Spec 347 depth 3) to make the ladder explicit + recorded.
- The verb-routing table (CLAUDE.md "How to use the agency MCP") gains a
  "review for over-engineering → `frugal.review`" row.

### 8. Setup + docs

- **Setup.** The Spec 333 multi-agent installer + the unified `hooks/dispatch`
  (Spec 076) already write the SessionStart hook. This spec makes the frugal
  SessionStart inject part of that canonical template (no separate ponytail
  activation script; agency's one dispatch hook carries it) and keeps ponytail's
  graceful-degrade contract: if the engine can't render (missing dep, bad
  config), the inject is empty, never an error (`_append_frugal` already degrades
  silently — keep it).
- **Docs.** A `frugal` capability page in `docs/guide/` (the capability
  reference is generated — `scripts/gen-capability-docs`; never hand-edit). Port
  ponytail's "before/after" pitch + the level table into the hand-written
  `docs/guide/frugal.md` with a `<!-- doc-source: -->` marker (Spec 054 doc-drift).

### What this slice does NOT do

- No new discipline content — Spec 332 owns the ladder/floor (single source).
- No second MCP server — the agency wire + `frugal.instructions` is the port.
- No floor weakening — Spec 347 owns the non-removable floor; `off` quiets the
  *ladder* injection, never the floor invariant.
- No event-bus work — the first-use-once emit + subscriptions are Spec 349;
  this spec only *consumes* the existing SessionStart/PreToolUse seams.

## Acceptance (Gherkin)

```gherkin
Scenario: the frugal capability auto-discovers
  When I call agency_welcome
  Then "frugal" appears in the capability list
  And the welcome payload reports the active frugal level

Scenario: instructions is the MCP port
  When I call frugal.instructions(level="ultra")
  Then the ultra ruleset is returned
  And it contains every safety-floor marker (validate, data loss, security, accessibility)

Scenario: review emits findings as artefacts
  Given a diff that reinvents a stdlib validator
  When I call frugal.review(diff)
  Then at least one Finding artefact is recorded with tag "stdlib"
  And the result reports "net: -N lines" computed from the findings

Scenario: debt catches an HTML comment the original missed
  Given a file containing "<!-- frugal: global lock, per-account if throughput matters -->"
  When I call frugal.debt
  Then a DEBT edge records that marker with has_trigger=true
  And a marker with no upgrade path is recorded has_trigger=false (surfaced, not dropped)

Scenario: help cannot drift from the verb surface
  When I call frugal.help
  Then every frugal verb (incl. audit and debt) is listed
  And the list is derived from the live registry, not a literal

Scenario: gain never invents a per-repo number
  When I call frugal.gain
  Then the scoreboard figures come from the committed benchmark data file
  And the only per-repo figure is the live frugal.debt count

Scenario: frugal is mandatory but the level is overridable
  Given frugal.set_level("off")
  When a session starts
  Then the SessionStart inject carries no ladder text
  But the frugal capability and its verbs remain callable
  And the safety floor invariant (Spec 347) is unaffected

Scenario: the floor is intact at every non-off level
  Then frugal.safety-floor check passes for lite, full, and ultra
```

## Refinement — spec-panel pass (2026-06-20)

`spec-panel-review.md` (critique, 7.0→8.0). These folds are **authoritative** over
the design above where they differ:

- **B1 — one `review` verb, not two (the spec applies its own ladder).**
  `frugal.audit` is not a separate verb; it is `frugal.review(scope="repo")`. The
  surface is **7 verbs**: `level · set_level · instructions · review · debt · gain
  · help`. ("audit" survives as the `scope="repo"` mode + a documented alias.)
- **B2 — "mandatory" = two gate-checked invariants** (not a re-statement of Spec
  332): (1) `agency_welcome` always lists the frugal *capability surface* (the
  verbs), not just the discipline text; (2) a gate asserts the SessionStart
  payload carries the discipline at every non-`off` level AND the capability is
  discoverable at every level including `off`. 332 injects text; 348 guarantees
  the *surface* + the *gate*.
- **M1 — `review` input contract:** defaults to the working-tree diff (`git diff`
  HEAD); `ref`/`diff` overrides; `scope="repo"` walks `paths`.
- **M2 — operational bound:** `review(scope="repo")` and `debt` take a `paths`
  scope (default: tracked source minus `node_modules`/`.git`/build dirs); capture
  stays full *within scope* (CLAUDE.md #76 governs no-truncation, not scan-the-world).
- **M3 — `debt` matches comment-prefixed markers only** across the widened prefix
  set (`#` `//` `--` `<!-- -->` `;` `%` `/* */`), never a bare substring — a
  `"frugal:"` inside a string literal is not harvested.
- **M4 — `instructions`' primary actor** is an external / no-hook host (the
  ponytail-MCP case); agency-internal agents receive frugal from the SessionStart
  inject and never call it.
- **m1 — `gain`'s `benchmark.json`** is a documented external constant (a
  published, cited measurement) — the explicit CLAUDE.md #8 exception, not a
  frozen current-state snapshot.
- **m2 — `help`** equals the live `frugal.*` registry set (computed + asserted by
  a test, rule 8) — drift-proof.

Acceptance additions (fold into the Gherkin): a `debt` string-literal **negative**
(not harvested); `help` **== registry** equality; the **mandatory-surface gate**
(welcome lists the verbs + the SessionStart discipline is non-empty at non-`off`).

### 2nd-pass folds (post-fold verification, 2026-06-20)

`spec-panel-review.md` §"2nd pass" (8.0→8.5, no open blockers). B1+B2 verified;
two new folds:

- **M5 — dedupe the `frugal` walkable against Spec 347's `frugal` machine.** 347
  depth-3 OWNS the drivable `frugal` machine (the ladder states); 348's capability
  EXPOSES/walks it (`open(machine="frugal")` + the derived SkillDoc), never
  re-defines it. Single source.
- **M6 — the ladder on the spec's own scope bound:** `review(scope="repo")` and
  `debt` scan **`git ls-files`** (tracked files honour `.gitignore` for free) —
  git's native ignore over a hand-rolled exclusion set (supersedes M2's list).
- **m3 — welcome token economy (Spec 066/068):** `agency_welcome` surfaces frugal
  COMPACTLY (level + a one-line capability pointer), not 7 expanded verb schemas.

## Refinement — 3rd pass (Jules critical review, PR #222 / REVIEW-348-349.md)

A delegated Jules review severity-ranked both specs → REFINE. Two 348 findings,
both folded (authoritative):

- **S2 (major) — the drop-in-bar coupling (the architectural fix).** 348 graduates
  frugal to `agency/capabilities/frugal/`, but B2's "mandatory" relied on hardcoded
  frugal checks in core (`agency_welcome` + `engine._session_start_handler`) —
  violating CLAUDE.md's drop-in bar ("if adding a capability needs an edit
  elsewhere, that coupling is the bug"). **FIX:** the mandatory wiring is delivered
  through the **Spec 349 event bus**, not a core edit. Frugal declares a
  `hook:SessionStart` **subscription** (the configurable inject) and the welcome
  surface is automatic — `agency_welcome` already lists EVERY discovered capability
  from the registry, so frugal needs NO frugal-specific code there. Graduating
  frugal then touches only `agency/capabilities/frugal/` (+ the generic bus). While
  349 is unbuilt the inject stays in core `_frugal.py`+engine (frugal is still the
  Spec 332 core discipline today — no coupling exists yet); the move to a bus
  subscription lands **with** the capability graduation, so the coupled
  intermediate state never ships. 348 now `depends_on` 349 for this wiring.
- **S3 (minor) — separate graph capture from the MCP return (token economy).** M2
  keeps capture full within scope (CLAUDE.md #76) — correct for the GRAPH. But
  returning a whole-repo `review(scope="repo")` / `debt` ledger as MCP text blows
  the token budget (Spec 066/068). **FIX:** those verbs record the FULL findings to
  the graph and **return a token-bounded summary** — "Recorded N findings to the
  graph; top K by severity: …" + a locator/cursor to fetch the rest (the Spec 336
  paginate precedent). Full fidelity in the graph, bounded text on the wire.

## Followup — Implementation Status (2026-06-20)

Not started — design record. Opened by the owner's "port ponytail completely +
make it mandatory + setup into SessionStart" directive. Graduates `frugal` from
the `_frugal.py` core module (Spec 332, shipped) into
`agency/capabilities/frugal/` (the `gate/` drop-in template), porting the five
ponytail sub-commands as provenance-emitting verbs + `frugal.instructions` as the
MCP port, wiring the discipline mandatorily into SessionStart + `agency_welcome`
(level overridable, floor non-removable per Spec 347), and fixing three
doctrine hazards a faithful port would import (gain's frozen medians, debt's
comment-prefix gap, help's drift). Reuses Spec 332 (content), Spec 333 (install),
Spec 076/195 (hook seams), Spec 347 (floor/machine). Research:
`research/ponytail-port/{scenario-analysis,agency-infra}.md`. Build-order:
independent of Spec 349, but `frugal` is 349's reference emitter/subscriber.
