<!-- agency-generated: v1 -->
# recommend.route

Recommend the capability + verb best matched to a free-text ``request`` (Spec 298).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `request (str — what you want to do), top (int — how many).` |  |  |

## Returns

``{request, top, recommendations: [{capability, verb, score, usage, why}]}``.

## Chain-next

call the recommended ``capability.verb`` via execute.

## Details

Scores every live capability by token overlap between the request and its (name + verbs + skills + gist) vocabulary; suggests the verb whose own name best matches; records a ``Recommendation`` node SERVING the intent. Scored capabilities are ranked by relevance first, then by graph usage frequency (the follow-up signal): among equally-relevant capabilities, the more-used one wins — the live provenance graph breaks ties.

## Example

```bash
agency-recommend-route --intent-id $IID …
```
