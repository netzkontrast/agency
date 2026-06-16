<!-- agency-generated: v1 -->
# persona.summon

Summon a specialist — compose a dispatch brief + record provenance (Spec 297).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `persona (auto | one of the roster names), task (str).` |  |  |

## Returns

``{persona, brief, persona_brief_id}`` or ``{error}``.

## Chain-next

hand ``brief`` to subagent.develop / the Agent tool.

## Details

``persona="auto"`` picks the best match for ``task`` via ``recommend``. Composes a brief (role + focus + approach + task) ready for the Agent tool / ``subagent.develop``, and records a ``PersonaBrief`` node SERVING the intent.

## Example

```bash
agency-persona-summon --intent-id $IID …
```
