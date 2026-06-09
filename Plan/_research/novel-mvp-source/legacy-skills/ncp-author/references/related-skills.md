# Related Skills

This file documents Michael's existing skill ecosystem that `ncp-author` should cooperate with. The principle is **delegate, don't duplicate**: NCP-mechanics (schema compliance, JSON IO, enum validation) live here; Dramatica-theory reasoning, normative spec authoring, and agentic loop scaffolding live in their respective skills.

When you (the agent running `ncp-author`) hit a question that falls under one of the domains below, prefer to invoke the existing skill rather than improvise.

---

## `dramatica-theory` (user skill)

**Source:** `/mnt/skills/user/dramatica-theory/SKILL.md`
**Language:** EN (theory book is in English)
**Scope:** Apply Dramatica narrative theory (Phillips & Huntley, *Dramatica*, 4th ed., 2001) to story analysis, storyforming, drafting, and draft diagnosis. Models a complete story as one mind solving one problem, viewed through four throughlines (Overall Story, Main Character, Impact Character, Subjective/Relationship), with a structural model of 4 Classes / 16 Types / 64 Variations / 64 Elements selected to form a "storyform". Ships the full source book as nine thematic reference chunks plus an in-skill conceptual overview and storyforming quick-reference.

**Defer to this skill when:**
- The user asks *why* a particular Storyform choice is theoretically right (e.g., "should this be Universe or Mind domain?")
- A draft "feels flat" or "characters feel unmotivated" and you need to diagnose against Dramatica canon
- The user says "dramatica anwenden", "throughlines bestimmen", "story mind", "grand argument story"
- You need to look up archetype definitions (Protagonist, Antagonist, Guardian, Contagonist, Sidekick, Skeptic, Reason, Emotion)

**`ncp-author` provides:** the *target schema slot* (e.g., where Domain goes in `subtext.storypoints[appreciation="Main Character Domain"]`).
**`dramatica-theory` provides:** the *theoretical content* that fills that slot (e.g., why "Psychology" is right for this character).

---

## `dramatica-vocabulary` (user skill)

**Source:** `/mnt/skills/user/dramatica-vocabulary/SKILL.md`
**Language:** DE
**Scope:** Aktive Dramatica-Theorie für Storyform-Aufbau, Encoding und Storyweaving — kein passives Dictionary, sondern Werkzeug. Liefert präzise Definitionen mit Dynamic Pairs, strukturelle Verortung in der Dramatica-Hierarchie (Class → Type → Variation → Element), Encoding-Vorschläge und Konsistenz-Checks gegen die 75 Dynamic Pairs. Indexed terms: 265.

**Defer to this skill when:**
- The user is mid-flow in a German narrative session and a Dramatica term comes up
- You need a Dynamic Pair check (e.g., "ist 'Truth' das richtige Element für Knowledge-Quad an dieser Stelle?")
- Encoding-Übersetzung gefragt: "wie wird 'Symptom' aus der Storyform in eine konkrete Szene?"
- Konsistenz-Audit eines schon befüllten Storyforms gegen die 75 Dynamic Pairs

**`ncp-author` provides:** the canonical enum (144 narrative_functions in the schema).
**`dramatica-vocabulary` provides:** the Dynamic Pair logic (which Elements pair, where they sit in the KTAD matrix).

This is the **most direct collaborator** for `ncp-author`. The two skills are complementary by design: `ncp-author` enforces NCP-compliance at the JSON level; `dramatica-vocabulary` enforces Dramatica-correctness at the meaning level.

---

## `spec-skill` (user skill)

**Source:** `/mnt/skills/user/spec-skill/SKILL.md`
**Language:** EN
**Scope:** Authoring, applying, and auditing normative specifications for autonomous AI agents and long-horizon agentic workflows — using RFC-2119 keywords, Gherkin acceptance criteria, and a fixed five-aspect schema (Explore, Plan, Implement, Review, Validate).

**Why this matters here:** `SPEC.md` in this skill was generated via `spec-skill` workflow (per its document metadata, "Conformance Level: High (RFC 2119 / BCP 14)"). When SPEC.md needs revision, audit, or extension, route through `spec-skill` to keep RFC-2119 / BCP-14 compliance intact.

**Defer to this skill when:**
- Updating SPEC.md (especially adding new normative requirements)
- Auditing SPEC.md for "MUST"/"SHOULD"/"MAY" misuse
- Generating prompts/workflows derived from SPEC.md sections

---

## `ralph-skill` (user skill)

**Source:** `/mnt/skills/user/ralph-skill/SKILL.md`
**Language:** EN
**Scope:** Generate Ralph agentic-loop files (loop.sh, PROMPT_build.md, PROMPT_plan.md, AGENTS.md, IMPLEMENTATION_PLAN.md), customize or extend an existing Ralph workflow, audit a Ralph setup for playbook compliance, or convert research-prompt-optimizer output into Ralph specs and an implementation plan.

**Why this matters here:** SPEC.md §7 ("Autonomous hand-off via NCP-state") is essentially a description of a Ralph-style loop — agents poll status, react to file changes, write back. If/when SPEC.md gets implemented as an actual running loop (rather than a skill catalog inside a single chat session), `ralph-skill` is the bridge from SPEC to runnable artifacts.

