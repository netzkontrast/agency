---
spec_id: "058"
slug: reflection-link-lint
status: draft
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["016", "019"]
affects:
  - agency/capabilities/plugin.py        # NEW _check_reflection_links lint rule
  - tests/test_reflection_link_lint.py   # NEW
  - docs/vision/CAPABILITY-AUTHORING.md  # codify the convention
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 058 — Reflection-link convention as a lint rule

## Why

The agency engine has a strict convention for Reflection nodes: a verb
that records a `Reflection` must link it with BOTH `SERVES`
(provenance — surfaces in `Memory.provenance(intent_id)`) AND
`OBSERVED_DURING` (the intent-scoped reflection view used by
`document.render(scope='reflections', for_intent_id=...)` and the
`index_repo` recent-activity filter).

Today the convention is implicit. PR #17's round-1 review caught the
exact bug:

> `document.explain` only adds `SERVES`, but `document.render(scope=
> 'reflections', for_intent_id=)` and the repo-index recent-activity
> filter the Reflections through `OBSERVED_DURING`. As a result,
> explanations generated for an intent disappear from the intent-scoped
> view even though they are Reflection nodes.

There's no test or lint that catches a Reflection write missing the
`OBSERVED_DURING` link. Authors copy-paste from `reflect.note` (which
does both) but a verb authored fresh (`document.explain` was) easily
omits one half.

Pair with Spec 016's lint scaffold and Spec 019's wire-shape rule:
this is the next decidable lint check on the capability surface.

## Done When

- [ ] **`plugin.lint_capability` gains `_check_reflection_links`** —
      walks each verb's source for `record("Reflection", ...)` calls.
      For each such call, requires the same method to also contain BOTH
      `link(..., "SERVES")` and `link(..., "OBSERVED_DURING")` linking
      the recorded id to the current intent. Missing either edge =
      `reflection_link` finding.
- [ ] **The rule is WARN-mode initially.** Flips to BLOCK once the
      audit shows zero remaining bare-`SERVES`-only Reflection writes.
- [ ] **Audit + migration**: scan the live registry; verbs missing
      `OBSERVED_DURING` get the edge added. Sites known to need
      review (non-exhaustive — the lint will surface the full list):
  - `develop.record_authoring_outcome` (links `OBSERVED_DURING` only —
    needs `SERVES`).
  - Any future verb that writes a Reflection.
- [ ] **`tests/test_reflection_link_lint.py`** — 4 tests:
  - Verb with both edges → lint passes.
  - Verb with SERVES only → lint warns.
  - Verb with OBSERVED_DURING only → lint warns.
  - Verb that doesn't write a Reflection → lint silent (no false-fire).
- [ ] **CAPABILITY-AUTHORING.md gains a section** "Reflection
      write convention" — names the two edges + their consumers + the
      lint rule that enforces both.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### Detection heuristic

`_check_reflection_links` walks the verb's source via AST. For each
verb method:

1. Find `Call` nodes matching `<obj>.record("Reflection", ...)` or
   `<obj>.memory.record("Reflection", ...)`. Each match captures the
   variable assignment of the returned id (e.g. `rid = self.ctx.
   record(...)`).
2. For each captured id name, scan the rest of the method body for
   `<obj>.link(<id_name>, ..., "SERVES")` and `<obj>.link(<id_name>,
   ..., "OBSERVED_DURING")` calls.
3. Verbs missing either edge emit a `reflection_link` finding naming
   the verb + the missing edge.

The heuristic is conservative — it can't catch a Reflection recorded
via dynamic label (`record(label_var, ...)` where `label_var` is set
in a branch). Those rare cases skip the rule with no false-fire.

### Why both edges matter

| Edge | Consumer | Purpose |
|---|---|---|
| `SERVES` | `Memory.provenance(intent_id)` | Cross-concern provenance traversal |
| `OBSERVED_DURING` | `document.render(scope='reflections', for_intent_id=)` | Intent-scoped reflection view |
| `OBSERVED_DURING` | `document.index_repo` recent-activity filter | Repo-briefing surface |
| (future) | `reflect.recall_semantic` intent filter | Intent-scoped semantic recall |

A verb that records a Reflection without `OBSERVED_DURING` writes a
node that's invisible to half the consumers — a silent provenance
hole that only surfaces when an author queries the missing-edge path
and finds nothing.

## Files

- **Create:**
  - `tests/test_reflection_link_lint.py`.
- **Modify:**
  - `agency/capabilities/plugin.py` — add `_check_reflection_links` +
    plumb into `lint_capability`.
  - Audit sites (per migration): `agency/capabilities/develop.py`
    `record_authoring_outcome` (add `SERVES`); any verb the lint
    scan surfaces.
  - `docs/vision/CAPABILITY-AUTHORING.md` — new section.

## Open Questions

1. **Should the lint also enforce the inverse?** A verb that writes a
   Reflection but DOESN'T tag it with a `scope` (the ontology's
   required field) already fails ontology validation at record time.
   So the inverse case is already covered by the substrate; this
   spec only adds the edge check.

2. **What about Reflection-writing verbs that intentionally skip
   `OBSERVED_DURING`?** Hypothetical case: a verb that records a
   Reflection that's NOT scoped to the calling intent (e.g. a
   cross-intent observation). Recommend: such verbs declare an
   `# agency-skip-link-check: <reason>` marker on the relevant line;
   the lint reads the marker and skips.

3. **Path to BLOCK mode.** WARN immediately. Once the audit migrates
   any surfaced sites, flip to BLOCK. Expect 1-3 sites to migrate.

## Evidence (cites)

- `agency/capabilities/document/_main.py:116-121` — the round-1 fix
  that added the missing `OBSERVED_DURING` link.
- `agency/capabilities/reflect.py:32-34` + `:50-52` — the canonical
  pattern (both edges).
- `agency/capabilities/dogfood.py:123-124` — the same pattern in
  `dogfood.note`.
- `agency/capabilities/develop.py::record_authoring_outcome` — the
  site likely flagged by the audit (links only `OBSERVED_DURING`).
- PR #17 review r3345071835 — the source comment.
- Spec 016 Hint #7 — the docstring-contract lint scaffold this
  rule extends.
- Spec 019 — the wire-shape rule that proved out the lint
  extensibility this spec follows.
