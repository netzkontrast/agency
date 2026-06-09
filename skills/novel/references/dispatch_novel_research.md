<!-- agency-generated: v1 -->
# novel.dispatch_novel_research

Mint a research lead + record NovelClaim (delegates to research cap).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `question, domain (one of RESEARCH_DOMAINS).` |  |  |

## Returns

``{research_id, claim_id, question, domain}``.

## Chain-next

``research.specialist`` per domain or ``novel.verify_sources``.

## Details

Routes through ``research.lead`` to mint the Research node, then binds the resulting research_id into a NovelClaim that SERVES the novel's intent. domain must be one of ``RESEARCH_DOMAINS``.

## Example

```bash
agency-novel-dispatch_novel_research --intent-id $IID …
```
