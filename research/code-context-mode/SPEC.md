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
estimated_jules_sessions: 2
domain: shared
wave: D
---

# Spec 112 — Code-mode & Context-mode SOTA

## Why
The Agency plugin utilizes FastMCP's Code Mode natively (`agency/engine.py:108`) to reduce the boot token budget to < 500 tokens by exposing only the meta-tools `search`, `get_schema`, and `execute`. While this effectively curtails initial payload size, the current implementation leaks tokens across subsequent round trips. Currently, tool returns are bare dictionaries (`agency/engine.py:91`), forcing the LLM to guess its next step. Additionally, context loading is limited to a single hardcoded tool (`develop.reference` at `agency/capabilities/develop.py:126`), leaving the rest of the documentation graph inaccessible.

By unifying tool returns within a structured envelope (`ToolResult` with `next_suggested_tools`) and generalizing context retrieval into an anchor triad (`context_search`, `context_describe`, `context_invoke`), we achieve maximum token efficiency through precise progressive disclosure (Path B).

## Done When

- [ ] `agency/engine.py` defines a `ToolResult` dataclass envelope containing `result` (dict) and `next_suggested_tools` (list of strings).
- [ ] All auto-wired tools in `agency/engine.py:_wire` wrap capability returns in the `ToolResult` envelope instead of returning a bare dictionary.
- [ ] `agency/capabilities/context.py` is created to export the `ContextCapability` containing the exact anchor triad: `search`, `describe`, and `invoke`.
- [ ] `ContextCapability.search` accepts a query string and returns a `ToolResult` with matching document IDs and points to `capability_context_describe` in `next_suggested_tools`.
- [ ] `ContextCapability.describe` accepts a list of document IDs, returns summaries, and points to `capability_context_invoke` in `next_suggested_tools`.
- [ ] `ContextCapability.invoke` accepts a single document ID, returns the full document text, and suggests relevant actionable capabilities in `next_suggested_tools`.
- [ ] `agency/capabilities/develop.py` drops `reference` as it is fully superseded by `ContextCapability`.
- [ ] `tests/test_agency.py` is updated to assert the presence of `next_suggested_tools` in tool returns and tests the `ContextCapability` anchor triad behavior.
- [ ] `pytest tests/test_agency.py` passes with zero failures.

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
```

## Files

- **Create**:
  - `agency/capabilities/context.py` — The generic context anchor triad capability.
- **Modify**:
  - `agency/engine.py` — Introduce `ToolResult` envelope; modify `_wire` to wrap returns.
  - `agency/capabilities/develop.py` — Remove `reference` verb.
  - `tests/test_agency.py` — Update tests for envelope checking and test `context` capability.
- **Move / Delete**: None.

## Evidence

- **Token Budgets & Code Mode**: `vendor/the-agency-system/Plan/000-overview.md:7` sets the target of `< 4 KB` and `< 500 tokens context`. `agency/engine.py:108` correctly applies `CodeMode()`, leaving only `search`, `get_schema`, and `execute`.
- **Anchor Triads**: `vendor/the-agency-system/Plan/000-overview.md:46` specifies the `*_search`, `*_describe`, `*_invoke` anchor triad pattern.
- **Context Loading**: `agency/capabilities/develop.py:126` currently hardcodes progressive disclosure via `reference(topic)`. It must be migrated to the full anchor triad.
- **Envelope Returns**: `agency/engine.py:91` forces a raw dictionary return: `return out if isinstance(out, dict) else {"result": out}`. It must be updated to structure sequential calls.
- **FastMCP Code Mode**: `https://gofastmcp.com/servers/transforms/code-mode` confirms that `search` and `get_schema` operate purely on metadata, meaning contextual workflow guidance must be pushed into the tool return envelope.

## Self-Review

- **Did I list source clones and exact paths?** Yes, cloned into `~/work/vendor/` with exact SHAs documented.
- **Did I rely on advice or concrete artifacts?** The spec prescribes the exact shape of `ToolResult` and the required methods (`search`, `describe`, `invoke`) for the `ContextCapability`.
- **Did I modify external code?** No, changes are strictly limited to providing the `SPEC.md` artifact within `research/code-context-mode/`.
