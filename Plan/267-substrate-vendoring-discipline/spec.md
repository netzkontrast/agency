---
spec_id: "267"
slug: substrate-vendoring-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "060"
depends_on: ["060", "174", "129", "133", "149", "259"]
vision_goals: [4, 7]
affects:
  - agency/_templates/
  - scripts/check-vendoring
  - tests/test_vendoring_discipline.py
---

# Spec 267 — substrate vendoring discipline

## Why

Spec 060 + Spec 174 close template/schema coverage. As enhancements
land, MORE vendored data accumulates (KP fragments Spec 143, structure
templates Spec 133, Dramatica fragments Spec 129, classifier rubrics
Spec 258, agent YAML Spec 147, Anthropic SDK constants). Each file
carries provenance — "vendored from X, dated Y, license Z" — and
today the provenance is hand-maintained inline prose. Inevitably the
source moves, the version drifts, the license changes, and the
substrate ships stale data without anyone noticing. The discipline:
every vendored file carries a structured `# vendor:` header;
check-drift extension audits that sources still exist and content
hashes match documented vendor versions; updates produce supersede
records same as story-canon (Spec 137).

## Done When

- [ ] **`# vendor:` header required** on every `data/*` and
      `agency/_templates/*` file:
      ```
      # vendor: <source-url>
      # vendor-version: <git-sha | semver | iso-date>
      # vendor-hash: sha256:<hash-of-vendored-content>
      # vendor-license: <SPDX-id>
      # vendor-fetched: <iso-date>
      ```
- [ ] **`scripts/check-vendoring`** computes the live content hash,
      verifies sources accessible (HEAD against the URL, or
      `git cat-file -e <sha>` for vendored sub-trees), and compares to
      documented vendor versions.
- [ ] **Typed `VendoringReport` return shape**:
      ```python
      class VendoringReport(TypedDict):
          files_total: int
          files_unmarked: list[str]       # missing header
          files_stale: list[str]          # source moved / unavailable
          files_hash_drift: list[str]     # content changed locally
          files_license_unknown: list[str]
          generated_at: str
      ```
- [ ] **Updates produce supersede records** — when a vendor refresh
      happens, the old version persists as `superseded` in the graph
      (Spec 137 canon-status discipline). A diff between
      `vendor-version` values is recoverable from the graph.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `len(files_unmarked) == 0` (every vendored file is marked)
      - `len(files_hash_drift) == 0` (local edits to vendored files
        are caught — they should NEVER be hand-edited; refresh from
        source instead)
      - `len(files_license_unknown) == 0` (license known for every
        file)
      - `len(files_stale) > 0 ⇒ a reflection records the broken URL`
        (so the next session can fix or refetch)
- [ ] Test: missing vendor header trips audit; stale URL warns +
      reflects; local edit to a vendored file trips hash drift; a
      proper refresh produces a supersede record.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  agency/_templates/dramatica_fragments.yaml has header
        # vendor: https://example.org/dramatica/v3.tar.gz
        # vendor-version: v3.2.1
        # vendor-hash: sha256:abc...
        # vendor-license: CC-BY-4.0
        # vendor-fetched: 2026-04-12
When:   scripts/check-vendoring runs
Then:   computes local sha256 of the file content; compares to
        vendor-hash; HEADs the URL → 200; emits VendoringReport{
        files_total: 47, files_unmarked: [], files_stale: [],
        files_hash_drift: [], files_license_unknown: []}
        AND exit 0

Given:  developer hand-edits agency/_templates/dramatica_fragments.yaml
        to "fix a typo"
When:   check-vendoring runs
Then:   files_hash_drift: ["agency/_templates/dramatica_fragments.yaml"]
        AND exit non-zero with message "refresh from source instead of
        hand-edit — vendored files are non-editable; propose upstream
        if needed"

Given:  vendor URL returns 404 (source moved)
When:   check-vendoring runs
Then:   files_stale: [...] AND a reflection node "vendor source
        broken: <url>" is emitted so the next session can refetch from
        the new source location
```

## Failure modes (Nygard)

| Failure | Audit response |
|---|---|
| Missing `# vendor:` header | `files_unmarked` lists it; exit non-zero; PR blocked |
| Local hash drift (file edited in repo) | `files_hash_drift`; the discipline forbids hand-editing vendored files |
| Source URL 404 / unavailable | `files_stale`; reflection node records the broken source; the file remains usable (cached locally) but flagged |
| Vendor version updated upstream | Detection only by `vendor-version` field staleness — not auto-fetch (operator-driven refresh per Spec 137 canon discipline) |
| License field unknown or non-SPDX | `files_license_unknown`; PR blocked until license is named |
| Vendored data shipped to a downstream user (marketplace) | License field carried through marketplace.json (Spec 265) so the downstream user sees the terms |
| Vendor source MITM / hash collision | The pinned hash is the trust anchor; a fresh fetch with mismatched hash fails before content lands in the repo |

## Interconnects

- Spec 060 + 174 (parent template/schema coverage) — vendoring
  discipline extends the substrate hardening rules.
- Spec 137 (canon-status) — vendoring uses the same supersede pattern
  applied to data files instead of story canon.
- Spec 129 (Dramatica) + Spec 133 (structure templates) — large
  vendored sub-trees that exercise the discipline.
- Spec 149 (derived-doc discipline) — vendoring header is a `# vendor:`
  marker analogous to the doc's `<!-- doc-source: -->`.
- Spec 259 (derived-doc self-test) — sibling drift coverage; the two
  audits together span hand-written docs + vendored data.
- **Drift-derivation chain** for vendored data.

## Open questions

1. **Hash algorithm — sha256 or BLAKE3?** **Recommend**: sha256 —
   universal tooling, sufficient strength; BLAKE3 is faster but adds
   a dependency.
2. **What about generated vendored files (e.g. tokenizer tables
   re-derived from upstream)?** **Recommend**: header includes
   `vendor-generator: <script>` so the regeneration is reproducible;
   `check-vendoring --refresh` re-runs the generator.
3. **License compatibility check across the substrate?**
   **Recommend**: emit an SPDX expression for the aggregated license
   set; flag incompatibilities (e.g. GPL inside a permissive
   substrate) in CI as WARN; let the operator decide.
