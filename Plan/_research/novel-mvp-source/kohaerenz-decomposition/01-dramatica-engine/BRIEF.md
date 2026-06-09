# Jules Brief — Slice 1: Dramatica Engine

- **alias:** `kp-decomp-dramatica`
- **work repo (source):** `netzkontrast/kohaerenzprotokoll`
- **starting branch:** `claude/dreamy-galileo-06exy`
- **target dir (write only here):** `Plan/decomposition/01-dramatica-engine/`
- **goal:** First-principles decomposition of the **Dramatica model & lookup**
  slice, and a proposal for how it should live in the KP repo as an agency
  capability + on-disk artefacts.

## Dispatch prompt

```
You are decomposing ONE slice of a novel-writing capability for the Kohärenz
Protokoll repo. Work language: English. Never translate German canon prose.

Gates (JULES_PROTOCOL style): Confidence >= 0.90 before writing · evidence =
cited paths + measured numbers + grep hits (TDD N/A: this is design/analysis) ·
Self-Review (drift/risk/next) in your PR. On a load-bearing ambiguity you cannot
resolve from the data, call request_user_input ONCE with two interpretations,
then stop.

READ-ONLY clone (learn the plugin contract; never commit it):
  git clone --depth=1 --branch=main https://github.com/netzkontrast/agency.git ~/work/vendor/agency
  Study: examples/music.py (template capability), agency/capability.py
  (CapabilityBase, OntologyExtension, @verb role tags act/transform/effect),
  agency/ontology.py (Ontology.extend), agency/engine.py (extra_capabilities
  auto-wiring of one MCP verb per tool). The wire contract is exactly
  search · get_schema · execute; the graph is the store, files are a rendered view.

READ (read-only, in THIS repo):
  Legacy/skills/dramatica-theory/**
  Legacy/skills/dramatica-vocabulary/**   (75 dynamic pairs, encoding, storyweaving)
  Legacy/tools/dramatica-nav/**           (the dramatica_lookup navigator)
  Legacy/tasks/042-dramatica-nav-followups, 078..082-dramatica-scenarios-*
  Legacy/maintenance/schemas/narrative-ontology/** (novel.dual-storyform, etc.)

MEASURE, don't assume: count the real entries in the dramatica ontology data,
the kind breakdown (Class/Type/Variation/Element), and the dynamic-pair table
size. Cite exact paths and numbers.

WRITE ONLY inside Plan/decomposition/01-dramatica-engine/ :
  DECOMPOSITION.md  — the irreducible primitives of Dramatica as this corpus
    models them (storyform: 4 Classes / 16 Types / 64 Variations / 64 Elements;
    throughlines; dynamic pairs; the lookup/navigation operation). Separate the
    essential model from incidental skill-packaging.
  PROPOSAL.md       — how this slice should live in the KP repo: which operations
    become agency capability verbs (e.g. a dramatica_lookup transform), what data
    is vendored (with .sha sidecar) under a data/ dir, what is a graph node vs a
    rendered file, and the concrete paths.
  OPEN-QUESTIONS.md — anything needing a human decision.

Then open a PR from your branch into claude/dreamy-galileo-06exy. Do NOT touch
any path outside your target dir.
```
