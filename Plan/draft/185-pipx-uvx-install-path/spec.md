---
spec_id: "185"
slug: pipx-uvx-install-path
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "065"
depends_on: ["065", "062", "170", "177"]
vision_goals: [5]
affects:
  - hooks/session-start.sh
  - agency/install.py
  - tests/test_uvx_install.py
---

# Spec 185 — uvx install path (faster cold start)

## Why

Spec 065 settled pipx-only install. But Claude Code Web cold starts are
slow because pipx builds the editable install on first session (Spec
062 hook). `uvx` (the uv tool runner) resolves + caches dramatically
faster and is now the common Claude-Code-ecosystem default. Adding a
uvx path (preferred when present, pipx fallback) cuts first-touch
latency — the UX chain's silent tax.

## Done When

- [ ] **SessionStart hook prefers `uvx`/`uv tool install` when on PATH**,
      falls back to pipx (Spec 065 chain preserved), then prints the
      Spec 065 HINT when neither is present. Resolution order encoded
      as a typed `InstallStrategy = Literal["uvx", "pipx", "hint_only"]`
      with a probe function returning the chosen value.
- [ ] **`agency_doctor.install_method` reports `InstallReport{method:
      InstallStrategy, resolved_path: str, resolve_duration_ms: int}`**
      (Spec 170). Drift catches a missing field.
- [ ] **Cold-start improves measurably** (rule 8, relationship): when
      `uvx` available, `resolve_duration_ms(uvx) < resolve_duration_ms(pipx)`
      on the same machine — no pinned millisecond target.
- [ ] **Idempotent** (Spec 062) — `install()` called twice in the same
      session does zero network IO the second time, regardless of which
      installer chose path 1.
- [ ] **`.mcp.json` command resolution unchanged** (`agency-mcp` on
      PATH) — both installers put it there; a parity test asserts the
      same `agency_welcome()` payload from either install path.
- [ ] **Test matrix**: uvx-present chooses uvx; uvx-missing falls to
      pipx; neither prints HINT exit-0; doctor reports the live method
      under each path.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a fresh Claude Code Web sandbox with uvx on PATH
When:   the SessionStart hook fires (first session)
Then:   probe() returns InstallStrategy.uvx, installer runs
        `uv tool install .`, agency-mcp lands on PATH, .mcp.json points
        at it, agency_doctor.install_method.method == "uvx", and
        the second SessionStart in the same sandbox does zero network IO

Given:  a sandbox WITHOUT uvx but WITH pipx
When:   the SessionStart hook fires
Then:   probe() returns InstallStrategy.pipx, the Spec 065 install path
        runs unchanged, doctor reports method == "pipx", parity test
        confirms agency_welcome() payload matches the uvx path

Given:  a sandbox without either
When:   the hook fires
Then:   probe() returns InstallStrategy.hint_only, the Spec 065 HINT
        prints on stderr, exit code is 0, nothing else mutates
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| `uv` on PATH but broken | corrupted uv cache | `uv tool install` exits non-zero | fall back to pipx; record failure on the InstallReport |
| Race on first-touch | two SessionStart hooks fire concurrently | resolve_duration_ms doubles | install path takes a flock; second waiter no-ops |
| Stale uv cache | uv resolves an old wheel | doctor reports a version older than the spec frontmatter | `uv tool upgrade agency` on a version mismatch |
| Network partition mid-resolve | uvx fails after partial download | exit non-zero, no `agency-mcp` on PATH | fall to pipx; HINT only if both fail |

## Interconnects

- Spec 062 (sessionstart install) is the hook; Spec 170 (doctor)
  reports the method; Spec 177 (reference audit) checks the shape.
- **UX-onboarding chain** (148): faster cold start IS the first-touch UX.
- Spec 149 (derived docs) reads `InstallReport` for the install
  section of generated docs — never hand-pinned.
- Spec 195 (event replay) records the install method on the
  SessionStart Event for replayability.

## Open questions

1. Default to uvx or keep pipx canonical? **Recommend**: prefer uvx
   when present (speed), keep pipx as the documented canonical fallback
   — additive, not a doctrine flip.
2. Cache the probe result for the session? **Recommend**: yes — once
   per SessionStart, cache the InstallStrategy in the graph as an
   `EnvironmentProbe` artefact, so downstream verbs read it without
   re-probing PATH.
3. Surface install method to the user on `/agency`? **Recommend**: only
   on `/agency doctor` — keep the default `/agency` welcome silent so
   the prefix stays cache-stable (Spec 146).
