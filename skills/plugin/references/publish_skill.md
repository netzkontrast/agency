<!-- agency-generated: v1 -->
# plugin.publish_skill

Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `cap_name (capability to publish); dry_run (True → return the package manifest WITHOUT uploading — the safe default; set False to publish).` |  |  |

## Returns

``{skill_name, files:[…], bytes, uploaded, skill_id?, version?}``.

## Chain-next

re-run with dry_run=False to upload; re-publish makes a new version.

## Details

Packages the capability's emitted skill (SKILL.md at root + references/) and, unless ``dry_run``, uploads it via /v1/skills — so the capability becomes a first-class Agent Skill on ANY Claude surface (API, Managed Agents, claude.ai), not just Claude Code. The upload is recorded as a `published-skill` Artefact.

## Example

```bash
agency-plugin-publish_skill --intent-id $IID …
```
