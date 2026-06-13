<!-- agency-generated: v1 -->
# novel.create_storyform

Mint the Storyform node for a novel + STORYFORM_OF edge (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id (parent Novel), body (the NCP v1.3.0 storyform dict — stored JSON-serialised; optional, defaults to empty).` |  |  |

## Returns

``{storyform_id, novel_id, has_body}``.

## Chain-next

``novel.pre_draft_gate`` (now satisfiable) or the ``storyform-build`` skill which fills the body.

## Details

Spec 103 Slice 2 (Workstream D) — closes the documented ENGINE GAP: the storyform gates + checks read a ``Storyform`` node, but no verb minted one (it had to be inserted surgically). This verb records it properly, carrying the NCP payload as a JSON ``body`` and wiring the STORYFORM_OF edge to the parent Novel. Idempotent per novel: a second call updates the existing Storyform's body rather than minting a duplicate.

## Example

```bash
agency-novel-create_storyform --intent-id $IID …
```