**Defer to this skill when:**
- Converting any phase of SPEC.md into a runnable Ralph loop
- Producing a `loop.sh` + `PROMPT_*.md` set for a specific NCP authoring phase (storyform, outline, draft)
- Cross-agent portability work (Claude Code ↔ Gemini Jules) — SPEC.md §9 is exactly the territory `ralph-skill` covers

---

## `research-prompt-optimizer` (user skill)

**Source:** `/mnt/skills/user/research-prompt-optimizer/SKILL.md`
**Language:** EN/DE bilingual
**Scope:** Generate, optimize, audit, version, or architect a Deep Research prompt for any autonomous research system (Gemini Deep Research, Perplexity, Claude Research, GPT Deep Research, custom agentic pipelines). Five-phase pipeline — intent capture, planning across three approval gates, Python rendering of a self-contained Markdown research prompt, opt-in fresh-frame reader-test audit, workspace finalize step.

**Why this matters here:** SPEC.md was originally produced via this skill (per metadata: "Source Skill: research-prompt-optimizer v2.1.0"). When upstream NCP changes (new schema versions, new Dramatica research) trigger a SPEC.md update cycle, you may want to re-run a research pass to keep references current.

---

## `memory-sync` (user skill)

**Source:** `/mnt/skills/user/memory-sync/SKILL.md`
**Language:** EN
**Scope:** Manage Claude's 13-slot memory at session end or whenever a canon decision is made. Originally for the Kohärenz Protokoll novel project; the pattern generalizes.

**Why this matters here:** If `ncp-author` becomes a long-running collaboration (as the SPEC envisions), the canon decisions made during NCP authoring (chosen Storyform, locked archetypes, resolved Open Questions per §12) need to land in memory. Use this skill at the end of substantive NCP authoring sessions.

---

## Skills NOT in scope (mentioned for completeness)

- **`the-agency-system-architect`** — Album-triptych orchestrator, Suno-focused. Out of scope for `ncp-author`.
- **`suno-lyric-writer`** — Lyric drafting + Suno tag engineering. Out of scope.
- **`notebooklm-prompt-architect`** — NotebookLM podcast persona prompts. Out of scope.
- **`gdrive-notion-curator`**, **`drive-markdown-converter`**, **`pdf-to-markdown`** — File/IO utility skills. Out of scope unless an NCP project happens to source from Drive/Notion documents (in which case they're called separately, not from inside `ncp-author`).
- **`prompt-optimizer`** — Initial-prompt rewriter. Acts at session start, not during NCP authoring.

---

## `novel-architect` (user skill)

**Source:** `/mnt/skills/user/novel-architect/SKILL.md`
**Language:** DE
**Status:** WIP at the time of writing (`0.1.0-wip`, blocked on OQ-01/02/03 per its frontmatter)
**Scope:** Roman-Entwicklungs-Pipeline für das *Kohärenz Protokoll*. Dual-Agent: Gemini als Archivist/Analyst (Research-Ingestion, 1M-Kontext, Widerspruchs-Analyse), Claude als Orchestrator/Writer (Interview, Kanon-Entscheide, Entwurf, Revision). Phasen: `/analyze`, `/interview`, `/synthesize`, `/draft`. Kanonische Drive-Dokumente: `CANON_STATE.md`, `OPEN_QUESTIONS.md`, `SESSION_HISTORY.md`.

**Relationship to `ncp-author`:** Orchestrator → backend. `novel-architect` owns the *creative* state (kanonische Wahrheiten, blockierende Open Questions, Session-History, POV-Schutz). When `novel-architect` needs to read or write *structured narrative intent* — a Storyform, archetype slot list, throughline-level Storypoints, signpost-level Storybeats — it should call `ncp-author` rather than re-invent JSON wrangling.

**Defer to this skill when:**
- The user mentions Kohärenz Protokoll, CANON_STATE, OPEN_QUESTIONS, AEGIS, Kael, Juna, or any Alter from that novel
- The user asks for `/analyze`, `/interview`, `/synthesize`, or `/draft` (these are `novel-architect`'s phase commands, not `ncp-author`'s)
- The work is novel-prose-adjacent: chapter scaffolding, scene-level Storyweaving, prose-style canon enforcement
- Open Questions need to be raised, tracked, or closed against canon

**`ncp-author` provides:** the JSON file format, the schema, the canonical enums, the validator, and the templates that `novel-architect` writes its Storyform into.
**`novel-architect` provides:** the project-specific creative governance (which decisions are locked, which are open, who's the orchestrator vs. archivist, which prose constraints apply).

**Wiring direction (recommended):** `novel-architect`'s `/synthesize` phase, when it touches Storyform or Storypoint state, should treat the file as an NCP document and route through `ncp-author` for IO + validation. Reciprocally, `ncp-author` should not duplicate `novel-architect`'s Open-Questions or canon-locking discipline; if a session is novel-shaped, route there. See `TODO.md` T-7 for the open wiring patch on the `novel-architect` side.
