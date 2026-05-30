# Spec-Panel Review — 001 Unified `ToolResult` Envelope + Typed Errors

Reviewers (composite): Wiegers specification-quality, software architecture,
faithfulness-to-source, testability, security. Grounded in the real
`the-agency-system` tree @ `0a6a9e71` (paths cited below are relative to
`/home/user/the-agency-system`).

---

## Verdict

**Conditional accept — strong structurally, but NOT yet faithful to what the
source actually shipped.** The spec correctly identifies the #1 rewrite vector,
names the two real seams (`Registry.invoke`, `_wire`), gives honest before/after
exemplars with accurate line numbers, and pins a regression-guarded test list.
That is good spec craft.

But the proposed envelope is reconstructed from the agency-internal
`research/oo-architecture/PROPOSAL.md` sketch, **not** from the source's
authoritative schema. Three of the spec's "Open Questions" are already
*resolved by the source* — the spec treats invented decisions as open while
copying the proposal's drift. The single load-bearing decision (Open Q-2) is
correctly identified as load-bearing but the source gives a clear steer the spec
ignores. Do a source-reconciliation design pass before coding.

---

## Source-grounded corrections

### 1. The envelope field set is wrong: `artefacts_written: list[str]`, not `artefact: dict`
The authoritative schema (canvas §5, `docs/superpowers/specs/_drafts/2026-05-19-agency-base-canvas.md:156-179`) declares:
```
required: ["ok", "warnings", "artefacts_written"]
optional: data, next_suggested_tools, error, archived_to
```
Every shipped handler hand-rolls exactly this — `artefacts_written` is a
**top-level, plural `list[str]`, IN the wire shape** (`handlers/shared/skills.py:47-54`, `handlers/shared/search.py:85-87,132-134`, `handlers/shared/config.py:16-34`, `handlers/shared/session.py:21-92`). The spec's design instead invents a singular `artefact: dict` field that it then *excludes* from `to_dict()` (spec lines 192, 227-229) and re-routes only as a provenance signal to `Registry.invoke`. That is a clean fit for agency's *current* `result["artefact"]` PRODUCES sniff (`agency/capability.py:177-179`) — but it is **not the source envelope**, and it silently drops the source's caller-visible "what did this write" contract. The design pass must reconcile: keep the source's `artefacts_written: list[str]` on the wire, and derive the PRODUCES edge from it, rather than smuggling a private `artefact` dict.

