# RESEARCH-skills — the shape of Jules skills (subagent A3)

## 1. The canonical skill shape

Per `CORE.md:47-62` + `agency/skill.py:24-86`:

A skill is a **Lifecycle template** — an ordered list of atomic `Phase`
dicts, each with `index`, `name`, `produces` (required outputs), optional
`inputs`, optional `invoke` (binds to a real Capability verb so walking
EXECUTES), and optional `gate: "hard"`.

- **Progressive disclosure** (`skill.py:40-46`): `current()` returns only
  the *current* phase's spec — tokens are paid per phase, never the whole
  skill.
- **Per-phase verification** (`skill.py:68-70`): `submit()` raises if
  `produces` fields are missing. Verification happens via the data the
  agent gathers (typically `read_file` / `list_files` / a predicate verb)
  BEFORE the walker advances.
- **Hard gate** (`skill.py:71-72`): returns `{"status": "input-required"}`
  and pauses; `confirmed=True` resumes. This IS the `elicit` from
  `CORE.md:56-60` — "askuser is one node in the chain."
- **Provenance** (`skill.py:73-83`): every phase records a `Phase` node
  edged `HAS_PHASE` to the skill run, `SERVES` to the intent, `PRECEDES`
  to the prior phase and to any invoked Invocation. The walk mirrors
  itself into provenance.

The music exemplar (`examples/music.py:22-43`) is canonical: 7 phases, 6
document phases producing typed outputs, ending in a hard confirm gate.
`develop.py:28-80` adds advisory phases plus the `invoke`-binding pattern
(`review.dispatch → delegate.fan_out`).

## 2. The Jules skill set, refined

Spec-013's hypothesis holds:

- `jules-protocol-preamble` — once-per-dispatch boilerplate enforcement.
- `jules-tool-discipline` — phases binding `submit`,
  `pre_commit_instructions`, `request_user_input`,
  `replace_with_git_merge_diff`, `request_code_review` to their right
  moment; each phase's `produces` is the recorded tool choice.
- `jules-recovery-when-stuck` — probe via `message`, extract patch, apply
  locally, never re-dispatch; hard gate on "branch-on-origin verified."
- `jules-pr-review-cycle` — `read_pr_comments` → `reply_to_pr_comments`
  → `request_code_review`.
- `jules-fanout` — composes `delegate.fan_out` via an `invoke` phase
  (mirrors `develop.review`).
- `jules-self-improvement` — appends dogfood notes; advisory only.

## 3. Intersection model

Three candidates: (a) `develop`-style chaining (skill A's done-gate is
B's entry), (b) shared gates by name, (c) a meta-skill composing others.
**Recommendation: (a).** `develop.review.dispatch`'s `invoke` binding
proves it. (b) is unsupported — the walker has no name-keyed gate
registry. (c) adds indirection. `jules-protocol-preamble`'s hard gate
becomes the precondition every other Jules skill checks at entry —
enforced socially in `jules.dispatch`, not in the walker.

## 4. Boundary with `develop`

`develop.py` owns RED-then-GREEN (tdd), root-cause (debug), evidence
(verify), plan approval, spec critique. Jules skills MUST extend, not
duplicate. Concretely: TDD is `develop.tdd`; verifying the branch via
`git ls-remote origin` is Jules-specific (the `COMPLETED ≠ done`
predicate, `_jules_reference.md` §7). Jules skills layer Jules-tool
naming + remote-state verification onto disciplines `develop` enforces.

## 5. Worked example — `jules-protocol-preamble`

```python
{"name": "jules-protocol-preamble", "kind": "discipline", "phases": [
  _phase(1, "verify-remote-state", ["remote_head"]),          # advisory
  _phase(2, "name-canonical-tools", ["submit_named",          # advisory
                                     "precommit_named"]),
  _phase(3, "set-scope", ["scope_boundary"]),                 # advisory
  _phase(4, "dispatched", ["session_id"], gate="hard"),       # HARD
]}
```

Phase 1 verifies via a recorded `git ls-remote` invocation (predicate).
Phase 4 is the `elicit` (`CORE.md:56-60`): walker pauses at
`input-required` until `confirmed=True` carries the real `session_id` —
the canonical silent-fail guard. Compiles directly into
`OntologyExtension.skills` like `DEV_SKILLS` (`develop.py:127`).
