# Spec 348 — Spec-panel review (critique mode)

> Panel: Wiegers (requirements), Adzic (examples), Fowler (interface/SRP),
> Cockburn (actor/goal), Nygard (failure/ops), Crispin (testing). Mode: critique.
> Score **7.0/10** → **8.0/10** after the folds below. 2 blockers, 4 majors, 2
> minors. Findings the spec already handles are omitted.

## Blockers

**B1 — Fowler (and the spec's own discipline): `review` + `audit` are one
implementation behind two names.** `frugal.review` (diff) and `frugal.audit`
(repo) share tags, output shape, and logic — they differ only by *scope*. A
capability whose whole reason for existing is "no abstraction with one
implementation, no layer with one caller" cannot ship two verbs that are the same
transform with a scope flag. This is the `yagni:` tag turned on the spec itself.
→ **FOLD:** collapse to **`frugal.review(scope="diff"|"repo", …)`** (default
`diff`). `audit` becomes `review(scope="repo")` — documented alias at most, not a
second verb. Verb count 8→7. (Self-referential proof that the discipline works.)

**B2 — Wiegers: "mandatory" has no measurable delta over Spec 332.** Spec 332
already injects frugal at SessionStart (`_append_frugal`, engine.py:476-491). The
spec says 348 makes it "canonical and non-optional" but never states the *new,
testable* invariant. As written, "mandatory" is vacuous — 332 already does it.
→ **FOLD:** name the delta precisely — 348 adds **two** things 332 lacks: (a) the
frugal *capability surface* (the verbs) is always discoverable in
`agency_welcome` (332 only injects the discipline *text*, not the verb surface);
(b) a **gate** asserts the SessionStart payload carries the discipline at every
non-`off` level AND the capability is listed regardless of level. "Mandatory" =
those two gate-checked invariants, not a re-statement of 332.

## Majors

**M1 — Adzic: `review`'s input contract is unspecified.** "Given a diff" — from
where? A param? `git diff`? The working tree? Untestable until pinned. → **FOLD:**
`review` defaults to the working-tree diff (`git diff` HEAD), overridable by an
explicit `ref`/`diff` arg; `scope="repo"` walks the tree under `paths`. Add a
worked example showing the default (no-arg) path.

**M2 — Nygard: `review(scope=repo)` and `debt` have no operational bound.** A
repo-wide scan on a large tree emits an unbounded Finding set (the
scenario-analysis flagged this too). Full-capture (CLAUDE.md #76) governs *not
truncating what you collect* — it does not license scanning the whole world by
default. → **FOLD:** both take a `paths` scope (default: tracked source, excluding
`node_modules`/`.git`/build dirs) and rank/emit within it; capture stays full
*within scope*. Name the default exclusion set.

**M3 — Crispin: widening `debt`'s comment prefixes reintroduces prose false
positives.** The spec fixes ponytail's `#//`-only gap by matching all comment
styles — but ponytail used the comment-prefix precisely to keep the word
"frugal:" in prose/string-literals out of the ledger. Widen the prefixes and you
risk matching `"frugal: …"` inside a docstring or a test string. → **FOLD:** the
match contract is *comment-prefixed marker only* across the widened prefix set
(`#`, `//`, `--`, `<!-- -->`, `;`, `%`, `/* */`) — never a bare substring. Add a
negative scenario: a `"frugal:"` inside a string literal is NOT harvested.

**M4 — Cockburn: name the primary actor for `instructions`.** Agency's own
agents already receive frugal via the SessionStart inject — so who calls
`frugal.instructions`? Only an **external / no-hook host** (the ponytail-MCP use
case: a host whose sole injection point is a tool/prompt pull). Unstated, the verb
looks redundant with the inject. → **FOLD:** one line in §4 naming that actor and
why agency-internal agents never need it.

## Minors

**m1 — Wiegers: pre-empt the CLAUDE.md #8 contradiction on `gain`'s data file.**
A committed `benchmark.json` could read as a "frozen snapshot" (rule 8). It isn't
— it is a *documented external constant* (published, cited measurement), the
explicitly-allowed exception. → **FOLD:** state the exception inline so a future
audit doesn't flag it.

**m2 — Adzic: `help` derivation needs a tie to the registry test.** "Derived from
the live registry" is the right fix for drift, but assert it: a test that `help`'s
verb list equals the registry's `frugal.*` set (compute, don't pin — rule 8). →
**FOLD:** add that scenario.

## Consensus

The cluster is well-grounded and the provenance upside is real. The headline fix
is **B1** — the spec must apply its own ladder to itself (one `review` verb, not
two). **B2** turns "mandatory" from a slogan into two gate-checked invariants.
With B1/B2 + the four majors folded, the surface is 7 verbs, each with a pinned
input contract and an operational bound, and the discipline is enforced by gates
rather than asserted in prose.
