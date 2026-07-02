# DOGFOOD-NOTES — {{ plan_slug }}

{# AGENT: This template renders observation Reflections tagged with
the matching `plan_slug` into the canonical DOGFOOD-NOTES.md shape.
The graph IS the store (GOALS.md #7); this file is the rendered view
for humans reading the spec folder. These render-time notes are Jinja
comments (Spec 388) — the engine strips them from the human-facing
output, which used to be a manual regex in dogfood observe. #}

{{ body }}

{# AGENT: After rendering, do NOT auto-commit the file — the caller
decides whether to persist. If you write it to disk, place it at
`Plan/<plan_slug>/DOGFOOD-NOTES.md` so the rendered view sits next to
the spec it documents. #}
