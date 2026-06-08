# Jules Brief — Slice 2: Narrative Context Protocol (NCP)

- **alias:** `kp-decomp-ncp`
- **work repo (source):** `netzkontrast/kohaerenzprotokoll`
- **starting branch:** `claude/dreamy-galileo-06exy`
- **target dir (write only here):** `Plan/decomposition/02-ncp-protocol/`
- **goal:** First-principles decomposition of the **NCP state/schema/validation**
  slice — the structured narrative state that everything else reads and writes.

## Dispatch prompt

```
You are decomposing ONE slice of a novel-writing capability for the Kohärenz
Protokoll repo. Work language: English. Never translate German canon prose.

Gates (JULES_PROTOCOL style): Confidence >= 0.90 before writing · evidence =
cited paths + measured numbers + grep hits (TDD N/A) · Self-Review in PR. On a
load-bearing ambiguity, call request_user_input ONCE, then stop.

READ-ONLY clone (learn the plugin contract; never commit it):
  git clone --depth=1 --branch=main https://github.com/netzkontrast/agency.git ~/work/vendor/agency
  Study examples/music.py + agency/{capability,ontology,engine}.py. Note that the
  graph is the store and files are a rendered view; the wire contract is
  search · get_schema · execute.

READ (read-only, in THIS repo):
  Legacy/skills/ncp-author/**   (schema cheatsheet, canonical vocabulary:
    463 appreciations + 144 narrative_functions, validator, 10-stage workflow)
  Legacy/research/ncp-novel-co-authoring-spec/**
  Legacy/tasks/015-integrate-dramatica-ncp-skills, 076-novel-architect-canon-status-schema
  Legacy/maintenance/schemas/narrative-ontology/**

MEASURE, don't assume: find the NCP schema file, confirm its JSON-Schema draft
and top-level shape ({schema_version, story} or similar), the schema version,
and assert the real vocabulary counts (appreciations / narrative_functions).
Cite exact paths + numbers; do not hard-code counts that the data can yield.

WRITE ONLY inside Plan/decomposition/02-ncp-protocol/ :
  DECOMPOSITION.md  — NCP as a data model: what the schema actually constrains,
    the canonical vocabulary, the validation rules, and the relationship between
    NCP state and the Dramatica storyform.
  PROPOSAL.md       — how NCP lives in the KP repo: an ncp_validate capability
    verb, where the schema + vendored vocabulary live (with .sha sidecar), the
    per-work ncp.json skeleton (draft + schema_version), and crucially: what is
    canonical in the graph vs rendered to disk (the graph-vs-disk tension —
    state your recommendation but flag it as a human decision).
  OPEN-QUESTIONS.md — decisions needing a human call.

Then open a PR into claude/dreamy-galileo-06exy. Touch nothing outside your dir.
```
