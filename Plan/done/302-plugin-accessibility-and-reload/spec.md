---
spec: 302
title: plugin-accessibility-and-reload
status: Partial (Slice 1 shipped)
state: done
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

## Slice 2 — mid-session reload (`agency_reload`) [SHIPPED — answers the user]

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
- [x] Slice 2: `agency_reload` substrate tool — `Engine.reload()` re-discovers +
  rebuilds the registry/ontology in place, re-wires new verbs onto the held MCP,
  returns `{added, removed, rewired_tools, …}`. A new capability written to disk
  is discovered AND invocable mid-session (acceptance test writes a probe cap,
  reloads, invokes it, cleans up). Fail-safe (import error leaves the prior
  registry intact).
- [x] Slice 3: `agency install --enable` (one-step install + enable; implies
  `--patch-claude-settings`) + `agency_doctor.onboarding` — a
  time-to-first-successful-call probe (intent_bootstrap → verb invoke → SERVES
  edge) run on a throwaway in-memory engine so the live graph is untouched.

## Followup — Implementation Status (2026-06-16)

**Done.** Slice 1: `engine._surface_freshness` + `_drift_signals` acceptance-dir
fix; `install.generate` stamps `_surface_hash`. Slice 2: `Engine.reload()` +
`agency_reload` substrate tool (held `self._mcp` for re-wiring; existing tools
re-dispatch via the registry so changed code is picked up; new verbs wired).
4 acceptance scenarios total.

**Caveat (documented).** Code-mode `execute` reaches the reloaded surface
immediately; a non-code-mode client must re-list tools to see brand-new verbs.
(Folder-template caps re-merge their `templates/`/`schemas/` files on reload too,
since `reload()` and `__init__` now share `_register_capability` — `/simplify`
pass 2026-06-17.)

**Still.** Slice 3 (auto-enable + first-call probe).

## Followup — Slice 4: installed-version sync on reload (2026-06-23)

**Why.** The fresh-agent-onboarding-proof loop hit a hard stale-MCP blocker: the
live `agency_welcome` was stuck at **30** capabilities while a fresh engine
discovered **36** (adr/workflow/frugal/loop/config/toolcalls). Root cause —
codegraph + `/proc` traced the running MCP server (`agency-mcp`, a pipx console
script) to a **non-editable** pipx site-packages COPY of `agency` frozen at an
older snapshot, while the server's cwd was the current repo checkout. Slice 2's
`reload()` purged `agency.capabilities.*` and re-imported, but from that SAME
stale install dir — so it could never see the newer caps. A manual `rsync`
source→install + server restart proved the only thing that worked; an in-process
reload after the sync raised `phase() got an unexpected keyword argument 'goal'`
because `skill.phase` (a CORE module, not under `capabilities/`) had drifted.

**Done.** New `agency/_reload_sync.py::sync_installed_from_source` mirrors the
source `agency/` checkout onto the installed package (copy new/changed, drop
vanished; skips byte-caches). `Engine.reload()` now calls it FIRST and reports
the result as `installed_sync`. When the drift touches a **core** module
(anything outside `capabilities/`), reload updates the install on disk but
**skips** the in-process purge/reimport — returning `restart_required: True`
rather than skewing the live process — so a restart applies it cleanly.
Capability-only edits still hot-reload in process exactly as before. No-op for an
editable install (`source == installed`) or when not run from a checkout, so the
common dev/CI path is unchanged. 4 new acceptance scenarios in
`tests/acceptance/test_reload.py` (6 total pass).

**Doctrine note.** The pipx-only install doctrine (Spec 055/065) *intends* an
editable install (`pipx install --editable`), which would never drift; this slice
makes `reload` self-heal the non-editable-copy environments the loop ran in.
