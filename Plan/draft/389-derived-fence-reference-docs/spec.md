<!-- agency-node: spec-389 -->
---
spec_id: "389"
slug: derived-fence-reference-docs
status: draft
state: draft
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [2, 9]
depends_on: ["149", "259"]
affects:
  - scripts/derive_docs.py                  # extend the derived-fence engine with code-introspection fence kinds
  - scripts/check-doc-drift                 # teach the detector to treat derived fences as auto-resolved, not hand-stamped
  - docs/vision/reference/overview.md        # first consumer — substrate-tools list becomes a derived fence
domain: docs / drift / derivation
wave: doc-drift-hardening
---

# Spec 389 — Derived fences for hand-authored reference docs

> Discovered by the **Fresh-Agent Onboarding Proof loop** (`docs/loops/fresh-agent-onboarding-proof.md`).
> Pass 3 of that loop established that `docs/vision/reference/*.md`, `docs/guide/frugal.md`,
> `docs/README.md`, etc. are **hand-authored — no generator targets them**; `check-doc-drift`
> only *detects* drift (hashes `doc-source` files) and prompts a human re-stamp. The drift it
> catches is overwhelmingly in **mechanically-derivable fragments** copied from code — e.g.
> `overview.md` said "the **eight** `SUBSTRATE_TOOLS`" while the tuple had grown to **11**
> (Spec 339 added `lifecycle_open`/`move`/`close`). The hand-copy is the defect.

## Problem

A reference doc mixes two kinds of content:

1. **Prose** — narrative an author must write and maintain (the value of a hand doc).
2. **Derived fragments** — facts that already live in code: the `SUBSTRATE_TOOLS` roster,
   a capability's verb list, the driver-boundary count, the four-concept→module table.

Today both are hand-typed, so (2) silently rots on every refactor and `check-doc-drift` can
only say "a source changed — re-read the whole doc and re-stamp," which is high-friction and,
when an author bulk-`--update`s, invites blind re-stamping (the very gaming the drift gate
exists to stop). CLAUDE.md rule 2 (derive, don't duplicate) and rule 9 (never silently lie
about the tree) both point the same way: the derivable fragments should regenerate from the
live source, leaving only prose hand-maintained.

## Approach — extend the `<!-- derived:… -->` fence pattern (Spec 149) to reference docs

`scripts/derive_docs.py` already ships a fence engine — `find_fence` / `rewrite_fence` /
`render_fence_content` — used for spec.md `test-count` zones. This spec extends it with a
small set of **code-introspection fence kinds** that render from the live engine, and runs
them over `docs/` (not just `Plan/`):

- `substrate-tools` → the `SUBSTRATE_TOOLS` wire-name list (from `agency/_substrate_tools.py`).
- `capability-verbs:<cap>` → a capability's verb roster (from the live registry).
- `driver-boundaries` → the `_boundary_defaults` count + names (from `agency/engine.py`).

An author opts a fragment in by wrapping it in `<!-- derived:substrate-tools -->` …
`<!-- /derived:substrate-tools -->`; everything outside the fence stays byte-preserved prose.
`check-doc-drift` learns that a doc whose **only** changed bytes are inside derived fences is
*auto-resolved by regeneration*, not a hand-review item — so the human-review signal narrows
to genuine prose drift.

## Scope

IN: the fence-render functions for the three kinds above; a `derive_docs --write-docs` pass
over `docs/`; `check-doc-drift` integration that distinguishes derived-zone drift (auto-fix)
from prose drift (hand-review); migrate `overview.md`'s substrate-tools list as the first
consumer + proof.

OUT: rewriting prose; a full templating engine (Spec 388 owns Jinja); auto-generating whole
docs (these stay hand-authored — only fragments derive); the non-derivable reference docs'
prose drift (still hand-reviewed, this spec just shrinks that surface).

## Acceptance (Gherkin-shaped, to expand in the acceptance phase)

- Given `overview.md` with a `substrate-tools` derived fence, When the substrate-tool set
  changes in code, Then `derive_docs --write-docs` updates the fence to match and
  `check-doc-drift` reports the doc auto-resolved (no hand re-stamp required).
- Given a reference doc whose prose changed but whose derived fences match code, When
  `check-doc-drift` runs, Then it still flags the prose drift for hand review (the derived
  pass never masks genuine prose rot).
- Given a derived fence that is opened but unclosed, Then the run fails with
  `Codes.DERIVE_FENCE_BROKEN` (reuse the Spec 149 contract).

## Followup — Implementation Status (draft)

Not started — drafted from the onboarding-proof loop's Pass-3 finding. Next: triage against
Spec 259 (derived-doc-self-test) for overlap, then the acceptance phase.
