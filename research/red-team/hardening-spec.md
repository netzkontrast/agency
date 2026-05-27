---
spec_id: 150
slug: red-team-hardening
status: ready
owner: jules
depends_on: []
affects:
  - agency/memory.py
  - agency/capabilities/_jules_api.py
  - agency/capabilities/jules.py
  - agency/engine.py
source-repos:
  - url: https://github.com/netzkontrast/the-agency-system
    ref: master
  - url: https://github.com/obra/superpowers-marketplace
    ref: main
  - url: https://github.com/SuperClaude-Org/SuperClaude_Framework
    ref: default
  - url: https://github.com/SuperClaude-Org/SuperClaude_Plugin
    ref: default
  - url: https://github.com/bitwize-music-studio/claude-ai-music-skills
    ref: v0.91.0
estimated_jules_sessions: 2
domain: core
wave: 1
---

# PR1 Hardening Spec

> **Status: ready.** Proposed fixes for the risks identified in the red-team analysis (`research/red-team/FINDINGS.md`).

## Why

The Agency FastMCP plugin PR1 implements the core four-concept model over a bi-temporal graph (`agency/memory.py`). A red-team review revealed four architectural risks:
1. **Code-mode sandbox escape:** The `CodeMode()` transform in `agency/engine.py` executes arbitrary Python. If an attacker can access sensitive environment variables (e.g. `JULES_API_KEY`) before they are cleared, or directly import `sqlite3` to modify the graph without ontology validation, the security boundary fails.
2. **Single-graph scaling cliff:** `Memory._max_persisted_tick` in `agency/memory.py` uses unbounded `MATCH` queries to scan every node and edge. As graph size grows, the O(N) scan linearly degrades the CLI's boot performance.
3. **Provenance trust gap:** `jules.verify` (`agency/capabilities/jules.py`) accepts a `branch_on_remote` boolean from the caller instead of independently verifying it via the `VCSBackend`. This violates the principle established in `Plan/JULES_PROTOCOL.md` §8 that completion cannot be trusted without remote evidence.
4. **Jules API pagination cap:** `_paginate` in `agency/capabilities/_jules_api.py` hardcodes `max_pages=10`, blocking users with >1000 repositories from correctly resolving their github sources.

Furthermore, ingestion of the referenced vendor plugins (bitwize-music, SuperClaude, and superpowers) highlights that relying strictly on the unified MCP surface requires every tool and script in these domains to be correctly mapped and registered. The `hardening-spec.md` establishes the baseline fixes, while subsequent specs will need to address the structural mapping of the ~90 tools in bitwize-music (e.g. `get_streaming_urls`, `list_skills`, `check_explicit_content`, `db_init`, `analyze_audio`), and the extensive references, config, and script tooling inside SuperClaude and superpowers.

## Done When

- [ ] `agency/memory.py` implements a fast O(1) path for `_max_persisted_tick`, either by using an aggregation query or maintaining a `_Metadata:Clock` node.
- [ ] `agency/capabilities/_jules_api.py` modifies the `_paginate` function to stop on `nextPageToken` exhaustion rather than relying on a hardcoded loop count.
- [ ] `agency/capabilities/_vcs.py` adds a new `remote_exists(branch: str)` method to `GitClient` that runs `git ls-remote` (since `state()` only checks local ahead/behind), and `jules.verify` calls this method via the injected `vcs` object.
- [ ] `agency/engine.py` or the CLI initialization path securely removes `JULES_API_KEY` from `os.environ` after capturing it in memory, mitigating exposure to scripts running in the code-mode sandbox. **Test Idea:** A unit test calls the `execute` tool with `import os; return os.environ.get('JULES_API_KEY')` and asserts the result is `None`.


## Source clones

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git        ~/work/vendor/the-agency-system
git clone --depth=1 https://github.com/obra/superpowers-marketplace.git          ~/work/vendor/superpowers-marketplace
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git ~/work/vendor/superclaude-framework
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git    ~/work/vendor/superclaude-plugin
git clone --depth=1 --branch=v0.91.0   https://github.com/bitwize-music-studio/claude-ai-music-skills.git             ~/work/vendor/bitwize-music
```

## Files

- **Create**: none.
- **Modify**:
  - `agency/memory.py`
  - `agency/capabilities/_jules_api.py`
  - `agency/capabilities/jules.py`
  - `agency/engine.py`
  - `agency/capabilities/_vcs.py`
- **Move / Delete**: none.

## Evidence

- Read `~/work/vendor/the-agency-system/Plan/JULES_PROTOCOL.md` (Commit SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22) and `~/work/vendor/the-agency-system/Plan/harness/design.md`.
- Read PR1 work repo files (`agency/memory.py:35-51`, `agency/engine.py:94`, `agency/capabilities/_jules_api.py:32`, `agency/capabilities/jules.py:46-50`, `agency/capabilities/_vcs.py`).
- Identified the scaling, sandbox, remote verification, and pagination limits directly from the PR1 source code.

## Self-Review

1. **Coverage:** 44 of 44 files read (100% of scope).
2. **Residual risk / unknowns:** I could not test the FastMCP CodeMode execution directly to see exactly what `Monty` allows or restricts, so the extent of the sandbox escape risk is theoretical but architecturally present.
3. **Method reflection:** Chesterton's fence forced me to understand *why* the logical clock scan and the `branch_on_remote` boolean exist (stateless CLI boots and delegated capability checks) before attacking them, which led to more accurate risk assessments rather than just saying "this is slow" or "this is insecure."
