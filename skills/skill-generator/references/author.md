<!-- agency-generated: v1 -->
# skill_generator.author

Draft a skill for a capability by sampling the host LLM with a per-type skill-creator prompt grounded in the cap's real surface (Spec 374 Slice 2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `capability (a name in the live registry), skill_type (R15` |  | pillar|capability|technique|pattern|reference|discipline), spec_text (optional governing-spec excerpt), max_tokens (sampling budget). |

## Returns

``{result: {status, ...}}`` where status is ``drafted`` (carries a schema-valid ``draft``), ``no-host`` (carries ``grounding`` + ``prompt`` for hand-authoring), ``unparseable`` (host output failed JSON/schema — carries ``raw`` + ``error``), or ``error`` (unknown capability).

## Chain-next

review the draft, then write ``skill.yaml`` + commit (Slice 3 adds registry validation + the ``source_stamp``).

## Details

Authoring-time only (NOT install — A7): install renders committed skills, it never samples. With no sampling host the verb returns the grounding + the prompt so a human/agent authors by hand (graceful degrade).

## Example

```bash
agency-skill_generator-author --intent-id $IID …
```
