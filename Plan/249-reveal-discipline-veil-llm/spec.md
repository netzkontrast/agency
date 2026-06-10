---
spec_id: "249"
slug: reveal-discipline-veil-llm
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "139"
depends_on: ["139", "147", "242", "150"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_veil_llm.py
---

# Spec 249 — reveal-discipline veil LLM augmentation

## Why

Spec 139 ships RevealRule + 3-tier check + `check_veil` (decidable
substring scan over veil terms). The decidable scan misses CONCEPTUAL
leaks ("a shifting voice" implies plurality without naming it). With
Spec 147 the Driver can scan for conceptual leaks tagged `judged` —
advisory, the decidable scan stays the gate.

## Done When

- [ ] **`check_veil_conceptual(novel_id, ...)`** runs the Driver to flag
      paragraphs that conceptually leak veil content; tagged `judged`.
- [ ] **The decidable scan stays the hard gate** (Spec 139).
- [ ] **Fuzzy name leak** uses Spec 242 substrate (shared with codex).
- [ ] **Findings → Reflections** (Spec 150).
- [ ] Test: a fixture with a conceptual leak is flagged (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 242 (shared fuzzy substrate).
- **Dogfood-loop chain** (150).
