---
spec_id: "395"
slug: host-capability-loader
status: proposed
state: draft
last_updated: 2026-10-26
owner: "@agency"
vision_goals: [4, 8]
depends_on: ["016", "302"]
domain: substrate
---

# Spec 395 — Load a host repository's out-of-tree capability into the MCP and CLI entry points

> `Engine(extra_capabilities=[…])` already lets a capability live outside `agency/capabilities/`
> (GOALS #4, `examples/`), but only code that constructs an `Engine` can use it. The two
> production entry points — `agency-mcp` (`agency/__main__.py:main`) and the bash CLI
> (`agency/cli.py`) — build `Engine(db_path)` bare, so a host repository that ships its own
> capability folder cannot reach it through the plugin or the CLI. This spec adds one
> environment variable, `AGENCY_EXTRA_CAPABILITIES`, resolved at both entry points into the
> existing `extra_capabilities` argument. Nothing else changes.

## Why

The first host that needs it is `netzkontrast/kohaerenzprotokoll` (the novel-research
repository the `novel` capability's example corpus came from). Its rebuild concept
(`Plan/concept/rebuild-with-agency_2026-10-26.md` there) chooses a three-tier bridge: agency's
doctrine as standard-library patterns first, agency as an *optional plugin for development
sessions* second, and — only on the owner's word — a thin `kohaerenz` capability that relays
the host's existing scripts (`quotes.py`, `read.py`, `ask.py`, `storyform.py`, `aegis.py`) as
verbs with provenance. Tier two needs the plugin to see that folder; today it cannot. The
host's own rules make the shape strict: the capability must not live inside this repository
(the host is file-authoritative and standard-library only), must not require editing agency
to register (the drop-in bar, CLAUDE.md "If adding a capability needs an edit anywhere else,
that coupling is the bug to fix"), and must fail loudly, not silently, when it cannot load.

`Engine.__init__` already dedupes by capability name, first-wins for discovered caps over
re-supplied extras (Spec 302 reload path preserves `_extra_capabilities`). The loader only
needs to turn a string into the list the engine already accepts.

## Design

- **Variable.** `AGENCY_EXTRA_CAPABILITIES` — comma-separated entries, each `module` or
  `module:ClassName`. `module` is imported with `importlib.import_module` (the host's
  `.mcp.json`/CLI sets `PYTHONPATH` or `cwd` so the module resolves; `.mcp.json` already runs
  with `cwd: ${CLAUDE_PROJECT_DIR}`). Without `:ClassName`, every top-level `Capability`
  instance or `CapabilityBase` subclass in the module is taken, exactly as
  `discover_capabilities()` does for the package. Whitespace and empty entries are ignored.
- **Resolution point.** One function `resolve_extra_capabilities(env: str | None) ->
  list[Capability]` in `agency/_capability_loader.py` (the existing folder-loader module),
  called by `agency/__main__.py:main` and by the CLI's engine constructor
  (`agency/cli.py` `_engine`/`_resolve_db` neighbourhood), passing the result as
  `extra_capabilities`. `Engine` itself stays unchanged — the env is an entry-point concern,
  not an engine concern, so tests that build engines directly see nothing new.
- **Failure.** An entry that does not import, names a class that is not a `CapabilityBase`
  subclass / `Capability` instance, or yields zero capabilities raises at startup with the
  entry and the underlying error in the message. Fail loud at the entry point, like the
  missing-`skill_doc` bootstrap check; never skip silently (a silently dropped capability is a
  dormant surface the host would then "use" without effect).
- **Doctor.** `agency_doctor` reports the resolved extras (name, module, verb count) under a
  new `host_capabilities` key so a host can see what loaded. Read-only.
- **Dedupe.** First-wins by name, as today: a host extra that collides with a built-in name is
  dropped with a doctor warning naming both modules (not an error — a host may legitimately
  ship a same-named cap while agency is upgraded underneath it).
- **Not in scope.** Writing the `kohaerenz` capability (it lives in the host; see the host's
  prompt D3); any change to the wire contract (still `search · get_schema · execute`); any new
  injector or driver; hot reload of host caps (`agency_reload` re-reads the env — that is the
  reload path's existing `_extra_capabilities` preservation, unchanged).

## Acceptance (behaviour, Gherkin under `tests/acceptance/features/host_capability_loader.feature`)

- Given `AGENCY_EXTRA_CAPABILITIES` names a module on `sys.path` that defines one
  `CapabilityBase` subclass, when the MCP engine is built through the entry point's resolver,
  then that capability's verbs are discoverable via `search` and callable via `execute`, and an
  invocation `SERVES` the confirmed intent (the moat holds for host caps).
- Given the same variable with `module:ClassName`, when two classes exist in the module, then
  only the named one is registered.
- Given an entry that does not import, when the engine is built, then startup fails with a
  message naming the entry and the import error (no engine, no partial registration).
- Given an extra whose name collides with a built-in capability, when the engine is built,
  then the built-in wins and `agency_doctor.host_capabilities` reports the dropped module.
- Given the variable is unset or empty, when the engine is built, then the registry is
  identical to today's (a relationship, not a frozen count: the sorted name list equals the
  list from `Engine(":memory:")`).
- The bash CLI resolves the same variable, so `agency <host-cap> <verb>` works for a host cap
  (bash ↔ MCP isomorphism extends to host caps).

## Slices (TDD)

1. `resolve_extra_capabilities` + its failure modes (unit-level behaviour in the acceptance
   scenarios above; no internals asserted).
2. Wire into `agency/__main__.py:main` and the CLI; the doctor key.
3. `docs/vision/reference/` + `README.md` install section: one paragraph on
   `AGENCY_EXTRA_CAPABILITIES` for host repositories; `scripts/check-drift` clean.

## Followup — Implementation Status (2026-10-26)

Not started. Opened as a draft from the Kohärenz rebuild session; the owner's approval of its
decisions (ADR hinge) precedes implementation. The host-side consumer is specified in
`kohaerenzprotokoll/Plan/briefings/rebuild-prompts_2026-10-26.md` (prompts D1–D3).
