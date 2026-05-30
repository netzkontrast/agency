# Schemas Catalogue

This catalogue defines strict strict fields schemas and FastMCP-enriched verb input schemas for the artefact kinds uncovered in the gap analysis.

## 1. Ontology Strict Schemas (`REQUIRED`)

These arrays represent the minimum required fields to be validated via `memory.validate_schema`. They complement the existing `REQUIRED` dictionary in `agency/templates.py`.

```python
REQUIRED.update({
    "baseline": ["workspace", "command", "exit_code", "output"],
    "findings": ["branch", "base", "issues_found", "summary", "details"],
    "jules-session": ["session_id", "url", "state", "history"],
    "reduction": ["parent_intent", "children", "summary"],
    "discipline": ["name", "rules", "checklists"],
    "rationalization-table": ["target", "rule", "rationalization", "verdict"],
    "red-flags": ["source", "issues"],
    "user-confirmed": ["prompt", "response", "timestamp"],
    "authoring": ["task", "files", "diff"],
    "entry": ["key", "value"],
    "lint": ["source", "issues"],
    "manifest": ["components"],
    "rationalizations": ["items"],
})
```

### The Generate ↔ Validate Loop
A verb (`act`) uses the **Template** to structurally compile the raw text or JSON of the payload, ensuring it is always formatted correctly. When the result is committed to memory (`memory.record("Artefact", ...)`), the graph automatically verifies that every key specified in the corresponding **Schema** (`REQUIRED["artefact-kind"]`) is present and non-empty. This completes the generator/validator loop.

## 2. Enriched Verb Input Schemas (FastMCP)

These schema extensions decorate the Python verb functions to make `get_schema` fully self-documenting to standard MCP clients, substituting pure `dict` strings with parameter descriptions, enums, and explicit shapes.

### `workspace.baseline`
*Current:* `def baseline(self, vcs, workspace: str, command: str) -> dict:`
*Proposed Enriched Schema:*
```json
{
  "name": "baseline",
  "description": "Executes a command within an isolated workspace to record a baseline run.",
  "parameters": {
    "type": "object",
    "required": ["workspace", "command"],
    "properties": {
      "workspace": {
        "type": "string",
        "description": "The absolute path to the vcs workspace."
      },
      "command": {
        "type": "string",
        "description": "The bash shell command to execute for the baseline (e.g., 'npm run test')."
      }
    }
  }
}
```

### `delegate.reduce`
*Current:* implicitly relies on `self.ctx.record("Artefact", {"kind": "reduction", "children": children})` within its dispatch fan-out logic.
*Proposed Enriched Input (when exposed as a tool):*
```json
{
  "name": "reduce_intent",
  "description": "Reduces a monolithic parent intent into sub-intents (children).",
  "parameters": {
    "type": "object",
    "required": ["parent_intent", "children", "summary"],
    "properties": {
      "parent_intent": {
        "type": "string",
        "description": "The ID of the Intent node being reduced."
      },
      "children": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of child Intent IDs that replace the parent."
      },
      "summary": {
        "type": "string",
        "description": "A short summary explaining the delegation fan-out strategy."
      }
    }
  }
}
```

### `branch.assess`
*Current:* `def assess(self, vcs, branch: str, base: str = "main") -> dict:`
*Proposed Enriched Schema:*
```json
{
  "name": "assess",
  "description": "Assesses a development branch against a base branch to surface review findings.",
  "parameters": {
    "type": "object",
    "required": ["branch", "base"],
    "properties": {
      "branch": {
        "type": "string",
        "description": "The target branch containing the work to be assessed."
      },
      "base": {
        "type": "string",
        "default": "main",
        "description": "The base branch to diff against (defaults to 'main')."
      }
    }
  }
}
```

### `jules.dispatch`
*Current:* `def dispatch(self, session_url: str = "") -> dict:`
*Proposed Enriched Schema:*
```json
{
  "name": "dispatch",
  "description": "Dispatches a new Jules session or reconnects to an existing one.",
  "parameters": {
    "type": "object",
    "properties": {
      "session_url": {
        "type": "string",
        "description": "Optional URL to an existing Jules chat session to resume.",
        "default": ""
      }
    }
  }
}
```
