<!-- agency-generated: v1 -->
# music.research_scope

Define a research question + plan specialist domains (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `question, album (optional slug), depth (brief/standard/deep).` |  |  |

## Returns

``{research_id, specialists, plan, album}``.

## Chain-next

``music.dispatch_research`` to fan out to specialists.

## Details

Delegates to `research.lead` to mint a Research node + plan specialists.

## Example

```bash
agency-music-research_scope --intent-id $IID …
```
