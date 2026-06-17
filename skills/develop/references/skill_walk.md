<!-- agency-generated: v1 -->
# develop.skill_walk

Walk a registered skill to the first hard gate in ONE call (the atomic walker).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (registered skill, e.g. 'tdd'), inputs (map of produce→value), resume_from (a prior skill_id to resume; "" starts fresh).` |  |  |

## Returns

a status-contract shape — one of: - ``{status: "completed", skill_id, outputs}`` - ``{status: "input-required", phase, blocked_on, resume_with, skill_id, partial_outputs}`` - ``{status: "failed", phase, error, skill_id, completed_phases}``

## Chain-next

on input-required, re-call with resume_from + resume_with keys.

## Details

Replaces the 5× ``SkillRun(...).submit(...)`` boilerplate: supply the skill name + a flat ``inputs`` map (keyed by the phases' ``produces``), and the walker runs every plain/bound phase, executes the bound verbs, and PAUSES at the first hard gate. Resume by re-calling with ``resume_from=<skill_id>`` and the gate's ``resume_with`` keys populated — re-entering a paused walk confirms that gate and continues.

## Example

```bash
agency-develop-skill_walk --intent-id $IID …
```
