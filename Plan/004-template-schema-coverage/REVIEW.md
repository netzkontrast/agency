# REVIEW — Spec 004 Template & Schema Coverage

Spec-panel review of `Plan/004-template-schema-coverage/spec.md`, grounded in the
live `agency/` tree (every claim re-verified against source at `path:line`) and
the prior-art repo `the-agency-system/`.

Panel lenses applied: **Wiegers** (testability / verifiability of each requirement),
**Adzic** (specification by example — does the round-trip test actually bite?),
**Nygard** (operational drift / loud-fail discipline), **plus a source-of-truth
audit** to resolve the count discrepancy the spec parks as blocking.

---

## Verdict

**APPROVE the spec's substantive ruling; REQUEST CHANGES on its self-presentation.**

The spec's own audit is **correct**: the research's "18 / 5 / 13" is a namespace
conflation, and the true count of **uncovered recorded artefact kinds is 2**
(`jules-session`, `reduction`). The spec already reaches the right recommendation
(Open Q1 option **(a)**: cover the 2 real kinds; defer slots→artefacts to a
follow-up). That is the correct scope and matches the prior art.

But the spec is **not yet implementable as written**, because it leaves the count
it has already resolved sitting in a BLOCKING Open Question, and it ships a 13-key
`REQUIRED.update` superset in the Design body that — if a Jules session copies it
verbatim — installs 11 dead schemas the spec's own WARNING says not to add. The
fix is editorial-but-load-bearing: promote the verified answer into the spec body,
delete the superset from the canonical Design, and make the round-trip test the
sole arbiter. Details below.

---

## The VERIFIED true count of uncovered kinds

I independently grepped the entire `agency/` package (not just `capabilities/`)
for every site that actually writes an `Artefact` node. There are exactly **two**
ways an Artefact reaches the graph:

1. A verb returns `{"artefact": {...}}`, which the engine records at
   **`agency/capability.py:178`** — `art = memory.record("Artefact", dict(result["artefact"]))`.
2. A verb calls `self.ctx.record("Artefact", {...})` directly.

Grepping both forms across the whole tree:

```
$ grep -rn 'record("Artefact"' agency/ examples/
agency/capability.py:178   ← the engine's single record-from-result site
agency/capabilities/delegate.py:78   ← kind "reduction"
```

…plus the five `{"artefact": {"kind": ...}}` returns in `plugin.py` and the one in
`jules.py`. The complete, deduplicated set of artefact `kind` literals that are
**actually recorded as Artefact nodes**:

| kind | recorded at (`path:line`) | schema in `REQUIRED`? |
|---|---|---|
| `plugin-manifest` | `agency/capabilities/plugin.py:43` | YES (`templates.py:73`) |
| `skill-md` | `agency/capabilities/plugin.py:53` | YES (`templates.py:74`) |
| `command-md` | `agency/capabilities/plugin.py:59` | YES (`templates.py:75`) |
| `marketplace-entry` | `agency/capabilities/plugin.py:65` | YES (`templates.py:76`) |
| `step-doc` | `agency/capabilities/plugin.py:74` | YES (`templates.py:77`) |
| `jules-session` | `agency/capabilities/jules.py:88` | **NO** |
| `reduction` | `agency/capabilities/delegate.py:78` | **NO** |

**Uncovered recorded artefact kinds = 2: `jules-session`, `reduction`.** The spec's
headline number is confirmed exactly.

### Why "18 / 13 / 8" are all wrong (each traced to source)

