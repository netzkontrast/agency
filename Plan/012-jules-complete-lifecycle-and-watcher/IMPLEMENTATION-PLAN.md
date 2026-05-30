# Implementation Plan — Spec 012 (Jules complete lifecycle + watcher)

TDD-first, phased, with a clean commit + green pytest gate per phase. Each
phase is independently revertable; the order minimises rework. Spec 001 is
shipped (envelope dataclass), so phases 2/5/7 can `from agency.toolresult
import ToolResult` from day one.

| # | Phase | Files | Notes |
|---|---|---|---|
| **1** | **Ontology extension on `JulesCapability`** | `agency/capabilities/jules.py` (`ontology=OntologyExtension(...)`) | Pure data: `JulesSession`/`JulesAlias`/`JulesWatchEvent`/`JulesPatch` node kinds + `OBSERVED_OF`/`RECOVERED_BY`/`ALIAS_OF` edges + `JulesState`/`WatchAction` enums. RED: an ontology-violation test. **Inline (this turn).** |
| 2 | **API endpoint wrappers** | `agency/capabilities/_jules_api.py` | Add `jules_get_full`, `jules_status_all`, `jules_approve_awaiting`, `jules_quota`, `jules_resolve_source_public`, `jules_patch_extract`. Pure httpx-Client functions; tests use `unittest.mock.patch` on `_request`. |
| 3 | **Read/admin verbs on the capability** | `agency/capabilities/jules.py` + tests + `StubJulesClient` extension | `resolve_source`, `status_all`, `quota`, `alias`, `patch`, `patch_body`. Update `Plan/000-overview.md` + the help skill regen. |
| 4 | **Recovery-plan planner** | `agency/capabilities/_jules_patch.py` (new) + `tests/test_jules_patch.py` (new) | Pure unidiff parser → ordered `[{tool, args}]` ops with multi-output `current_base` propagation + rename handling. TDD with sample patches under `tests/fixtures/jules/`. |
| 5 | **Dispatch-param completeness + verify independence + status full shape** | `agency/capabilities/jules.py`, `agency/capabilities/_vcs.py` (add `remote_exists`) | `dispatch(title=, require_plan_approval=True default, auto_create_pr=, alias=)`; `verify` calls `vcs.remote_exists` (drops the caller bool); `status` returns the full session dict. |
| 6 | **Watcher (the load-bearing one)** | `agency/capabilities/_jules_watch.py` (new) + `tests/test_jules_watch.py` (new) | Lifespan task; state-aware adaptive cadence (10 → 30 → 300 s; 600 s on `429`); per-intent `asyncio.Queue` (`maxsize=8`, drop-oldest); `_classify(prev, curr, last_agent_msg_id)`; `INSTRUCTIONS: dict[WatchAction, str]`; baseline-seed; terminal-stickiness; `recovery_in_flight` tracker. Fake-clock tests for every transition in the table. Wrap sync httpx with `asyncio.to_thread`. |
| 7 | **`watch`, `approve_awaiting`, `recover`, `apply_patch` verbs** | `agency/capabilities/jules.py` + tests | `watch(session?, intent_id?, timeout=30)` awaits the per-intent queue with `min(timeout, 25)` and a 20 s heartbeat. `recover` returns `status=probing` immediately; the poll loop owns probe-wait-recheck. `apply_patch` returns the planner output verbatim. |
| 8 | **Lifespan wiring + smoke** | `agency/__main__.py`, `agency/engine.py` (lifespan hook if absent) | Start `_jules_watch.start(engine)` in the FastMCP lifespan; cancel on shutdown. Smoke test: `python -m agency` boots without raising. |
| 9 | **Regenerate install + dogfood** | `python -m agency.install` (auto) + commit | The `help` skill picks up the new verbs; `test_agency_plugin_install_is_self_hosted` stays green. |

**Per-phase gate:** RED test → GREEN implementation → `pytest -q` all green → commit
+ push. No phase merges until its tests pass. The watcher (phase 6) is the only
phase that introduces concurrency; it gets fake-clock + queue-mocking tests, not
real `asyncio.sleep`.

**Dispatch options for phases 2–9:**
- **Parallel-safe pairs:** {2, 4} (independent), then {3, 5} (both depend on 2), then 6, then 7, then 8+9.
- **Conservative:** sequential phases 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9.
- **Single-orchestrator:** one long-running agent does all phases with commits-per-phase (highest risk if it stalls; preserves linear history).

**Parking lot** (out of v1 scope; track for follow-on):
- Session-registry persistence across MCP restarts (OQ3) — re-seed from `JulesSession` nodes on startup.
- Auto-approve-plan policy (OQ4) — `policy=auto-if-affects-only` checks plan vs spec's `affects:`.
- C4 (engine.py:102) — MCP-exposed `SkillRun` walker (separate spec).
