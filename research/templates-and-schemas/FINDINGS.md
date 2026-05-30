# Templates & Schemas Findings

## Gap Matrix: Artefact Kind vs Template & Schema

The following matrix maps every artefact kind produced in the PR1 repo (`agency/capabilities/`) against its defined Template and strict Schema in `agency/templates.py` and `agency/ontology.py`.

| Artefact Kind | Has Template? | Has Schema? | Cited Path:Line |
|---|---|---|---|
| authoring | No | No | `agency/capabilities/plugin.py:136` |
| baseline | No | No | `agency/capabilities/plugin.py:139` |
| command-md | Yes (COMMAND_MD) | Yes | `agency/capabilities/plugin.py:163` |
| discipline | No | No | `agency/capabilities/develop.py:62` |
| entry | No | No | `agency/capabilities/plugin.py:166` (marketplace produces) |
| findings | No | No | `agency/capabilities/develop.py:67` |
| jules-session | No | No | `agency/capabilities/jules.py:56` |
| lint | No | No | `agency/capabilities/plugin.py:143` (lint produces) |
| manifest | No | No | `agency/capabilities/plugin.py:157` (manifest produces) |
| marketplace-entry | Yes (marketplace_obj) | Yes | `agency/capabilities/plugin.py:65` |
| plugin-manifest | Yes (manifest_obj) | Yes | `agency/capabilities/plugin.py:43` |
| rationalization-table | No | No | `agency/capabilities/plugin.py:147` (refactor produces) |
| rationalizations | No | No | `agency/capabilities/plugin.py:139` |
| red-flags | No | No | `agency/capabilities/plugin.py:147` (refactor produces) |
| reduction | No | No | `agency/capabilities/delegate.py:78` |
| skill-md | Yes (SKILL_MD) | Yes | `agency/capabilities/plugin.py:140` |
| step-doc | Yes (STEP_DOC) | Yes | `agency/capabilities/plugin.py:74` |
| user-confirmed | No | No | `agency/capabilities/plugin.py:148` (deploy produces) |

## Analysis
The PR1 core defines 18 output `Artefact` kinds, but only 5 have formal templates (`COMMAND_MD`, `SKILL_MD`, `STEP_DOC`, `manifest_obj`, `marketplace_obj`) and matching schemas defined in `REQUIRED`. The remaining 13 artefacts (such as `findings`, `baseline`, `reduction`, and `jules-session`) are currently emitted opaquely without a validated schema or a structural template, which prevents reliable generation and validation in memory.

## Self-Review
1. **Coverage:** 152 of 152 files read. 100% of the in-scope items for `agency` (work repo), `the-agency-system`, and `bitwize-music` (reference repos) were swept and ingested.
2. **Residual risk / unknowns:** The capabilities discover dynamically at runtime (`agency/capabilities/__init__.py`), so there may be implicit artefacts not captured by static analysis of the `produces` list or explicit `record("Artefact")` calls.
3. **Method reflection:** SCAMPERing the templates against the prior art in `the-agency-system` and mapping the artefact×capability matrix uncovered that while the `plugin.py` capability has strong typing, `develop.py` and `delegate.py` rely heavily on ad-hoc dictionaries for `baseline`, `reduction`, and `discipline`.
