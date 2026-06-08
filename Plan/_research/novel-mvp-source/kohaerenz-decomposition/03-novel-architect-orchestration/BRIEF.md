# Jules Brief — Slice 3: Novel-Architect Orchestration

- **alias:** `kp-decomp-orchestration`
- **work repo (source):** `netzkontrast/kohaerenzprotokoll`
- **starting branch:** `claude/dreamy-galileo-06exy`
- **target dir (write only here):** `Plan/decomposition/03-novel-architect-orchestration/`
- **goal:** First-principles decomposition of the **phase orchestration, gates,
  and command surface** that drives a novel from idea to draft.

## Dispatch prompt

```
You are decomposing ONE slice of a novel-writing capability for the Kohärenz
Protokoll repo. Work language: English. Never translate German canon prose.

Gates (JULES_PROTOCOL style): Confidence >= 0.90 · evidence = cited paths +
grep hits (TDD N/A) · Self-Review in PR. On a load-bearing ambiguity, call
request_user_input ONCE, then stop.

READ-ONLY clone (learn the plugin contract; never commit it):
  git clone --depth=1 --branch=main https://github.com/netzkontrast/agency.git ~/work/vendor/agency
  Study agency/skill.py (the skill walker: progressive disclosure + gate:"hard"),
  agency/capabilities/gate.py (gate.check -> PASSED / BLOCKED_ON + input-required
  pause), examples/music.py, and how Lifecycle + Intent model a multi-step flow.

READ (read-only, in THIS repo):
  Legacy/skills/novel-architect/**          (8-phase orchestrator: Bootstrap,
    Intent, Narrative Architecture, Characters, World & Research, Scene Matrix,
    Drafting, Iteration; hard exit gates; AskUserQuestion loops; NCP persistence)
  Legacy/skills/novel-architect/commands/** (/novel-start, -design, -characters,
    -world/-research, -scenes, -draft, -reflect)
  Legacy/skills/novel-architect-legacy/**   (frozen v0.3.3 — the original KP skill)
  Legacy/tasks/003,070,071,083,088
  Legacy/research/integrate-dramatica-ncp-skills/**

WRITE ONLY inside Plan/decomposition/03-novel-architect-orchestration/ :
  DECOMPOSITION.md  — the orchestration as a state machine: the phases, the hard
    gates between them, where human input is elicited, and what state each phase
    reads/writes (NCP, Dramatica, character, world). Map novel-architect's phases
    onto agency's Lifecycle/Intent/gate primitives.
  PROPOSAL.md       — how orchestration lives in the KP repo: which phases become
    a gated agency skill (e.g. a work-concept skill walked via the engine),
    command surface, and the scaffold verb that initialises a new novel repo
    (the novels/{author}/works/{genre}/{slug}/ layout + root files + subfolders).
  OPEN-QUESTIONS.md — decisions needing a human call.

Then open a PR into claude/dreamy-galileo-06exy. Touch nothing outside your dir.
```
