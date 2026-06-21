<!-- agency-generated: v1 -->
# adr.extract_decisions

EXTRACT_DECISIONS — surface a spec's key decisions as WH(Y) candidates and (``apply=True``) draft them as ``proposed`` ``Decision``s that ``REFINES`` the spec. **Decidable-first** (no API key): a canonical WH(Y) statement is parsed verbatim (SPEC-001-A), else the ``## Design`` cue sentences + ``## Why``/``## Failure modes`` sections are mined.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (a Document id OR a frontmatter spec_id), theme_id (the AdrTheme to file decisions under; inferred/get-or-created when empty), apply (False = preview only; True = draft the Decisions).` |  |  |

## Returns

``{spec_id, theme_id, candidates: [...], drafted: [ids]}`` or ``{error}``.

## Chain-next

human edits the candidates → apply=True → adr.approve (355) → adr.spec_decisions_ready gates /open→/inprogress (358).

## Details

(no further detail)

## Example

```bash
agency-adr-extract_decisions --intent-id $IID …
```
