# Supporting modules

<!-- doc-source: agency/cache.py agency/_monitor.py agency/_runner.py agency/_predicates.py agency/_checks.py agency/_pressure.py agency/_db_path.py agency/_capability_loader.py agency/templates.py agency/capabilities/_embed.py agency/capabilities/_vcs.py -->
<!-- doc-hash: 30919ffaae2a685a -->

The modules that support the core but aren't themselves a concept. Pointers, not prose.

| Module | Role |
|---|---|
| `_capability_loader.py` | `discover()` — walks `agency/capabilities/`, finds `CapabilityBase` subclasses (folder-per-cap or single-file), enforces kebab-case names. The drop-in entry point. |
| `cache.py` | A small cache used on hot read paths. |
| `_db_path.py` | Resolves the per-project graph DB location (`.agency/session.db`, `AGENCY_DB`). |
| `_monitor.py` | The single Monitor channel (Spec 021) — `MonitorEvent`s an agent receives out-of-band (`ctx.emit_monitor`). |
| `_runner.py` | The shell-execution boundary the `shell` capability uses (allowlisted). |
| `_predicates.py` | Reusable gate/agentic predicates (`spec_validate`, `confidence_check`) — Spec 011. |
| `_checks.py` | Graph invariant checks (e.g. no-orphan Lifecycle) — Spec 011. |
| `_pressure.py` | Pressure-test harness (`load_scenario`, `score_transcript`, `run_pressure_test`) — Spec 011/133. |
| `_embed.py` | The embedder boundary (BGE when `AGENCY_EMBEDDER` + `[recall]`; else TF-IDF) for semantic recall. |
| `_vcs.py` | `VCSBackend` Protocol + `GitClient` default — the git/gh driver (`vcs`). |
| `templates.py` | Render templates for plugin artefacts (manifest, SKILL.md, command, marketplace). |

## Where these plug in

- `discover()` → [engine.md](engine.md) (bootstrap).
- `_runner` / `_vcs` / `_embed` → [drivers.md](drivers.md) (the boundaries).
- `_predicates` / `_checks` / `_pressure` → the `develop`/agentic capabilities
  ([../../guide/capabilities.md]).
- `templates` → [install-cli.md](install-cli.md) (emission).
