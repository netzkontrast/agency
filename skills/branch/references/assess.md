<!-- agency-generated: v1 -->
# branch.assess

Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `branch (str), base (str — defaults to 'main').` |  |  |

## Returns

``{ahead, behind, dirty, recommended}`` (wire shape).

## Chain-next

``branch.finish(branch=, action=recommended)``.

## Details

(no further detail)

## Example

```bash
agency-branch-assess --intent-id $IID …
```
