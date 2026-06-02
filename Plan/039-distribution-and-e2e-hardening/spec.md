---
spec_id: "039"
slug: distribution-and-e2e-hardening
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [020, 023, 029, 030]
incorporates: [017, 018, 019]
affects:
  - pyproject.toml                                       # [project.scripts] entries + extras_require
  - agency/__main__.py                                   # MCP entrypoint, console-script target
  - agency/cli.py                                        # CLI entrypoint, console-script target
  - agency/install.py                                    # regen contract + traceback truncation
  - agency/engine.py                                     # docstring contract + result-unwrapping discipline
  - agency/capabilities/dogfood.py                       # graph-native ledgers (incorporates Spec 017)
  - agency/capabilities/_jules_skills.py                 # skills use reflect.note instead of disk reads
  - bin/agency-mcp                                       # reduced to a console-script discovery shim
  - bin/agency                                           # reduced to a console-script discovery shim
  - bin/agency-install                                   # still needed for the marketplace-install path
  - .mcp.json                                            # template uses agency-mcp from PATH when present
  - tests/test_e2e_mcp_stdio.py                          # NEW — real JSON-RPC roundtrip over stdio
  - tests/test_e2e_pipx_install.py                       # NEW — pipx install + smoke
  - tests/test_engine_result_envelope.py                 # NEW — Spec 019 docstring lint (incorporated)
  - tests/test_cli_traceback_truncation.py               # NEW — Spec 018 token-leak fix (incorporated)
  - tests/test_install_graph_native.py                   # NEW — Spec 017 graph-record-then-render (incorporated)
estimated_jules_sessions: 3
domain: meta
wave: 2
---

# Spec 039 — Distribution & E2E Hardening

## Why

