# Jules Brief — Slice 5: Structure, Scene & Coherence

- **alias:** `kp-decomp-structure-coherence`
- **work repo (source):** `netzkontrast/kohaerenzprotokoll`
- **starting branch:** `claude/dreamy-galileo-06exy`
- **target dir (write only here):** `Plan/decomposition/05-structure-scene-coherence/`
- **goal:** First-principles decomposition of **plot structure, the scene matrix,
  coherence checks/linters, and the render pipeline.**

## Dispatch prompt

```
You are decomposing ONE slice of a novel-writing capability for the Kohärenz
Protokoll repo. Work language: English. Never translate German canon prose.

Gates (JULES_PROTOCOL style): Confidence >= 0.90 · evidence = cited paths +
measured numbers + grep hits (TDD N/A) · Self-Review in PR. On a load-bearing
ambiguity, call request_user_input ONCE, then stop.

READ-ONLY clone (learn the plugin contract; never commit it):
  git clone --depth=1 --branch=main https://github.com/netzkontrast/agency.git ~/work/vendor/agency
  Study how a transform (pure, decidable) differs from a judgement-skill, and the
  gate.check PASSED / BLOCKED_ON pattern — coherence checks split along this line.

READ (read-only, in THIS repo):
  Legacy/skills/novel-architect-structure/** (40-chapter matrix, Hero's Journey,
    Save the Cat, Dramatica Quad)
  Legacy/skills/novel-architect-scene/**     (scene matrix, Q1-Q5 scene-level
    bridge audit, drafting pre-checks)
  Legacy/tasks/073-hard-rules-validation, 074-anti-patterns,
    075-scene-level-bridge, 084-storyform-integrity-linter,
    085-phase-flow-linters, 086-canon-status-linter,
    087-render-architecture-wiring, 090-render-pipeline
  Legacy/decisions/0010-novel-architect-error-tier-linter-policy.md

DECIDE (grounded in the corpus): which coherence checks are genuinely DECIDABLE
(can be pure transforms / linters with a deterministic pass-fail) vs which are
JUDGEMENT checks (need an LLM/human call). Build the list from what the data
actually supports; cite the source for each classification.

WRITE ONLY inside Plan/decomposition/05-structure-scene-coherence/ :
  DECOMPOSITION.md  — plot-structure primitives, the scene matrix as a data
    structure, the coherence-check catalogue split decidable-vs-judgement, and
    the render pipeline (state -> rendered chapters/scenes on disk).
  PROPOSAL.md       — how this lives in the KP repo: a coherence_check verb
    (decidable subset) + a pre_drafting_gate, the scene-matrix artefacts, and the
    render architecture (graph/NCP state -> Markdown view). Flag the graph-vs-disk
    tension explicitly for the render step.
  OPEN-QUESTIONS.md — decisions needing a human call.

Then open a PR into claude/dreamy-galileo-06exy. Touch nothing outside your dir.
```
