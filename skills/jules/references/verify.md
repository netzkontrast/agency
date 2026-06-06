<!-- agency-generated: v1 -->
# jules.verify

COMPLETED != done — verifies the branch landed on origin.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `state (caller-reported session state), branch (str), remote (str, default 'origin').` |  |  |

## Returns

``{done, state, branch_on_remote, sha, error?}``.

## Chain-next

when ``done=True``, open a PR; otherwise ``jules.recover``.

## Details

Derives ``branch_on_remote`` INDEPENDENTLY via the injected ``vcs`` boundary (``git ls-remote``). Fail-closed: any lookup error → ``done=False`` (Spec 006 F3 / Spec 012 Phase 5).

## Example

```bash
agency-jules-verify --intent-id $IID …
```
