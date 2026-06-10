---
spec_id: "185"
slug: pipx-uvx-install-path
status: draft
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
      Spec 065 HINT when neither is present.
- [ ] **`agency_doctor.install_method` reports uvx vs pipx** (Spec 170).
- [ ] **Idempotent** (Spec 062) — no rebuild when already resolved.
- [ ] **`.mcp.json` command resolution unchanged** (`agency-mcp` on
      PATH) — both installers put it there.
- [ ] Test: uvx-present path chosen; pipx fallback; doctor reports the
      live method.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 062 (sessionstart install) is the hook; Spec 170 (doctor)
  reports the method; Spec 177 (reference audit) checks the shape.

## Open questions

1. Default to uvx or keep pipx canonical? **Recommend**: prefer uvx
   when present (speed), keep pipx as the documented canonical fallback
   — additive, not a doctrine flip.
