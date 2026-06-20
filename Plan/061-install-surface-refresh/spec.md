---
spec_id: "061"
slug: install-surface-refresh
status: complete   # 2026-06-04: PYTHONPATH stripped + dynamic marketplace description + README refreshed + tests + install regen
last_updated: 2026-06-04
owner: "@agency"
depends_on: ["039", "055", "060"]
affects:
  - agency/install.py                                    # strip PYTHONPATH; richer marketplace description
  - .mcp.json                                            # regenerated (post-Spec 055 form)
  - .claude-plugin/marketplace.json                      # regenerated description
  - README.md                                            # capability table 11→14 rows; test count refresh
  - tests/test_install_mcp_skill.py                      # assert no PYTHONPATH; assert marketplace description shape
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 061 — Install surface refresh

## Why

The reviewed-from-scratch audit (2026-06-04, post-Spec 060 merge)
surfaced three concrete drifts between what `python -m agency.install`
regenerates and what the live engine actually delivers:

1. **README still lists 11 capabilities (it's 14 since 042 / 043 / 044
   shipped).** A new reader sees a stale surface — analyze, research,
   document don't appear in the canonical capability table.
2. **`marketplace.json` description is a one-liner** that says nothing
   about the now-shipped surface. A marketplace browser sees a generic
   engine pitch with no signal of the analyze / research / document /
   delegate / jules verb count.
3. **`.mcp.json` carries `PYTHONPATH=${CLAUDE_PLUGIN_ROOT}` env entry
   that's vestigial under Spec 055** (pipx-only doctrine). The pipx
   venv carries its own site-packages; `PYTHONPATH` is irrelevant and
   risks shadowing the pipx-installed `agency` package with the
   plugin-tree source on systems where both are present.

All three are install-surface bugs — they affect every new user of the
plugin. None requires deep work; together they close the
discoverability + correctness loop on what gets installed.

## Done When

- [ ] **`.mcp.json` env block drops `PYTHONPATH`.** Spec 055 made pipx
  the canonical install path; the pipx-installed `agency-mcp` already
  resolves `agency` from its own venv site-packages. `PYTHONPATH`
  in `.mcp.json` shadowed by `${CLAUDE_PLUGIN_ROOT}` actively risks
  picking up the plugin-tree source over the pipx-installed package
  on systems where both are present. `AGENCY_DB` + `JULES_API_KEY`
  stay (substrate config, not python-path config).
- [ ] **`marketplace.json` description carries surface signal.** The
  generator's `DESCRIPTION` constant currently reads:
  > Harness-in-harness agency engine: code-mode capabilities
  > (macroskills) over one provenance graph.
  Augment with a per-install one-line surface summary the install
  generator produces dynamically — e.g.
  > Harness-in-harness agency engine: 14 self-registering
  > capabilities (analyze / research / document / delegate / jules /
  > reflect / plugin …) over one provenance graph. Code-mode IS the
  > contract.
  The dynamic count + alphabetised list is computed from the live
  registry at generate-time so it never drifts.
- [ ] **README capability table refreshed.** Add rows for analyze,
  research, document. Update verb counts where they grew. Update the
  "216+ tests" claim to the current count (663 as of merge).
- [ ] **`tests/test_install_mcp_skill.py` asserts the new shape.**
  - assert `.mcp.json` env has NO `PYTHONPATH` key.
  - assert `.mcp.json` env still has `AGENCY_DB` + `JULES_API_KEY`.
  - assert `marketplace.json` description contains the per-cap surface
    signal (e.g. references "capabilities" + the live cap count).
- [ ] `python -m agency.install` produces a diff that matches the
  changes above; `scripts/check-drift` is clean.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### `.mcp.json` env block, post-refresh

```python
# agency/install.py — _mcp_json()
return {
    "mcpServers": {
        "agency": {
            "command": "${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp",
            "args": [],
            "env": {
                # Spec 055: pipx-only — agency-mcp resolves `agency`
                # from its own venv. PYTHONPATH would shadow that with
                # the plugin-tree source. Removed.
                "AGENCY_DB": "${CLAUDE_PROJECT_DIR}/.agency/session.db",
                "JULES_API_KEY": "${user_config.jules_api_key}",
            },
        }
    }
}
```

### Marketplace description, post-refresh

The generator builds a richer description by sampling the live
`engine.registry.names()`:

```python
def _marketplace_description(engine) -> str:
    """Spec 061 — dynamic description that names the cap surface so a
    marketplace browser sees what actually ships."""
    caps = sorted(engine.registry.names())
    cap_sample = ", ".join(caps[:7])   # first 7 alphabetised
    return (
        f"Harness-in-harness agency engine: {len(caps)} self-registering "
        f"capabilities ({cap_sample}…) over one provenance graph. "
        f"Code-mode IS the contract."
    )
```