- **The "18" and "13 remaining"** come from
  `research/templates-and-schemas/FINDINGS.md:6-29`, whose gap matrix lists 18
  rows. I verified the cited `path:line` for each "uncovered" row — **11 of them
  are not Artefact records at all**:
  - `authoring` → `plugin.py:136` / `:155` is a **skill `kind`**
    (`SKILL_CREATION_SKILL["kind"]`, `PLUGIN_DEV_SKILL["kind"]`), confirmed at
    `agency/capabilities/plugin.py:136,155`. Never a `record("Artefact", ...)`.
  - `discipline` → `develop.py:29,34,40,46,52,57,65,74` are **skill `kind`s**
    (`"kind": "discipline"` on the eight discipline skills). Never recorded.
  - `baseline`, `rationalizations`, `lint`, `skill_md`, `command_md`, `manifest`,
    `entry`, `rationalization_table`, `red_flags`, `user_confirmed`, `findings`
    → these are **`produces:` phase-slot names**, verified at
    `agency/capabilities/plugin.py:139,140,143,147,148,157,160,163,166,169` and
    `develop.py:67`. They are snake_case slot strings the skill walker validates
    per phase, **not** artefact `kind`s. Nothing calls `record("Artefact", {"kind":
    "findings"})` anywhere — confirmed:
    `grep -rn '"findings"|"baseline"|"manifest"|"lint"|"entry"' agency/capabilities/*.py | grep -i 'record|artefact'`
    returns **no rows**.
- **The FINDINGS matrix even mis-cites the *covered* kinds**: it lists `skill-md`
  at `plugin.py:140` (a `produces:["skill_md"]` slot) and `command-md` at
  `plugin.py:163` (the plugin-dev `command` phase), when the real records are at
  `plugin.py:53` and `:59`. It cites `jules-session` at `jules.py:56` when the real
  record is `jules.py:88`. The research read slot names and skill kinds as if they
  were artefact records — this is the root error, and the spec is right to flag it.
- **The "13"** is `research/templates-and-schemas/schemas-catalogue.md:10-24`'s
  `REQUIRED.update` — the 18-row matrix minus the 5 already covered = 13 keys, i.e.
  the same conflation carried into a code block.
- **The "8"** is the subset the research's own `spec.md` prose/`Files` actually
  names as templates — an internal inconsistency *within the research*, not a third
  reading of the code.

So: **(A)** the namespaces are real and distinct — artefact `kind`s (kebab, 7
total) vs `produces:` slots (snake, ~11) vs skill `kind`s (`authoring`,
`discipline`); **(B)** only artefact `kind`s are validatable by
`Memory.validate_schema` (`agency/memory.py:144`), because only they become
`Artefact` nodes; **(C)** of the 7 recorded kinds, 2 lack schemas. The spec's audit
(its "Verified counts" section) is sound. Its one numeric slip: it says "9 distinct
`kind` literals" by counting the two skill `kind`s (`authoring`, `discipline`) in
the same table — those are not Artefact kinds, so the *recorded-Artefact* set is
**7**, of which 2 are uncovered. Recommend the spec state "7 recorded artefact
kinds, 2 uncovered" to avoid re-seeding the very confusion it diagnoses.

---

## Source-grounded corrections (spec claims vs live code)

1. **`children` is an int count, not a list — confirmed, and it matters.**
   `agency/capabilities/delegate.py:76` sets `children = len(rows)`; line 78 records
   `{"kind": "reduction", "children": children}`. The spec's AFTER snippet keeps the
   field name `children` but reuses the same identifier as a *count* inside the
   `summary` f-string while assigning a *joined id list* to `children` — but the
   surrounding code defines no `child_ids` or `states` variable in `join` (those
   live in `fan_out`). The AFTER block at spec lines 217-224 references
   `child_ids` and `states` that **do not exist in `join`'s scope**. Must-fix: the
   verb rewrite must derive its own ids/states from the `rows` query at
   `delegate.py:69-75`, not borrow `fan_out`'s locals.

2. **`jules` has no `ontology` attribute — confirmed.** `grep -n ontology
   agency/capabilities/jules.py` returns nothing; `JulesCapability` (`jules.py:72`)
   inherits the empty default `OntologyExtension` from `CapabilityBase`
   (`agency/capability.py:29`, `ontology: OntologyExtension = field(default_factory=
   OntologyExtension)`). The spec's parenthetical is accurate.

