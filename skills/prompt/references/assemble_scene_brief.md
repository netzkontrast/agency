<!-- agency-generated: v1 -->
# prompt.assemble_scene_brief

Compose a Novelcrafter-style scene brief from graph state (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id (graph id of a Scene node), max_tokens (total cap), section_budget (per-section cap), cache_floor_tokens (0 → the CACHE_MIN_PREFIX_TOKENS=1024 claude-api floor; override for smaller-context drivers).` |  |  |

## Returns

``{prompt, sections, token_count, sources, truncated, brief_id, prefix, suffix, prefix_tokens, suffix_tokens, total_tokens, sections_meta: [{name, stability, byte_offset, token_count}], cache: {eligible, breakpoint_offset, min_prefix_tokens, ttl, code}}`` — invariants: ``prompt == prefix + suffix`` (byte-exact), ``prefix_tokens + suffix_tokens == total_tokens``, sections_meta stability ranks are non-increasing. ``{error: 'NOT_FOUND', ...}`` when scene_id doesn't resolve (Spec 127 contract).

## Chain-next

hand ``prompt`` to a generation driver with ``cache_control`` at ``cache.breakpoint_offset``; on return, record the scene body back to the graph (Spec 130 scene-writer skill phase 5).

## Details

Walks Scene → Chapter → Novel → Storyform, then for each section (storyform / pov_card / voice_constraints / world_rules / scene_cast / continuity / foreshadowing) calls a private composer that truncates to ``section_budget``. Spec 237: sections render in stability-descending order (frozen first, volatile last; volatile alphabetical) and the brief splits into a byte-stable ``prefix`` (frozen + semi — the ``cache_control`` breakpoint candidate) and a volatile ``suffix``. When ``max_tokens`` binds, later (more volatile) sections drop with a ``truncated`` flag. Token counts come from a wired ``anthropic`` driver's ``count_tokens`` (Spec 201) when present, else the 4-chars/token heuristic; the driver's ``supports_cache_control=False`` degrades to ``cache.code = cache_unsupported`` (breakpoint omitted, brief intact).

## Example

```bash
agency-prompt-assemble_scene_brief --intent-id $IID …
```
