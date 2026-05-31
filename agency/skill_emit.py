"""Spec 031 §D + Spec 032 §G — per-capability skill emission pipeline.

Public surface:
  emit_skill(cap_name, doc, verbs) -> {path: content}
    — renders skills/<cap_name>/SKILL.md from a SkillDoc + verb registry
    — runs plugin.lint_skill_doc PRE-emit (block mode)
    — Tier A verbs (with Inputs:/Returns:/chain_next: markers) link to
      references/<verb>.md
    — Tier B verbs (missing markers) link to #<verb> anchor in SKILL.md
      and append a `## <verb>` section at the bottom

Helpers:
  _classify_tier(verb_fn) -> "A" | "B"  (per Spec 031 §5 Gherkin)

emit_references and emit_bash_wrappers land in Task 2.2 and 2.3.
The capability hash (cache invalidation key) lands in Task 2.4 (cache.py).
"""
from __future__ import annotations

import inspect
from pathlib import Path
from string import Template


# Spec 031 generator version (bumped when template shape changes).
GEN_VERSION = 1

# Resolve the engine-owned template once at import.
_RENDER_DIR = Path(__file__).parent / "render"
_CAPABILITY_SKILL_TEMPLATE = Template(
    (_RENDER_DIR / "capability-skill.md").read_text()
)


def _classify_tier(verb_fn) -> str:
    """Tier A iff all three Spec 016 structural markers present + non-empty
    (terminal chain_next counts as A per §5 Gherkin). Else Tier B."""
    doc = (verb_fn.__doc__ or "")
    from agency.disclosure import parse_slices
    slices = parse_slices(doc)
    inputs = slices.get("inputs", "").strip()
    returns = slices.get("returns", "").strip()
    chain_next = slices.get("chain_next", "").strip()
    if not inputs or not returns or not chain_next:
        return "B"
    return "A"


def _first_sentence_brief(fn) -> str:
    """Get the first-sentence brief from a verb function's docstring."""
    if not fn or not fn.__doc__:
        return "(no docstring)"
    from agency.disclosure import parse_slices
    return parse_slices(fn.__doc__)["brief"] or "(no brief)"


def _render_tier_b_anchor(verb_name: str, fn, brief: str) -> str:
    """Render a `## <verb>` section for a Tier B verb (no separate reference file)."""
    sig = "()"
    if fn:
        try:
            sig = str(inspect.signature(fn))
        except (TypeError, ValueError):
            sig = "()"
    return (
        f"## {verb_name}\n\n"
        f"{brief}\n\n"
        f"Parameters: `{sig}`.\n\n"
        f"_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: "
        f"markers; reference is in-skill only. Add markers to upgrade to a "
        f"separate references/{verb_name}.md.)_"
    )


def emit_skill(cap_name: str, doc, verbs: dict) -> dict[str, str]:
    """Render skills/<cap_name>/SKILL.md from the SkillDoc + verb registry.

    Returns {path: content} dict. Runs plugin.lint_skill_doc PRE-emit;
    raises ValueError with structured violations on failure.
    """
    from agency.capabilities.plugin import lint_skill_doc

    # PRE-emit lint (panel — no bad file ever lands on disk)
    lint = lint_skill_doc(cap_name, doc, verbs)
    if not lint["ok"]:
        msgs = "; ".join(f"{v['rule']}: {v['message']}"
                         for v in lint["violations"])
        raise ValueError(
            f"emit_skill({cap_name!r}): SkillDoc lint failed — {msgs}"
        )

    # Verb table (Tier A linked; Tier B anchored)
    table_rows: list[str] = []
    tier_b_anchors: list[str] = []
    for verb_name in sorted(verbs):
        spec = verbs[verb_name]
        fn = spec.get("fn")
        role = spec.get("role", "?")
        brief = (doc.verb_briefs or {}).get(verb_name) or _first_sentence_brief(fn)
        tier = _classify_tier(fn) if fn else "B"
        if tier == "A":
            link = f"[details](references/{verb_name}.md)"
        else:
            link = f"[details](#{verb_name})"
            tier_b_anchors.append(_render_tier_b_anchor(verb_name, fn, brief))
        table_rows.append(f"| `{verb_name}` | {role} | {brief} | {link} |")

    # Render the template
    required_subskills_block = ""
    if doc.required_subskills:
        required_subskills_block = (
            "\n## Required sub-skills\n\n" +
            "\n".join(f"- **REQUIRED SUB-SKILL:** {s}"
                     for s in doc.required_subskills)
        )

    rendered = _CAPABILITY_SKILL_TEMPLATE.substitute(
        gen_version=str(GEN_VERSION),
        cap_name=cap_name,
        description=doc.description,
        overview=doc.overview,
        triggers_bulleted="\n".join(f"- {t}" for t in doc.triggers),
        verb_table="\n".join(table_rows),
        canonical_example=doc.canonical_example,
        red_flags_bulleted=("\n".join(f"- {r}" for r in (doc.red_flags or []))
                            or "- (none documented)"),
        required_subskills_block=required_subskills_block,
    )

    if tier_b_anchors:
        rendered = rendered.rstrip() + "\n\n" + "\n\n".join(tier_b_anchors) + "\n"

    return {f"skills/{cap_name}/SKILL.md": rendered}
