---
spec_id: "079"
slug: click-cli-verb-mirror
status: draft
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["018", "065"]   # the CLI token-efficiency bundle + the CLI subcommand surface
research_first: false
affects:
  - agency/cli.py                       # argparse → Click; auto-generated verb commands
  - pyproject.toml                      # add `click` dependency
  - agency/engine.py                    # (read-only) the live registry is the command source
estimated_jules_sessions: 0
domain: capability
wave: 5
---

# Spec 079 — Click CLI that mirrors every capability verb as a command

## Why

User directive (2026-06-06): *"after Spec 18 — extend it — use additional
dependencies like Click to rewrite the CLI and add all verbs as commands to the
CLI, mirroring the agency capabilities."* Today `agency/cli.py` is stdlib
`argparse` with a handful of hand-wired subcommands (`search` / `get-schema` /
`execute` / `intent` / `install` / `welcome` / `doctor` / `provenance`). A bash
agent reaches a capability verb only by writing an inline `execute --code
'await call_tool(...)'` block. The directive wants the FULL surface ergonomic
from bash: `agency <capability> <verb> --arg … --intent-id …`, one command per
verb, mirroring the live MCP catalog.

## Doctrine reconciliation (the load-bearing decision)

CORE.md / CLAUDE.md hold that **code-mode IS the contract** — "no separate
four-verb surface", token-economy first. A flat command per verb is exactly such
a surface, so this spec lands it as a **convenience layer, not a new contract**:

1. **Code-mode stays canonical.** `agency execute` (code-mode) remains the one
   wire contract; MCP and the code-mode CLI stay isomorphic. The per-verb
   commands are sugar that ultimately route through the SAME
   `registry.invoke` / engine path — no second execution model.
2. **Auto-generated from the live registry — zero per-verb boilerplate.** The
   commands are built by reflecting over `engine.registry` at CLI-construction
   time (mirroring how `engine._wire` builds one MCP tool per verb). Adding a
   capability/verb adds its command for free — no drift, honoring the open-set
   rule + Spec 054 (`AGENCY-DRIFT`). A frozen hand-written command list is
   explicitly rejected (it would rot — CLAUDE.md #8).
3. **Token-economy note.** The per-verb commands help a HUMAN at a shell; an
   agent optimizing tokens still prefers code-mode chaining. The help text says
   so (point agents at `agency execute`).

## Done When

- [ ] **`click` added** to `pyproject.toml` deps; `agency/cli.py` rewritten on
  Click while preserving EVERY existing subcommand's behaviour + exact JSON-on-
  stdout contract (search/get-schema/execute/intent/install/welcome/doctor/
  provenance — one JSON document per call, rc semantics unchanged).
- [ ] **Auto-generated verb group:** `agency <capability> <verb> [--param …]
  [--intent-id …] [--json '<dict>']` for every verb in the live registry. Params
  come from the verb signature (`inspect.signature`, minus injected params —
  same elision `engine._wire` does). `--intent-id` defaults to `AGENCY_INTENT`
  (Spec 018 Win 3). Output is the verb's wire delta as one JSON document.
- [ ] **Discovery parity:** `agency --help` lists capabilities; `agency <cap>
  --help` lists its verbs (gist from the brief docstring slice — Spec 023).
- [ ] **The result routes through the engine** (`registry.invoke` /
  `call_tool`), NOT a parallel path — same provenance, same SERVES guard, same
  wire-shape contract.
- [ ] Tests: a generated command resolves + invokes its verb (provenance
  recorded); param parsing from the signature; `--intent-id` env fallback; the
  legacy subcommands still pass their existing tests; `--help` lists the live
  capability/verb set (computed, not pinned).
- [ ] `pytest` green; `check-drift` clean (install regen unaffected — CLI is not
  in the generated plugin surface); CORE.md / CLAUDE.md note the convenience
  layer + its code-mode-canonical reconciliation.

## Open Questions

1. **Param typing.** Verb params are largely `str`/`dict`; Click needs a type per
   option. v1: map `str→STRING`, `int→INT`, `bool→FLAG`, `dict/list→a `--json`
   passthrough that `json.loads`. Richer typing deferred.
2. **Name form.** `agency shell run` (group-per-capability) vs `agency
   shell-run` (flat). Recommend group-per-capability — mirrors the
   `capability_<cap>_<verb>` wire name and reads naturally.
3. **Collision with reserved subcommands.** A capability named `search`/`intent`
   etc. would clash with a legacy top-level command. Guard: legacy commands win;
   the verb group is mounted under the capability name, and a collision is a lint
   warning (Spec 067 surface-size family).

## Evidence

- `agency/cli.py` (the argparse surface this rewrites) + Spec 065 (the CLI
  subcommand consolidation it extends).
- `agency/engine.py` `_wire` (the per-verb reflection pattern to mirror) + Spec
  018 Win 3 (the `AGENCY_INTENT` default the commands reuse).
- CORE.md "code-mode is the contract" + CLAUDE.md rule #1/#8 (the doctrine this
  reconciles).
- User directive (2026-06-06).
