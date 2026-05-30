---
spec_id: "019"
slug: engine-output-shape-contract
status: draft
owner: "@agency"
depends_on: ["016"]
affects:
  - agency/engine.py                     # add a comment defending the unwrap
  - agency/capability.py                 # extend lint_capability to enforce return-shape docstring
  - agency/capabilities/**/*.py          # docstring sweep
  - docs/vision/CAPABILITY-AUTHORING.md  # codify the wire-shape rule (Spec 016 doctrine page)
estimated_jules_sessions: 0
domain: meta
wave: 3
---

# Spec 019 — Engine output-shape contract (resolves Jules's vision-drift finding without removing the unwrap)

## Why

**Jules's Spec 015 review** (`Plan/015-architecture-review/
ARCHITECTURE-REVIEW.md` W4, `Plan/015-…/JULES-OBSERVATIONS.md` Round 1
bullet 2) flagged a real inconsistency: `reflect.note` returns
`{"result": rid}` internally, but the engine unwraps at
`agency/engine.py:85` so callers see just the bare string `rid`.
Jules wrote a script expecting `r["reflection_id"]`, got a `KeyError`,
spent trial-and-error figuring out the actual return shape. Classified
as `vision-drift`.

**Jules's `Plan/015-…/PROPOSED-SPECS.md` Spec 018 proposed REMOVING the
unwrap.** I rejected that in the @jules review (`4582949678`,
must-fix #3): the unwrap is intentional. It's the Spec 001 envelope
discipline — verbs return `{"result": <delta>}` internally so the engine
can detect the ok-path vs. error-path uniformly; the wire shape that
crosses to the agent is `<delta>` (the lean code-mode contract per
CORE.md:9-18 + GOALS.md goal #5).

**Removing the unwrap would break ~30 verbs + many tests.** It also
re-introduces the "every verb wraps its delta with a `result` key the
caller has to unwrap" boilerplate code-mode is designed to avoid.

**The right fix is the OTHER side of the same problem:** the wire shape
is correct, but the docstrings don't tell the agent what shape it'll
actually see. Jules's frustration was a documentation bug, not a
contract bug.

## Done When

- [ ] **`agency/engine.py:85` gets a defensive comment** explaining why
  the unwrap exists, citing Spec 001 + this spec. Future readers (LLM
  or human) reading the line in isolation now have the context.
- [ ] **Every existing verb docstring states the WIRE shape, not the
  internal-wrap shape.** Per Spec 016 Hint #7:
  ```python
  @verb(role="act")
  def note(self, scope: str, text: str) -> dict:
      """Write a scope-tagged insight node.

      Inputs:  scope (one of REFLECT_SCOPES), text (str).
      Returns: <reflection id, str>      # ← NOT {"result": <id>}
      chain_next: reflect.recall(scope=) | reflect.search(query=).
      """
  ```
- [ ] **`plugin.lint_capability` (Spec 016 Done When item) enforces the
  rule.** A verb whose docstring says `Returns: {result: ...}` AND whose
  implementation returns `{"result": ...}` is flagged: "Docstring leaks
  the engine wrap; describe the wire shape, not the internal envelope."
- [ ] **Docstring sweep across all 11 capabilities.** A single mechanical
  pass: read each `@verb` method's actual return + update the docstring's
  `Returns:` line to match the WIRE shape (what code-mode callers see)
  not the INTERNAL shape (what the verb's `return` statement carries).
- [ ] **Test landmark** — `tests/test_engine_unwrap_contract.py`:
  - Asserts the unwrap behavior on a representative verb (`reflect.note`)
    against BOTH transports (registry.invoke direct → wrapped;
    code-mode execute → unwrapped). Locks in the contract.
  - Asserts `plugin.lint_capability` flags a verb whose docstring
    `Returns:` line contains the `result` key when the actual return
    is wrapped.

## Files

- **Modify:**
  - `agency/engine.py:85` — add the defensive comment (1 line).
  - `agency/capabilities/plugin.py` — extend `lint_capability`
    (Spec 016 Done When item) with the new rule.
  - `agency/capabilities/*.py` — docstring sweep on every `@verb`.
- **Create:**
  - `tests/test_engine_unwrap_contract.py`.
- **Documentation:**
  - `docs/vision/CAPABILITY-AUTHORING.md` (Spec 016 deliverable) gets
    a new section: "Wire shape vs internal wrap" with the example
    above + the explicit rule "docstring describes wire shape."
  - `docs/vision/CORE.md` "Engine" section gets a one-line addendum:
    "Verbs may wrap their delta as `{result: <delta>}` for engine-side
    ok-path detection; the wire shape strips the wrap."

## Open Questions

1. **`plugin.lint_capability` rule strictness: BLOCK vs WARN.**
   Spec 016 Open Question 1 already raises this. Recommend: WARN until
   the docstring sweep is complete; BLOCK after. Sequence matters — if
   we BLOCK before sweeping, every existing capability test fails.
2. **What about verbs that DON'T wrap?** Some verbs return rich dicts
   directly (`{status, session, url, alias, artefact}` from `jules.dispatch`).
   The lint rule must not penalize these — the rule is "if you wrap,
   say so" not "you must always wrap."
3. **`jules.dispatch` returns `{status, session, ..., artefact: {...}}`
   — does the engine ALSO check `artefact` for `PRODUCES` provenance
   recording?** Yes (per `agency/capability.py:226-228` per the
   vision-conformance subagent finding). The docstring must mention
   this OR the lint must understand the `artefact` convention as a
   second wrap-variant. Recommend: document the convention; lint reads it.

4. **Exception for genuinely-rich-dict verbs (panel addition).** Some
   verbs return rich structured dicts without the `{result: <delta>}`
   wrap — `jules.dispatch` returns `{status, session, url, alias,
   artefact}` straight to the wire. The lint rule must NOT flag these.
   The detection heuristic: if the verb's actual return contains a
   `result` key at the top level AND no other keys, treat as wrapped;
   otherwise treat as rich. The lint then requires the docstring's
   `Returns:` line to MATCH the actual top-level shape (the wire
   shape). Test: assert lint passes on `jules.dispatch` (rich) AND
   on `reflect.note` (wrapped, docstring says "reflection id (str)").
4. **Should this spec absorb Spec 016 Hint #7 entirely?** Hint #7 says
   "every verb docstring follows the Inputs/Returns/chain_next shape."
   This spec is just one slice (the Returns line). Recommend KEEP them
   separate — Spec 016 lands the doctrine page + lint scaffold;
   Spec 019 lands one specific lint rule + the sweep. Spec 019 is the
   first proof-of-concept for the lint extensibility.

## Evidence

- `Plan/015-architecture-review/ARCHITECTURE-REVIEW.md` W4
  (vision-drift, the original finding).
- `Plan/015-architecture-review/JULES-OBSERVATIONS.md` Round 1 bullet 2
  (the trial-and-error story — Jules wrote `r["reflection_id"]` and
  got KeyError).
- `Plan/015-architecture-review/PROPOSED-SPECS.md` Spec 018 (the
  proposal this spec REJECTS the implementation strategy of, while
  keeping the underlying problem).
- @jules review comment 4582949678 (must-fix #3 — the nuance that
  drove this spec's rewrite).
- `agency/engine.py:85` — the unwrap. `agency/capability.py:185-200`
  — the ToolResult envelope unwrap path (Spec 001).
- `docs/vision/GOALS.md` goal #5 (code-mode IS the contract; the
  wire shape stays lean).
- `Plan/016-capability-authoring-doctrine/spec.md` Hint #7
  (the docstring contract this spec proves out).
