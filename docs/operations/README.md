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
| **Code/spec drift** (Spec 054) | `scripts/check-drift` | install regen produces no diff · **orphan check** (stale `bin/`/`references/` for removed verbs, Spec 092 G1) · capability-test-gap · `# AGENCY-DRIFT:` tag inventory · token-economy lint. Run **before commit** when adding a capability/extra/tool. |
| **Doc drift** (this docs tree) | `scripts/check-doc-drift` | each hand-written doc declares its sources via `<!-- doc-source: … -->`; the script hashes those sources and flags any doc whose sources changed since it was stamped. **Runs in CI as an advisory step** (Spec 092 G5). |
| **Followup grounding** (Spec 092 G6) | `scripts/check-followup` | for each `Shipped` spec, the `## Followup` section should cite tests that exist on disk — catches a roll-up claim that overstates completeness. **Advisory CI step.** |

```bash
scripts/check-drift                  # exit 0 = clean; 1 = drift (incl. orphans)
scripts/check-doc-drift              # report stale docs
scripts/check-doc-drift --update     # re-stamp doc-hash markers after reviewing a doc
scripts/check-doc-drift --strict     # also flag docs with NO marker
scripts/check-followup               # advisory: Shipped specs cite tests that exist
```

CI (`.github/workflows/test.yml`) runs the full suite + the self-hosted install check as
hard gates, and `check-doc-drift` + `check-followup` as **advisory** steps
(`continue-on-error`) — they surface staleness in the logs without failing the build yet
(promote to gating once the marked set stabilises).

When you change a core module, `check-doc-drift` will flag the architecture page that
documents it — review the page, then `--update` to re-stamp. Generated docs
(`docs/guide/capabilities.md`, carrying `<!-- doc-generated-by: … -->`) are **skipped** —
regenerate them with `scripts/gen-capability-docs`, don't hand-edit.

## Known gaps (tracked)

- **Installer prune** — ✅ **fixed (Spec 092 G1)**: `python -m agency.install` now prunes
  generator-owned `bin/`/`references/` files that no longer map to a live verb, and
  `check-drift` flags any committed orphan the prune removes (`orphans:` section). The
  remaining substrate improvements are tracked in `Plan/092-…` (G2–G6).

## Releasing

Tagged builds (`v*`) run the E2E suite + a self-hosted install-drift check that gates
merge. The plugin install surface (`skills/`, `bin/`, `hooks/`, manifest) is regenerated
from the registry — never hand-edited.
