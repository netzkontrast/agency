# Model Detection and Privacy Notes

Looper detection is intentionally dumb and transparent. It stores invocation
metadata only, never credentials.

## Registry

Default registry path:

```text
~/.looper/models.json
```

Registry entries should look like:

```json
{
  "claude": {
    "cli": "claude",
    "invoke": ["claude", "-p"],
    "available": true,
    "authed": true,
    "local": false
  }
}
```

`authed` means the basic probe command exited cleanly. It is a convenience
signal, not a guarantee that a future paid model call will succeed.

## Default Redactions

- `.env`
- `.env.*`
- `secrets/**`
- `**/*.key`

Add project-specific globs for customer data, private transcripts, or internal
design docs before sending anything to a non-local council member.

## Local Model UX

A council member that runs locally (e.g. `ollama`) keeps plan and delivery
context on the user's machine — no cross-vendor egress, no consent prompt. Looper
treats a local model as the **privacy-preserving default** for the council and
surfaces it accordingly:

- `looper.py detect-models` prints a recommendation after the registry JSON: the
  best authed local model to use as the council default, or — when none is ready
  — how to get one plus a reminder that cross-vendor members need egress consent.
  (`recommend_council_default` is the helper behind it.)
- The wizard offers a detected local model first, and only steers toward a
  cross-vendor reviewer/judge when loop quality needs it, naming the egress and
  asking for consent before the first send.

Local models may be lower quality than frontier hosted models; that trade-off is
the user's to make, but Looper makes the private option the visible one.

