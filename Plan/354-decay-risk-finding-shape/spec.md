---
spec_id: "354"
slug: decay-risk-finding-shape
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4]
depends_on: ["042", "286", "336"]
domain: analyze
wave: brooks-port
parent_spec: "353"
---

# Spec 354 — Decay-risk Finding shape + decay-risk knowledge (the foundation)

> Part of the Spec 353 brooks-lint port. This is the **foundation slice**: it
> teaches agency's `Finding` value object the Iron Law, vendors the decay-risk
> knowledge as data, and tags the decidable findings `analyze` already produces
> with the risk code + book source they evidence. 355–358 build on it.

## Why

brooks-lint's entire output discipline is one rule — the **Iron Law**:

```
NEVER suggest fixes before completing risk diagnosis.
EVERY finding must follow: Symptom → Source → Consequence → Remedy.
```

> *"A finding without a consequence and a remedy is not a finding — it is
> noise."* — brooks-lint `_shared/common.md`

Agency's `Finding` (`agency/capabilities/analyze/_findings.py:34`) is a frozen
dataclass — `rule · severity · file · line · message · evidence` — with a typed
`FindingSeverity` enum (`info/warn/fail`, Spec 286). It carries the **Symptom**
(message/evidence) but has nowhere to put **Source** (which book/principle),
**Consequence** (what decays if unfixed), or **Remedy** (the concrete action),
and no **risk_code** to group findings by decay pattern. Without those fields the
port cannot record a brooks finding at all — so this is the first slice.

It is also where the **hybrid engine** (Spec 353 §3) is grounded: `analyze`
already *mechanically* detects the decidable half of several decay risks (long
functions → R1, import cycles → R5, file bloat → R4) but emits them untagged.
This slice maps those existing findings onto risk codes, so the decidable engine
*feeds* the judgment framework instead of duplicating it.

## Design

### 1. Extend `Finding` with the Iron Law fields (backward-compatible)

`agency/capabilities/analyze/_findings.py` — add four optional fields to the
frozen dataclass, defaulted so every existing `make_finding` call site (10
callers across `_quality/_security/_performance/_architecture/_paths/_bandit/
_radon`, per codegraph blast-radius) stays valid unchanged:

```python
@dataclass(frozen=True)
class Finding:
    rule: str
    severity: FindingSeverity
    file: str
    line: int
    message: str          # the Symptom (already present)
    evidence: str
    # --- Spec 354 Iron Law extension (all optional → backward-compatible) ---
    risk_code: str = ""   # "R1".."R6", "T1".."T6", or a custom "Cx" ("" = decidable-only)
    source: str = ""      # "Book — Principle/Smell" (the Iron Law Source)
    consequence: str = "" # what decays if unfixed
    remedy: str = ""      # concrete action
```

`to_dict()` emits the new keys (the wire/graph shape grows additively — Spec 286
contract preserved). `make_finding(...)` gains the four optional params with the
same token-budget truncation discipline already applied to `message`/`evidence`
— **except** that, per CLAUDE.md #9, the budget governs the *wire preview*; the
graph node stores the full text via `keep_full` (`agency/_capture.py`). A finding
with an empty `risk_code` is a pure-decidable `analyze` finding (today's
behaviour); a non-empty `risk_code` is a brooks finding.

> **These structured fields are what make the Iron Law gate decidable (355,
> Wiegers fix).** Because `consequence`/`remedy` are first-class fields, the
> judgment gate is a pure predicate — `all(f.consequence and f.remedy for f in
> findings)` — not an agent self-assertion. The shape exists so the gate is
> machine-checkable.

> **Tension resolved — one severity enum, two vocabularies (rule 2).**
> `analyze` scores `info/warn/fail`; brooks reports `suggestion/warning/critical`.
> Do NOT add a second enum. `FindingSeverity` stays canonical
> (`info/warn/fail`, the wire value); a **derived** `tier` mapping
> (`fail→critical, warn→warning, info→suggestion`) renders the brooks vocabulary
> for reports + the Health Score (356). Single source; the mapping is a pure
> function, not a stored field.

### 2. Vendor the decay-risk knowledge as data (single source, cited)

`agency/capabilities/analyze/data/decay-risks.json` — the twelve decay risks
(R1–R6 code, T1–T6 test) vendored from brooks-lint `_shared/decay-risks.md` +
`test-decay-risks.md`, cited to upstream (the Dramatica-ontology-vendoring
precedent, Spec 101). One entry per risk:

