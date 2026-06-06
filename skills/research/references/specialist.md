<!-- agency-generated: v1 -->
# research.specialist

One bounded sub-search; records Citations under the research_id.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `research_id (str — from research.lead), role (str — codebase|prior-reflections|doc-corpus|web), query (str), search_root (str — codebase only), docs_root (str — doc-corpus only), k (int — max hits).` |  |  |

## Returns

``{citations, summary}``.

## Chain-next

more specialists OR research.verify.

## Details

(no further detail)

## Example

```bash
agency-research-specialist --intent-id $IID …
```
