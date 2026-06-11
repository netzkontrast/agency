---
spec_id: "249"
slug: reveal-discipline-veil-llm
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "139"
depends_on: ["139", "147", "242", "150", "146", "245", "247"]
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

- [ ] **`check_veil_conceptual(novel_id, chapter_range=None) ->
      VeilCheckProposal`** — typed return `VeilCheckProposal{ findings:
      list[{span: SpanRef, leak_kind: Literal["conceptual","fuzzy_name",
      "register_tell"], reveal_rule_id: RevealRuleId, severity:
      Literal["info","warn"], rationale: str}], decidable_pass:
      DecidableVeilResult, status: Literal["proposal"], driver_model:
      str }`. Driver scans paragraphs only WITHIN the novel's veil-
      active range (Spec 139 tier-3); decidable pass runs FIRST and
      is unconditionally included.
- [ ] **Invariant: decidable scan is the hard gate, judged is
      advisory** — `proposal.findings` NEVER promote to a hard veil
      block; only `proposal.decidable_pass.violations` block. Property
      test: a Driver-flagged paragraph with zero decidable violations
      never blocks publishing.
- [ ] **Invariant: fuzzy-name leaks share substrate with codex** — the
      fuzzy-name detector is ONE implementation in Spec 242, consumed
      by both novel.reveal-discipline and codex.character-sheet.
      Relationship: `import path to fuzzy detector == 1 location`.
- [ ] **Invariant: leak_kind taxonomy is closed and derived** —
      `leak_kind` enum re-derives from the RevealRule taxonomy; adding
      a leak kind is one registry edit, not 4 module edits (CLAUDE.md
      rule 8).
- [ ] **Invariant: dogfood feedback structural** — recurring
      `(reveal_rule_id, leak_kind)` patterns mint Spec 150 amendment
      proposals (rule under-specified / over-broad).
- [ ] **Failure modes**: Driver `REFUSAL` on edgy veil content → keep
      decidable result, emit zero conceptual findings + log Spec 150
      reason; `RATE_LIMITED` → retry-with-jitter (Spec 147);
      `BAD_REQUEST` schema → reject + log; cache prefix drift from
      RevealRule edits → re-emit byte-stable (Spec 146); empty
      chapter range → decidable pass only, zero Driver call.
- [ ] Test: a fixture with a conceptual leak is flagged (mocked); a
      decidable violation blocks; a Driver-only flag does NOT block.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with RevealRule "plurality-veiled-until-ch12"; the
        decidable scan whitelists alter-names; chapter 5 contains
        "her voice shifted, became someone newer" (conceptual leak,
        no whitelist hit) AND "Mira-Alex" (decidable violation)
When:   check_veil_conceptual(novel_id, chapter_range=[5,5])
Then:   proposal.decidable_pass.violations contains the "Mira-Alex"
        span (HARD block); proposal.findings contains the "voice
        shifted" span with leak_kind="conceptual", severity="warn",
        status="proposal" (ADVISORY only); the recurring conceptual
        leak pattern across 3 chapters mints a Spec 150 amendment
        proposal suggesting the RevealRule needs a register-rule
```

## Interconnects

- **LLM-driver chain** (147) — Driver authors the judged pass.
- Spec 242 (shared fuzzy substrate) — fuzzy-name detection lives
  there; this spec consumes, doesn't duplicate.
- **Dogfood-loop chain** (150) — leak patterns → R-rule proposals.
- **Output-budget chain** (146) — chapter context obeys envelope;
  RevealRule registry sits in the cacheable prefix.
- Spec 245 (sensitivity managed) — runs the same Driver pattern for
  a different lens; the two compose on the same scene.
- Spec 247 (canon-lock approval) — when leak severity warrants a new
  R-rule, it flows through the canon approval workflow.

## Open questions

1. **Driver scope per call.** Whole chapter at once, or paragraph-
   batched? **Recommend**: chapter-batched with sorted paragraph
   batching for byte-stable prefix (Spec 146) — paragraph-at-a-time
   loses cross-paragraph conceptual signals.
2. **Severity ceiling.** Allow Driver-minted `warn`? **Recommend**:
   yes — `warn` is the cap for judged findings; only the author can
   elevate to a hard block (mirrors Spec 245 doctrine).
3. **False-positive suppression.** Author-marked false positives
   feedback into the Driver context? **Recommend**: yes via
   per-novel "veil-allowlist" — but the allowlist is bounded
   (max N entries) to prevent allowlist creep masking real leaks.
