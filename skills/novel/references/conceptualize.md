<!-- agency-generated: v1 -->
# novel.conceptualize

Render a novel-concept document, the first verb of the MVN flow (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `title, author, premise, central_question.` |  |  |

## Returns

``{result, artefact}`` novel-concept artefact.

## Chain-next

``novel.create_novel`` to mint the Novel node.

## Details

(no further detail)

## Example

```bash
agency-novel-conceptualize --intent-id $IID …
```