Why "first 7": keeps the line under ~200 chars so the marketplace UI
renders it cleanly, but still names enough capabilities that a reader
recognises the surface domains.

### README capability table

Replace the 11-row table with the canonical 14 rows (alphabetised by
cap name):

| analyze   | transform/effect | 4-axis decidable analysis (quality/security/performance/architecture) + run/improve/cleanup + paths (Spec 048) |
| branch    | transform/effect | …  |
| delegate  | transform/effect | …  |
| develop   | transform/act    | …  |
| document  | transform/effect | render (markdown projections) + explain + index_repo |
| dogfood   | transform/effect | graph-native observation ledgers + JSON export/import |
| gate      | act              | …  |
| jules     | effect/transform | …  |
| plugin    | act/transform    | …  |
| reflect   | act/transform    | …  |
| research  | act              | lead → specialist → verify deep-research flow |
| skill_generator | act         | …  |
| subagent  | effect           | …  |
| workspace | effect           | …  |

Plus refresh the test-count line ("216+ passing" → "663 passing
+ 1 skip" or the current truth at ship time).

## Files

- **Modify:**
  - `agency/install.py` — drop `PYTHONPATH`; add `_marketplace_description(engine)`.
  - `.mcp.json` — regenerated.
  - `.claude-plugin/marketplace.json` — regenerated.
  - `README.md` — capability table + test count.
- **Modify (tests):**
  - `tests/test_install_mcp_skill.py` — three new assertions.

## Open Questions

1. **Should the dynamic description name ALL 14 capabilities?** The
   line gets long but loses no information. v1 uses "first 7 + …"
   ellipsis; v2 can flip to "all 14" if marketplace UI handles wrap.
   Recommend v1 (concise) for now.

2. **Should we strip the PYTHONPATH NOTE from install.py's docstrings
   too?** Lines 119/165 mention "PYTHONPATH so the agency package is
   always …". They're inaccurate post-Spec 055. Recommend YES — clean
   the doctrine in the same sweep.

3. **Do existing pipx installs need a migration step?** No — the
   generated `.mcp.json` is what Claude Code loads at session start;
   re-installing the plugin (or just re-cloning the marketplace) picks
   up the new shape on the next session. No data migration needed.

## Evidence (cites)

- `agency/install.py:186` — the `PYTHONPATH` line this spec removes.
- `agency/install.py:208` — `DESCRIPTION` constant the marketplace
  generator uses (this spec replaces with a generator).
- `.mcp.json` (post-merge) — current shape with `PYTHONPATH`.
- `README.md:114-138` — the 11-row capability table to expand.
- Spec 055 §"What goes" — established pipx as the only path; this
  spec closes the `.mcp.json` follow-up.
- Spec 039 §"agency-doctor" — the doctor verifies `agency-mcp` on
  PATH; PYTHONPATH is unrelated.
- 14 caps + 69 verbs live (per registry.names() + sum verb count,
  2026-06-04 at HEAD).

## Followup — Shipped (2026-06-04)

**Verdict:** Shipped.

### Done

- **`.mcp.json` `PYTHONPATH` removed** — pipx-only doctrine (Spec 055)
  makes it vestigial; pipx venv already resolves `agency`.
  `AGENCY_DB` + `JULES_API_KEY` stay (substrate config, kept).
- **`agency/install.py::_marketplace_description(engine)` ships** —
  dynamic per-cap-surface description ("Harness-in-harness agency
  engine: 14 self-registering capabilities (analyze, branch, …) over
  one provenance graph. Code-mode IS the contract."). First 7 caps
  alphabetised + "…" when more remain; bounded < 400 chars.
- **`_marketplace()` takes `engine` now** — generates the description
  from `engine.registry.names()` at generate-time, not from a static
  constant.
- **Stale PYTHONPATH docstring references** in `install.py` (CMD_BODY
  + the `Path conventions` block) updated to reflect the Spec 055
  pipx-router shape.
- **README capability table** expanded from 11 rows to 14 (added
  analyze, document, research; each with role tags + Spec-aligned
  one-liners).
- **README test count** refreshed: "216+ passing" → "663 passing".
- **`tests/test_install_mcp_skill.py`** gains 2 new asserts:
  `test_mcp_json_has_no_pythonpath` + `test_marketplace_description_
  names_live_surface` (asserts the dynamic cap count + bounded length).
- **`python -m agency.install` regen** produces a clean 3-file diff
  the spec wanted (`.mcp.json` minus PYTHONPATH, `marketplace.json`
  with the dynamic description, `commands/help.md` minor regen).

### Live measurements
- `pytest tests/test_install_mcp_skill.py` — 6/6 green.
- `scripts/check-drift` post-commit — clean (regen committed).

### Cluster-coherence (Spec 047)
- C13 (Plugin/MCP Authoring) — closes the Spec 055 follow-up loop;
  install surface now reflects the post-merge live registry.
