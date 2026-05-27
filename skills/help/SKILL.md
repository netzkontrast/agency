---
name: help
description: Use when you need to discover the agency engine's capabilities (macroskills) and their verbs (the micro-skills).
allowed-tools:
  - Read
  - Write
  - Edit
---

# help

# agency — capabilities (macroskills) and their verbs (micro-skills)

- **branch** — assess, finish
- **delegate** — fan_out, join
- **develop** — checklist, reference
- **gate** — check
- **jules** — activities, approve_plan, dispatch, list, message, plan, status, stop, verify
- **plugin** — author_command, author_skill, help, lint_skill, marketplace_entry, scaffold, step_doc
- **reflect** — note, recall, search
- **skill_generator** — generate
- **subagent** — develop
- **workspace** — baseline, isolate

## Discovery

There is no separate 'remember to use the skill' layer — discovery IS the contract:

- `search` finds a capability/verb or a discipline by symptom;
- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);
- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).

Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until
confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's
heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS
the recorded walk, so there is nothing extra to remember.

