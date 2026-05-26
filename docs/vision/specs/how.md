---
slug: spec-how
type: spec
status: ready
summary: how — the craft. The OPEN domain of capability-specific verbs (music: write/master/mix; jules: patch/bulk). A mandatory how.<capability>.help discovers them. Every verb is TAGGED with the canonical frame role it fills; a specialist verb living in a closed domain surfaces its role as a call-site alias.
---

# how — the craft

> **Status: specced — not built (except where noted).** The `jules` how aspect
> is lazy until its first specialist verb (`how.jules.patch`) is needed.

## Concept

`how` is the craft: skills, tools, actions. Unlike who / when / where it is the
**OPEN** domain — its verbs are capability-specific and cannot be enumerated by
a fixed frame. Each verb is nonetheless **TAGGED** with the canonical frame role
it fills, so the open domain stays legible against the closed ones.

## Interface

- Capability verbs are named freely for the craft:
  - music: `write` · `master` · `mix`
  - jules: `patch` · `bulk`
- **Mandatory discovery**: every capability with a how aspect MUST publish
  `how.<capability>.help` — the single entry point that lists the capability's
  craft verbs, each with its declared frame role and arguments.

```
how.jules.help()    -> { verbs: [ {name:"patch", frame_role:"move", ...}, ... ] }
how.jules.patch(...)
```

## Frame-role tagging

Every how verb declares which canonical role it fills (`open`/`move`/`close`/
`read`/`find`/`check`). This is metadata, not a rename — the craft name stays.

## Specialist verbs in closed domains → call-site alias

A specialist verb is allowed to live in any closed domain (who/when/where), but
it MUST declare its frame role, and that role is surfaced as a **call-site
ALIAS**:

```
where.music.supersede(...)   ≡   where.music.close(...)
```

The frame is the spine; the specialist name is a skin over it. Callers may use
either name; both resolve to the same handler.

## Interactions

- `how` verbs are invoked by `who`-driven sessions to do the actual work; their
  outputs are recorded in `where`.
- A how aspect materializes lazily — it does not exist until the capability
  needs a craft verb (see [capability-and-aspects](capability-and-aspects.md)).
