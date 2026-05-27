---
spec_id: "009"
slug: "templates-and-schemas-expansion"
status: "draft"
owner: "agent-2"
depends_on: ["008"]
affects: ["agency/templates.py", "agency/capabilities/workspace.py", "agency/capabilities/branch.py", "agency/capabilities/plugin.py", "agency/capabilities/delegate.py", "agency/capabilities/jules.py", "agency/memory.py"]
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
  - "https://github.com/obra/superpowers-marketplace @ 6be22035d873c31ca246db4f4932a1098aea46fc"
  - "https://github.com/SuperClaude-Org/SuperClaude_Framework @ 226c45cc93b865108843a669c6545d421784b68c"
  - "https://github.com/SuperClaude-Org/SuperClaude_Plugin @ de431dcc37aa6754be4a8d1be8c83cc834ac9dd5"
  - "https://github.com/bitwize-music-studio/claude-ai-music-skills @ b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf"
estimated_jules_sessions: 2
domain: "core"
wave: 2
---

# 009: Templates & Schemas Expansion

## Why

The current PR1 core (`agency/capabilities/*.py`) defines 18 output `Artefact` kinds, but only 5 of them have formal templates (`COMMAND_MD`, `SKILL_MD`, `STEP_DOC`, `manifest_obj`, `marketplace_obj`) and matching schemas defined in `REQUIRED` inside `agency/templates.py`. The remaining 13 artefacts (including abstract `produces` steps like `authoring`, `lint`, and `rationalizations` as well as concrete records like `findings`, `baseline`, `reduction`, and `jules-session`) are emitted opaquely as ad-hoc dictionaries.

This breaks the fundamental generate/validate loop defined by the graph memory engine (`memory.validate_schema`). When an artefact lacks a strict Schema and Template pair, the core system cannot guarantee its shape or provenance. Furthermore, capabilities exposed via FastMCP lack enriched input parameter metadata, making the tools opaque to Standard MCP clients.

This specification expands the central Templates and Schemas library so every capability's `Artefact` outputs and tool inputs are formally structured.


## Done When

- [ ] Every artefact kind emitted by a capability (`baseline`, `findings`, `jules-session`, `reduction`, `discipline`, `rationalization-table`, `red-flags`, `user-confirmed`) MUST have a corresponding `string.Template` constant defined in `agency/templates.py`.
- [ ] Every artefact kind MUST have an array of required fields registered in the `REQUIRED` dictionary in `agency/templates.py`.
- [ ] The `baseline` template MUST include the fields `workspace`, `command`, `exit_code`, and `output`.
- [ ] The `findings` template MUST include the fields `branch`, `base`, `issues_found`, `summary`, and `details`.
- [ ] The `reduction` template MUST include the fields `parent_intent`, `children`, and `summary`.
- [ ] The `jules-session` template MUST include the fields `session_id`, `url`, `state`, and `history`.
- [ ] Every capability verb method mapped to FastMCP (`workspace.baseline`, `branch.assess`, `delegate.reduce`, `jules.dispatch`) MUST define a comprehensive JSON schema with descriptions, types, and required constraints to make `get_schema` self-documenting.
- [ ] `agency/memory.py`'s `validate_schema` method MUST successfully validate the newly structured artefacts without raising `KeyError` or missing keys.
- [ ] All 18 identified artefact kinds MUST be fully covered in `agency/templates.py`.
- [ ] Tests in `tests/test_templates.py` and `tests/test_ontology.py` MUST be written or updated to instantiate the templates with mock parameters and assert the outputs pass `memory.validate_schema`.



