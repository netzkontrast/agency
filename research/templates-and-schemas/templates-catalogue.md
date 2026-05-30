# Templates Catalogue

This catalogue defines concrete `string.Template`-style skeletons for the artefact kinds uncovered in the gap analysis (see `FINDINGS.md`) that currently lack a template.

## 1. Baseline Report
**Artefact Kind:** `baseline`
**Fields:** `workspace`, `command`, `exit_code`, `output`

```python
BASELINE_REPORT = Template(
    "---\n"
    "kind: baseline\n"
    "workspace: $workspace\n"
    "command: $command\n"
    "exit-code: $exit_code\n"
    "---\n"
    "\n"
    "# Baseline Run\n"
    "\n"
    "## Output\n"
    "```\n"
    "$output\n"
    "```\n"
)
```

**Rendered Example:**
```markdown
---
kind: baseline
workspace: /tmp/worktree-abc
command: npm run build
exit-code: 0
---

# Baseline Run

## Output
```
> build
> tsc
Done in 1.2s.
```
```

## 2. Review Findings
**Artefact Kind:** `findings`
**Fields:** `branch`, `base`, `issues_found`, `summary`, `details`

```python
REVIEW_FINDINGS = Template(
    "---\n"
    "kind: findings\n"
    "branch: $branch\n"
    "base: $base\n"
    "issues-found: $issues_found\n"
    "---\n"
    "\n"
    "# Findings Summary\n"
    "$summary\n"
    "\n"
    "## Details\n"
    "$details\n"
)
```

**Rendered Example:**
```markdown
---
kind: findings
branch: feature/auth
base: main
issues-found: 2
---

# Findings Summary
Two minor style violations found in the core handlers.

## Details
- `handlers.py:22`: Missing type hint on `authenticate`.
- `handlers.py:45`: Unused import `sys`.
```

## 3. Jules Session
**Artefact Kind:** `jules-session`
**Fields:** `session_id`, `url`, `state`, `history`

```python
JULES_SESSION = Template(
    "---\n"
    "kind: jules-session\n"
    "session-id: $session_id\n"
    "url: $url\n"
    "state: $state\n"
    "---\n"
    "\n"
    "# Session Log\n"
    "$history\n"
)
```

**Rendered Example:**
```markdown
---
kind: jules-session
session-id: sess_9f8d7a
url: https://claude.ai/chat/sess_9f8d7a
state: completed
---

# Session Log
- **System**: Initialized
- **Agent**: Explored directory `tests/`
- **Agent**: Ran `pytest tests/` (exit 0)
```

## 4. Delegation Reduction
**Artefact Kind:** `reduction`
**Fields:** `parent_intent`, `children`, `summary`

```python
DELEGATION_REDUCTION = Template(
    "---\n"
    "kind: reduction\n"
    "parent-intent: $parent_intent\n"
    "children: $children\n"
    "---\n"
    "\n"
    "# Reduction Summary\n"
    "$summary\n"
)
```

**Rendered Example:**
```markdown
---
kind: reduction
parent-intent: int_a1b2c3
children: int_x9y8z7, int_m4n5o6
---

# Reduction Summary
The monolithic feature request was fanned out into a database schema migration and an API endpoint update.
```

## 5. Discipline Definition
**Artefact Kind:** `discipline`
**Fields:** `name`, `rules`, `checklists`

```python
DISCIPLINE_DEF = Template(
    "---\n"
    "kind: discipline\n"
    "name: $name\n"
    "---\n"
    "\n"
    "# Rules\n"
    "$rules\n"
    "\n"
    "## Checklists\n"
    "$checklists\n"
)
```

**Rendered Example:**
```markdown
---
kind: discipline
name: Python Code Health
---

# Rules
- All functions must have type hints.
- No unused imports.

## Checklists
- [ ] Run `ruff check .`
- [ ] Run `mypy .`
```

## 6. Rationalization Table
**Artefact Kind:** `rationalization-table`
**Fields:** `target`, `rule`, `rationalization`, `verdict`

```python
RATIONALIZATION_TABLE = Template(
    "---\n"
    "kind: rationalization-table\n"
    "target: $target\n"
    "---\n"
    "\n"
    "| Rule | Rationalization | Verdict |\n"
    "|---|---|---|\n"
    "| $rule | $rationalization | $verdict |\n"
)
```

**Rendered Example:**
```markdown
---
kind: rationalization-table
target: auth_plugin
---

| Rule | Rationalization | Verdict |
|---|---|---|
| No raw SQL | Uses ORM for all queries. | PASS |
```

## 7. Lint / Red Flags
**Artefact Kind:** `red-flags` (also used for `lint` and `authoring` feedback)
**Fields:** `source`, `issues`

```python
RED_FLAGS = Template(
    "---\n"
    "kind: red-flags\n"
    "source: $source\n"
    "---\n"
    "\n"
    "# Issues Found\n"
    "$issues\n"
)
```

**Rendered Example:**
```markdown
---
kind: red-flags
source: skill_generator.py
---

# Issues Found
- Hardcoded absolute paths on line 42.
- Missing exception handling block.
```

## 8. User Confirmation
**Artefact Kind:** `user-confirmed`
**Fields:** `prompt`, `response`, `timestamp`

```python
USER_CONFIRMATION = Template(
    "---\n"
    "kind: user-confirmed\n"
    "timestamp: $timestamp\n"
    "---\n"
    "\n"
    "**Prompt:** $prompt\n"
    "**Response:** $response\n"
)
```

**Rendered Example:**
```markdown
---
kind: user-confirmed
timestamp: 2024-05-27T10:15:30Z
---

**Prompt:** Deploy to production?
**Response:** YES
```

## 9. Authoring
**Artefact Kind:** `authoring`
**Fields:** `task`, `files`, `diff`
```python
AUTHORING_RECORD = Template(
    "---\nkind: authoring\ntask: $task\n---\n\n# Files\n$files\n\n## Diff\n```diff\n$diff\n```\n"
)
```

## 10. Generic Entry
**Artefact Kind:** `entry`
**Fields:** `key`, `value`
```python
GENERIC_ENTRY = Template(
    "---\nkind: entry\nkey: $key\n---\n\n# Value\n$value\n"
)
```

## 11. Lint Report
**Artefact Kind:** `lint`
**Fields:** `source`, `issues`
*(Re-uses RED_FLAGS template structure)*
```python
LINT_REPORT = Template(
    "---\nkind: lint\nsource: $source\n---\n\n# Issues Found\n$issues\n"
)
```

## 12. Component Manifest
**Artefact Kind:** `manifest`
**Fields:** `components`
```python
COMPONENT_MANIFEST = Template(
    "---\nkind: manifest\n---\n\n# Components\n$components\n"
)
```

## 13. Rationalizations
**Artefact Kind:** `rationalizations`
**Fields:** `items`
```python
RATIONALIZATIONS_LIST = Template(
    "---\nkind: rationalizations\n---\n\n# Items\n$items\n"
)
```
