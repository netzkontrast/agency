<!-- agency-generated: v1 -->
# skill_generator.author

Draft a skill for a capability by sampling the host LLM with a per-type skill-creator prompt grounded in the cap's real surface (Spec 374 Slices 2–3).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `capability (a name in the live registry), skill_type (R15` |  | pillar|capability|technique|pattern|reference|discipline), spec_text (optional governing-spec excerpt), max_tokens (sampling budget), dry_run (True = return draft for review; False = write ``skills/<name>/skill.yaml`` and return the path — default True). |

## Returns

``{result: {status, ...}}`` where status is ``drafted`` (carries a schema-valid ``draft`` + ``source_stamp``), ``invalid`` (a referenced verb was absent from the live registry — carries ``hallucinated_verbs``), ``no-host`` (carries ``grounding`` + ``prompt`` for hand-authoring), ``unparseable`` (host output failed JSON/schema), or ``error`` (unknown capability).

## Chain-next

review the draft, edit if needed, then commit ``skill.yaml``.

## Details

Authoring-time only (NOT install — A7): install renders committed skills, it never samples. With no sampling host the verb returns the grounding + the prompt so a human/agent authors by hand (graceful degrade).

## Example

```bash
agency-skill_generator-author --intent-id $IID …
```
