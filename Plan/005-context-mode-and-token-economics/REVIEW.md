# Spec 005 — Context Mode (output-side) & Token Economics — Panel Review

**Mode:** critique · **Focus:** requirements + architecture + faithfulness to prior art
**Reviewed against real source:** `the-agency-system` Plan/108, 111, 112, 114, 120, 130;
`agency/engine.py`, `agency/capabilities/develop.py`, `agency/Plan/001`; the live
`context-mode` repo (WebFetched 2026-05-27).
**Panel:** Wiegers (requirements), Fowler (interfaces), Nygard (failure modes),
Newman (boundaries/versioning), Adzic (examples/measurability), Hohpe (process I/O).

---

## Verdict

**Conditionally approved — strong spec, three load-bearing factual corrections required before code.**

This is a genuinely good spec: it correctly identifies three real token leaks (all
verified against the tree), it correctly separates the schema-side win (already
banked at `engine.py:91-95`) from the output-side problem, and it is admirably
honest that its token numbers are placeholders. The triad-as-capability framing is
faithful to the engine's self-registration contract. It is markedly tighter than its
exemplar in one respect: it *fuses* the SessionDB with an in-engine triad rather than
leaving them as two disconnected canons.

But it contains **one wrong path that violates its own stated rule**, it **misreads
the real context-mode hook lifecycle** (and Plan/108 partly misread it too), and it
**inherits a field-name mismatch with its hard dependency (Spec 001)** that will break
the very tests it specifies. None are fatal; all are pre-code blockers. The vendor
decision (Open Q-1) leans the right way and should be locked to **(a) reimplement**.

**Quality scorecard (0-10):** clarity 8.5 · completeness 7.5 · testability 8.0 ·
faithfulness-to-prior-art 6.5 · path/source correctness 6.0.

---

## Source-grounded corrections (cite path:line)

### C-1 — `plugin.json` path is wrong and contradicts the spec's own rule (MUST FIX)
The spec's `affects:` line 24 and Files→Modify both name
`agency/.claude-plugin/plugin.json`. **That file does not exist.** The real plugin
manifest is at the **repo root**: `/home/user/agency/.claude-plugin/plugin.json`
(verified; `name:"agency"`, exposes `skills:"./skills/"`, `commands:"./commands/"`).
This is doubly damning because the spec's own Files preamble (lines 260-262) declares
*"This repo is `agency/`. All paths below use `agency/`."* — and then immediately
mis-prefixes the one path that is **not** under the package. The package is `agency/`;
the **plugin metadata, `skills/`, and `commands/` are at the root.** So:
- `skills/ctx-insight/SKILL.md` and `commands/ctx-insight.md` (lines 18-19, 273-274) are
  **correct as root-relative** (the existing `skills/` and `commands/` live at root —
  verified: `skills/brainstorming`, `commands/help.md`).
- `.claude-plugin/plugin.json` must be **root-relative, not `agency/`-prefixed.**
- `agency/hooks/…` and `agency/context/…` are correctly under the package (Python import
  targets), but see C-2 on whether hooks belong in the importable package at all.
**Fix:** correct line 24 and the Files→Modify entry to `.claude-plugin/plugin.json`
(root), and add a one-line note that `skills/`/`commands/`/`.claude-plugin/` are
root-level while `agency/` is the Python package — the "all paths use `agency/`" blanket
rule is false for exactly these three.