3. **`delegate` already HAS an `ontology` — but with NO `schemas`.**
   `agency/capabilities/delegate.py:23-26` defines
   `ontology = OntologyExtension(nodes={"Delegation": [...]}, edges={"DELEGATES_TO",
   "REDUCES_INTO"})`. So Open Q2's "move `reduction` into delegate's
   `OntologyExtension.schemas`" is a one-line `schemas={...}` addition to an
   *existing* extension, not a new attribute. Good news the spec under-states: the
   `REDUCES_INTO` edge is already registered (`delegate.py:25`), so the verb change
   needs no edge work and won't trip `Ontology.extend`'s edge check.

4. **The `baseline` collision is real but mis-stated (Open Q6).** `workspace.py:21`
   declares the `Baseline` **node** schema as `["command", "passed"]` — *not*
   `["command","passed","output"]` as the spec's Open Q6 says. `output` is recorded
   (`workspace.py:46`) but is **not** a required field. Minor, but since the spec is
   the document that adjudicates the collision, get the required-field list right:
   `Baseline` node = `["command","passed"]`. (The point stands: it is a *node*
   schema in `Ontology.nodes`, keyed separately from `Ontology.schemas`, so no hard
   clash — and `baseline` should not be added to `REQUIRED` at all under option (a).)

5. **The generate/validate loop is NOT auto-wired today — verify before claiming
   "schemas flow in automatically."** The spec (lines 246-254) says new `REQUIRED`
   keys "flow in automatically" via `schemas=dict(templates.REQUIRED)`
   (`plugin.py:179`) into `Ontology.schemas`. That populates `Ontology.schemas`,
   yes — but `Memory.validate_schema` (`agency/memory.py:144-153`) takes a
   `schema_id` (a **node id**), and nothing in the live tree creates a `Schema`
   *node* from `Ontology.schemas`, nor links an Artefact `VALIDATES_AGAINST` it.
   `grep -rn 'validate_schema|VALIDATES_AGAINST' agency/` shows the only call sites
   are the definition (`memory.py:144`) and a docstring (`templates.py:6`); **no
   production code records a `Schema` node or invokes `validate_schema`.** So adding
   a `REQUIRED` entry alone does **not** make a kind validatable — the loop's
   validate side has no driver. The spec's "Done When" round-trip test
   (lines 127-129) silently assumes a `Schema` node exists to pass `schema_id` to.
   **Must-fix:** the spec must say *how* a `Schema` node gets created from each
   `REQUIRED` entry (e.g. an engine bootstrap that records one `Schema` node per
   `Ontology.schemas` entry and the recording verbs link `VALIDATES_AGAINST`), or
   the test will have nothing to validate against. This is the single biggest gap:
   the spec extends a registry that is not yet wired to the enforcement point.

6. **`_jules_api.py:226` `"kind": kind` is a red herring — correctly excluded.**
   That is an *activity-summary* trimming field (`_activity_summary`,
   `agency/capabilities/_jules_api.py:215-228`), not an Artefact record. The spec
   does not list it; correct.

---

## Open-Questions triage

