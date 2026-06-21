# Naming & Token-Economy Audit — Spec 049

> **Status:** audit deliverable (v1). This document is the **review**, not the
> rename. No code names change in this PR. Implementation lands in a follow-up
> spec (see [§7](#7-implementation-handoff)).
>
> **Method:** `tiktoken` `cl100k_base` over the **live registry**
> (`Engine(":memory:")`), 2026-06-06. Reproduced by
> `tests/test_naming_audit.py` so the figures can't silently drift.

## 1. Executive summary

| Surface | Count | Token cost (names) | Headline finding |
|---|---:|---:|---|
| Code-mode contract (`search`/`get_schema`/`execute`) | 3 | 4 | **KEEP** — the canon wire surface (note: `reflect.search` shadows the contract `search` under a bare-name surface — see §4) |
| Substrate `@mcp.tool`s | 6 | 18 | already short (avg 3 tok); a rename saves only **10 tok** total |
| Capability verbs (wire `capability_<cap>_<verb>`) | 69 | 311 | the `capability_<cap>_` prefix is **202 tok of pure repetition** |
| Skill folders (SKILL.md) | 19 | 59 | consistent kebab — **KEEP** |
| Ontology Lifecycle-skill keys | 21 | 67 | short; **FLAG** folder↔ontology name divergence (§6b) |

**The one finding that matters:** the `capability_<cap>_` prefix repeated across
69 verbs costs **202 tokens of pure prefix** (65% of the 311-token verb-name
corpus). Modelled over a synthetic `- <name>: <brief>` corpus (the name-controllable
slice of the `search` discovery payload — see §2 for why this is a model, not a
capture of the live tool), that is **1471 → 1261 tokens, a 210-token / 14%
reduction** if the prefix is dropped from the code-mode `call_tool` surface.
Everything else in this audit is rounding error by comparison.

**Recommendation in one line:** drop the `capability_<cap>_` prefix from the
**code-mode** `call_tool` surface (keep it on the FastMCP wire for multi-plugin
host disambiguation); alias-and-rename **5** of the 6 substrate tools as a cheap,
low-risk follow-on (KEEP `intent_bootstrap` — see §3); KEEP everything else.

## 2. Methodology

- Names pulled from the live `Registry` (not hardcoded), so the audit reflects
  the **current** 69-verb / 19-skill surface — note this is already larger than
  the spec's drafted "56 verbs / 12 skills" (the surface grew through specs
  042–058).
- Token counts are `cl100k_base` (the encoding GPT-4/Claude-adjacent tokenizers
  approximate; agency already standardises on it via `analyze`/`document`).
- **"Search payload" is a MODEL, not a live capture.** It is a synthetic
  reconstruction — `- <name>: <brief>` per verb — of the name-controllable slice
  of what `search` returns. It is built synthetically *on purpose*: the **delta**
  (prefixed vs bare) is the deliverable, and there is no bare-name registry to
  call `search` against, so the real tool can only give the BEFORE number, never
  the −210 tok delta. The synthetic corpus is the only way to compute the win;
  it is NOT claimed to byte-match the live tool's formatted output (which adds an
  `N of M tools` header etc.). Figures are guarded by `tests/test_naming_audit.py`.

## 3. Substrate tools (`@mcp.tool`)

| Current | tok | Proposed | tok | Δ | Verdict |
|---|---:|---|---:|---:|---|
| `agency_welcome` | 3 | `welcome` | 1 | −2 | ALIAS-AND-RENAME |
| `agency_install` | 2 | `install` | 1 | −1 | ALIAS-AND-RENAME |
| `agency_doctor` | 3 | `doctor` | 1 | −2 | ALIAS-AND-RENAME |
| `intent_bootstrap` | 2 | `intent` | 1 | −1 | **KEEP** (see note) |
| `lifecycle_gate` | 3 | `gate` | 1 | −2 | ALIAS-AND-RENAME |
| `memory_graph_provenance` | 5 | `provenance` | 3 | −2 | ALIAS-AND-RENAME |
| **total** | **18** | | **8** | **−10** | |

