# Release and Distribution

> Generic Claude Code distribution covers GitHub-direct, marketplace, and
> private/team patterns — see [`common-patterns.md`](common-patterns.md)
> and the Superpowers `developing-claude-code-plugins` skill's release
> phase. This file covers the agency-specific lifecycle.

## The single source of truth: `python -m agency.install`

The agency plugin is **self-hosted**: the engine generates and validates its
own install. Three manifest-class files are regenerated from the live engine
state, NOT hand-edited:

| Generated file | Source of truth |
|---|---|
| `.claude-plugin/plugin.json` | `agency/install.py` template + the engine's metadata |
| `.mcp.json` | `agency/install.py` template + the engine's MCP entrypoint |
| `commands/agency-*.md` (slash-commands) | The engine's verb registry (live introspection) |
| `skills/help/SKILL.md` | The engine's capability map (live introspection) |

> **Rule:** after any change to `agency/capabilities/`, `agency/engine.py`,
> or a verb signature/docstring, re-run `python -m agency.install` and commit
> the regenerated files alongside the source change. The CI/lint pipeline
> would catch a drift, but committing the regen with the change keeps the
> diff coherent.

## The release loop

```bash
# 1. Code change (new capability, new verb, doc tweak)
$EDITOR agency/capabilities/my_cap.py
python -m pytest -q                       # green

# 2. Lint the changed capability (block mode)
python -m agency.cli execute --code '
return await call_tool("capability_plugin_lint_capability",
                       {"name": "my_cap"})'

# 3. Regenerate the install
python -m agency.install
git status                                # see which manifest files changed

# 4. Smoke test
$CLAUDE_PLUGIN_ROOT/.venv/bin/python -m agency &       # MCP server stdio
# … or run the agency-doctor over the CLI:
python -m agency.cli execute --code '
return await call_tool("agency_doctor", {})'

# 5. Commit + tag
git add agency/ tests/ .claude-plugin/ .mcp.json commands/ skills/
git commit -m "feat(my_cap): <one-line why>"
git tag v0.1.<n>
git push origin main
git push origin v0.1.<n>
```

## Versioning

Semver. The agency plugin treats:

- **MAJOR** — ontology breaks (a node-type rename, an enum-shrink, a removed verb).
- **MINOR** — additive capability (new verb, new ontology fragment, new substrate tool).
- **PATCH** — docstring fix, bugfix, lint tightening, test addition.

The engine is `0.x` today — minor bumps for capability additions, patch for fixes.

## Distribution paths

### Path A — marketplace install (today, the only working path)

User adds the marketplace and installs:
```
/plugin marketplace add netzkontrast/agency
/plugin install agency@agency
```

The marketplace lives in this repo itself
(`.claude-plugin/marketplace.json` — note: NOT in `marketplace.json` at
root). `agency.install` regenerates it from the live engine.

### Path B — `pipx install` from repo checkout (Spec 039, not yet shipped)

Forward-pointer for the in-flight hygiene work:
```
pipx install git+https://github.com/netzkontrast/agency
# … exposes `agency-mcp` console-script on PATH
# … no .venv bootstrap in the plugin tree
# … no `bin/agency-mcp` bash wrapper needed
```

This requires:
- `[project.scripts] agency-mcp = "agency.__main__:main"` in `pyproject.toml`.
- The MCP `.mcp.json` to use the resolved `agency-mcp` binary (or a discovery
  shim) instead of `${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp`.

Tracked in Spec 039 — see [`docs/superpowers/specs/`](../../../docs/superpowers/specs/) once written.

### Path C — `pip install -e .` (developer install)

The current developer flow:
```bash
git clone https://github.com/netzkontrast/agency
cd agency
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

This is what `bin/agency-install` runs on first MCP-server launch, scoped to
the plugin tree's `.venv`.

## Pre-release checklist

Before tagging:

- [ ] `python -m pytest -q` is green.
- [ ] `python -m agency.cli execute --code 'return await call_tool("capability_plugin_lint_capability", {"name": "<cap>"})'` is `ok=True` for every changed capability.
- [ ] `python -m agency.install` produced no diff (or the diff is the one you intend to ship).
- [ ] `agency_doctor` is `ok=True` on a fresh venv (`rm -rf .venv && bin/agency-install`).
- [ ] `tests/test_search_isomorphism.py` passes — MCP/CLI parity is unbroken.
- [ ] Spec or PR body references which spec the change implements (Spec 016, 023, 029, …).

## After release

- Bump the version in `pyproject.toml` AND `.claude-plugin/plugin.json` (the
  `agency.install` regen keeps these in sync, but check).
- Add a CHANGELOG entry under the new tag if the change is user-visible.
- If the change adds a substrate tool, update `docs/vision/CORE.md`'s tool
  list (CORE.md IS hand-maintained — that's an explicit exception to the
  graph-is-the-store rule).

## Doctrine reminders

- **Never commit the `.venv` tree** — `.gitignore` already excludes it.
- **`.agency/session.db` IS committed** (Spec 020) — the provenance graph is
  durable across machines. Don't `.gitignore` it.
- **Don't rewrite history** on `main` (CLAUDE.md: "additive history; never
  rewrite or force-push").
