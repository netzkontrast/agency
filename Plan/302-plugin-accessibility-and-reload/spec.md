---
spec: 302
title: plugin-accessibility-and-reload
status: Partial (Slice 1 shipped)
depends_on: [039, 054, 062, 114, 276]
clusters: [develop]
vision_goals: [1, 4]
---

# Spec 302 — plugin accessibility, surface-freshness + mid-session reload

> User questions (2026-06-16): *how accessible is the plugin? what's missing? is
> there a usability/discoverability spec?* and *can the MCP server reload
> mid-session?* This is the missing holistic accessibility spec — discoverability
> is well-specced (025/068/161/188/070/071/262/276), but install→enable→first-call
> friction and **surface staleness** were not.

## The accessibility friction (evidence)

Driving the engine all session surfaced concrete gaps:
1. **`plugin_enabled: false`** — `agency install` *offers* the
   `--patch-claude-settings` one-liner (Spec 292 C5) but the user must run it.
2. **Stale installed surface** — the running MCP server is the package that was
   last installed; new capabilities added on a branch are NOT live until
   `agency install` re-runs. There was **no signal** that the surface was stale.
3. **Misleading health signal** — `agency_doctor.drift.capabilities_without_tests`
   only looked in `tests/`, so every `tests/acceptance/`-tested capability was
   FALSELY reported untested (25 false positives).

## Slice 1 — surface-freshness + accurate coverage (shipped)

- `agency install` stamps the live `capability_set_hash` into the generated
  `.claude-plugin/plugin.json` (`_surface_hash`).
- `agency_doctor.drift.surface_freshness` compares the live registry hash to that
  stamp: `{fresh, live_hash, installed_hash, hint?}`. `fresh=False` ⇒ "run
  `agency install`" — a runtime stale-surface signal, not just CI drift.
- `_drift_signals` test discovery now scans `tests/` AND `tests/acceptance/`,
  so the coverage signal is accurate (25 false positives → real gaps only).

## Slice 2 — mid-session reload (`agency_reload`) [PLANNED — answers the user]

**Yes, a mid-session reload is feasible — *because of code-mode*.** The wire
contract is three tools (`search`/`get_schema`/`execute`); per-verb dispatch
happens through the **registry at call time** inside `execute`, not through
statically-registered FastMCP tools. So re-discovering capabilities and
rebuilding the engine's `registry` makes new verbs reachable via `execute`
*without restarting the server*.

Design: an `agency_reload` substrate tool that
1. `importlib.reload`s `agency.capabilities` (+ submodules) and re-runs
   `discover()`,
2. rebuilds `engine.registry` + the effective ontology in place,
3. returns `{reloaded, capability_set_hash, added, removed}`.

Caveats (documented, not blockers): the **non-code-mode per-verb tools** are
registered once at `build_mcp` and would NOT update (code-mode is the canonical
contract, so this is acceptable); Python module reload is best-effort (a hard
import error leaves the previous registry intact — fail-safe).

## Done-When

- [x] Slice 1: `surface_freshness` doctor field + plugin.json stamp; accurate
  `capabilities_without_tests`; acceptance scenarios.
- [ ] Slice 2: `agency_reload` substrate tool (mid-session capability reload via
  code-mode); returns the added/removed delta.
- [ ] Slice 3: install auto-enable (opt-in) + a `time-to-first-successful-call`
  doctor probe.

## Followup — Implementation Status (2026-06-16)

**Done (Slice 1).** `engine._surface_freshness` + `_drift_signals` acceptance-dir
fix; `install.generate` stamps `_surface_hash`. 2 acceptance scenarios.

**Still.** Slice 2 (`agency_reload`) + Slice 3 (auto-enable + first-call probe).