- **Q1 (count / scope) — RESOLVE NOW, do not leave blocking.** The verified answer
  is **2 uncovered recorded artefact kinds**; scope is option **(a)**. The spec
  already recommends (a); the only defect is leaving it as an unanswered BLOCKING
  gate. The audit *is* the maintainer ruling. **Move the answer into the spec body,
  mark Q1 RESOLVED.** Prior art backs (a): `the-agency-system`
  `Plan/131-manifest-coverage-lint/spec.md` ("Out of scope: auto-defaulting
  placeholder entries would mask the human decision") — adding schemas for kinds no
  code emits is exactly the "mask the decision" anti-pattern. Option (c) is dead
  schemas; reject. Option (b) (slots→artefacts) is a legitimate but **separate**
  feature requiring verb rewrites in `develop.py`/`plugin.py` — split to a follow-up
  spec (005).

- **Q2 (ownership) — RESOLVE: capability-owned.** `reduction` → add
  `schemas={"reduction": [...]}` to the existing `delegate.py:23` extension;
  `jules-session` → add `ontology = OntologyExtension(schemas={"jules-session":
  [...]})` to `JulesCapability`. This honours "schemata live with the capability
  that owns them" (`agency/ontology.py:60-86`) and keeps `templates.REQUIRED`
  plugin-owned. **Consequence:** drop `jules-session`/`reduction` out of the
  `REQUIRED.update` block entirely — they should never be in `templates.REQUIRED`
  if ownership is capability-local. The spec's Design block currently puts them in
  `REQUIRED.update`, contradicting its own Q2 recommendation. Reconcile.

- **Q3 (field names) — RESOLVE: catalogue names win, but verify the test surface.**
  `jules.dispatch` renames `session`→`session_id` and adds `state`/`history`;
  `delegate.join` adds `parent_intent`/`summary` and re-types `children`. Both
  change the verbs' **public result dict**, so any test asserting on
  `result["session"]` or the reduction shape in `tests/test_agency.py` breaks. The
  spec must enumerate which existing assertions move (it does not). Per
  Adzic/Wiegers, list them or the "all existing tests pass" Done-When is untestable.

- **Q4 (snake vs kebab) — RESOLVE: intentional namespace split; no normalisation in
  004.** `produces:` slots are phase-output names; artefact `kind`s are kebab. They
  are different namespaces (confirmed: slots never become Artefact nodes). Under
  option (a) there is **nothing to normalise** in 004 — defer the slot→kind mapping
  to the option-(b) follow-up. Mark Q4 deferred, not blocking.

- **Q5 (test location) — RESOLVE: extend `tests/test_agency.py`.** Repo convention
  is one test file; `affects:` already lists it. Cosmetic; pick the existing file.

- **Q6 (`baseline` collision) — MOOT under option (a).** `baseline` is a `produces:`
  slot, never recorded as an Artefact, so it is **not** in scope and must not enter
  `REQUIRED`. The collision only arises if someone copies the superset. Removing the
  superset (Must-fix 2) dissolves Q6 entirely. (Correct the `Baseline` node fields
  to `["command","passed"]` per Correction 4 regardless.)

---

## Must-fix list (blocking implementation)

1. **De-block Q1: write the verified answer into the spec body.** State plainly:
   "7 recorded artefact kinds; 2 uncovered (`jules-session`, `reduction`); scope =
   cover those 2." Remove the "Do NOT start coding until Q1 answered" banner — the
   audit *is* the answer. Re-label the table to say "recorded artefact kinds" (7),
   not "9 distinct `kind` literals," so it stops counting skill `kind`s.

2. **Delete the 13-key `REQUIRED.update` superset from the canonical Design.**
   Replace with the **2-key**, capability-owned form to match Q2:
   ```python
   # delegate.py — add to the EXISTING OntologyExtension(delegate.py:23)
   schemas={"reduction": ["parent_intent", "children", "summary"]}
   # jules.py — JulesCapability gains:
   ontology = OntologyExtension(schemas={"jules-session":
       ["session_id", "url", "state", "history"]})
   ```
   Leaving the 13-key block in the body (even "for the maintainer to strike rows")
   is the exact footgun a fan-out Jules session will paste verbatim → 11 dead
   schemas + the `baseline` collision. Prior art (`131-manifest-coverage-lint`)
   forbids schemas for unemitted kinds.

3. **Specify how a `Schema` node is created so `validate_schema` has a target**
   (Correction 5). Today `Ontology.schemas` is populated but **no `Schema` node is
   ever recorded and `validate_schema` is never called in production**
   (`agency/memory.py:144`, `agency/capabilities/plugin.py:179`). The round-trip
   test (Done-When lines 127-129) cannot pass without a `Schema` node id. The spec
   must add a step that records one `Schema` node per agreed kind (and ideally a
   `VALIDATES_AGAINST` edge from the Artefact) — otherwise it covers the *generate*
   side and the *registry* side but leaves the *validate* side unwired.

4. **Fix the `delegate.join` AFTER snippet** (Correction 1): it references
   `child_ids`/`states` that exist only in `fan_out`, not `join`. Derive them from
   `join`'s own `rows` query (`delegate.py:69-75`).

5. **Enumerate the test assertions that move under Q3** so "all existing tests pass"
   is verifiable — list the `tests/test_agency.py` jules/delegate assertions that
   change when `session`→`session_id` and the reduction shape grows.

## Nice-to-have

- Adopt the **coverage-lint pattern** from `the-agency-system`
  `Plan/131-manifest-coverage-lint/spec.md` as a follow-up: a parity check
  `recorded_kinds − schema'd_kinds` that fails CI on either-direction drift. This
  turns "every recorded kind has a schema" from a one-time spec into a standing
  invariant — and would have caught this gap mechanically. Cite it as the
  acceptance model for the option-(b) follow-up.
- Correct the `Baseline` node required-field list to `["command","passed"]`
  wherever the spec cites it (Open Q6 / Evidence).

---

## Evidence (re-verified, this review)

- `agency/capability.py:178` — `memory.record("Artefact", dict(result["artefact"]))`:
  the engine's single record-from-verb-result site.
- `agency/capabilities/delegate.py:78` — `record("Artefact", {"kind":"reduction",
  "children": children})`; `children` = `len(rows)` (`delegate.py:76`), an int.
- `agency/capabilities/delegate.py:23-26` — delegate's existing `OntologyExtension`
  (nodes + `REDUCES_INTO` edge, **no schemas**).
- `agency/capabilities/jules.py:88` — `{"kind":"jules-session","session": sid,
  "url": ...}`; `jules.py:72` `JulesCapability` defines no `ontology`.
- `agency/capability.py:29` — default `ontology = OntologyExtension()` (empty).
- `agency/capabilities/plugin.py:43,53,59,65,74` — the 5 covered artefact records.
- `agency/capabilities/plugin.py:136,155` — `"kind":"authoring"` skill kinds.
- `agency/capabilities/plugin.py:139-169` — the snake_case `produces:` slots.
- `agency/capabilities/develop.py:29-74` — `"kind":"discipline"` skill kinds;
  `develop.py:67` — `produces:["findings"]` slot.
- `agency/capabilities/workspace.py:20-21` — `Baseline` node = `["command","passed"]`
  (output recorded at `:46` but not required).
- `agency/templates.py:72-78` — `REQUIRED` = exactly 5 kinds.
- `agency/ontology.py:60-126` — `OntologyExtension` contract + `Ontology.extend`
  (schemas merged, unique-name guard); `agency/ontology.py:97` `self.schemas={}`.
- `agency/memory.py:144-153` — `validate_schema(node_id, schema_id)`; **no
  production caller, no `Schema`-node creation** anywhere in `agency/`.
- `research/templates-and-schemas/FINDINGS.md:6-29` — the 18-row matrix conflating
  slots/skill-kinds with artefact kinds (root of "18/13"); mis-cited covered rows.
- `research/templates-and-schemas/schemas-catalogue.md:10-24` — the 13-key
  `REQUIRED.update`.
- `the-agency-system/Plan/131-manifest-coverage-lint/spec.md:33,121` — prior-art
  keyspace-parity lint + "no placeholder entries for unemitted tools" doctrine.
- `the-agency-system/Plan/harness/VOCABULARY.md` — the canonical cross-cutting
  vocabulary the prior art keeps single-sourced (the discipline 004 should mirror:
  one namespace ruling, cited, not re-derived).
