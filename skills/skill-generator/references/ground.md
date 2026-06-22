<!-- agency-generated: v1 -->
# skill_generator.ground

Build the authoring grounding for a capability — its live verbs, signatures, docstrings, and ontology — the structured input a skill-creator prompt fills, and the no-host fallback an author reads.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `capability (a name in the live registry), spec_text (optional governing-spec excerpt to ground the author in).` |  |  |

## Returns

``{result: {capability, home, verbs:[{name,role,signature,doc}], ontology:{nodes,edges,skills}, spec}}``; or ``{error, available}`` when the capability is unknown.

## Chain-next

``skill_generator`` samples the host with this grounding to draft a schema-valid skill (Spec 374 Slice 2).

## Details

(no further detail)

## Example

```bash
agency-skill_generator-ground --intent-id $IID …
```
