# DOGFOOD-NOTES — building Spec 013 inline

Running record of what landing Spec 013 (the Jules skills + capability
improvements) inline teaches us about the design we shipped. Each entry
folds back into the spec or a follow-on when a pattern is clear.

---

## 2026-05-30 — Phases 1-12 shipped sequentially inline

**Sessions:** none dispatched to Jules; per the `delegate.dispatch-decision`
skill heuristic (`AGENCY_PROTOCOL.md` formerly §9a → now the
`delegate.dispatch-decision` skill), none of the 12 phases individually
met the "context-heavy" bar: each was a clear greenfield write of
50-150 lines against verbs already in the orchestrator's window.
Dispatching each one would have paid ~700 tokens of preamble + the
review-cycle wake budget for marginal savings.

**Cost calculus, observed:**
- Phases 1-3 (doctrine docs + preamble assembler + lint_prompt verb):
  ~30 minutes orchestrator wall-clock, ~9000 tokens of message budget
  including all test iteration. Dispatching would have cost ~700 *
  3 = 2100 tokens for preamble + ~3000 for review-cycle prompts
  + idle time waiting for Jules wake events.
- Phases 5-10 (six skills): each ~40 lines of schema in
  `_jules_skills.py` + a focused test file. The schemas share a
  pattern (phase index/name/produces/invoke/inputs), so writing them
  inline was strictly faster than fanning out.

**Observation 1 — the engine-on-context refactor was load-bearing.**
Phase 7's `jules.watch` / `jules.recover` / `jules.apply_patch` verbs
needed to reach `engine._jules_watcher` from a verb context. Initial
attempt used a module-level `_SINGLETON` in `_jules_watch.py` as a
shim. The user flagged this immediately ("rely on the engine because
we want to test it") — the singleton bypassed the registry, made
tests fragile (need cleanup between tests, can leak), and broke the
"tests exercise the engine wiring" invariant. Fix: added `engine`
field to `CapabilityContext`; threaded through `Registry`; verbs
use `self.ctx.engine`. → **Design fold-back to a future spec:** the
`CapabilityContext.engine` field is now a real surface — should be
documented in `docs/vision/specs/capability-base.md`. Until that
lands, every new verb that needs engine-attached state has a clean
path; no per-feature singleton shims.

**Observation 2 — the intent question (calling vs watching) was real.**
`jules.watch(session=sid)` raised the question: is the *calling* intent
(auto-injected `intent_id`) the same as the *watching* intent (the one
that originated the dispatch, recorded as `JulesSession SERVES Intent`)?
The answer matters for cross-session resume — a fresh intent later
asking `watch(session=sid)` differs from the dispatch intent. The
SERVES edge is the bridge; the verb resolves through it. → Now
documented in the `jules.watch` docstring; `for_intent` overrides
the resolution; response includes `_for_intent` trace field so the
caller knows whose queue was read.

**Observation 3 — back-compat code aged out within hours.**
Phase 4 landed `auto_create_pr=True` as a deprecation alias mapping to
`automation_mode="AUTO_CREATE_PR"`, with a one-shot `DeprecationWarning`.
Forty-five minutes later, the user directed: "since this is the initial
version, remove deprecated code without warning". The alias was cut
entirely — `_AUTO_CREATE_PR_DEPRECATION_FIRED` module flag, the
`warnings.warn` branch, the 3 alias-semantics tests, and the docstring
bullets all stripped in one clean commit. → **Lesson:** for pre-v1
software, the back-compat machinery is dead weight. Code paths added
"to be safe" survive only as long as the project is younger than the
first user. The right v0.x discipline: cut, don't carry.

**Observation 4 — the `reflect.note` scope ontology is closed.**
Phase 10's `jules-self-improvement` skill binds Phase 2 to
`reflect.note(scope, text)`. Initial test used `scope="dogfood"` —
caught by the ontology validator: scopes are constrained to
`['observation', 'project', 'reflection', 'technical', 'user', 'world']`.
Dogfood observations land under `observation` (closest semantic match).
→ **Design fold-back:** consider adding `dogfood` as a real scope in
the next core ontology update — the agency's own `Plan/**/DOGFOOD-NOTES.md`
artefacts are a distinct enough kind of observation to deserve a
first-class tag.

**Observation 5 — opentelemetry-util's deprecation noise is third-party
debt.**
Adding `pytest-asyncio` for Phase 8's lifespan tests surfaced an
`opentelemetry.util._importlib_metadata` DeprecationWarning on every
test run. It's third-party code calling legacy
`SelectableGroups.values()` instead of `entry_points(group=…).select(…)`.
No newer opentelemetry-api version fixes it as of this commit. Filtered
at the pytest layer via `pyproject.toml [tool.pytest.ini_options]
filterwarnings`. → Track upstream; remove the filter when a fixed
version ships.

## What to fold into the next spec

- **Promote `CapabilityContext.engine` to `docs/vision/specs/`** — it's a
  real surface now and every new effect-verb that needs engine state
  will reach for it.
- **Add `dogfood` to the closed scope set on `reflect.note`** — the
  ontology change is small (one enum entry); the value is making
  Spec 013's own ledger machine-queryable via `reflect.search(scope="dogfood")`.
- **Remove the opentelemetry filterwarnings** when upstream ships a
  fix that drops the `SelectableGroups` path.
