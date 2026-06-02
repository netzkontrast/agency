# Template shapes — PROJECT_INDEX.md schema

The briefing's structure is fixed. Changing it is a Spec 043
amendment, not a runtime decision.

## The six sections

```
# Project Index — <repo name>

## Substrate
- language: <python | …>
- package_config: <pyproject.toml | setup.cfg | …>
- test_runner: <pytest (pytest.ini) | pytest (inferred) | …>

## Macro-structure

### `<dir>/` (<N> files)
- **<file.py>** — <first-sentence brief slice>
- **<file.py>** — <…>

### `<other_dir>/` (<N> files)
- …

## Entry points
- `<name> = <ref>` (from [project.scripts])
- …

## Notable patterns
- agency-style capability folder pattern
- Claude Code plugin manifest (.claude-plugin/)
- MCP server config (.mcp.json)
- skills/<name>/SKILL.md disclosure pattern
- Plan/NNN-slug/spec.md doctrine

## Recent activity
- `<scope>` · <text truncated to 120 chars>
- …
```

## Source of each section

| Section | Source | Determinism |
|---|---|---|
| Substrate | os.path.isfile checks | full |
| Macro-structure | walk `*.py`; ast.parse → module docstring → first sentence | full |
| Entry points | pyproject.toml `[project.scripts]` lines | full |
| Notable patterns | os.path.isdir / isfile sentinels | full |
| Recent activity | memory.find("Reflection") filtered + sorted | full (graph state) |

## Token-budget enforcement

Two-stage truncation:

1. **Mid-macro-structure** — after rendering each `### \`<dir>/\``
   section, check `_count_tokens(rendered_so_far)` against
   `max_tokens * 0.92`. If over → append `_… (N modules omitted to fit
   token budget)_` and break.

2. **Post-full-render** — if Substrate / Entry / Notable / Recent
   pushed the total over `max_tokens` after the macro section settled
   under budget → tail-trim to `max_tokens * 4` chars (cl100k average)
   minus a 40-char marker, append `_… (content omitted to fit token
   budget)_`.

The token count returned to the caller is the FINAL count after
truncation; the `content_sha` on the RepoIndex node is over the
truncated content (so caching is deterministic per-budget).

## What ISN'T in the briefing

- File contents beyond the module docstring's first sentence.
- Per-symbol signatures (`document.explain` is the verb for that).
- Test results / coverage stats (out of scope for v1).
- Git history (out of scope for v1).
- LLM-generated synopses (NEVER — the structure IS the synthesis).

## Customisation surface (v1: none)

`max_tokens` is the only knob. All other rendering decisions are
spec-pinned. Custom briefing shapes are a v2 conversation.
