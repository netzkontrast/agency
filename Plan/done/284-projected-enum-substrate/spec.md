---
spec: 284
title: projected-enum-substrate
status: Shipped
state: done
depends_on: [282]
clusters: [core]
vision_goals: [4, 5, 6]
---

# Spec 284 — projected-enum substrate (Workstream B)

> Status: **Implementing** · Parent: Spec 282 (error-severity-taxonomy) §"Still — B"
> Branch: `claude/agency-error-enum-fixes-13tpnf`

## Problem (evidence-grounded)

The `kohaerenzprotokoll/.agency/session.db` census recorded **513
`create_scene` failures** — all `INVALID_ARGUMENT` on the closed `pov` enum
(`SCENE_POV = {first, second, third-limited, third-omniscient}`). The caller
was passing **rich voice descriptions** ("auktorialer Erzähler",
"Erzähler (Vermittler-Stimme, suggestiv-personal)") that carry the canonical
signal but don't string-equal a member. Two substrate gaps:

1. **Discovery gap.** `get_schema` (FastMCP code-mode, default `detailed`
   markdown) renders each param as `` `name` (type, required) `` — it surfaces
   neither the param `enum` nor the param `description`. So an agent calling
   `get_schema("capability_novel_create_scene")` sees `pov (string, required)`
   and has **no way to learn the four legal values** short of reading source.
   The closed set is invisible at the exact moment of discovery.

2. **Lossy rejection.** Even knowing the members, a caller with a rich
   description must hand-collapse it to a bare enum token and **discard** the
   descriptive text (the CLAUDE.md gotcha: "project rich voice descriptions
   onto it; keep the full register text in codex"). The substrate forces a
   lossy choice instead of preserving the original.

## Design — a *projected enum*

A **projected enum** is a field whose graph value is a closed enum, but whose
caller-facing parameter accepts free text, is **projected** onto a canonical
member, and keeps the original rich text in a paired `<field>_detail` prop —
the **non-lossy** contract. Two substrate moves + one capability adoption.

### 1. `param_enums` on the verb spec (declaration)

`verb(role, …, param_enums={"pov": SCENE_POV})` — the verb points a parameter
at its canonical member set. The members live where they already live (the
`SCENE_POV` module constant the ontology enum also references — **single
source**, CLAUDE.md rule 2). No per-verb duplication of the value list.

Threaded `fn._verb["param_enums"]` → `_wrap_method` → `spec["param_enums"]`.
Functional-form capabilities and verbs that don't declare it are unaffected
(`spec.get("param_enums")` defaults to `{}`).

### 2. `_wire` surfaces the members two ways (discovery)

For each declared `(pname, members)`, `engine._wire`:

- wraps the param annotation in
  `Annotated[<ann>, Field(json_schema_extra={"enum": sorted(members)})]` — so
  the tool's **JSON inputSchema** carries `enum` (surfaced by `get_schema`
  `detail="full"` and by any real MCP client reading `inputSchema`).
  `json_schema_extra` is **schema-only** — pydantic does **not** validate
  against it, so rich free text still flows through to the verb (the
  projection happens there, not at the wire).
- appends a concise hint to the wired tool **description** (the one free-text
  field the `detailed`/`brief` code-mode renderer always shows):
  `… Enums: pov ∈ {first, second, third-limited, third-omniscient}.`

Both derive from the single `param_enums` declaration. Why description-folding
**and** schema `enum`: FastMCP's `detailed` markdown renderer
(`serialize_tools_for_output_markdown`) prints only `name (type, required)` and
the tool description — it ignores per-param `enum`/`description`. Folding the
hint into the description is therefore the only renderer-independent way to
reach the **default** code-mode view; the schema `enum` serves `full` detail
and raw MCP clients.

Why opt-in (not auto-derived from the ontology): the engine cannot reliably
map a param name to an ontology `(label, field)` enum — `status` alone is a
field on Novel, Chapter, Idea, … with different member sets. Explicit
`param_enums` is the safe, unambiguous declaration.

### 3. `project_enum` primitive + capability adoption (non-lossy)

`agency/_enums.py::project_enum(value, members, *, aliases=None, default=None)
-> (canonical|None, detail)`:

- exact member (case-sensitive) → `(value, "")` — already canonical, no detail.
- exact member (case-insensitive, whitespace-trimmed) → `(member, value)`.
- alias keyword: any `aliases` key that is a substring of the normalized
  value, **longest key first** (specific signal beats generic — `omniscient`
  before `third`) → its canonical member, detail = original.
- `default` when supplied; else `(None, value)`.

`detail` is the original value whenever it differs from the canonical — the
rich text to preserve. `(None, …)` means **no signal**: the caller raises a
PERMANENT typed error (Spec 282) listing the members — never a silent
mis-file. Projection is **forgiving on signal, strict on noise**.

The projection *primitive* is engine substrate; the *alias map* is
domain-specific and lives in the capability (`novel._POV_ALIASES`).

`novel.create_scene` adopts it: declares `param_enums={"pov": SCENE_POV}`,
projects `pov` through `project_enum(pov, SCENE_POV, aliases=_POV_ALIASES)`,
records `pov=<canonical>` plus `pov_detail=<original>` (optional prop; no
ontology change — `Scene` required fields stay `[chapter, slug, pov]`, and the
recorded canonical `pov` still satisfies the `("Scene","pov")` enum).
`check_pov_consistency` keeps reading the canonical `pov`, so consistency
checks are unaffected.

## Tests (RED → GREEN)

`tests/test_projected_enum.py`:
1. `project_enum` exact member → `(value, "")`.
2. case-insensitive exact → `(member, original)`.
3. alias substring, longest-first precedence (`"…omniscient…"` → omniscient
   even when `"third"` also matches).
4. no signal → `(None, original)`; with `default` → `(default, original)`.
5. wired tool JSON schema carries `enum` for a `param_enums` param
   (`create_scene.pov`), `type` stays `string`.
6. wired tool description carries the `Enums: pov ∈ {…}` hint.
7. rich non-member `pov` flows through the wire unrejected (pydantic does not
   validate `json_schema_extra` enum).

`tests/test_novel_lifecycle_slice2.py` (updated):
8. `create_scene` exact `pov="third-limited"` → no `pov_detail`.
9. `create_scene` rich `pov="auktorialer Erzähler"` → `pov="third-omniscient"`,
   `pov_detail="auktorialer Erzähler"` preserved; recorded Scene node enum-valid.
10. `create_scene` no-signal `pov="left-handed narration"` → permanent
    `INVALID_ARGUMENT` (replaces the old typo-rejection case, which now
    projects on its `omniscient` signal).

## Acceptance

- `get_schema` surfaces the canonical members for a `param_enums` param (both
  in the JSON `enum` and the description hint) — the discovery gap closes.
- A rich `pov` description is projected onto a canonical member with the
  original preserved in `pov_detail` — the 513 evidence failures would now
  succeed, non-lossily.
- No-signal input still fails PERMANENT (Spec 282), listing the members.
- `check_pov_consistency` and the `("Scene","pov")` ontology enum are
  unaffected (canonical value recorded).
- Focused slices green (`scripts/test-cap novel`, new `test_projected_enum`);
  full regression on CI; `scripts/check-drift` exit 0.

## Migration

Additive. Existing Scenes lack `pov_detail` (optional). Verbs without
`param_enums` are untouched. Seeded graphs unaffected.
