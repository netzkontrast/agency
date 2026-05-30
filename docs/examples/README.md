# Examples

Runnable, self-contained examples that drive the agency engine. Run from the repo
root with the package on the path:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python docs/examples/author_a_plugin.py
```

## `author_a_plugin.py`

Authors a tiny Claude Code plugin by walking the **`plugin-dev` skill** one phase
at a time (progressive disclosure). Each phase emits a prestructured document and
the chain ends at a hard confirm gate:

```
phase manifest     -> working
phase skill        -> working
phase command      -> working
phase marketplace  -> working
phase confirm      -> hard gate
confirm        -> completed

artefacts produced (each a prestructured step document):
  - plugin-manifest
  - skill-md
  - command-md
  - marketplace-entry
```

What it demonstrates:

- **The skill walker** — one phase disclosed at a time, each validated before
  advancing, blocking at the hard gate until confirmed.
- **Capabilities produce provenance** — every step records an Invocation that
  `SERVES` the intent and `PRODUCES` an Artefact, so the whole run is one
  connected subgraph (`e.memory.provenance(iid)`).
- **Templates prestructure each step's document** — the manifest, SKILL.md,
  command, and marketplace entry are rendered from strict templates.

From here, try the bash contract (`AGENTS.md`) or add your own capability by
dropping a file in `agency/capabilities/` — it self-registers and auto-wires.