### C-2 — the hook lifecycle is misread vs. the real `context-mode` (MUST FIX)
The spec's hook map (lines 196-202) assigns: `SessionStart` → "open/attach SessionDB;
rebuild the static manifest if stale", `PreCompact` → "flush in-flight summaries",
`UserPromptSubmit` → "(optional) seed a recall hint". **The live context-mode repo
(WebFetched 2026-05-27) defines these roles differently:**
- `SessionStart` — **restores state after compaction or resume** (not manifest rebuild).
- `PreCompact` — **builds the snapshot before compaction** (the checkpoint, not a flush).
- `UserPromptSubmit` — **captures user decisions and corrections** (an *input* capture,
  the decision-extraction seam — exactly Plan/120's `decisions.extract` regime).
- `PreToolUse` — **enforces sandbox routing before execution** (not the no-op the spec
  proposes at line 198).
- `PostToolUse` — captures events after each tool call (this one the spec gets right).

So the spec has the *count* (5) and *names* right but the *semantics* of three of them
wrong. The snapshot/restore pair (`PreCompact`→`SessionStart`) is the **smart-compaction
checkpoint pattern** that `the-agency-system` Plan/120 (`120-smart-compaction-checkpoints/spec.md:36-57`)
implements as a whole 2-session spec (`snapshot`/`pick_richest`/`compose_digest`,
`~/.cache/.../checkpoints/`). The spec currently waves at it as "flush in-flight
summaries" — that is not what the hooks do and will produce a hook layer that silently
loses decision continuity across a compaction.
**Fix:** either (a) re-scope `PreCompact`/`SessionStart` to honest snapshot→restore
(adopting Plan/120's richness-restore), or (b) explicitly declare snapshot/restore
*out of scope* and reduce this spec to `PostToolUse`-routing + `SessionStart`-attach
only, deferring the checkpoint pair to a follow-up (cleaner; recommended). Do not ship
a `PreCompact` handler that claims to preserve detail but only flushes.

### C-3 — envelope field name collides with Spec 001 (`result` vs `data`) (MUST FIX)
The spec repeatedly describes the envelope as **"`ok` + `result` + optional `error` +
`next_suggested_tools`"** (lines 83, 101-103, 158) and the triad sketches return
`ToolResult(result={matches:…})` (lines 177-182). But Spec 001 — its sole `depends_on`
— defines the field as **`data`**, not `result`:
`agency/Plan/001-toolresult-and-typed-errors/spec.md:90-93,184-192` (`ToolResult.data`),
and `to_dict()` emits `{"ok","data","warnings","next_suggested_tools","error"}`
(`001 spec:209-216`). The-agency-system's own envelope decision uses
`{ok, data, warnings, artefacts_written, next_suggested_tools}`
(`130-shared-toolresult-envelope/spec.md:34,38`). **`result` is the *legacy* unwrapped
key** that `_wire` strips today (`engine.py:73`) and that develop.py still emits
(`develop.py:124,145`: `{"result": {...}}`). Spec 005 is conflating the legacy wrapper
with the new envelope. As written, `tests/test_context_capability.py` (a Done-When item)
would assert on `result.result` against a `ToolResult` whose attribute is `.data`.
**Fix:** replace every `result=` / "`result`" in the triad with `data=` / "`data`",
and state the envelope shape verbatim as Spec 001 defines it
(`ok/data/warnings/next_suggested_tools/error`). Add `artefacts_written` if 001 lands it
(001 Open Q-3 still parks `artefact` exclusion — track that dependency).

### C-4 — Spec 001 Open Q-2 is an unacknowledged hard blocker (MUST FIX)
Spec 005 assumes `invoke`/`describe`/`search` return through the envelope and that
`next_suggested_tools` rides on it. But **whether the envelope even surfaces at the
`execute()` boundary is still an open question in 001** —
`001 spec:359-366 (Open Q-2)`: *"This is the single load-bearing decision — it
determines whether 001 is additive or breaking."* If 001 resolves to keep returning
unwrapped `data` for back-compat (a live option), then `next_suggested_tools` never
reaches the model through `_wire` and **the entire glue mechanism of Spec 005 collapses.**
The agency Plan/000-overview.md:65 explicitly lists this as cross-cutting "Decide first"
question #1, gating 002/005/007.
**Fix:** add an Open Question (or a hard `depends_on` precondition) stating: *"Spec 005's
`next_suggested_tools` glue requires 001 Open Q-2 to resolve in favour of surfacing the
envelope (or a `next` field) at `_wire`. If 001 keeps the unwrapped-`data` contract, 005
must define its own surfacing path."* Right now the spec silently bets on one resolution.

### C-5 — "26 event categories" is not in this spec, and is wrong upstream anyway (NOTE)
The task framing references Plan/108's "26 event categories." Plan/108 indeed claims 26
(`108 spec:45,48-49`), but the **live context-mode repo states 23** ("23 event categories"
in the session-continuity table; `/ctx-insight` reports "90 metrics, 37 insight patterns,
4 composite scores across 23 event categories"). Spec 005 carries **zero** event
categories — which is arguably *correct* for its scope (it bridges *outputs*, not the
SessionLog event taxonomy that Plan/108's `event_map.py` needed because it had a Spec 100
SessionLog to map *into*). Agency has no Spec 100 equivalent, so there is nothing to map
to. This is a legitimate scope reduction, **but the spec should say so explicitly** rather
than leave a reader wondering where the 26/23 categories went. See "Missing depth" below.

### C-6 — triad verb naming diverges from the established prior-art triad (NOTE)
Plan/112 (`112-context-anchor-triad/spec.md:31,39-41`) names the document triad
`context_search` / `context_describe` / `context_read`, mirroring Plan/104's tool triad
`agency_tool_search/_describe/_invoke`. Spec 005 uses `search` / `describe` / **`invoke`**.
`invoke` is defensible (it auto-wires to `capability_context_invoke`, and "invoke" matches
the tool-side triad's third verb), but `read` is the term the document-side prior art
settled on, and "invoke" reads like *executing* something rather than *fetching a body*.
Minor, but call it out so the divergence is intentional, not accidental.

---

## Missing depth (event categories, hook lifecycle, the snapshot pair)

1. **No snapshot/restore depth (the biggest gap).** The real context-mode's headline
   feature is *session continuity* across compaction (PreCompact snapshot → SessionStart
   restore), which Plan/120 spends a whole spec on (richness-weighted `pick_richest`,
   decision regex, 8 KB checkpoint cap, `compose_digest`). Spec 005 reduces this to one
   bullet ("flush any in-flight summaries"). Either adopt the depth or cut the pair — but
   the current half-measure is the spec's weakest seam (see C-2).

2. **Event taxonomy is absent and unexplained.** Plan/108's value was the 26-category
   `event_map.py` *because* it bridged into Spec 100's SessionLog. Spec 005 has no
   SessionLog to bridge into, so it legitimately drops the taxonomy — but it should add a
   one-paragraph "Why no event categories" note (the corpus here is `{doc, discipline-howto,
   tool-output}` `kind`s, line 185, not a 23/26-category event stream). Without that note a
   reviewer who knows Plan/108 will read the omission as a miss rather than a decision.

3. **Hook I/O contract under-specified for the multi-writer reality.** The spec asserts
   WAL + `busy_timeout` (lines 109, 218) and "survives concurrent writers" but never pins
   the **hook-subprocess-vs-MCP-server process boundary** the way it should. Plan/108
   referenced a `0001-sessiondb-multi-writer` ADR; Spec 005 cites it (line 219) but does
   not reproduce the contract (who creates the DB, what happens on first-write race,
   schema-migration ordering when both processes open a fresh DB). Hohpe: *"what's the
   write-ordering guarantee when two processes hit an uninitialised FTS5 table
   simultaneously?"* — needs an answer in `## Design`.

4. **`/ctx-insight` surface is mis-described.** The live repo says `/ctx-insight`
   **"Opens a local web UI"** (HTTP). Spec 005 Open Q-4 *recommends* file-direct/no-port
   (lines 307-311) — a reasonable simplification, but it should state plainly that this
   **diverges from upstream's HTTP surface** and therefore the `skills/ctx-insight` surface
   is *our own* reader over the SQLite file, not a bridge to context-mode's web UI. As
   written, a reader could think they're the same thing.

5. **Failure-mode coverage is good but asymmetric (Nygard).** The `PostToolUse` no-op-on-
   failure contract (lines 124-128, 206-208) is excellent and correctly load-bearing
   ("a hook must never break the session"). But there is no symmetric statement for the
   *engine-side* triad: what does `capability_context_invoke(id)` return when the
   SessionDB is locked/corrupt mid-session (vs. merely absent)? The graceful-degradation
   test (line 142) covers *absent* but not *locked*. Add a locked/corrupt case.

6. **Threshold provenance.** The 2 KB PostToolUse threshold (lines 119, 199) is asserted
   without a source. Plan/114 cites token-optimizer's published thresholds (50 KB / 2000
   lines / 1000-token-minimum) for its read-cache; Plan/108 used context-mode's ">2 KB"
   Think-in-Code rule (`108 spec:47`). 2 KB is plausibly right (it matches context-mode's
   own ">2 KB → prefer ctx_execute"), but cite it rather than asserting it.

---

## Open-Questions triage

| # | Question | Triage | Panel note |
|---|---|---|---|
| 1 | Vendor vs depend | **LOCK to (a) reimplement** | Correct lean. The triad MUST read the same in-process corpus to back `invoke` without a network hop (the spec's own argument, line 295). ELv2 confirmed on the live repo — reimplementing the *pattern* in stdlib is the only clean path; an ELv2 *runtime dep* drags a copyleft-adjacent obligation into an opt-in plugin. Decide now; it gates the file layout. |
| 2 | License (ELv2) | **Resolved by #1** | Confirmed ELv2 via WebFetch. Once #1 = reimplement, this is a no-op: copy no source, claim no API. Keep the one-line note. |
| 3 | The name collision | **Real; resolve before merge** | `context-mode` already means schema-side disclosure in `docs/guide/usage.md:36,61`, `concepts.md:74`, `CORE.md:11-13` (all verified). Recommend the explicit **"schema-side / output-side" qualifier** umbrella over a rename, *but* the new capability is `name="context"` (line 89) — confirm that doesn't shadow the existing doc term in `search` results. Lower risk than a rename that breaks `develop.reference` muscle memory. |
| 4 | Local HTTP port | **Accept file-direct, note the divergence** | File-direct is simpler and removes egress (good). But it **diverges from upstream's HTTP `/ctx-insight`** (C-4 / Missing-depth #4) — say so. No Claude-Code hook constraint requires HTTP; hooks are stdin/stdout. Safe. |
| 5 | Real token numbers | **Hard gate — already correctly a Done-When** | The spec is exemplary here (lines 132-136, 256-257, Open Q-5): it asserts the *method*, parks the percentage. Keep it. Do not let "97%/98%" leak into prose. The honest before/after reasoning (lines 233-257) is fine *as labelled estimates.* |
| 6 | PreToolUse read-cache (deferred) | **Correctly deferred — keep deferred** | This is literally Plan/114 (`114-read-cache-delta-mode`), a standalone 2-session spec with `difflib` thresholds. Splitting it out is the right call. Cite Plan/114 by name in the deferral. |
| 7 | Manifest staleness | **Resolve to mtime-gated at SessionStart** | The proposed answer (line 321) is correct and matches Plan/111's `--check` sha256/mtime drift guard (`111 spec:53,87`). Pin it. But note C-2: if `SessionStart` is re-scoped to *restore*, the manifest-rebuild needs its own trigger (or move to first-`search` lazy build). |

**Missing Open Question to add:** the 001 Open-Q-2 dependency (C-4) — surfacing the
envelope at `_wire`. This is the spec's true critical-path blocker and is currently
implicit.

---

## Must-fix list (pre-code, ordered by blast radius)

1. **C-3 + C-4 — envelope field name (`data`, not `result`) and the 001 Open-Q-2
   dependency.** Without this the triad sketches, the Done-When acceptance, and the two
   test files are written against a contract that doesn't exist. Align verbatim to Spec
   001's `ToolResult` (`001:184-216`) and add the explicit 001-Q2 precondition. *Highest
   blast radius: every verb signature + every test.*
2. **C-1 — fix the `.claude-plugin/plugin.json` path** to root-relative and add the
   "root vs `agency/` package" note. *A Jules session will fail `affects:`-allow-list
   validation on a path that doesn't exist.*
3. **C-2 — correct the hook lifecycle** (`PreToolUse`/`PreCompact`/`SessionStart`/
   `UserPromptSubmit` semantics) to match the live repo, and either adopt Plan/120's
   snapshot/restore depth or explicitly defer the `PreCompact`/`SessionStart` pair.
   *A hook that mis-implements PreCompact silently loses continuity — the opposite of the
   spec's goal.*
4. **Lock Open Q-1 to (a) reimplement** (and thereby resolve Q-2/Q-4) before code; it
   determines the entire `agency/context/` file layout. *Vendor-vs-depend is a fork in the
   road, not a footnote.*
5. **Add the "why no event taxonomy" + "multi-writer write-ordering" + "locked-DB
   degradation" notes** (Missing-depth 2/3/5) and **cite the 2 KB threshold** (Missing-
   depth 6).
6. **C-6 (minor) — acknowledge the `invoke` vs `read` verb divergence** from Plan/112 as
   intentional.

---

## Vendor-vs-depend recommendation (the headline decision)

**Reimplement the pattern in-tree (Open Q-1 option (a)). Do not depend on the marketplace
plugin.** Three converging reasons:

1. **Architectural necessity (the spec's own argument).** The whole point of Spec 005 is
   that the `ContextCapability` triad and the `PostToolUse` router read the **same**
   SessionDB so `context_invoke(id)` can return a body stored by the hook. A bridge-only
   dependency (Plan/108's choice, `108 spec:39,51`) cannot back `invoke` without a network
   hop into context-mode's HTTP `/ctx-insight` — which defeats the in-process, in-flow
   design and re-introduces the egress question Open Q-4 wants to delete.
2. **License.** The live repo is **ELv2** (confirmed via WebFetch; `108 spec:143` agrees).
   Reimplementing the *pattern* in stdlib `sqlite3` is clean; taking an ELv2 *runtime
   dependency* into an opt-in Claude-Code plugin pulls a non-OSI, field-of-use-restricted
   obligation into the distribution. The pattern (SQLite + FTS5 + BM25 + 5 hooks) is
   well-known prior art (Plan/111-114, token-optimizer); no source need be copied.
3. **Cost is genuinely low.** It is pure-stdlib `sqlite3` (no new dependency — the spec
   says so, line 219), and the engine already owns the injector seam (`engine.py:55-56`)
   to hand the `Index` to the capability exactly like `jules_client`/`vcs_backend`. The
   reimplementation is *smaller* than the bridge would be, because there's no HTTP client,
   no retry/timeout layer, and no two-canon reconciliation.

**Caveat:** keep the marketplace `context-mode` plugin as a *documented, opt-in companion*
(the spec already does this, lines 284-285) — a user who installs both gets context-mode's
richer `/ctx-insight` web UI alongside our in-engine triad. Just do not make it a hard
dependency, and make the SessionDB schemas independent so the two never fight over one DB
file (name our DB distinctly under `$CLAUDE_PLUGIN_DATA`/`~/.agency/`, line 222).

---

## What the spec gets right (so it survives the rewrite)

- Correctly banks the schema-side win and refuses to re-count it (lines 42-52, 234-235).
- The three leaks are all real and verified: bare-dict no-`next` (`engine.py:73-74`),
  hardcoded 3-string doc loader (`develop.py:86-111,139-145`), no output seam (no
  `agency/hooks` or `agency/context` — confirmed by `ls`).
- The triad-as-self-registering-capability framing is faithful to the engine
  (`engine.py:48-52,61-89`) and rides the real injector seam (`:55-56`).
- The narrow→narrow→pay funnel (search→describe→invoke; bodies only on `invoke`, one id)
  is the correct mirror of the FastMCP code-mode loop and of Plan/112's view ladder.
- The token-economics honesty (method-not-percentage) is best-in-class for this corpus.
- The `PostToolUse` never-break-the-session contract is exactly right.
