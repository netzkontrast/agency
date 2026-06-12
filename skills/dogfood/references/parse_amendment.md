<!-- agency-generated: v1 -->
# dogfood.parse_amendment

Classify recent Reflections into amendment proposals.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (substring filter on plan_slug), since (reserved bi-temporal cursor), limit (caps proposals; default 20), use_llm (default True; set False to force keyword path), host_completion (Spec 279 resume envelope from Claude Code — ``{text, parsed?}`` where ``parsed`` is the ProposalPayload list).` |  |  |

## Returns

``{proposals: [ProposalPayload], classifier: str, kind?: "llm_delegate", request?: HostLLMRequest dict}``.

## Chain-next

``dogfood.apply_amendment(payload, dry_run=True)``.

## Details

Slice 1 shipped the keyword classifier (the documented fallback path). Slice 2 (this) swaps in Spec 147 AnthropicDriver structured-output classification — same ProposalPayload shape, sharper recall — wrapped through Spec 279's ``complete_or_delegate`` so the no-key host (Claude Code) can run inference itself instead of degrading to keywords. Three paths (resume wins): 1. ``host_completion`` supplied — the host already ran inference after a prior delegation; parse the result into proposals. 2. ``use_llm=True`` AND an AnthropicDriver is wired AND capable: structured-output ``complete()`` call. 3. ``use_llm=True`` AND ``prefer_delegate=True`` AND driver backend is ``"none"`` → return a ``llm_delegate`` envelope so the host (Claude Code) can run inference and re-call (Spec 279). When ``prefer_delegate=False`` (default), backend ``"none"`` silently degrades to keyword — backwards-compat default so tests + non-host callers don't have to handle the envelope. 4. else / ``use_llm=False`` / no driver — keyword classifier fallback (Slice 1 path).

## Example

```bash
agency-dogfood-parse_amendment --intent-id $IID …
```
