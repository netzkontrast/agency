---
description: Use when starting fresh work in a repo and you want the agency engine to capture your intent through a short guided interview before any verb runs.
---

## `/agency-onboard` — first-touch intent capture

A short four-beat interview that turns 'what you want to do' into a graph-captured Intent every later capability verb SERVES against. The user stays creative; the engine captures everything (the GOALS.md provenance moat).

### The four beats

1. **describe** — ask the user what they want to ship in one sentence ('a novel chapter', 'a token-economy lint', …). Capture the verbatim answer.
2. **configure** — ask what 'done' looks like + any constraints (deadline, format, acceptance test). Capture it.
3. **confirm** — read the captured purpose + deliverable back to the user and ask them to confirm or correct. Capture the confirmation.
4. **capture** — call `intent_bootstrap` with `purpose` / `deliverable` / `acceptance` DERIVED from the three captured answers (never invent fields the user didn't give):

```python
await call_tool('intent_bootstrap', {
    'purpose': '<from beat 1>',
    'deliverable': '<from beat 2>',
    'acceptance': '<from beat 2/3>',
})
```

### After capture

The returned `intent_id` is the handle every capability verb takes. Walk a discipline skill next (`develop.brainstorm` for design, `develop.implement` for code) rather than improvising — the engine delivers one phase at a time so context stays bounded.

If the user declines onboarding, do not re-prompt; the session can still mint an Intent later via `intent_bootstrap` directly.

