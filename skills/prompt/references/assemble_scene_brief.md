<!-- agency-generated: v1 -->
# prompt.assemble_scene_brief

Compose a Novelcrafter-style scene brief from graph state (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id (graph id of a Scene node), max_tokens (total cap), section_budget (per-section cap).` |  |  |

## Returns

``{prompt, sections, token_count, sources, truncated, brief_id}`` — ``brief_id`` is the Artefact node id recorded for provenance. ``{error: 'NOT_FOUND', ...}`` when scene_id doesn't resolve.

## Chain-next

hand ``prompt`` to a generation driver; on return, record the scene body back to the graph (Spec 130 scene-writer skill phase 5).

## Details

Walks Scene → Chapter → Novel → Storyform, then for each section (storyform / pov_card / scene_cast / world_rules / continuity / foreshadowing / voice_constraints) calls a private composer that truncates to ``section_budget``. Sections render in priority order (storyform highest, voice_constraints lowest); when ``max_tokens`` binds, lower-priority sections drop with a ``truncated`` flag.

## Example

```bash
agency-prompt-assemble_scene_brief --intent-id $IID …
```