### 2. `ErrorCode` Enum is invented; the source uses free-string `code` + `trace_id`
The source's `error` sub-object (canvas §5 `:168-176`) is `{code: string, message: string, trace_id?: string}` — **`code` is a free string, there is no closed Enum, and the third field is `trace_id` (a correlation id), not `context`.** Real `code` values in the tree are inconsistent by design: `"unsupported"` (`handlers/jules/lifecycle.py:476`), `"illegal_transition"` (`handlers/novel/status.py:64,123,165`), `"PRE_DRAFTING_GATES_FAILED"` (`handlers/novel/gates.py:298`), `"NOT_IMPLEMENTED"` (`handlers/novel/coherence.py:361`), `"MANIFEST_DRIFT|MANIFEST_INVALID|EDGE_BROKEN"` (canvas `:235`). The spec's `ErrorCode` Enum + `context: dict` come straight from the agency-internal `research/oo-architecture/PROPOSAL.md:138-167` sketch, not from the source. This is a legitimate *agency design choice* (a typed enum is arguably better than the source's free strings for the loop-recovery goal), but the spec presents it as source-faithful when it is not. The spec must either (a) own this as an intentional improvement over source and say so, or (b) align to `{code:str, message:str, trace_id:str}`. Recommend (a) but keep `trace_id` — see Missing depth.

### 3. `next_suggested_tools` is a reserved-but-unpopulated field in the source — the spec over-claims its semantics
Across the entire shipped tree, **`next_suggested_tools` is always `[]`** (grep: zero non-empty literals in `handlers/`). It exists because the router (ADR-0001 step 6, per ADR-0005 `:58`) is *designed* to inspect it, but no handler populates it yet. The spec's `jules.dispatch` after-sketch populates it with real values (spec `:304`) and the `jules.stop` sketch is openly confused about where it lives on a failure (`:318` "passed via warnings/context — see Open Q-1"). Faithful reading: this field is a **forward-looking routing hook**, not a per-verb obligation. Don't gate the spec on getting failure-path `next_suggested_tools` right; mark it as a populated-later field with a stable empty default.

### 4. `0011-repair-authority-tiers` does NOT map error classes to repair tiers
The spec's "Why" (lines 73-76) and Open Q-1 assert that ADR-0011 "maps error classes to repair tiers" and that `ErrorCode` may need to "route a failure to the right tier." **It does not.** ADR-0011 (`Plan/decisions/0011-repair-authority-tiers.md:17-48`) is about classifying *document/code mutations* into T1 Mechanical / T2 Additive / T3 Structural / T4 Immutable — a governance discipline for how changes are *made* (Edit-in-place vs. open-a-spec vs. supersede-only), confirmed verbatim in `Plan/harness/VOCABULARY.md:269-280`. It has nothing to do with runtime tool-error recovery tiers. The spec has conflated "repair-authority tiers (change governance)" with an imagined "error→recovery-tier" mapping. **This invalidates the central premise of Open Q-1.** There is no source-sanctioned `tier` field for `ErrorCode`; drop it.

### 5. ADR-0005's decorator (`@domain_tool`) is "Proposed", not shipped — the source is hand-rolled
ADR-0005 is `adr_status: Proposed` (`:11`) and spec 130 "has not shipped" (`:28`). The real tree still hand-rolls the envelope in every handler. So agency is free to choose its enforcement seam (the spec's choice — serialise at `_wire` — is reasonable and arguably cleaner than a decorator given the reflection-based wiring). Good: the spec does not blindly copy `@domain_tool`. Worth stating explicitly in the spec that agency intentionally diverges from ADR-0005's decorator surface because its `Engine._wire` reflection seam already centralises emission.

### 6. Missing the `archived_to` / oversize-body trim — a load-bearing source field
The source envelope carries `archived_to` and the decorator "routes any return body > 4 KB to the spec-117 archive and replaces it with a pointer" (ADR-0005 `:69`, `:79`; canvas `:177`). This is the structural fix for the measured top-3 token sink (Lesson 14, ADR-0005 `:39`). The spec's envelope has **no oversize-body handling at all.** For an orchestration engine that fans out across child lifecycles (`delegate.fan_out`), unbounded `data` bodies will reproduce the exact token sink the source spent an ADR closing. At minimum the spec should reserve `archived_to: str | None` in the envelope even if the archive intercept is deferred to a follow-up spec.

---

## Missing depth / surface

- **`trace_id` / correlation id.** The source error carries `trace_id` (canvas `:174`) to correlate a failure across the bi-temporal graph. Agency has an `Invocation` node id (`inv`) that is the natural `trace_id` — the spec should thread `inv` (or a derived id) into `TypedError` so a returned failure is joinable to its provenance. Currently absent.
- **Oversize-body trim / `archived_to`** (see correction 6).
- **`data` typed as `{}` (any) in the source, but the spec types it `dict | None`.** The source schema (`:164`) leaves `data` unconstrained (some handlers return a `list` in `data`, e.g. `skills.py:49` `data: limited_skills`). The spec's `dict | None` would *break* the list-returning verbs (`jules.list`, `jules.activities`). The envelope must allow `data: Any`, not just `dict`.
- **`next_cursor` pagination field.** `skills.py:45,52` ships `next_cursor` in the envelope for pagination. Not in the spec's field set; the `jules.list`/`activities` read-verb migration will need it or an equivalent. Flag for the read-verb pass.
- **Warnings semantics.** The source uses `warnings` as the *soft-failure / partial-success* channel even on `ok=False` (`handlers/novel/promo.py:14,59,65,69` return `{"ok": False, "warnings": [...]}` with **no `error` object at all**). The spec's model assumes `ok=False ⇒ error is not None` (the `Registry.invoke` migration at spec `:244` keys off `not result.ok and result.error is not None`). A source-faithful migration must handle `ok=False` *without* a structured `error` (warnings-only failure) — otherwise those become silent non-failures in provenance. Decide: is `error` mandatory when `ok=False`? The source says no.
- **Security/`__eq__` round-trip.** Done-When requires `from_dict(to_dict()) == r` for *every* result; with `next_cursor`/`archived_to`/`artefacts_written` omitted from `to_dict()` (as currently drafted) the round-trip equality will silently fail or drop fields. The test must cover lossy fields explicitly.

---

## Open-Questions triage

| # | Question | Source verdict |
|---|----------|----------------|
| **Q-1** | Final `ErrorCode` set + repair-tier mapping; where `next_suggested_tools` lives on failure | **PARTIALLY RESOLVED → drop the tier premise.** ADR-0011 has *no* error→tier mapping (correction 4); `ErrorCode` must NOT carry a `tier`. The source uses free-string `code` (no closed enum) + optional `trace_id` (canvas `:168-176`). `next_suggested_tools` is a top-level field, always `[]` in source — it stays top-level (not in context), defaults empty, populated later (correction 3). The only genuinely-open part is *whether agency upgrades the source's free-string code to a closed Enum* — that's an agency choice, decidable now, recommend yes + keep it open/extensible. |
| **Q-2** | Does `to_dict()` at `_wire` break the code-mode return contract? | **STAYS BLOCKING — but source gives a steer.** ADR-0005 "Neutral" (`:90`): *"The schema does not change the MCP wire format; clients see the same JSON shape they always did."* The source's intent is that the envelope IS the wire shape (handlers already return `{ok, data, warnings, ...}` to MCP directly). So the faithful answer is: **the full envelope on the wire, callers read `data`** — agency's current unwrapped-inner-dict is the deviation to migrate *away* from, not preserve. This is a real breaking change for existing `execute()` scripts + `agency/cli.py`; it needs a maintainer decision, but "keep unwrapping for back-compat" is *unfaithful* to source. Frame Q-2 as "accept the documented break vs. dual-surface during migration", not as open-ended. |
| **Q-3** | Exclude `artefact` from `to_dict()`? | **RESOLVED → wrong question.** The source has no singular `artefact`; it has `artefacts_written: list[str]` that **is on the wire** (correction 1). Reframe: keep `artefacts_written` in `to_dict()`, derive PRODUCES from it. |
| **Q-4** | Raised exceptions vs. returned failures; is `INTERNAL` the right default | **STAYS BLOCKING (agency-local).** No source equivalent — the source decorator wraps but the raise-vs-return policy isn't specified there. Reasonable to keep raising legal + map to a default `internal` code; specific exception→code mapping is a nice-to-have, not blocking. |
| **Q-5** | Legacy-dict coexistence window | **STAYS BLOCKING (agency-local).** Scope/sequencing decision, no source input. Recommend dual-path during the spec, drop legacy in a follow-up once all 12 verbs migrate — the spec already lists the follow-up verbs. |
| **Q-6** | `gate.check(passed=False)` — `ok` or not-`ok`? | **STAYS BLOCKING, but source confirms the proposal.** Source treats domain outcomes as `ok=True` with the result in `data` (`novel/status.py` dry-run returns `ok=True` with the outcome in `data`; only the *illegal* call returns `ok=False`). So the spec's proposal (failed gate = `ok=True`, failure encoded in `data`, BLOCKED_ON provenance; reserve `GATE_FAILED` for malformed calls) is **source-aligned** — confirm and close. |

---

## Must-fix list for the design pass

1. **Align the envelope to the source schema** (canvas §5 `:156-179`): replace the singular private `artefact: dict` with `artefacts_written: list[str]` *on the wire*; add `archived_to: str | None`; type `data` as `Any` (not `dict`); preserve `next_cursor` for paginating read-verbs. Derive the PRODUCES edge from `artefacts_written`. (Corrections 1, 6; Missing depth.)
2. **Excise the repair-tier premise from Open Q-1 and the "Why".** ADR-0011 governs document-change authority (T1-T4), not runtime error recovery — there is no error→tier mapping in the source (`0011:17-48`, `VOCABULARY.md:269-280`). Drop any `tier` field on `ErrorCode`. (Correction 4.)
3. **Decide `ErrorCode` honestly as an agency *improvement* over the source's free-string `code`** — and keep `trace_id` (wire the `Invocation` id into `TypedError`). State the divergence explicitly; make the enum extensible (open string fallback) so it doesn't reject source-style codes like `illegal_transition`. (Corrections 2; Missing depth `trace_id`.)
4. **Handle `ok=False` with no structured `error`** (warnings-only failure) in `Registry.invoke` — the source does this routinely (`novel/promo.py:14,59,65,69`); the current migration sketch (`:244`) would record it as a non-failure. (Missing depth — warnings semantics.)
5. **Reframe Q-2 with the source steer**: the envelope IS the wire shape (ADR-0005 `:90`); the faithful migration surfaces the full envelope and has callers read `data`. Decide accept-the-break vs. dual-surface-during-migration — not "preserve unwrapping forever." Pin BOTH the success and failure wire shapes in tests, and audit `agency/cli.py` + any `execute()` scripts for the break. (Correction; Open-Q-2.)
6. **Fix `next_suggested_tools` over-claim**: keep it top-level with an empty default; do not block the spec on populating it on failure paths; remove the `jules.stop` "passed via warnings/context" confusion (`:318`). (Correction 3.)
7. **Make the round-trip test lossless-aware**: `from_dict(to_dict()) == r` must account for every wire field (incl. `artefacts_written`, `next_cursor`, `archived_to`) or the Done-When invariant is unverifiable.

---

### Note on citations the spec gets right
Spec line refs are accurate: `agency/capability.py:174-175,177-179` (`Registry.invoke` failure capture + PRODUCES sniff) ✓; `agency/engine.py:69-74` (`_wire` unwrap/re-wrap) ✓; `agency/capabilities/jules.py:79-89` (`dispatch`) and `:124-136` (`stop` stringly-typed `{"error":"unsupported"}`) ✓ (verified against current files). The `research/oo-architecture/{FINDINGS,PROPOSAL}.md` references resolve and match. **The one stale path-class:** the spec cites `vendor/the-agency-system/...` (lines 71-74, 140-143, 401) but no `vendor/` dir exists in the agency repo — those are the clone targets from the "Source clones" block (`~/work/vendor/...`). Make the path convention consistent so Jules doesn't blocked-clarification on a missing `vendor/`.
