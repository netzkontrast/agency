<!-- agency-generated: v1 -->
# novel.generate_scene_body

Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id` | str — Scene node id; the body is recorded as an Artefact PRODUCES_FROM this Scene) - brief (str — assembled scene brief from Spec 127; the scene-writer phase 1 output) - alter_id (str — when set, the scene is voice-locked via Spec 144; ``voice_locked=True`` in the result) - system (str — system prompt override) - host_completion (dict | None — Spec 279 resume envelope) - prefer_delegate (bool — when True + backend "none", emit the llm_delegate envelope instead of failing) - max_tokens (int — request budget for the LLM call |  |

## Returns

``WetSceneResult`` dict with ``{intent_id, scene_id, body_handle, wc, driver, voice_locked, refusal?, kind?, request?, regen_count, passes_all, checks}``.

## Chain-next

``novel.integrate_scene_body(scene_id, body)`` after fetching via ``memory.recall_overflow_slice``. Failure modes: ``Codes.VOICE_BRIEF_MISSING`` (alter_id set but brief empty); ``Codes.SCENE_OVERFLOW_LOST`` (capture failed); ``Codes.DRIVER_REFUSAL`` (Spec 147 propagates).

## Details

Drives the Spec 130 scene-writer phase 3 (generate) with a real TextDriver backed by the AnthropicDriver. Three paths (resume wins): 1. ``host_completion`` supplied — Claude Code already ran the inference after a prior delegation; parse the result. 2. AnthropicDriver capable → ``driver.complete(messages, system)`` direct (Spec 147 Slice 1). 3. Driver backend ``"none"`` AND ``prefer_delegate=True`` → return a ``kind="llm_delegate"`` envelope so the host runs inference and re-calls (Spec 279). The generated body is ALWAYS captured via Spec 154 ``capture_overflow`` and returned through ``body_handle`` (Artefact id) — never inline. A wrapping LLM driver fetches only the slice it needs (Spec 146 prefix discipline). Slice 1 ships the driver-bound generate path + the typed ``WetSceneResult`` shape. Slice 2+ adds the gate-driven regenerate loop (the shipped prose checks gate the output).

## Example

```bash
agency-novel-generate_scene_body --intent-id $IID …
```
