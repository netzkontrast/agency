<!-- agency-generated: v1 -->
# develop.reload

Reload edited capability code into the live session (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `(none).` |  |  |

## Returns

``{reloaded, capability_count, added, removed, rewired_tools, reimported}``.

## Chain-next

develop.validate_skill(name) on the reloaded capability.

## Details

Purges + re-imports the ``agency.capabilities.*`` subtree so a verb you just edited or scaffolded is live WITHOUT a session restart — the authoring loop's last step (delegates to ``Engine.reload``, Spec 302). Picks up edits inside a folder-cap's ``_main`` / ``clusters`` submodules, not just brand-new caps. Code-mode ``execute`` reaches new verbs immediately; a non-code-mode client must re-list tools to see them.

## Example

```bash
agency-develop-reload --intent-id $IID …
```
