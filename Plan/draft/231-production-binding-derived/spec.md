---
spec_id: "231"
slug: production-binding-derived
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "121"
depends_on: ["121", "149", "170", "214"]
vision_goals: [4, 5]
affects:
  - agency/capabilities/novel/_config.py
  - tests/test_novel_binding_derived.py
---

# Spec 231 — novel production-binding: derived config + doctor

## Why

Spec 121 wires NovelConfig + FileNovelStateDriver. Like the music
parallel (Spec 214), the novel binding's surface should derive: the
config schema, the driver bundle, the render templates — all visible to
`agency_doctor` so a user knows what's wired before they invoke.

## Done When

- [ ] **`agency_doctor.novel_readiness` returns `NovelReadiness`** =
      `{drivers_wired: dict[name, bool], content_root: Path | None,
      template_count: int, missing_drivers: list[str], hints:
      list[str]}` — every field DERIVED from the live registry +
      filesystem, never hand-authored. Invariant: `len(missing_drivers)
      + sum(drivers_wired.values()) == len(drivers_wired)`.
- [ ] **`NovelConfig.bootstrap()` is idempotent** — invariant: two
      consecutive calls yield byte-identical config + zero filesystem
      mutations on the second. Reported under `agency_doctor` as
      `bootstrap_idempotent: bool`.
- [ ] **Missing-driver hint is TYPED + derived** — for each missing
      driver name, hint string is rendered from the driver's
      registration metadata (Spec 170 pattern). Invariant: every entry
      in `missing_drivers` has a corresponding entry in `hints` and
      every hint names the extra + the install command derived from
      `pyproject.toml`, never a literal.
- [ ] **Template count derives from the templates directory** — invariant:
      `template_count == len(list(templates_dir.glob("*.j2")))`. No
      pinned integer in the test.
- [ ] **Failure modes** — `content_root` missing → `Codes.CONFIG_MISSING`;
      a driver registered but failing health-probe → recorded under
      `drivers_wired[name] = False` with the probe error in `hints`;
      filesystem-permission denied → surface as hint, never as a crash.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a fresh checkout with NO content_root configured AND the
        novel_format extra not installed
When:   agency_doctor() runs
Then:   novel_readiness.content_root is None AND
        "format" in missing_drivers AND
        any(h for h in hints if "pip install" in h and "novel-format" in h)
        AND bootstrap_idempotent is True (no mutations attempted)

Given:  content_root configured, novel_format extra installed
When:   NovelConfig.bootstrap() called twice in sequence
Then:   second call's filesystem-mutation count == 0 AND
        novel_readiness.drivers_wired["format"] is True AND
        template_count equals the live glob over templates_dir
```

## Interconnects

- **Drift-derivation chain** (149) · Spec 214 (music sibling).
- Spec 170 (doctor) is the report surface.
- Spec 146 (output-prefix) — `novel_readiness` is part of the engine
  prefix; capability-set-stable bytes for cache friendliness.
- Spec 121 (production binding) is the surface being reported on.
- Spec 234 (format-driver Pandoc + Managed-Agent) — its install state
  is one of the drivers this doctor reports.

## Open questions

1. **Should `template_count` distinguish by extension?** **Recommend:**
   yes — break into `{j2: int, md: int}` so drift between rendered +
   source templates is visible.
2. **Probe cost.** Health-probing each driver on every doctor call?
   **Recommend:** cache probe results for 60s in the engine prefix;
   re-probe on `agency_doctor(force=True)`.
3. **Hint locale.** Hints are English-only? **Recommend:** yes for now;
   defer i18n to a future spec.