```json
{
  "R1": {
    "name": "Cognitive Overload",
    "diagnostic": "How much mental effort to understand this?",
    "symptoms": ["function > 20 lines mixing abstraction levels", "nesting > 3",
                 "param list > 4", "magic numbers", "train-wreck chains", "..."],
    "sources": [
      {"symptom": "Long Method", "book": "Fowler — Refactoring", "principle": "Long Method"},
      {"symptom": "fn length/nesting", "book": "McConnell — Code Complete", "principle": "Ch.7 High-Quality Routines"}
    ],
    "severity_guide": {"critical": "fn > 50 lines / nesting > 5", "warning": "20-50 / 4-5", "suggestion": "minor"},
    "what_not_to_flag": ["linear code with clear names + guard clauses", "deep-but-simple module boundary"],
    "decidable": ["long_function", "long_params", "deep_nesting"]
  },
  "...": {}
}
```

The `decidable` array names the `analyze` rule-ids that mechanically evidence
this risk (§3). Everything the skills (355) and the scanners read about a risk
comes from this file — no risk definition is duplicated in prose-in-code (rule 2).
The 12-book matrix itself is owned by Spec 358 (`source-coverage.json`); this file
references books by the same canonical titles.

> **Vendored-data versioning (Newman fix, 2026-06-20).** `decay-risks.json` (and
> 358's `source-coverage.json`) carry a top-level `"_source":
> "brooks-lint@<rev>"` provenance key — the data analogue of 359's
> `<!-- doc-source: -->` markers on the prose. `scripts/check-drift` gains a check
> that the vendored `_source` rev matches the pinned upstream, so a brooks update
> to a severity threshold flags the JSON as stale instead of drifting silently.
> Prose and data are tracked symmetrically.

### 3. Tag the decidable findings with risk codes (the bridge)

`agency/capabilities/analyze/_decay.py` — a small mapping layer that takes the
`Finding`s already produced by the existing scanners and, for any whose `rule` is
listed in a risk's `decidable` array, returns an enriched copy with `risk_code`,
`source` (the first matching book), `consequence`, and `remedy` filled from the
decay-risk data. The mapping mirrors the **`gate` capability's `CapabilityLintRule`
pattern** (`agency/capabilities/plugin/clusters/lint.py` — `check()` + a
`remediation` dict): a rule knows its remedy. Initial decidable→risk map (extends
the existing `_quality`/`_architecture`/`_performance` rule-ids — no new
detection logic, just tagging):

| `analyze` rule (existing) | Risk | Source (book) |
|---|---|---|
| `long_function`, `long_params`, `deep_nesting` | **R1** | Fowler / McConnell |
| `duplicate_block` | **R3** | Fowler — Duplicate Code |
| `large_file`, `speculative_*` | **R4** | Ousterhout / Brooks |
| `import_cycle`, `high_fan_out` | **R5** | Martin — ADP/SDP |

`analyze.run` records the enriched `Finding`s as graph nodes (the existing
record path, now carrying the Iron Law props). Risks with no `decidable` entry
(R2, R6, all T-risks beyond the trivially decidable) are filled by the judgment
pass (355) — this slice ships the *bridge*, not the judgment.

> **This tagging IS the write side of the merge contract (355 §3b).** The
> enriched decidable finding carries the join key `(risk_code, file, line)`; the
> judgment pass later *enriches it in place* (filling `consequence`/`remedy`)
> rather than emitting a duplicate. So `_decay.py` tagging and the judgment pass
> converge on one `Finding` per `(risk_code, span)` — no double-count downstream.

### 4. Custom risks (`Cx`) — open set

The decay-risk data is a **definable registry** (CLAUDE.md #8 / the `shell.define`
precedent): a project's `custom_risks` config (356) merges `Cx` entries at load,
so the scanner + skills pick them up without a code edit. The validator (356)
accepts `R1–R6`, `T1–T6`, and any defined `Cx`.

### What this slice does NOT do

- No judgment pass (355 owns the reasoning-heavy risks).
- No Health Score (356) — this slice only *produces* tagged findings.
- No SARIF (357), no report rendering (357).
- No new severity enum — `tier` is derived (§1).
- No new detection rules — §3 *tags* existing `analyze` findings; richer decidable
  detectors (if any) are a 355/356 follow-up, not the foundation.

## Acceptance (Gherkin)

```gherkin
Scenario: Finding carries the Iron Law, backward-compatibly
  Given the existing analyze.quality scanner
  When it flags a long function
  Then the Finding has the legacy fields unchanged
  And after decay-tagging it also has risk_code "R1", a Source, Consequence, and Remedy

Scenario: severity tier is derived, not stored
  Given a Finding with severity "fail"
  Then its rendered tier is "critical"
  And no second severity field exists on the dataclass

Scenario: the decay-risk data covers every risk
  Then decay-risks.json defines exactly the live risk-code set (R1-R6, T1-T6)
  And each entry has diagnostic, symptoms, sources, severity_guide, and what_not_to_flag
  And the count is derived from the data, not pinned to 12

Scenario: a decidable finding maps to its risk via data, not a literal
  When import_cycle is detected by analyze.architecture
  Then the tagged Finding's risk_code is "R5"
  And its Source is read from decay-risks.json (Martin — Clean Architecture)

Scenario: an untagged analyze finding stays decidable-only
  Given a finding whose rule is in no risk's decidable list
  Then its risk_code is "" and it is recorded as a plain analyze Finding

Scenario: a custom Cx risk is accepted from config
  Given config defines custom_risks.C1
  Then a finding tagged "C1" validates and records like a built-in risk
```

## Open questions

- **OQ1** — should `duplicate_block` map to R3 confidently, or stay decidable-only
  until the judgment pass confirms it is a *decision* duplicated (not incidental
  similarity)? (Default: tag as R3 *suggestion*; judgment may upgrade.)
- **OQ2** — store `tier` denormalized on the graph node for query convenience, or
  always derive? (Default: derive; a query computes it — rule 8.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — foundation slice of the Spec 353 program. No code yet.
Grounded in codegraph: `Finding`/`make_finding`/`count_by_severity`
(`analyze/_findings.py`), the 10-caller blast radius, and the `CapabilityLintRule`
remediation pattern (`plugin/clusters/lint.py`).

**Amended 2026-06-20 (spec-panel critique):** the structured `consequence`/`remedy`
fields are explicitly the enabler of 355's decidable Iron Law gate (Wiegers); the
decidable tagging is the write side of the 355 §3b merge contract — one `Finding`
per `(risk_code, span)`, no double-count (Hohpe); `decay-risks.json` carries a
`_source: brooks-lint@<rev>` provenance key checked by `check-drift` so vendored
data is drift-tracked symmetrically with 359's prose (Newman). Next: RED→GREEN on
the `Finding` extension + `decay-risks.json` (+ `_source`) + `_decay.py` tagging,
then 355/356.

**IMPLEMENTED 2026-06-20 (TDD, branch `claude/stoic-cannon-hqv1te`).** The
foundation slice ships GREEN — behaviour-tested via
`tests/acceptance/features/decay_risk.feature` + `test_decay_risk.py`
(**13 Gherkin scenarios**); full suite green; drift / doc-drift / prefix-lint clean.

- **§1 Finding shape + tier** — `agency/capabilities/analyze/_findings.py`: four
  optional Iron Law fields (`risk_code/source/consequence/remedy`, defaulted `""` so
  every existing `make_finding` call site stays valid unchanged); `to_dict()` emits
  them additively (Spec 286 six-key contract preserved); `make_finding` keeps the
  message/evidence truncation but routes the prose fields through `keep_full`
  (CLAUDE.md #9 — captured prose never silently cut); a derived `tier` **property**
  maps the single `FindingSeverity` enum → critical/warning/suggestion (no second
  stored field — rule 2/8). `schemas/finding.json` grown additively (the 4 keys,
  optional).
- **§2 vendored data** — `agency/capabilities/analyze/data/decay-risks.json`: the 12
  risks R1–R6 + T1–T6 from brooks-lint `decay-risks.md`/`test-decay-risks.md`, each
  with name · diagnostic · consequence · remedy · symptoms · sources (book+principle)
  · severity_guide (critical/warning/suggestion) · what_not_to_flag · decidable; a
  top-level `_source: brooks-lint@ec44ec8` provenance key. `_decay.load_risks()` is
  the single reader (excludes `_`-prefixed metadata); the risk count is derived from
  the data, never a pinned literal (rule 8).
- **§3 the bridge** — `agency/capabilities/analyze/_decay.py`:
  `tag(findings, risks=None)` enriches the decidable findings analyze already
  produces with the risk code + Iron Law fields read from the data. High-confidence
  decidable map (the spec's illustrative names resolved to the REAL rule-ids):
  `Q003`(long function)→R1, `Q004`(long file)→R4, `A001`(import cycle)/`A004`(high
  fan-out)→R5; everything else stays judgment-only (OQ1's conservative default —
  `A005`/`A006`/`Q001`/`Q002` left for the 355 judgment pass). It is the WRITE side
  of the 355 §3b merge contract (join key `(risk_code, file, line)`), and is **wired
  into `analyze.run`** so the recorded Finding graph nodes carry the decay diagnosis.
- **§4 open set** — `tag(risks=)` is the seam Spec 356's config-driven custom-`Cx`
  merge plugs into; a custom registry over an existing rule-id tags exactly like a
  built-in (tested). No closed risk-code enum anywhere.

**Remaining in 354:** the `check-drift` `_source`-vs-upstream comparison guard — the
`_source` MARKER ships now (drift-trackable), but the automated comparison needs an
upstream-reference mechanism (agency has no brooks-lint submodule), so it folds into
357's CI work. **Next sibling:** 355 (the `develop`/`analyze` review seam + judgment
pass) builds directly on this `Finding` shape + the `_decay.tag` bridge.
