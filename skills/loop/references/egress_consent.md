<!-- agency-generated: v1 -->
# loop.egress_consent

Decide the cross-vendor egress gate (consent + redaction) — pure (369).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `member (dict — the council member), consent_given (bool), policy (str), redact_globs (list), context_paths (list).` |  |  |

## Returns

``{permit, requires_consent, redacted, reason}``.

## Chain-next

record the consent as provenance, then send (or redact).

## Details

(no further detail)

## Example

```bash
agency-loop-egress_consent --intent-id $IID …
```
