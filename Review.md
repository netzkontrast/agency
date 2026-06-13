# Review.md — Review-Partner log for the Substrate OOP Refactor (Spec 286)

> **Role split (user directive, 2026-06-13).** This session is now the
> **Review Partner** for PR #141. It no longer implements refactor work.
> It reviews **every commit** the refactor agent pushes, logs verdicts here,
> and coordinates via PR comments. The refactor agent owns implementation and
> maintains a companion **`refactor.md`** (expected in repo root) describing
> intent/plan per slice. This file ↔ `refactor.md` is the detailed exchange.

## The goal we are driving toward

Refactor the **complete codebase into a clean OOP architecture** where
**every capability is contained inside its own folder** —
`agency/capabilities/<name>/` — behavior-preserving, per Spec 286.

- **Capability-per-folder progress:** 16 caps already foldered. **Stragglers
  still as bare files:** `agency/capabilities/intent.py`, `shell.py`,
  `skills.py` (plus private `_embed.py` / `_vcs.py` helpers). These are the
  remaining "own folder" migrations.
- **Spec 286 phases:** 0 foundational ports → 1 invocation spine → 2 substrate
  + concept cleanup → 3 leaf decomposition. Sequenced **leaves-first** so the
  shared branch's #141 spine work (`capability.py`/`engine.py`/`memory.py`/
  `novel/`/`skill.py`/`develop`) settles before the spine is touched.

## Review rubric (what every commit is checked against)

1. **Behavior-preserving — the prime directive.** Zero contract / wire /
   verb-name change. The 3-tool wire (`search`/`get_schema`/`execute`) is
   byte-stable; live verb count unchanged; `agency_doctor` field-set unchanged;
   MCP vs bash output identical.
2. **Vision-goal alignment** (`docs/vision/GOALS.md`): goal 4 (open set =
   add-a-folder), goal 5 (code-mode IS the contract), rule 2 (graph is store,
   files rendered), rule 8 (assert invariants, never frozen counts/snapshots).
3. **#141 seam preservation** — the refactor must carry, not drop:
   - `param_enums` surfacing (Spec 284) through any `ParameterInjector` extract.
   - the `_host_ctx` ContextVar capture + `finally` reset (Spec 285-A).
   - `_host_llm.complete_or_delegate`'s sample branch untouched.
   - the `{ok, error:{code,message,severity,retryable,trace_id}}` failure
     envelope (Spec 282 A) in any `WireEnvelope.unwrap()`.
   - `Memory.link`'s transient-`vfrom` retry/backoff (Spec 282 C) inside the
     `GraphStore` port.
   - a clean **post-mutation hook** in `ResultProcessor` for Spec 283's
     renderer + the Spec 282-E permanent-failure dedup (`retry_count`).
4. **Test discipline** — RED→GREEN per slice; FULL non-e2e suite per migration
   (touches repo-wide invariant tests, not just the slice); `check-drift` exit 0;
   `TODO.md` row updated in the same commit (CLAUDE.md rule 4).
5. **Blast-radius** — a leaf type change (e.g. `Finding`→dataclass) must audit
   **non-test runtime consumers**, not just tests.

## Verdict legend
✅ Approve · 🟡 Approve-with-nits (non-blocking) · 🔶 Changes-requested (blocking) · ⏳ Pending

---

## Commit review log

### `5ad2655` — refactor(286): extract SubprocessAnalyzer Template Method — ✅ Approve
- **What:** `analyze/_subprocess_analyzer.py` owns the which-guard →
  `subprocess.run(timeout)` → returncode-tolerance → json-parse →
  payload→Finding scaffold + one shared `_SUBPROCESS_TIMEOUT` (was 3×);
  ruff/bandit/radon become small subclasses with 3 hooks.
- **Behavior-preserving:** ✅ public `scan`/`cyclomatic`/`maintainability` +
  `AXIS_PREFIXES` unchanged → composers + `_build_axis_registry` untouched.
