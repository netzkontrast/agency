<!-- agency-generated: v1 -->
# jules.dispatch

Spawn a remote Jules session (external effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source (owner/repo), starting_branch, prompt, title (optional), require_plan_approval (bool, default True), alias (optional), automation_mode ('' | AUTO_CREATE_PR), protocol_preset (e.g. 'agency-default').` |  |  |

## Returns

``{status, session, url, alias, artefact: {kind, session, url}}``.

## Chain-next

``jules.status(session=)`` then ``jules.approve_plan(session=)`` when state hits AWAITING_PLAN_APPROVAL.

## Details

Param completeness: the default `require_plan_approval=True` is the recommended doctrine shape the watcher's `review_and_approve_plan` WatchEvent is built for. Spec 013 Phase 4 adds: - `automation_mode` — canonical Jules-side field (``"" | "AUTO_CREATE_PR"``). The flag interaction matrix (`Plan/013-…/DESIGN.md`): - `require_plan_approval=True`, `automation_mode=""` — doctrine default. Plan-gated, agent confirms PR. - `require_plan_approval=True`, `automation_mode="AUTO_CREATE_PR"` — agency-driving-Jules pattern. Plan-gated, PR auto-opens. - `require_plan_approval=False`, `automation_mode="AUTO_CREATE_PR"` — zero-touch. Only safe with a tight `affects:` allow-list. - `protocol_preset` (e.g. ``"agency-default"``) — when non-empty, prepends the Mode-A/B preamble assembled by `_jules_preambles.assemble(...)`. Mode A (dogfood) when source == `DISPATCH_SELF_SOURCE`; Mode B (delegate) otherwise. The Mode B preamble carries the explicit READ-ONLY `git clone` instruction + `read_file` pointers to both root docs. When `alias` is supplied, the alias + the JulesSession node are recorded in the bi-temporal graph (the registry IS the graph, per CORE.md:38-45).

## Example

```bash
agency-jules-dispatch --intent-id $IID …
```