**`intent_bootstrap` → `intent` — KEEP (the one disagreement with the user's
prompt).** The user's audit asked "could `intent-bootstrap` be just `intent`?".
It saves 1 token but loses the load-bearing semantic: `intent_bootstrap` says
*mint the first intent of this session*. Bare `intent` reads as "select" or
"describe" an intent — every conversation already has intents. The 1-token
saving is not worth the ambiguity on the **most important onboarding call**.
Recommend keeping the `_bootstrap` suffix; if shortening is desired,
`intent_mint` (2 tok) preserves the verb sense better than bare `intent`.

The other five are unambiguous when shortened (the namespace is implicit — there
is one agency MCP server per host). They are also already 2–5 tokens, so the
total win is **10 tokens** — real but small. ALIAS-AND-RENAME (emit both names
for one minor; deprecate the old) keeps the cost near zero.

**Out of scope (Spec 039 console-scripts):** `agency-mcp`, `agency`,
`agency-doctor` face the **shell**, not the MCP wire — they stay.

## 4. Capability verbs — the prefix tax (the real win)

The MCP wire registers each verb as `capability_<cap>_<verb>`
(e.g. `capability_delegate_dispatch_decision` = 8 tok; `Engine._wire` sets
`impl.__name__ = f"capability_{cap}_{verb}"`). **Correction (PR #23 review):**
code-mode callers currently invoke verbs by this **prefixed** name too — the CLI
examples call `call_tool("capability_plugin_lint_skill", …)`, and there is **no
existing bare alias**. So the prefix is paid at BOTH the discovery and the call
surface today; the win below is the *opportunity*, contingent on the follow-up
spec first designing the bare-name aliasing layer (it is not free, and it is not
already happening).

| Corpus | With prefix | Bare | Δ |
|---|---:|---:|---:|
| Verb names only (69) | 311 tok | 109 tok | **−202 (−65%)** |
| Synthetic name+brief corpus (models the `search` payload — §2) | 1471 tok | 1261 tok | **−210 (−14%)** |

Longest offenders: `capability_develop_record_authoring_outcome` (8),
`capability_jules_approve_awaiting` (8),
`capability_delegate_dispatch_bash_hints` (7).

**Verdict: RENAME (surface split).** Drop `capability_<cap>_` from the
**code-mode `call_tool` dispatch** surface that `search` advertises; **keep** the
fully-qualified name on the raw FastMCP wire (it disambiguates when an MCP host
loads several plugins — Open Question 2). The capability namespace stays in the
Python class hierarchy and in `get_schema` detail; only the discovery/call
shorthand drops it. Backward-compat: emit BOTH for one minor, deprecate the
prefixed form next minor.

**Caveat — bare names must stay unique.** Computed cross-capability verb-name
collisions once the prefix is dropped (the COMPLETE set across all 69 verbs):

| Bare name | Owning capabilities |
|---|---|
| `note` | `dogfood`, `reflect` |
| `render` | `document`, `dogfood` |
| `verify` | `jules`, `research` |

Plus one **contract shadow**: `reflect.search` would collide with the code-mode
contract tool `search` under a bare-name surface. (`help` lives only on `plugin`
and `recall` only on `reflect` — no cross-capability verb collision; an earlier
draft listed them in error.) The follow-up spec MUST resolve each — either (a)
keep the prefix for the colliding minority, or (b) pick a disambiguating bare
form — before exposing bare dispatch. This audit flags the complete set; the
implementation resolves it.

## 5. Per-verb naming consistency

| Pattern | Examples | Verdict |
|---|---|---|
| no-noun verbs | `run`, `note`, `check`, `join`, `finish`, `isolate` | **KEEP** — concise; the capability gives the noun (`analyze.run`) |
| `_decision`/`_bash_hints` suffix | `dispatch_decision`, `dispatch_bash_hints` | **KEEP** — the suffix disambiguates two `dispatch_*` verbs on `delegate` |
| `recall_semantic` vs `semantic_recall` | `reflect.recall_semantic` | **KEEP** — "recall, semantic variant" reads correctly; symmetric with `recall` |
| snake verb vs kebab skill | `dispatch_decision` (verb) / `dispatch-decision` (skill) | **KEEP** — different surfaces, each idiomatic (Python vs marketplace) |
| `record_authoring_outcome` | `develop.record_authoring_outcome` (8 tok, longest) | ALIAS candidate → `record_outcome` (saves 2 tok); low priority |

No systemic verb-name drift found. The one long outlier
(`record_authoring_outcome`) is a soft ALIAS candidate, not a RENAME-HARD.

## 6. Skills — TWO surfaces

There are **two** distinct skill name surfaces (the first draft of this audit
covered only the first — PR #23 review):

### 6a. SKILL.md folders (the marketplace/human surface)

19 folders, all **kebab-case**, 59 tok total (avg 3.1). **KEEP** — uniform.

### 6b. Ontology Lifecycle-skill keys (the walkable surface)

`Engine(":memory:").ontology.skills` carries **21** keys, **67 tok** total — the
templates a `SkillRun` walks (`tdd`, `plan`, `review`, `debug`, `verify`,
`execute`, `brainstorm`, `plugin-dev`, `dispatch-decision`, `code-analysis`,
`jules-*`, …). These are short (avg 3.2 tok) and a **mix of kebab and bare verbs**
(`tdd`, `plan` vs `dispatch-decision`).

**Finding — the two surfaces diverge in name for the same concept:** the ontology
key and its SKILL.md folder are NOT 1:1. Examples: `tdd` ↔ `test-driven-development`,
`plan` ↔ `writing-plans`, `review` ↔ `code-review`, `debug` ↔ `systematic-debugging`,
`brainstorm` ↔ `brainstorming`, `plugin-dev` ↔ `plugin-development`. Only ~7 of 21
ontology keys share their folder name. **Verdict: KEEP both (both short), but FLAG
the divergence** — a reader who knows the SKILL.md name can't guess the ontology
key. The follow-up should decide whether to reconcile (one canonical name per
skill across both surfaces) or document the mapping; this audit surfaces it as the
genuine skill-naming inconsistency (correcting Open Question 3, which the draft
wrongly marked "no split exists").

## 7. Implementation handoff

Per the Spec 015 → 017/018/019 precedent, the renames land in a **separate
implementation spec**, NOT here. **Note:** the draft of this spec called the
follow-up "Spec 050", but **050 already shipped** as `analyze-deps-integration`.
The implementation spec needs a **fresh number** (next free: **066**).

That follow-up (proposed **Spec 066 — naming-rename-implementation**) ships, gated
on a measured **≥ 20% reduction of the verb-name corpus** (this audit shows 65%,
so it clears easily):

1. Drop `capability_<cap>_` from the code-mode `call_tool` surface; keep it on
   the FastMCP wire. Resolve the §4 bare-name collisions.
2. Alias-and-rename the 5 substrate tools (§3); KEEP `intent_bootstrap`.
3. Emit old + new names for one minor; mark old `deprecated=True` in the tool
   description; deprecate next minor.
4. Regen `skills/help/SKILL.md`; update `CLAUDE.md` + `docs/vision/CORE.md`.
5. Prove the win: re-run `tests/test_naming_audit.py`'s payload measurement;
   AFTER < BEFORE by ≥ 20% on the name corpus.

## 8. Per-name verdict roll-up

- **RENAME (surface split):** the `capability_<cap>_` verb prefix → bare in
  code-mode. *(−210 tok / 14% of the discovery payload — the headline.)*
- **ALIAS-AND-RENAME:** `agency_welcome`/`install`/`doctor`, `lifecycle_gate`,
  `memory_graph_provenance`. *(−10 tok; cheap, low-risk.)* Soft: 
  `develop.record_authoring_outcome → record_outcome`.
- **KEEP:** `search`/`get_schema`/`execute` (contract); `intent_bootstrap`
  (semantic); all no-noun verbs; `recall_semantic`; all 19 kebab skill names.
