---
spec_id: "055"
slug: pipx-only-install
status: complete
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: [039]
affects:
  - bin/agency-mcp                  # thin PATH router only
  - bin/agency                       # thin PATH router only
  - bin/agency-install               # REMOVED
  - agency/__main__.py               # collision guard vestigial
  - agency/engine.py                 # install_method enum reduced
  - agency/install.py                # docstring updated
  - tests/test_distribution.py       # bootstrap-path tests removed
  - README.md                         # one install path
  - docs/getting-started.md           # pipx as canonical
estimated_jules_sessions: 0
domain: meta
wave: 2
---

# Spec 055 — Pipx-only install doctrine

## Why

User directive (2026-06-03): *"Now that we have the pipx install -
please remove all other install options and their tests."*

Spec 039 shipped pipx alongside the legacy marketplace `.venv`
bootstrap. Two paths means: two install surfaces to test, two
collision modes to guard, two doctrines to teach. Per-axis cost:

- `bin/agency-install` (the venv bootstrapper) — 60 LOC of bash;
  fragile on read-only mounts; required a separate `--scaffold-db`
  call in `agency.install`.
- `_warn_on_install_collision()` — guarded against the dual-install
  case (pipx + marketplace-venv); now there's only one path so the
  guard is vestigial.
- `bin/agency-mcp` / `bin/agency` had bootstrap-fallback branches
  (~30 LOC bash each); now they're thin PATH routers (~15 LOC).
- Tests covered the bootstrap-failure-127 path AND the
  PATH-vs-venv-priority path AND the collision-detection path —
  ~6 tests removed/simplified.

The pipx-only doctrine collapses all of this. The marketplace install
still works: it sets up the plugin tree, and a one-time `pipx install`
of that tree lands `agency-mcp` on PATH. The `bin/agency-mcp` shim
inside the marketplace tree then routes to the pipx-installed binary.

## Done When

- [ ] `bin/agency-install` removed.
- [ ] `bin/agency-mcp` reduced to thin PATH router (~15 LOC); no
  `.venv` fallback, no auto-bootstrap; exits 127 with the pipx install
  hint when `agency-mcp` isn't on PATH.
- [ ] `bin/agency` same shape.
- [ ] `agency/__main__.py::_warn_on_install_collision()` reduced to
  a no-op stub (kept so callers' error paths don't break).
- [ ] `agency_doctor.install_method` enum reduced to
  `{pipx-or-pip-on-path, degraded}` (was 5 values).
- [ ] `agency/install.py` docstring removes the `bin/agency-install`
  reference. `--scaffold-db` flag stays (it's a one-shot config-init,
  not an install path).
- [ ] `tests/test_distribution.py` rewritten:
  - REMOVED: `test_shim_falls_back_to_venv`,
    `test_collision_guard_silent_when_no_plugin_root`,
    `test_collision_guard_warns_on_two_different_paths`,
    `test_collision_guard_silent_on_same_realpath`,
    `test_shim_picks_path_first` (no priority to test).
  - KEPT: pyproject + doctor_main + shim-PATH-resolution +
    shim-exit-127.
  - SIMPLIFIED: install_method enum check (2 values).
- [ ] README.md: marketplace section updated to instruct
  `pipx install <plugin-root>` after marketplace install.
- [ ] `docs/getting-started.md`: local-dev section uses pip-install-e
  instead of `bin/agency-install`.

## Design

### What stays

- `pyproject.toml` `[project.scripts]` — three console-scripts
  (`agency`, `agency-mcp`, `agency-doctor`). Pipx wires these.
- `bin/agency-mcp` / `bin/agency` — still exist as thin shims because
  the marketplace `.mcp.json` references them. They just route to
  pipx now.
- `python -m agency.install` — still regenerates the manifest +
  .mcp.json + skills/help/SKILL.md + commands/*.md. Called by
  maintainers, by CI for drift detection.
- `--scaffold-db` flag — still useful for one-shot `.agency/` init.

### What goes

- `bin/agency-install` (the bootstrap bash wrapper).
- `_warn_on_install_collision()` body (kept as no-op stub).
- The 2 marketplace-* `install_method` enum values.

## Files

- **Delete:** `bin/agency-install`.
- **Modify:** bin/agency-mcp, bin/agency, agency/__main__.py,
  agency/engine.py, agency/install.py, tests/test_distribution.py,
  README.md, docs/getting-started.md.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped.

### Done
- `bin/agency-install` deleted.
- `bin/agency-mcp` + `bin/agency` reduced to thin PATH routers
  (~25 LOC each, including the pipx install hint heredoc).
- `_warn_on_install_collision()` reduced to no-op.
- `agency_doctor.install_method` enum reduced to 2 values
  (pipx-or-pip-on-path | degraded). Old marketplace-* values gone.
- `agency/install.py` docstring updated.
- `tests/test_distribution.py` rewritten — 7 tests (was 11), all
  green in 0.17s.
- README install section restructured: pipx is now THE canonical
  install; marketplace section explicitly directs users to follow
  up with `pipx install <plugin-root>`.
- docs/getting-started.md migrated to pipx + pip-install-e for
  local dev.

### Live measurements
- `scripts/test-cap "distribution or install"` — 22 tests in 2.6s.
- `scripts/check-drift` — NO DRIFT DETECTED.

### Cluster-coherence (Spec 047)
- C13 Plugin/MCP Authoring (it IS — collapses the install surface).
