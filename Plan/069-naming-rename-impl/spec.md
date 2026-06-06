---
spec_id: "069"
slug: naming-rename-impl
status: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
implements: "049"
fulfils: "CORE.md §Naming — wire form vs code-mode bare alias"
depends_on: ["049", "067", "072"]
affects:
  - agency/engine.py                      # bare code-mode alias on the call surface
  - agency/install.py                     # regen skills/help with bare names
  - tests/test_naming_rename.py           # NEW
estimated_jules_sessions: 0
domain: substrate
wave: 5
---

# Spec 069 — Naming rename implementation (the 049 audit, executed)

## Why

Spec 049 audited the surface and recommended: drop the `capability_<cap>_` prefix
from the **code-mode call surface** (keep the wire form, CORE.md §Naming);
alias-and-rename the 5 verbose substrate tools; KEEP `intent_bootstrap`. CORE.md
§Naming (Spec 072) now sanctions the wire/code-mode split. This spec implements it.

## Done When

- [ ] **Bare code-mode alias:** `execute`'s `call_tool` resolves the **bare verb**
  (`call_tool("dispatch_decision", …)`) in addition to the prefixed wire name. The
  FastMCP wire name `capability_<cap>_<verb>` is UNCHANGED (CORE §Naming).
- [ ] **Resolve the collisions FIRST** (Spec 049 §4, Spec 067 `bare_name_unique`):
  `note` (dogfood/reflect), `render` (document/dogfood), `verify` (jules/research),
  and the `reflect.search` ↔ contract `search` shadow — each gets a unique bare
  form OR keeps the prefix. No ambiguous bare dispatch ships.
- [ ] **Substrate aliases:** `agency_welcome`→`welcome`, `agency_install`→`install`,
  `agency_doctor`→`doctor`, `lifecycle_gate`→`gate`, `memory_graph_provenance`→
  `provenance` — emit BOTH names; old marked `deprecated=True` in the tool
  description. KEEP `intent_bootstrap` (Spec 049 verdict).
- [ ] **Regen** `skills/help/SKILL.md` + docs with the bare names; update
  `CLAUDE.md` / `CORE.md` references.
- [ ] Spec 067 `name_token_budget` + `bare_name_unique` go GREEN, then flip to BLOCK.
- [ ] `tests/test_naming_rename.py`: bare alias resolves; wire name still resolves;
  deprecated-alias resolves + carries the flag; collisions rejected.
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean.

## Migration

Alias-and-deprecate throughout: old + new for one minor, deprecation flag, removal
next minor. No hard break — every existing caller keeps working.

## Evidence

- `Plan/049-…/naming-audit-report.md` (the per-name verdicts + collision set).
- `CORE.md` §Naming (the sanctioned split); `agency/engine.py` `_wire`.
