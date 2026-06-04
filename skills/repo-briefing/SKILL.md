---
name: repo-briefing
description: Use when you need to understand a repo's structure without loading the whole thing into context — for onboarding to an unfamiliar codebase, generating a PROJECT_INDEX, or refreshing your mental model of a tree you haven't touched in weeks. Walks the 4-phase scope → scan → render → publish chain.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Repo briefing (4-phase, hard publish gate)

## When to use

- New codebase onboarding: you want a 3K-token map instead of reading
  50K of source.
- Returning to a project after weeks away: refresh the mental model
  fast.
- Before requesting a code review: ship the PROJECT_INDEX so reviewers
  have orientation without re-deriving it.
- Pre-flight for `document.explain deep`: the briefing tells you which
  modules are worth deep-explaining.

DON'T use when:
- You ALREADY have the repo in context (S9:context_overlap fires;
  dispatch_decision will recommend inline).
- You want LLM-generated prose summary (this is deterministic
  composition; LLM is your choice externally).
- The repo is single-file (briefing overhead exceeds benefit).

## The chain (4 phases — walk `document.ontology.skills["repo-briefing"]`)

```
1. scope    →  path, max_tokens (default 3000)
2. scan     →  index_id, tokens          (document.index_repo)
3. render   →  content                   (the rendered markdown body)
4. publish  →  written                   (HARD GATE — apply=True writes file)
```

The hard gate at phase 4 protects the working tree. Files are written
only after explicit approval; the index_id + content from phase 2 stays
in the graph regardless.

## How to call

```python
# 1) Plan and scan.
r = await call_tool('capability_document_index_repo', {
    'intent_id': iid, 'path': '.', 'apply': False, 'max_tokens': 3000})
# r → {index_id, content, tokens, files_scanned, writeup}

# 2) Review the content.
print(r['content'])

# 3) Publish (writes PROJECT_INDEX.md).
r = await call_tool('capability_document_index_repo', {
    'intent_id': iid, 'path': '.', 'apply': True})
```

## What the briefing contains

A deterministic six-section markdown:

- **Substrate** — language, package config, test runner.
- **Macro-structure** — every package, file count, first-sentence brief
  per module.
- **Entry points** — `[project.scripts]` from pyproject.toml.
- **Notable patterns** — agency markers (capability folders, plugin
  manifest, MCP config, Plan/ doctrine).
- **Recent activity** — newest 5 Reflections (technical / project).

NO LLM. The "synthesis" is the arrangement of brief slices that
Spec 023 already pinned on every module.

## Token budget enforcement

`max_tokens` is hard-capped:
1. Mid-loop truncation when the macro-structure section crosses ~92%
   of budget → emits `_… (N modules omitted)_`.
2. End-of-render truncation if the substrate / entry-points / recent
   activity sections still tip the total over → tail-trim with `_…
   (content omitted to fit token budget)_`.

The cl100k token count is recorded on the RepoIndex node alongside the
content_sha — agency_doctor and provenance render show the actual
budget consumed.

## Dispatch decision integration

For repos > 50 files the verb's `index_repo` work is heavy (Spec 040
S1:tokens fires). When called from inside a long session with the repo
already in parent context, S10:cache_warmth fires and dispatch_decision
recommends inline. See
[`skills/dispatch-decision/SKILL.md`](../dispatch-decision/SKILL.md).

## References

- [`references/template-shapes.md`](references/template-shapes.md) —
  the six-section schema + token-budget enforcement details.
