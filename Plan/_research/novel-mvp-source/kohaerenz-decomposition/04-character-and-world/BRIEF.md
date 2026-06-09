# Jules Brief — Slice 4: Character & World Subsystems

- **alias:** `kp-decomp-character-world`
- **work repo (source):** `netzkontrast/kohaerenzprotokoll`
- **starting branch:** `claude/dreamy-galileo-06exy`
- **target dir (write only here):** `Plan/decomposition/04-character-and-world/`
- **goal:** First-principles decomposition of the **character architecture** and
  **world/research** subsystems.

## Dispatch prompt

```
You are decomposing ONE slice of a novel-writing capability for the Kohärenz
Protokoll repo. Work language: English. Never translate German canon prose.

Gates (JULES_PROTOCOL style): Confidence >= 0.90 · evidence = cited paths +
grep hits (TDD N/A) · Self-Review in PR. On a load-bearing ambiguity, call
request_user_input ONCE, then stop.

READ-ONLY clone (learn the plugin contract; never commit it):
  git clone --depth=1 --branch=main https://github.com/netzkontrast/agency.git ~/work/vendor/agency
  Study examples/music.py + agency/{capability,ontology}.py to see how a domain
  adds nodes/edges via OntologyExtension (strict node-merge, widen-only enums).

READ (read-only, in THIS repo):
  Legacy/skills/novel-architect-character/** (TSDP/IFS, Big Five/OCEAN, Enneagram,
    Jung archetypes -> NCP players[], players[].motivations[], .perspectives[])
  Legacy/skills/novel-architect-world/**     (domain mapping, world bible,
    research briefs, delegation to a research-prompt optimizer)

WRITE ONLY inside Plan/decomposition/04-character-and-world/ :
  DECOMPOSITION.md  — the character model (which psychological frameworks are
    load-bearing vs optional, how they map to NCP player fields and to Dramatica
    archetypes/throughlines) and the world model (domain map, world bible,
    research brief lifecycle).
  PROPOSAL.md       — how these live in the KP repo: the cast.md / characters/
    and world/ + research/ on-disk artefacts, which operations become capability
    verbs, and how character/world state relates to NCP (graph node vs rendered
    file — state a recommendation, flag the human decision).
  OPEN-QUESTIONS.md — decisions needing a human call.

Then open a PR into claude/dreamy-galileo-06exy. Touch nothing outside your dir.
```
