<!-- agency-generated: v1 -->
# jules.lint_prompt

Lint a dispatch prompt against the canonical must-name tool list.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text (the dispatch prompt body), must_name (comma-separated override; empty falls back to the canonical list).` |  |  |

## Returns

``{ok, missing, extras}``.

## Chain-next

edit the prompt to add ``missing`` names; re-lint.

## Details

Symmetric with ``plugin.lint_skill``: a pure predicate, no side effects. Consumed by the ``jules-protocol-preamble`` skill Phase 3 (``name-canonical-tools``).

## Example

```bash
agency-jules-lint_prompt --intent-id $IID …
```
