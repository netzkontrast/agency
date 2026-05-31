---
spec_id: "030"
slug: jules-key-doctor-stateful-welcome
status: draft
owner: "@agency"
depends_on: ["029"]
affects:
  - agency/capabilities/_jules_api.py    # F2: better key error message
  - agency/engine.py                      # +agency_doctor substrate tool; agency_welcome state-aware
  - AGENTS.md                             # F5: venv-required note
  - tests/test_jules_key_error.py         # NEW — message names user_config + doctor
  - tests/test_agency_doctor.py           # NEW — doctor report shape + JULES_API_KEY redaction
  - tests/test_welcome_state.py           # NEW — welcome adapts to intents_count
estimated_jules_sessions: 0
domain: substrate
wave: 4
---

# Spec 030 — JULES_API_KEY clarity + agency_doctor + stateful welcome

## Why

Spec 029 closed F1/F4/F6. Three remaining Fehlerbericht findings need
attention before the agency plugin is truly self-explanatory:

- **F2 (Hoch)** — `JULES_API_KEY` error message is misleading.
  The current text says "Export it in the shell that launched the
  engine" — but for a marketplace-installed plugin the launching
  shell is Claude Code's, not the user's; the key is wired via
  `${user_config.jules_api_key}` at MCP server start. The user
  needs to know that, not the generic shell-export advice.

- **No diagnostic substrate tool.** When a fresh MCP client hits a
  silent failure (system `python3` without `graphqlite`, F5; or the
  key-substitution timing of F2), they have no single call that
  reports "what's broken." `agency_welcome` is for *first contact*;
  a separate `agency_doctor` covers *debugging*.

- **Empty-graph onboarding.** A fresh agent that calls `search` on
  an empty graph gets no hits and no hint. Spec 029 §B noted this
  but deferred. Cleanest fix: make `agency_welcome` state-aware so
  the canonical onboarding tool also serves session resumption.

## Done When

### A. F2 — `_api_key()` error message names user_config and doctor

- [ ] In `agency/capabilities/_jules_api.py::_api_key`, the
  `RuntimeError` message names:
  - `user_config.jules_api_key` (the marketplace plugin's wiring),
  - "reload the plugin" (the only fix that picks up an updated
    user_config in a marketplace install),
  - `agency_doctor` (the diagnostic substrate tool that confirms
    whether the key was inherited), and
  - the bash side-pipe (`JULES_API_KEY=... python -m agency.cli execute …`)
    for Jules / no-MCP hosts.
- [ ] Verified by `test_jules_key_error_names_user_config_and_doctor`.

### B. `agency_doctor()` substrate tool

- [ ] New tool in `engine.py::build_mcp`, alongside the Spec 029 trio.
- [ ] Returns a structured report `{ok, python_version, deps,
  db: {path, exists, writable}, env: {JULES_API_KEY, CLAUDE_PROJECT_DIR},
  next_steps: [...]}` where:
  - `ok` — `True` iff zero issues; `False` if any next_step is present.
  - `python_version` — e.g. `"3.11.15"`.
  - `deps` — `{fastmcp: "x.y.z"|"missing", graphqlite: "x.y.z"|"missing",
    tiktoken: "x.y.z"|"missing"}`.
  - `db.path` — resolved path (Spec 020 order).
  - `db.exists` — bool: does the file exist?
  - `db.writable` — bool: can the engine write to it (creates parent)?
  - `env.JULES_API_KEY` — `"set"` or `"missing"` — NEVER reveal the value.
  - `env.CLAUDE_PROJECT_DIR` — the literal env value or empty string.
  - `next_steps` — copy-pasteable strings, one per issue
    (`agency_install` if `.agency/` missing; the marketplace reload
    advice if `JULES_API_KEY` missing; etc.).
- [ ] **Security invariant.** The JULES_API_KEY VALUE is never in the
  report — only its presence/absence. Verified by
  `test_doctor_does_not_leak_jules_key`.
- [ ] No `intent_id` required (pure introspection, like `agency_welcome`).

### C. Stateful `agency_welcome`

- [ ] `agency_welcome` now returns an additional field
  `state: "fresh" | "in_progress"`:
  - `fresh` — Intent count == 0; the `next` list leads with
    `agency_install` + `intent_bootstrap`.
  - `in_progress` — Intent count > 0; the `next` list leads with
    `search('<keyword>')` + `memory_graph_provenance(intent_id)` and
    surfaces the most recent intent_id under `last_intent`.
- [ ] No graph WRITES — purely a read of `memory.find('Intent')`.
- [ ] Token budget invariant kept (≤ 1 KB total payload).
- [ ] Verified by `test_welcome_fresh_state` + `test_welcome_in_progress_state`.

### D. AGENTS.md — F5 venv note

- [ ] One paragraph added to AGENTS.md's "Dev" section saying that
  any direct `python -m agency.*` invocation MUST use the plugin venv
  (otherwise `ModuleNotFoundError: graphqlite` writes nothing — the
  silent-fail F5 documented).
- [ ] Mention `agency_doctor` as the way to confirm deps are present.

## Files

```
agency/capabilities/_jules_api.py        # F2 error message
agency/engine.py                          # +agency_doctor; agency_welcome state-aware
AGENTS.md                                 # F5 venv note
tests/test_jules_key_error.py             # NEW
tests/test_agency_doctor.py               # NEW (incl. security: no key in report)
tests/test_welcome_state.py               # NEW (fresh / in_progress branches)
```

## Open Questions

- **OQ-1 — Should `agency_doctor` open the DB?** Opening the DB to
  check writability has a side effect (graphqlite creates the file
  on first open). Resolution: probe by attempting `os.access` +
  `os.makedirs(parent, exist_ok=True)`; do not open the DB itself
  (cheaper, no side effect). The file's existence is the signal
  agents need; opening it is what intent_bootstrap does.

- **OQ-2 — Should the empty-graph search hint be a separate tool?**
  Considered; rejected. Wrapping FastMCP's builtin `search` requires
  CodeMode internals we shouldn't touch. The stateful `agency_welcome`
  is the canonical onboarding tool and naturally subsumes the
  use case ("agent calls welcome → sees fresh state → calls intent_bootstrap").

## Non-goals

- **F3** (sandbox timeout batch idempotency) — still out of scope;
  requires the Spec 031 idempotency-key work.
- **Substitution-timing reload.** The plugin cannot make
  `${user_config.jules_api_key}` re-evaluate without a server
  restart — that's Claude Code's contract. We only IMPROVE the
  message so the user knows to restart.

## Evidence

- KP Fehlerbericht F2 / F5 — `Plan/AGENCY-PLUGIN-FEHLERBERICHT.md`.
- Spec 029 §B (deferred empty-graph hint) — `Plan/029-mcp-bootstrap-and-self-explain/spec.md`.