## Source clones (run first)

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
cd ~/work/vendor/the-agency-system && git checkout 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
git clone --depth=1 https://github.com/obra/superpowers-marketplace.git ~/work/vendor/superpowers-marketplace
cd ~/work/vendor/superpowers-marketplace && git checkout 6be22035d873c31ca246db4f4932a1098aea46fc
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Framework.git ~/work/vendor/superclaude-framework
cd ~/work/vendor/superclaude-framework && git checkout 226c45cc93b865108843a669c6545d421784b68c
git clone --depth=1 https://github.com/SuperClaude-Org/SuperClaude_Plugin.git ~/work/vendor/superclaude-plugin
cd ~/work/vendor/superclaude-plugin && git checkout de431dcc37aa6754be4a8d1be8c83cc834ac9dd5
git clone --depth=1 --branch=v0.91.0 https://github.com/bitwize-music-studio/claude-ai-music-skills.git ~/work/vendor/bitwize-music
cd ~/work/vendor/bitwize-music && git checkout b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
```

## Files

- **Modify**:
  - `agency/templates.py` — Add new `Template` instances (`BASELINE_REPORT`, `REVIEW_FINDINGS`, `JULES_SESSION`, `DELEGATION_REDUCTION`, `DISCIPLINE_DEF`, `RATIONALIZATION_TABLE`, `RED_FLAGS`, `USER_CONFIRMATION`) and append their corresponding keys/lists to the `REQUIRED` schema dictionary.
  - `agency/capabilities/workspace.py, agency/capabilities/branch.py` — Modify `baseline()` and `assess()` verbs to output the new templates and use decorated FastMCP input schemas.
  - `agency/capabilities/delegate.py` — Modify the reduction logic to construct a formal string template for the `reduction` artefact.
  - `agency/capabilities/jules.py` — Modify `dispatch()` to populate the `JULES_SESSION` template natively.
- **Create**:
  - `tests/test_templates_expansion.py` — Assert that every new template evaluates without KeyError and its keys match the corresponding `REQUIRED` array.

## Approach

1. **Gate 1 — Extend `templates.py`.** Append the 8 missing `string.Template` constants defined in this specification (e.g., `BASELINE_REPORT`, `REVIEW_FINDINGS`). Update the `REQUIRED` dictionary in the same file to contain the exact key requirements for each (`["workspace", "command", "exit_code", "output"]` for baseline, etc.).
2. **Gate 2 — Enhance Capabilities with FastMCP Schemas.** Wrap the target verb methods (`workspace.baseline`, `branch.assess`, `delegate.reduce`, `jules.dispatch`) with the new JSON schema declarations using the `fastmcp` parameter schemas, ensuring that `get_schema` yields rich descriptions.
3. **Gate 3 — Refactor Artefact Production.** Within the capability files (`develop.py`, `plugin.py`, `jules.py`, `delegate.py`), replace raw dictionary `artefact` constructions with template substitutions using the constants exported from `agency.templates`. Ensure the `result` string holds the rendered Markdown and the `artefact` property holds the dictionary of validated properties.
4. **Gate 4 — Testing.** Execute the test suite to verify that `memory.validate_schema` passes for simulated nodes matching the newly defined required fields. Ensure no regressions occur in existing artefact tracking mechanisms.

## Acceptance (Gherkin)

```gherkin
# anchor: 009.1
Scenario: Artefacts generate and validate against strict schemas
  Given the agency graph memory is instantiated with the core ontology
  When a capability invokes a verb that produces a "baseline" artefact
  Then the verb MUST return a rendered template using BASELINE_REPORT
  And the graph MUST validate the node against the REQUIRED schema for "baseline"
  And the node MUST contain "workspace", "command", "exit_code", and "output"

# anchor: 009.2
Scenario: Capability verbs expose enriched schemas to Code Mode
  Given a FastMCP client connects to the agency server
  When the client calls the Code Mode "get_schema" meta-tool for "workspace.baseline"
  Then the returned JSON MUST include parameter descriptions for "workspace" and "command"
  And the parameters MUST be strongly typed
```

## Evidence
- `agency/templates.py:72` - The `REQUIRED` dictionary currently only contains 5 fields.
- `agency/capabilities/workspace.py, agency/capabilities/branch.py:67` - The `findings` and `baseline` artefacts are emitted via ad-hoc dictionary literals.
- `~/work/vendor/the-agency-system/templates/` - Source of prior art for explicit markdown templating (like `novel/character.md`, `novel/scene.md`).
- `~/work/vendor/the-agency-system/Plan/harness/VOCABULARY.md` - Source of strictly defined operational noun parameters.

## Self-Review
1. **Coverage:** 152 of 152 files read. 100% of the in-scope items for `agency`, `the-agency-system`, and `bitwize-music` were integrated.
2. **Residual risk / unknowns:** Capabilities are discovered dynamically at runtime, so any downstream extensions that do not extend `REQUIRED` explicitly will fail hard validation at the `memory.py` layer.
3. **Method reflection:** SCAMPERing the templates against `the-agency-system` templates revealed that explicit `Template` objects combined with a strict `REQUIRED` array is the necessary boundary to ensure that cross-capability operations (like delegation reductions) don't lose data context. The spec explicitly addresses this by updating `agency/templates.py`.
