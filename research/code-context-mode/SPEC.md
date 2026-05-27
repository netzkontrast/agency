---
spec_id: 112
slug: code-context-mode-sota
status: draft
owner: jules
depends_on: []
affects:
  - agency/engine.py
  - agency/capabilities/develop.py
source-repos:
  - url: https://github.com/netzkontrast/the-agency-system.git
    ref: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
  - url: https://github.com/obra/superpowers-marketplace.git
    ref: 6be22035d873c31ca246db4f4932a1098aea46fc
  - url: https://github.com/SuperClaude-Org/SuperClaude_Framework.git
    ref: 226c45cc93b865108843a669c6545d421784b68c
  - url: https://github.com/SuperClaude-Org/SuperClaude_Plugin.git
    ref: de431dcc37aa6754be4a8d1be8c83cc834ac9dd5
  - url: https://github.com/bitwize-music-studio/claude-ai-music-skills.git
    ref: b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
  - url: https://github.com/mksglu/context-mode.git
    ref: 11aeb2659e9c70811eef2a875704149e836ec9c4
estimated_jules_sessions: 3
domain: shared
wave: D
---

# Spec 112 — Code-mode & Context-mode SOTA Integration

## Why
The Agency plugin utilizes FastMCP's Code Mode natively (`agency/engine.py:108`) to reduce the boot token budget to < 500 tokens by exposing only the meta-tools `search`, `get_schema`, and `execute`. While this effectively curtails initial payload size, the current implementation leaks tokens across subsequent round trips.

First, tool returns are bare dictionaries (`agency/engine.py:91`), forcing the LLM to guess its next step. Second, context loading is limited to a single hardcoded tool (`develop.reference` at `agency/capabilities/develop.py:126`), leaving the rest of the documentation graph inaccessible. Finally, file reads and context insight events are un-optimized, incurring full token costs on repetitive accesses.

By integrating the external `context-mode` plugin patterns, we adopt a true **Path B Token Efficiency** model. We introduce:
1. **ToolResult Envelopes (Spec 130)**: Structured sequential guidance (`next_suggested_tools`) preventing token waste on orienting round-trips.
2. **Context Anchor Triad (Path B)**: A generic `context_search`, `context_describe`, `context_invoke` anchor triad over the entire documentation corpus indexed by a manifest (`context_manifest.json` - Spec 111).
3. **SessionDB / Hooks / Cache Integration (Specs 108, 114)**: Adopting the 5-hook standard (PreToolUse/PostToolUse) to route telemetry events to `/ctx-insight` while intercepting and diffing large file reads via a `difflib.unified_diff` cache to yield ~97% savings on subsequent reads.

## Done When

- [ ] `agency/engine.py` defines a `ToolResult` dataclass envelope (from Spec 130) containing `result` (dict), `ok` (bool), `error` (optional `ErrorInfo`), and `next_suggested_tools` (list of strings).
- [ ] All auto-wired tools in `agency/engine.py:_wire` wrap capability returns in the `ToolResult` envelope instead of returning a bare dictionary.
- [ ] `agency/capabilities/context.py` is created to export the `ContextCapability` containing the exact anchor triad: `search`, `describe`, and `invoke`.
- [ ] `ContextCapability.search` queries the BM25/manifest index from Spec 111, returns a `ToolResult` with matching document IDs, and points to `capability_context_describe` in `next_suggested_tools`.
- [ ] `ContextCapability.describe` accepts a list of document IDs, returns views (`views.summary` / `views.preview`), and points to `capability_context_invoke` in `next_suggested_tools`.
- [ ] `ContextCapability.invoke` accepts a single document ID, returns the full document text, and suggests relevant actionable capabilities.
- [ ] `agency/capabilities/develop.py` drops `reference` as it is fully superseded by `ContextCapability`.
- [ ] `hooks/hooks.json` declares the 5 entry points (`PreToolUse`, `PostToolUse`, `SessionStart`, `PreCompact`, `UserPromptSubmit`) syncing with the external `context-mode` execution pipeline.
- [ ] `agency_mcp/lib/codemode/read_cache.py` is authored, exposing `get`/`put` cache checks for file sizes < 50 KB on `PreToolUse`, invoking `difflib.unified_diff` on re-reads.
- [ ] `pytest tests/test_agency.py` passes with zero failures, alongside integration checks proving delta compression works.