The audit pass on `claude/blissful-volta-rJ3rP` (PR #17 thread) surfaced
seven findings (F1–F7). Three of them — **F1 (distribution fragility),
F2 (no real MCP-server end-to-end test), F3/F4/F5 (three doctrinal Tech-Debt
specs already drafted but unimplemented)** — share a substrate-hardening
theme and can ship as one coherent PR bundle. F6 (HTTP MCP-client) and
F7 (module decomposition) are deferred to their own specs.

**The core engine is sound.** The plugin's **edges** are brittle:

1. **Installation** is a bash-driven venv-bootstrap (`bin/agency-mcp` calls
   `bin/agency-install` to `pip install -e .` into `${CLAUDE_PLUGIN_ROOT}/.venv`).
   Breaks read-only mounts, immutable images, and any non-marketplace path.
   `pipx` is impossible today.
2. **Tests** never exercise the FastMCP server as a real client would
   (`subprocess.run(...cli...)` tests the CLI, not the MCP wire). A
   broken-on-the-wire server passes CI.
3. **Three identified doctrinal violations** (Specs 017/018/019) are
   documented in the repo but unimplemented. Continuing to add capabilities
   on this substrate accumulates more drift.

This spec makes the plugin **`pipx`-installable from a repo checkout**,
adds **real MCP-server end-to-end tests** (stdio JSON-RPC roundtrip), and
**incorporates Specs 017/018/019** in one PR bundle — because the three are
small, related, and benefit from landing alongside the install + test
hardening.

## Done When

### Distribution (F1)

- [ ] `pyproject.toml` declares console-script entrypoints:
  ```toml
  [project.scripts]
  agency      = "agency.cli:main"            # already present
  agency-mcp  = "agency.__main__:main"       # NEW — the MCP server entry
  agency-doctor = "agency.__main__:doctor_main"  # NEW — bare-CLI doctor
  ```
  `doctor_main()` is a new entrypoint that:
  (a) builds an `Engine(":memory:")`, calls the `agency_doctor` substrate tool,
  (b) prints the JSON payload to stdout (token-safe, scriptable — same shape
      as `python -m agency.cli execute --code ...`),
  (c) returns exit code `0` if `ok=True`, `1` otherwise.
- [ ] `pipx install git+https://github.com/netzkontrast/agency@main` works:
  - `agency-mcp` lands on PATH.
  - `agency-mcp` started without args binds to stdio and serves the
    FastMCP `search`/`get_schema`/`execute` surface.
  - No `${CLAUDE_PLUGIN_ROOT}/.venv` is created during pipx install
    (pipx manages its own venv).
- [ ] `pipx install --editable /path/to/agency` (editable, from local
  checkout — note: `--editable`, NOT `-e`, since pipx 1.4) works with the
  same guarantees.
- [ ] `.mcp.json` template updated: if `agency-mcp` is on PATH, use it
  directly; otherwise fall back to `${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp`
  (the marketplace-install path stays working).
- [ ] `bin/agency-mcp` and `bin/agency` reduced to **discovery shims**:
  - If `agency-mcp` is on PATH, exec it.
  - Else if `${CLAUDE_PLUGIN_ROOT}/.venv/bin/python` exists, use it.
  - Else bootstrap via `bin/agency-install` (existing path, unchanged).
- [ ] `bin/agency-install` continues to work for the marketplace-install
  path (no regression for the path users hit today).
- [ ] `agency_doctor` reports the resolved entrypoint (PATH vs. venv) and
  surfaces the install method in `next_steps[]` when degraded.

### End-to-end tests (F2)

- [ ] `tests/test_e2e_mcp_stdio.py` — spawns the resolved `agency-mcp`
  entrypoint as a subprocess and drives a real JSON-RPC stdio session:
  - `initialize` returns expected `protocolVersion` + `serverInfo.name`.
  - `tools/list` returns the substrate tools (`agency_welcome`,
    `agency_install`, `agency_doctor`, `intent_bootstrap`,
    `lifecycle_gate`, `memory_graph_provenance`) plus three code-mode
    tools (`search`, `get_schema`, `execute`).
  - `tools/call agency_welcome {}` returns the expected payload shape.
  - `tools/call intent_bootstrap {...}` mints an Intent; the returned
    `intent_id` is usable by a subsequent `tools/call execute`.
  - `tools/call execute {code: "return await call_tool('capability_plugin_help', {'intent_id': IID})"}`
    succeeds end-to-end.
- [ ] `tests/test_e2e_pipx_install.py` — runs `pipx install --suffix=test
  $(repo_root)` in a hermetic env, exercises one stdio roundtrip via the
  installed `agency-mcp-test`, then `pipx uninstall agency-test`.
- [ ] Both E2E tests are marked `@pytest.mark.e2e` (slow tag), runnable
  selectively (`pytest -q -m e2e`). CI runs them on a single platform
  (Linux) per push; full matrix on tags.
- [ ] The marker `e2e` is registered in `pyproject.toml`'s
  `[tool.pytest.ini_options].markers` to avoid pytest's
  `PytestUnknownMarkWarning`.
- [ ] Subprocess lifecycle discipline (Nygard — production resilience):
  - Every spawned `agency-mcp` subprocess has a hard timeout (default 10s
    per JSON-RPC roundtrip, 60s for the full test).
  - The fixture uses a try/finally to guarantee `proc.terminate()` and
    `proc.wait(timeout=5)` even on test failure (no zombie processes).
  - Discovery shim failure modes are explicit: if NEITHER `agency-mcp`
    on PATH NOR `${CLAUDE_PLUGIN_ROOT}/.venv/bin/agency-mcp` NOR
    `bin/agency-install` bootstrap succeeds, the shim exits 127 with a
    diagnostic message naming each attempted path (no silent hang, no
    infinite re-bootstrap).

### Spec 017 incorporated — graph-native install ledgers

- [ ] `agency/install.py` writes a `Reflection` node (scope=`technical`,
  body=`<render>`) for each generated artefact BEFORE writing the file.
  The file write becomes a render of the graph state, not the source of
  truth.
- [ ] `agency/capabilities/dogfood.py` ships a `dogfood.render` verb
  (transform) that emits the markdown ledger from `Reflection` nodes.
- [ ] `dogfood.collect` deprecated to a one-shot migration utility (reads
  existing `DOGFOOD-NOTES.md`, writes nodes, exits). Removed on next minor
  bump.
- [ ] `agency/capabilities/_jules_skills.py` uses `reflect.note` from
  code-mode, not file reads.
- [ ] `tests/test_install_graph_native.py` — assert: after
  `agency.install` runs, the `.agency/session.db` contains a `Reflection`
  for every generated file; running `install` twice produces no diff in
  the rendered files and no duplicate Reflections.

### Spec 018 incorporated — CLI token-efficiency

- [ ] `agency.cli execute` truncates Python tracebacks to the
  `ToolError`/`ValueError` message + the originating frame. Full trace
  available behind `--verbose`.
- [ ] `agency.cli execute --fields a,b,c` projects the result dict to
  only those keys (top-level; nested via `a.b` notation).
- [ ] `tests/test_cli_traceback_truncation.py` — assert: a script that
  raises in `execute` returns ≤ 200 tokens by default (down from
  ~thousands today); `--verbose` restores the full trace.

### Spec 019 incorporated — engine result envelope

- [ ] `agency/engine.py` documents the unwrapping contract explicitly:
  the docstring on `Engine._wire` explains that verbs return `{result:
  <delta>}` internally and clients see `<delta>`.
- [ ] `capability_plugin_lint_capability` adds a new rule family,
  `result_envelope`, that fails if a verb's docstring `Returns:` slice
  describes the wrapped shape (`{result: …}`) instead of the unwrapped
  shape.
- [ ] Existing verbs whose docstrings violate the new rule are fixed
  (incremental — same PR if ≤ 10 verbs, otherwise a follow-up). The lint
  starts in `warn` mode for unmarked verbs; `block` mode for scaffolded
  ones.
- [ ] `tests/test_engine_result_envelope.py` — assert: the lint catches
  a violating docstring; a clean docstring passes.

### Migration guarantees

- [ ] No regression in the 309-test baseline (`python -m pytest -q` green).
- [ ] `tests/test_search_isomorphism.py` continues to pass — MCP/CLI parity
  is unbroken.
- [ ] The current marketplace-install path (`/plugin install agency@agency`)
  continues to work without a `pipx` install — the bash wrappers degrade
  to shims, they don't disappear.
- [ ] `agency.install` regenerates `.mcp.json` with the new
  PATH-first / venv-fallback shape; the diff is a one-liner per
  environment.

## Design

### Distribution — what changes, what stays

**What changes:**
- `pyproject.toml` gains two `[project.scripts]` entries — `agency-mcp`
  (the missing one) and `agency-doctor` (a convenience).
- `bin/agency-mcp` and `bin/agency` become **discovery shims** (~15
  lines each), not venv-bootstrappers.
- `.mcp.json` prefers `agency-mcp` on PATH; falls back to the bash wrapper.

**What stays:**
- `bin/agency-install` continues to exist for the marketplace-install
  path (where users haven't pipx'd; the plugin lands in a managed
  `${CLAUDE_PLUGIN_ROOT}` and needs the venv-bootstrap path).
- The auto-discovery contract, the SERVES guard, the four substrate tools
  — all untouched.

**Why not delete the bash wrappers entirely?** Because marketplace
installs (today's only working path) hand the plugin to the host as a
directory tree; the host has no concept of "run `pipx install` on the
tree first". Bash wrappers are still the lowest-friction shim until
Anthropic's plugin host learns to invoke `pipx`.

### The discovery shim (`bin/agency-mcp`)

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# 1. If pipx put agency-mcp on PATH, use it. Most reliable.
if command -v agency-mcp >/dev/null 2>&1; then
  exec agency-mcp "$@"
fi

# 2. If a plugin-local venv exists, use it.
if [[ -x "$ROOT/.venv/bin/agency-mcp" ]]; then
  exec "$ROOT/.venv/bin/agency-mcp" "$@"
fi

# 3. First-run marketplace install: bootstrap the venv, then re-exec.
echo "agency: first run — bootstrapping .venv via bin/agency-install …" >&2
CLAUDE_PLUGIN_ROOT="$ROOT" "$ROOT/bin/agency-install" >&2
exec "$ROOT/.venv/bin/agency-mcp" "$@"
```

The shim is ~15 lines (down from 30+); the heavy lifting is in
`agency-install` (which itself just `pip install -e .`s and regens).

### `.mcp.json` template — new shape

```json
{
  "mcpServers": {
    "agency": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp",
      "args": [],
      "env": {
        "PYTHONPATH":    "${CLAUDE_PLUGIN_ROOT}",
        "AGENCY_DB":     "${CLAUDE_PROJECT_DIR}/.agency/session.db",
        "JULES_API_KEY": "${user_config.jules_api_key}"
      }
    }
  }
}
```

Identical to today's `.mcp.json` — the discovery work happens INSIDE the
shim. This keeps the marketplace path stable; the pipx path benefits
because the shim finds `agency-mcp` on PATH and skips the bootstrap.

### E2E test harness shape

```python
# tests/test_e2e_mcp_stdio.py
import json, subprocess, pytest

@pytest.mark.e2e
def test_initialize_and_tools_list(agency_mcp_binary):
    proc = subprocess.Popen(
        [agency_mcp_binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        env={"AGENCY_DB": ":memory:", **os.environ},
    )
    send_jsonrpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", ...})
    init_resp = recv_jsonrpc(proc)
    assert init_resp["result"]["serverInfo"]["name"] == "agency"

    send_jsonrpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = recv_jsonrpc(proc)["result"]["tools"]
    names = {t["name"] for t in tools}
    assert {"search", "get_schema", "execute",
            "agency_welcome", "intent_bootstrap"} <= names
    proc.stdin.close()
    proc.wait(timeout=5)
```

The `agency_mcp_binary` fixture resolves `agency-mcp` on PATH first, then
the venv, then `bin/agency-mcp` — same logic as the shim. This means the
test covers all three install paths transparently.

### Spec 017 — the graph-record-then-render contract

`agency/install.py` flow becomes:

```python
def install_op(target):
    intent_id = ensure_install_intent()                       # SERVES anchor
    for artefact in MANIFESTS:
        rendered = render_from_engine(artefact, target)        # pure compute
        ref_id = memory.record("Reflection", {
            "scope": "technical",
            "kind": "install-artefact",
            "name": artefact.name,
            "body": rendered,
        })
        memory.link(intent_id, ref_id, "PRODUCES")
        write_disk(artefact.path, rendered)                    # render of the node
```

Re-running `install_op` produces an idempotent set of Reflections (deduped
by `(scope, kind, name)` + content hash) — Spec 017 §"Open Question 1"
resolved: overwriting `DOGFOOD-NOTES.md` natively (return + write together,
the disk file is just a rendered view).

### Spec 018 — traceback truncation

```python
# agency/cli.py
def _emit_error(exc):
    if isinstance(exc, (ToolError, ValueError)):
        return {"error": type(exc).__name__, "message": str(exc),
                "origin": _last_frame(exc.__traceback__)}
    return {"error": type(exc).__name__, "message": str(exc),
            "origin": _last_frame(exc.__traceback__),
            "trace_hint": "rerun with --verbose for full trace"}
```

`--verbose` restores the full `traceback.format_exception()` output.

### Spec 019 — docstring contract

The `Returns:` slice describes what the **caller sees**, not the internal
wrapping. New lint rule family `result_envelope`:

```python
# agency/capabilities/plugin.py — lint_capability addition
def _lint_result_envelope(verb_spec):
    doc = verb_spec["fn"].__doc__ or ""
    returns_slice = parse_slices(doc).get("returns", "")
    if returns_slice.strip().startswith("{result:"):
        return Violation(
            family="result_envelope",
            message="Returns: describes the wrapped shape; document the "
                    "unwrapped delta the caller sees.",
        )
```

## Files

- **Modify:**
  - `pyproject.toml` — `[project.scripts]` entries; possibly new optional
    extras `[e2e]` for pytest-xdist + pexpect (E2E tests).
  - `agency/__main__.py` — add `doctor_main()` console-script target.
  - `agency/cli.py` — traceback truncation, `--fields`, `--verbose`.
  - `agency/install.py` — graph-record-then-render contract.
  - `agency/engine.py` — docstring on `_wire` documenting the envelope.
  - `agency/capabilities/dogfood.py` — `dogfood.render` verb; deprecate
    `collect`.
  - `agency/capabilities/_jules_skills.py` — switch to `reflect.note`.
  - `agency/capabilities/plugin.py` — `result_envelope` lint family.
  - `bin/agency-mcp`, `bin/agency` — reduce to discovery shims.
- **Add:**
  - `tests/test_e2e_mcp_stdio.py` (real JSON-RPC roundtrip).
  - `tests/test_e2e_pipx_install.py` (pipx install + smoke).
  - `tests/test_engine_result_envelope.py` (Spec 019 lint).
  - `tests/test_cli_traceback_truncation.py` (Spec 018).
  - `tests/test_install_graph_native.py` (Spec 017).
  - `tests/conftest.py` — `agency_mcp_binary` fixture (resolution logic
    mirrors the discovery shim — see §"Design"). Adds the `e2e` marker
    registration via `pytest_configure`.
- **Do not modify** (Fowler — keep blast radius small):
  - `agency/{engine,capability,ontology,memory,intent,lifecycle}.py`'s
    auto-discovery contract.
  - The SERVES guard.
  - The four substrate tools.
  - The bi-temporal graph schema (Spec 020) — `.agency/session.db`
    format stays compatible.
  - `agency/capabilities/jules.py` and the `_jules_*` private modules
    — Jules behaviour is out of scope for this hygiene pass.
  - The skill folder layout (`skills/*/SKILL.md`) except where Spec
    033 / 038 already plan changes (no overlap with this spec).

## Open Questions / Needs Research

1. **Pipx and the `.agency/session.db` location.** Today, `AGENCY_DB`
   resolves to `${CLAUDE_PROJECT_DIR}/.agency/session.db`. Under pipx,
   `agency-mcp` runs OUTSIDE Claude Code (e.g. someone curl'd a Jules
   prompt to it). Should the DB default fall back to `$XDG_DATA_HOME/agency/`
   when `CLAUDE_PROJECT_DIR` is unset? Lean yes; needs a sub-decision.
2. **E2E test platform coverage.** The acceptance lists Linux only on
   push; should we matrix-test on macOS-on-tag? The polyglot-hooks issue
   suggests Windows is a third concern but agency ships no hooks, so the
   stdio JSON-RPC path is platform-trivial. Lean: Linux on push, macOS on
   tag, Windows deferred.
3. **`dogfood.collect` deprecation timeline.** Hard-deprecate in this PR
   (raise + redirect) or soft-deprecate (warning) for one minor? Spec 017
   §"Open Question 1" leaned toward returning payloads; this spec leans
   soft-deprecate-one-minor.
4. **Should `agency-mcp` console-script entry-point name conflict with
   anything users install?** The name is generic enough; `pipx list` and
   `which agency-mcp` should be safe. If conflict ever found, rename to
   `agency-mcp-server`.

## Evidence

- Audit conversation: PR #17 thread on `claude/blissful-volta-rJ3rP`
  (Findings F1–F7, Pfad-A choice for hygiene-bundle).
- Related specs (all promoted to standalone, all unimplemented):
  `Plan/017-graph-native-dogfood-ledgers/spec.md`,
  `Plan/018-cli-token-efficiency-bundle/spec.md`,
  `Plan/019-engine-output-shape-contract/spec.md`.
- Architecture review (Spec 015):
  `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md`,
  `Plan/015-architecture-review/PROPOSED-SPECS.md`.
- Current install entrypoints: `bin/agency-mcp`, `bin/agency`,
  `bin/agency-install`.
- Current E2E gap: `tests/test_mcp_bootstrap.py`,
  `tests/test_search_isomorphism.py` (both use `subprocess.run(...cli...)` —
  CLI exercise, not MCP wire).
- Current packaging: `pyproject.toml`'s `[project.scripts]` lists `agency`
  only.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted from the audit conversation; no
code in flight.

### Done
- Audit identifying F1/F2 and the doctrinal Tech-Debt cluster (F3–F5)
  documented in PR #17 thread.
- Specs 017/018/019 (the three to incorporate) have spec.md files; none
  has shipped implementation.
- Spec 029/030 substrate (`agency_welcome`, `agency_install`,
  `agency_doctor`, `intent_bootstrap`) is shipped — this spec builds on it.

### Still to implement
- All the "Done When" checkboxes above.

### Refinement needed
- Open Question 4 (entry-point naming) should be settled before the PR.
- Open Question 1 (pipx + DB default) needs a one-line decision before the
  test fixtures land.
