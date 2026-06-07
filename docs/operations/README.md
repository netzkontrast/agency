# Operations — dev, test, CI, drift, docs

How to work on agency day to day.

<!-- doc-source: CLAUDE.md .github/workflows/test.yml scripts/check-drift scripts/check-doc-drift -->

## Dev loop

```bash
. .venv/bin/activate
scripts/test-cap <marker>     # focused slice (< 30s) — the TDD inner loop
scripts/test-changed          # only the capabilities your diff touched
python -m pytest -q -n auto -m "not e2e"   # full local suite (~1 min / 4 cores)
python -m agency.install      # regenerate the plugin install when capabilities change
```

Per CLAUDE.md rule 7: run **focused slices** locally; the **full regression** runs in CI
on every PR + push to `main` (`.github/workflows/test.yml`: `pytest -n auto -m "not e2e"`;
E2E on `v*` tags). When you push a feature branch, **subscribe to PR activity** so CI
failures + review comments arrive as session notifications.

## Two drift gates

Agency keeps generated/derived surfaces in sync with two checkable gates:

| Gate | Script | Checks |
|---|---|---|
| **Code/spec drift** (Spec 054) | `scripts/check-drift` | install regen produces no diff · capability-test-gap · `# AGENCY-DRIFT:` tag inventory · token-economy lint. Run **before commit** when adding a capability/extra/tool. |
| **Doc drift** (this docs tree) | `scripts/check-doc-drift` | each hand-written doc declares its sources via `<!-- doc-source: … -->`; the script hashes those sources and flags any doc whose sources changed since it was stamped. |

```bash
scripts/check-drift                  # exit 0 = clean; 1 = drift
scripts/check-doc-drift              # report stale docs
scripts/check-doc-drift --update     # re-stamp doc-hash markers after reviewing a doc
scripts/check-doc-drift --strict     # also flag docs with NO marker
```

When you change a core module, `check-doc-drift` will flag the architecture page that
documents it — review the page, then `--update` to re-stamp. Generated docs
(`docs/guide/capabilities.md`, carrying `<!-- doc-generated-by: … -->`) are **skipped** —
regenerate them with `scripts/gen-capability-docs`, don't hand-edit.

## Known gaps (tracked)

- **Installer prune** — `python -m agency.install` *writes* the `bin/` wrappers +
  `references/` but does **not prune** stale ones when a verb is removed/renamed, and
  `check-drift` doesn't flag the orphans. Remove them by hand for now (graph reflection
  `e42e67fe`).

## Releasing

Tagged builds (`v*`) run the E2E suite + a self-hosted install-drift check that gates
merge. The plugin install surface (`skills/`, `bin/`, `hooks/`, manifest) is regenerated
from the registry — never hand-edited.
