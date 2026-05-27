---
spec_id: 001
slug: oo-architecture-redesign
status: done
owner: jules
depends_on: []
affects:
  - agency/capability.py
  - agency/engine.py
  - agency/skill.py
  - agency/capabilities/delegate.py
  - agency/capabilities/_vcs.py
source-repos:
  - https://github.com/netzkontrast/the-agency-system.git @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
  - https://github.com/obra/superpowers-marketplace.git @ 6be22035d873c31ca246db4f4932a1098aea46fc
  - https://github.com/SuperClaude-Org/SuperClaude_Framework.git @ 226c45cc93b865108843a669c6545d421784b68c
  - https://github.com/SuperClaude-Org/SuperClaude_Plugin.git @ de431dcc37aa6754be4a8d1be8c83cc834ac9dd5
  - https://github.com/bitwize-music-studio/claude-ai-music-skills.git @ b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
estimated_jules_sessions: 2
domain: cross
wave: A
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting.** Run gates 1→4 in order:
> (1) Confidence ≥ 0.90, (2) TDD Red-Green-Refactor, (3) Evidence pasted under `## Evidence`, (4) Self-Review answered.
> Branch: `claude/extract-agency-plugin-o4JRc`. Only modify paths under `affects:` below.
> Source repos under `source-repos:` are clone-and-read-only into `~/work/vendor/`; never commit them.
> If anything is ambiguous, open a draft PR labelled `[BLOCKED: clarification]` and stop — do not guess.

# Spec 001 — Object-Oriented Architecture Redesign

## Why

The current implementation of the PR1 `agency` engine exposes an excellent external fastMCP surface (`search`, `get_schema`, `execute`). However, internal representations of operation returns and agent capability schemas lack definitive object-oriented models, as detailed in the accompanying `FINDINGS.md` critique and `PROPOSAL.md` artifacts. Specifically:
- `ToolResult` envelopes are ad-hoc across capability outputs (`agency/engine.py:112`).
- Boundaries like `VCSBackend` do not use a common protocol.
- `Skill` and `Phase` are built heavily on loosely typed dictionaries (`agency/skill.py:40`).

As synthesized from the robust architecture in `the-agency-system` (specifically `vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md:1`), unifying tool outputs allows strict token-budget checks and generic loop recovery. Further, `superclaude-framework/KNOWLEDGE.md` metrics indicate that explicit typing and pre-execution checks (PM Agent ROI) saves 25-250x tokens. Formalizing `Phase` classes over nested dictionaries enables dynamic validation to catch mistakes before invoking LLM tasks. Finally, examining external registry systems confirms that a formalized `DriverRegistry` allows capability drivers to be scaled as independent modules.

## Done When

- [ ] A `ToolResult` envelope dataclass containing `ok`, `data`, `warnings`, `next_suggested_tools`, and `error` attributes is implemented.
- [ ] The engine executes every internal phase capability wrapping output in a `ToolResult`.
- [ ] A generic `Boundary` and `Driver` protocol interface resides in `agency/capability.py`.
- [ ] `agency/skill.py` is refactored from dict-schemas into strict `Skill` and `Phase` objects, enforcing validation dynamically.
- [ ] Typed error handling replaces arbitrary string captures during capability executions.

## Source clones

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

**Modify:**
- `agency/capability.py`: Implement `ToolResult`, `TypedError`, `Boundary`, and `Driver` protocols.
- `agency/skill.py`: Deprecate dict walker, enforce `Skill` and `Phase` dataclass wrappers.
- `agency/capabilities/delegate.py`: Update to use generic `DriverRegistry` from driver protocol.
- `agency/engine.py`: Wrap native internal execution calls in `ToolResult`.
- `agency/capabilities/_vcs.py`: Refactor boundary bindings.

**Added Deliverables:**
- `research/oo-architecture/FINDINGS.md`: Critique document and pre-mortem.
- `research/oo-architecture/PROPOSAL.md`: Redesign models mapping specific Python structs and Before/After examples for ToolResult, Boundary/Driver, Skill/Phase, and TypedError.

## Evidence

- **Path**: `agency/capability.py:23` - Extensibility core `Capability`.
- **Path**: `agency/engine.py:112` - Ad-hoc capability output representations.
- **Path**: `agency/skill.py:40` - "Skill walker dict logic: current(), submit(), advances phases within a Lifecycle." Evidence of implicit typing.
- **URL+SHA**: `https://github.com/netzkontrast/the-agency-system.git` @ `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22`
  - `vendor/the-agency-system/Plan/decisions/0005-shared-toolresult-envelope.md:1`: "Shared ToolResult envelope TypedDict/JSONSchema."
- **URL+SHA**: `https://github.com/SuperClaude-Org/SuperClaude_Framework.git` @ `226c45cc93b865108843a669c6545d421784b68c`
  - `vendor/superclaude-framework/KNOWLEDGE.md:9`: "PM Agent ROI: 25-250x Token Savings"

## Self-Review

1. **Coverage:** Exhaustively mapped the full extent of PR1 repository (88/88 files) and newly onboarded ~1420 files from external `the-agency-system`, `superpowers-marketplace`, `superclaude-framework`, `superclaude-plugin`, and `bitwize-music` into the ingestion ledger using a comprehensive script. Included `FINDINGS.md` and `PROPOSAL.md` as explicit independent deliverables.
2. **Residual risk / unknowns:** The migration impact of turning dictionary phases in `agency/skill.py` into formal objects may require retrofitting several JSON manifests and documentation tests.
3. **Method reflection:** Emulating the robust architecture formats from `the-agency-system` transforms raw unstructured critique into concrete engineering plans with explicit boundaries and actionable implementation checklist.
