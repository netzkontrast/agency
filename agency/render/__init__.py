"""Spec 032 §H — engine-owned template files.

The 7 templates here power the install pipeline + capability authoring:
- capability-skill.md / verb-reference.md / bash-wrapper.sh / help-index.md
  → Spec 031's per-capability SKILL.md generator
- skill-md.tpl / command-md.tpl / step-doc.md
  → plugin.author_skill / author_command / step_doc

Loaded via `agency.templates._load_render_template(name)` (which uses
`pathlib.Path` + `string.Template`).
"""