- **Rubric:** degrade-silently contract (Spec 050) preserved (missing tool /
  subprocess fail / bad rc / unparseable → `[]`, never raise). Good docstring.
  63 analyze + 7 scaffold tests green; drift clean.
- **Nits:** none blocking. Clean Template Method.

### `f516a93` — refactor(286): Finding value object + open umbrella spec — 🟡 Approve-with-nits
- **What:** `Finding` → `@dataclass(frozen=True)`; `FindingSeverity(str, Enum)`.
  Migrated `test_analyze_architecture` + `test_analyze_deps_integration` to
  attribute access.
- **Behavior-preserving:** ✅ for the wire (`FindingSeverity` subclasses `str`
  → JSON-safe, `== "warn"` holds; `_main.py` wire dict preserved).
- **🟡 Blast-radius nit (non-blocking, already mitigated):** the migration
  **missed `test_intent_path_analysis.py`** (6 tests went red on
  `'Finding' object is not subscriptable`). Reviewer fixed it in `5a9d50c`
  (same mechanical `f["rule"]`→`f.rule` pattern). **Action for refactor agent:**
  when a leaf value-object lands, grep ALL consumers (`f\["` over `agency/` AND
  `tests/`), not just the sibling test files — and confirm no **runtime**
  (non-test) site subscripts the type.
- **🔶 Open CI item (NOT reviewer's to fix — yours):** `Plan/286/spec.md` has
  **no `vision_goals:` frontmatter** → `test_vision_goals_validator` is the
  **sole remaining red** on the branch (8/9 prior failures fixed). Add a YAML
  frontmatter block above the `<!-- doc-source -->` line; suggested
  `vision_goals: [4, 5]` (open-set maintainability + upholds the code-mode
  contract). CI goes green once it lands.

### `b22c350` + `b1b8b9e` + `36fa80a` — Finding wire-shape reconcile + budget + 286 frontmatter — ✅ Approve
- **What:** the refactor agent reconciled the `Finding` value-object so the
  **wire contract is preserved**, rather than migrating every consumer to
  attribute access:
  - `b22c350` — `Finding` stays a frozen dataclass **and** gains `to_dict()`
    returning the exact pre-286 plain-dict shape (`severity` → its string
    value). Verbs that surface findings over the wire + the Finding-node record
    path serialise through it. Also **added the `Plan/286` `vision_goals`
    frontmatter** — resolving the CI red I flagged.
  - `b1b8b9e` — reverted `test_intent_path_analysis` back to `f["rule"]` dict
    subscript, because that verb returns findings **over the wire (dicts)**,
    not as in-process `Finding` objects. This **supersedes the reviewer's
    `5a9d50c`** `.rule` change — and it's the **better fix**: it corrects the
    layer (the wire boundary emits dicts via `to_dict`) instead of bending the
    test to an object that only exists in-process.
  - `36fa80a` — loosened the welcome fixed-overhead budget `1000 → 2000` per
    owner directive (supersedes the reviewer's interim `1300`); applied
    consistently to **both** `test_welcome.py` + `test_welcome_state.py` (no
    drift between the two constants — checked).
- **Self-consistency (the thing I was watching for):** the two finding access
  styles now map to two genuinely different paths — `test_analyze_architecture`
  gets `Finding` objects in-process (`f.rule` ✓); `test_intent_path_analysis`
  gets wire dicts (`f["rule"]` ✓). No contradiction. ✅
- **Rubric:** behavior-preserving ✅ (wire shape restored — *more*
  contract-faithful than the reviewer's fix); the blast-radius lesson is
  applied (the fix moved to the seam).
- **Reviewer note:** my `5a9d50c` is now superseded, and that's correct — the
  agent found the right layer. No action needed; the supersession is clean.

---

## Branch CI snapshot (2026-06-13 ~12:05 UTC)
- HEAD `b1b8b9e`: **GREEN** (pytest success, run 27466219677). The branch went
  red → green: welcome-budget ×2 + Finding-migration ×6 (reviewer) + the
  Finding wire-shape reconcile + `Plan/286` frontmatter (refactor agent) closed
  all 9 prior failures. **PR #141 is mergeable on CI.**