## Source clones (run first)

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22

git clone --depth=1 https://github.com/obra/superpowers-marketplace.git ~/work/vendor/superpowers-marketplace
# SHA: 6be22035d873c31ca246db4f4932a1098aea46fc

git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git ~/work/vendor/superclaude-framework
# SHA: 226c45cc93b865108843a669c6545d421784b68c

git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git ~/work/vendor/superclaude-plugin
# SHA: de431dcc37aa6754be4a8d1be8c83cc834ac9dd5

git clone --depth=1 --branch=v0.91.0 https://github.com/bitwize-music-studio/claude-ai-music-skills.git ~/work/vendor/bitwize-music
# SHA: b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf

git clone --depth=1 --branch=main https://github.com/mksglu/context-mode.git ~/work/vendor/context-mode
# SHA: 11aeb2659e9c70811eef2a875704149e836ec9c4
```

## Files

- **Create**:
  - `agency/capabilities/context.py` — The generic context anchor triad capability.
  - `agency/hooks/hooks.json` — 5-hook orchestration configuration bridging to `SessionDB` / `context-mode`.
  - `agency/lib/codemode/read_cache.py` — LRU File Read cache to prevent full re-read token bursts.
  - `agency/lib/codemode/delta_diff.py` — `difflib.unified_diff` engine yielding `+N/-M` summaries for `PreToolUse`.
  - `agency/lib/envelope/models.py` — Dataclasses for `ToolResult` and `ErrorInfo`.
- **Modify**:
  - `agency/engine.py` — Introduce `ToolResult` envelope; modify `_wire` to wrap returns via `wrap_envelope`.
  - `agency/capabilities/develop.py` — Remove `reference` verb.
  - `tests/test_agency.py` — Update tests for envelope checking and test `context` capability, context manifest index searches, and delta compression.
- **Move / Delete**: None.

## Evidence

- **Token Budgets & Code Mode**: `vendor/the-agency-system/Plan/000-overview.md:7` sets the target of `< 4 KB` and `< 500 tokens context`. `agency/engine.py:108` correctly applies `CodeMode()`.
- **Anchor Triads**: `vendor/the-agency-system/Plan/000-overview.md:46` specifies the `*_search`, `*_describe`, `*_invoke` anchor triad pattern natively consuming `context_manifest.json` metadata indexes.
- **Envelope Returns**: `vendor/the-agency-system/Plan/130-shared-toolresult-envelope/spec.md` strictly bans bare dict returns: `"ok": True` and structured typing (`ToolResult`) are strictly required.
- **SessionDB Multi-writer / Hooks**: `vendor/context-mode/docs/adr/0001-sessiondb-multi-writer.md` outlines how SQLite natively supports concurrent `PreToolUse`/`PostToolUse` event telemetry tracking via `SessionDB`.
- **Read Cache Delta Mode**: `vendor/the-agency-system/Plan/114-read-cache-delta-mode/spec.md` specifies capturing `PreToolUse` on Read tools to slice token costs down 97% using unified diff outputs restricted to 1500 chars / 50 KB.

## Self-Review

- **Did I list source clones and exact paths?** Yes, cloned into `~/work/vendor/` with exact SHAs documented, including the new `context-mode` source repository.
- **Did I rely on advice or concrete artifacts?** The spec explicitly codifies architecture: dictating the integration of `SessionDB`, `hooks.json` declarations, the HTTP/local `/ctx-insight` pattern, and `difflib.unified_diff` boundaries.
- **Did I modify external code?** No, changes are strictly limited to providing the updated `SPEC.md` and `_ingest.md` files within `research/code-context-mode/`.
