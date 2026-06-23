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

import hashlib
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
_VERB_REFERENCE_TEMPLATE = Template(
    (_RENDER_DIR / "verb-reference.md").read_text()
)
_BASH_WRAPPER_TEMPLATE = Template(
    (_RENDER_DIR / "bash-wrapper.sh").read_text()
)
_VERB_RULES_TEMPLATE = Template(
    (_RENDER_DIR / "verb-rules.md").read_text()
)
# Spec 373 Slice 1 / Spec 375 — per-type skill HEAD templates (frontmatter +
# `# <Title> <type>` heading). One file per `Skill.type` under `render/skill/`; the
# self-contained data body (`_skill_data_sections`) is concatenated after the head
# (NOT substituted, so a literal `$` in an example never breaks the render). The
# renderer (`render_typed_skill`) selects by type — the per-type template set that
# replaces a single generic shape (the C2 coherence convergence in Spec 370).
# AGENCY-DRIFT: skill-type-templates — one render/skill/<type>.md per Skill.type.
_SKILL_TYPE_TEMPLATES = {
    t: Template((_RENDER_DIR / "skill" / f"{t}.md").read_text())
    for t in ("pillar", "capability", "discipline")
}
_PILLAR_SKILL_TEMPLATE = _SKILL_TYPE_TEMPLATES["pillar"]   # back-compat alias

# Engine-injected params: these are NOT user-facing args in the wrapper.
_INJECTED_PARAMS = frozenset({"ctx", "client", "vcs", "memory", "caps"})


def _ann_repr(annotation) -> str:
    """Render an inspect.Parameter annotation as a Python expression the
    bash wrapper's embedded code can evaluate at call time.

    `int`, `bool`, `float`, `str` → bare class name (assumes the wrapper
    imports them — `__builtins__` always has these). Container types
    (`list`, `dict`, `list[str]`, `dict[str, int]`) → ``list`` / ``dict``
    because runtime coercion only needs the top-level container.
    Anything else (missing annotation, callable, …) → ``str`` (the
    raw argv string is safe — verbs decide how to handle).

    Spec 060 round 9 — when the verb's module uses ``from __future__
    import annotations``, inspect.signature returns the annotation as a
    string (`'int'`, `'list[str]'`, …) instead of the type object. Match
    those string forms before falling through to the runtime-type path.

    Spec 150 Slice 2 review (round 2): unwrap ``Optional[X]`` /
    ``X | None`` (Union with a single non-None member) to ``X``. Without
    this, a verb param like ``host_completion: dict | None = None``
    falls through to ``str``, and the bash wrapper coerces the JSON
    payload to a string — breaking Spec 279 resume from the CLI surface.
    """
    if annotation is inspect.Parameter.empty:
        return "str"
    # Postponed-annotation string form: peel the typing-parametrised
    # decoration and match on the bare head. Also recognise the
    # ``"X | None"`` Optional shorthand (PEP 604 postponed).
    if isinstance(annotation, str):
        # Strip ``| None`` / ``None |`` from postponed-form unions so
        # ``"dict | None"`` becomes ``"dict"``.
        head = annotation.strip()
        for trailer in (" | None", "|None"):
            if head.endswith(trailer):
                head = head[: -len(trailer)].strip()
        for leader in ("None | ", "None|"):
            if head.startswith(leader):
                head = head[len(leader):].strip()
        head = head.split("[", 1)[0].strip()
        if head in ("int", "bool", "float", "str", "list", "dict"):
            return head
        return "str"
    # Union / Optional types — pick the single non-None member.
    import types as _types
    import typing as _typing
    origin = _typing.get_origin(annotation)
    if origin is _typing.Union or (
            hasattr(_types, "UnionType") and origin is _types.UnionType):
        non_none = [a for a in _typing.get_args(annotation)
                    if a is not type(None)]
        if len(non_none) == 1:
            return _ann_repr(non_none[0])
        return "str"
    # Strip the typing module's parametrised form: list[str] → list.
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        return "list"
    if origin is dict:
        return "dict"
    if annotation in (int, bool, float, str, list, dict):
        return annotation.__name__
    return "str"


def _skill_name(cap_name: str) -> str:
    """The spec-legal Agent Skill name for a capability (Spec 080). The Anthropic
    Agent Skills spec requires the `name` to be lowercase letters/digits/HYPHENS
    (no underscores), so a capability whose registry name has an underscore (e.g.
    ``skill_generator``) emits as ``skill-generator`` — for both the frontmatter
    `name:` field AND the skill directory, so the emitted skill is spec-faithful."""
    return cap_name.replace("_", "-")


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
    """Render a `## <verb>` in-skill section for a verb without a separate
    reference file. Spec 373 Slice 3: the apologetic ``_(Tier B…)_`` stub no
    longer ships to disk — a verb missing the Spec 016 Inputs:/Returns:/chain_next:
    markers is surfaced as a LINT finding (Spec 377 ``lint_skill_schema``), not as
    self-deprecating prose in the published skill. The section still carries the
    brief + signature so the verb stays documented in-skill."""
    sig = "()"
    if fn:
        try:
            sig = str(inspect.signature(fn))
        except (TypeError, ValueError):
            sig = "()"
    return (
        f"## {verb_name}\n\n"
        f"{brief}\n\n"
        f"Parameters: `{sig}`."
    )


def _render_phase_detail(sk: dict) -> str:
    """Spec 372/373 — render a skill's phases' inline TEACHING content
    (`goal`/`instructions` from the single source) beneath its walk row, so the
    file is self-contained (A1) and the rendered content equals what the walk
    surfaces (372 parity — one source, two surfaces).

    Returns "" when no phase authored inline content, so legacy disciplines
    (phase name only) render byte-identically. Deterministic: same schema ⇒
    same bytes (A7)."""
    phases = sk.get("phases", [])
    if not any(p.get("goal") or p.get("instructions") for p in phases):
        return ""
    lines = []
    for n, p in enumerate(phases, start=1):
        head = f"  {n}. **{p.get('name', '?')}**"
        if p.get("goal"):
            head += f" — {p['goal']}"
        lines.append(head)
        if p.get("instructions"):
            lines.append(f"     {p['instructions']}")
    return "\n" + "\n".join(lines)


def _render_walk_section(skills: dict) -> str:
    """Spec 081 — render the '## Walk this capability' section from the cap's
    ontology.skills (derived `<cap>-usage` or authored disciplines). Lists each
    walkable skill, its phase chain, and the develop.skill_walk invocation.

    Spec 372/373 — a discipline whose phases carry inline content renders that
    content inline (`_render_phase_detail`) so a reader gets the same
    instructions a walking agent does (walk↔file parity)."""
    if not skills:
        return ""
    rows = []
    for name in sorted(skills):
        sk = skills[name]
        phases = " → ".join(p.get("name", "?") for p in sk.get("phases", []))
        rows.append(f"- **`{name}`** ({sk.get('kind', 'skill')}): {phases}\n"
                    f"  — walk it: `await call_tool('capability_develop_skill_walk', "
                    f"{{'name': '{name}', 'inputs': {{}}, 'intent_id': '…'}})`"
                    + _render_phase_detail(sk))
    return ("\n## Walk this capability\n\n"
            "Drive this capability's verbs by WALKING a skill one phase at a time "
            "(progressive disclosure, recorded as provenance):\n\n"
            + "\n".join(rows) + "\n")


def _selector_description(doc) -> str:
    """The frontmatter ``description`` Claude Code shows in the skill selector.

    **Trigger-first** ("Use when …"), per SKILL-CONTRACT.md §1 (Spec 023/029 +
    Anthropic's CSO rule, enforced by ``plugin.lint_skill``): the description
    MUST start with "Use when …" and MUST NOT lead with a workflow summary
    (``description-no-workflow-summary``). A well-written trigger description
    already conveys WHAT the skill does via the activities it names — so the
    selector paragraph is informative without violating the contract. WHAT-it-
    does prose lives in the SKILL.md body (the overview), not the description."""
    return (doc.description or "").strip()


def _yaml_quote(s: str) -> str:
    """Double-quote a YAML scalar so a colon / '#' / special char in the value
    (now possible since the description leads with the overview prose) can't
    break frontmatter parsing."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _skill_data_sections(skill: dict) -> str:
    """The v2 Skill's self-contained DATA body — overview + when-to-use/when-not +
    the one example + the common-mistakes rationalization table + references —
    shared by every per-type render (`render_typed_skill`) and the capability-
    augment path. No frontmatter, no H1. Sections are appended only when the source
    carries them (frugal; no empty headers), so the render is deterministic (A7)
    and self-contained (A1). Type-agnostic: reads the v2 Skill schema fields, so a
    pillar / capability / discipline all body-render through this one function."""
    parts: list[str] = []
    overview = (skill.get("overview") or "").strip()
    if overview:
        parts.append(overview)
    when_to_use = (skill.get("when_to_use") or "").strip()
    if when_to_use:
        parts.append(f"## When to use\n\n{when_to_use}")
    when_not = (skill.get("when_not") or "").strip()
    if when_not:
        parts.append(f"## When not to use\n\n{when_not}")
    examples = skill.get("examples") or []
    if examples:
        ex_blocks = []
        for ex in examples:
            inp = (ex.get("input") or "").strip()
            out = (ex.get("output") or "").strip()
            ex_blocks.append(f"```python\n{inp}\n```\n\n{out}".rstrip())
        parts.append("## Example\n\n" + "\n\n".join(ex_blocks))
    mistakes = skill.get("common_mistakes") or []
    if mistakes:
        rows = "\n".join(f"| {m.get('symptom', '')} | {m.get('counter', '')} |"
                         for m in mistakes)
        parts.append("## Common mistakes\n\n| Symptom | Counter |\n|---|---|\n" + rows)
    refs = skill.get("references") or []
    if refs:
        ref_lines = "\n".join(
            f"- [{r.get('title') or r.get('path')}]({r.get('path')})" for r in refs)
        parts.append("## References\n\n" + ref_lines)
    return "\n\n".join(parts)


# Back-compat alias — `_pillar_sections` was the pre-373 name (the body renderer
# started pillar-only; it is now the type-agnostic v2-Skill data renderer).
_pillar_sections = _skill_data_sections


def render_typed_skill(skill: dict) -> dict[str, str]:
    """Spec 373 Slice 1 — the per-type skill renderer: render any v2 `Skill`
    (`type` ∈ pillar|capability|discipline) self-contained (A1) to
    `skills/<name>/SKILL.md` via its `render/skill/<type>.md` HEAD template + the
    schema-driven data body (`_skill_data_sections`).

    The body inlines whatever the Skill carries — overview, when-to-use/when-not,
    the one example (R9), the common-mistakes rationalization table, references
    one-deep (R4) — appended (NOT substituted), so a literal ``$`` in an example
    never breaks the render. Deterministic (A7): same `skill` dict ⇒ byte-identical
    output. Unknown/absent type → the capability template (the general case).
    The description is the AUTHORED `description` field — never sentence-truncated."""
    name = _skill_name(skill["name"])
    stype = skill.get("type") or "capability"
    template = _SKILL_TYPE_TEMPLATES.get(stype, _SKILL_TYPE_TEMPLATES["capability"])
    head = template.substitute(
        gen_version=str(GEN_VERSION),
        name=name,
        title=str(skill["name"]).capitalize(),
        description=_yaml_quote((skill.get("description") or "").strip()),
    )
    content = head.rstrip() + "\n\n" + _skill_data_sections(skill) + "\n"
    return {f"skills/{name}/SKILL.md": content}


def render_pillar(skill: dict) -> dict[str, str]:
    """Spec 375 — render a committed pillar `skill.yaml` (type=pillar) standalone
    to `skills/<name>/SKILL.md`. Thin wrapper over the per-type renderer
    (`render_typed_skill`, Spec 373) — pillars converge onto the ONE renderer so
    there is no second render path (the C2 coherence convergence). Used for pillars
    whose name does not collide with a live capability (lifecycle · memory); a
    colliding pillar (intent) augments the cap skill via `augment_with_pillar`."""
    return render_typed_skill({**skill, "type": "pillar"})


def augment_with_pillar(existing_md: str, skill: dict) -> str:
    """Spec 375 — append a pillar's concept section to a capability SKILL.md that
    already owns the pillar's name (the `intent` concept rides the `intent`
    capability skill rather than clobbering it). Adds the concept overview under a
    distinct `## The <Title> pillar (concept)` H2 so the capability's own verb
    table / sections stay intact. Deterministic (A7)."""
    title = str(skill["name"]).capitalize()
    overview = (skill.get("overview") or "").strip()
    section = f"## The {title} pillar (concept)\n\n{overview}"
    return existing_md.rstrip() + "\n\n" + section + "\n"


def emit_skill(cap_name: str, doc, verbs: dict, skills: dict | None = None) -> dict[str, str]:
    """Render skills/<cap_name>/SKILL.md from the SkillDoc + verb registry.

    Returns {path: content} dict. Runs plugin.lint_skill_doc PRE-emit;
    raises ValueError with structured violations on failure. `skills` (Spec 081 —
    the cap's ontology.skills) renders a '## Walk this capability' section.
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
        cap_name=_skill_name(cap_name),                 # Spec 080 — spec-legal name (hyphens)
        description=_yaml_quote(_selector_description(doc)),
        overview=doc.overview,
        triggers_bulleted="\n".join(f"- {t}" for t in doc.triggers),
        verb_table="\n".join(table_rows),
        canonical_example=doc.canonical_example,
        red_flags_bulleted=("\n".join(f"- {r}" for r in (doc.red_flags or []))
                            or "- (none documented)"),
        required_subskills_block=required_subskills_block,
    )

    walk = _render_walk_section(skills or {})
    if walk:
        rendered = rendered.rstrip() + "\n" + walk

    if tier_b_anchors:
        rendered = rendered.rstrip() + "\n\n" + "\n\n".join(tier_b_anchors) + "\n"

    return {f"skills/{_skill_name(cap_name)}/SKILL.md": rendered}


def _render_inputs_table(inputs_text: str) -> str:
    """Render the inputs block (parse_slices output) as a markdown table.

    Input format: lines like `- name (type): description` OR `name (type)` OR
    just `name`. Defensive against malformed entries.
    """
    if not inputs_text or not inputs_text.strip():
        return "(no inputs)"
    rows = ["| Param | Type | Description |", "|-------|------|-------------|"]
    for raw_line in inputs_text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip leading '- ' or '* '
        if line.startswith(("- ", "* ")):
            line = line[2:]
        # Try: name (type): description
        param = line
        type_ = ""
        desc = ""
        if ":" in line:
            head, _, desc = line.partition(":")
            desc = desc.strip()
            line = head.strip()
            # `line` now is "name (type)" or "name"
            if "(" in line and line.endswith(")"):
                p, _, t = line.partition("(")
                param = p.strip()
                type_ = t.rstrip(")").strip()
            else:
                param = line
        else:
            # No colon — try "name (type)" form
            if "(" in line and line.endswith(")"):
                p, _, t = line.partition("(")
                param = p.strip()
                type_ = t.rstrip(")").strip()
            else:
                param = line
        rows.append(f"| `{param}` | {type_} | {desc} |")
    return "\n".join(rows) if len(rows) > 2 else "(no inputs)"


def emit_references(cap_name: str, verbs: dict) -> dict[str, str]:
    """Render per-verb reference files for Tier-A verbs of one capability.

    For every Tier-A verb (parse_slices returns non-empty inputs/returns/
    chain_next), emit:
      skills/<cap_name>/references/<verb_name>.md

    Each file content is rendered from agency/render/verb-reference.md template
    populated with the verb's parsed docstring slices.

    Tier-B verbs (missing markers) DO NOT produce a reference file — they
    live as anchors inside SKILL.md (handled by emit_skill).

    Inputs:
      - cap_name: capability name (becomes the path prefix)
      - verbs: {verb_name: {role, fn, inject}}
    Returns: {path: content} dict; empty if no Tier-A verbs in the capability.
    chain_next: pass to install.write() alongside the skill output.
    """
    from agency.disclosure import parse_slices

    out: dict[str, str] = {}
    for verb_name in sorted(verbs):
        spec = verbs[verb_name]
        fn = spec.get("fn")
        if fn is None or _classify_tier(fn) != "A":
            continue

        doc = fn.__doc__ or ""
        slices = parse_slices(doc)

        rendered = _VERB_REFERENCE_TEMPLATE.substitute(
            gen_version=str(GEN_VERSION),
            verb_full_name=f"{cap_name}.{verb_name}",
            brief=slices.get("brief", "").strip() or "(no brief)",
            inputs_table=_render_inputs_table(slices.get("inputs", "")),
            returns=slices.get("returns", "").strip() or "(none documented)",
            chain_next=slices.get("chain_next", "").strip() or "(terminal)",
            body=slices.get("body", "").strip() or "(no further detail)",
            bash_example=(
                f"agency-{cap_name}-{verb_name} --intent-id $IID …"
            ),
        )
        out[f"skills/{_skill_name(cap_name)}/references/{verb_name}.md"] = rendered
    return out


def verb_tool_desc_flags(verbs: dict) -> list[tuple[str, str, list[str]]]:
    """Audit each verb's docstring against the ``tool-desc`` functional profile
    (Spec 306). Returns ``[(verb_name, role, flags), …]`` sorted by name — the
    shared backbone of the per-capability ``verb-rules.md`` block AND the
    repo-wide ``scripts/optimize-verb-docs`` sweep, so both agree on what 'needs
    work' means."""
    from agency.capabilities.prompt.clusters._profiles import tool_desc_profile
    out: list[tuple[str, str, list[str]]] = []
    for verb_name in sorted(verbs):
        spec = verbs[verb_name]
        fn = spec.get("fn")
        role = spec.get("role", "?")
        doc = (fn.__doc__ or "") if fn else ""
        _scores, flags = tool_desc_profile(doc)
        out.append((verb_name, role, flags))
    return out


def emit_verb_rules(cap_name: str, verbs: dict) -> dict[str, str]:
    """Render skills/<cap>/references/verb-rules.md — the per-capability
    verb-description rules block (Spec 306).

    Pairs the ``tool-desc`` grammar with THIS capability's verbs audited against
    it (which still lack a routing signal / failure mode / inputs / chain_next),
    so an author sees the rules and the gaps in one place. The full rules live in
    the prompt cap's ``references/tool-desc-authoring.md``.

    Inputs: cap_name (str), verbs ({verb_name: {role, fn}}).
    Returns: {path: content} — one verb-rules.md for the capability.
    chain_next: emit alongside emit_skill / emit_references in install.generate.
    """
    rows = []
    flagged = 0
    for verb_name, role, flags in verb_tool_desc_flags(verbs):
        if flags:
            flagged += 1
            status = ", ".join(f"`{f}`" for f in flags)
        else:
            status = "✓ clean"
        rows.append(f"| `{cap_name}.{verb_name}` | {role} | {status} |")
    content = _VERB_RULES_TEMPLATE.substitute(
        gen_version=str(GEN_VERSION),
        cap_name=_skill_name(cap_name),
        verb_count=len(verbs),
        flagged=flagged,
        verb_audit="\n".join(rows) or "| (no verbs) | | |",
    )
    return {f"skills/{_skill_name(cap_name)}/references/verb-rules.md": content}


def _user_params(fn, inject_list: list) -> list[str]:
    """Return the verb's user-facing parameter names (excluding engine injects).

    Filters out:
    - Names in the verb's own `inject` list (per the @verb decorator)
    - The global engine-injected set (ctx, client, vcs, memory, caps)
    - intent_id and agent_id (handled by the wrapper's --intent-id / env)
    """
    return [name for name, _ann in _user_params_with_annotations(fn, inject_list)]


def _user_params_with_annotations(fn, inject_list: list) -> list[tuple[str, object]]:
    """Spec 060 review (round 8): for typed argv coercion in the bash
    wrapper, callers need the parameter's annotation alongside its name.
    Returns ``[(name, annotation), …]``; annotation is ``inspect.Parameter.
    empty`` when the verb didn't declare one."""
    return [(name, ann) for name, ann, _has_default
            in _user_params_full(fn, inject_list)]


def _user_params_full(fn, inject_list: list) -> list[tuple[str, object, bool]]:
    """Spec 150 Slice 2 review (round 2): the bash wrapper needs to know
    which user-facing params have defaults so they can be omitted
    from the positional arg list — without this, adding an optional
    keyword param to a verb breaks every existing bash caller.

    Returns ``[(name, annotation, has_default), …]``."""
    if fn is None:
        return []
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return []
    excluded = _INJECTED_PARAMS | set(inject_list or []) | {"intent_id", "agent_id"}
    return [(p.name, p.annotation, p.default is not inspect.Parameter.empty)
            for p in sig.parameters.values()
            if p.name not in excluded]


def emit_bash_wrappers(cap_name: str, verbs: dict) -> dict[str, str]:
    """Render per-verb bash wrappers (Spec 031 §D + Spec 032 §H).

    For EVERY verb in the capability (Tier A and Tier B both), emit:
      bin/agency-<cap_name>-<verb_name>

    The wrapper is a bash script that:
    - Sources $AGENCY_INTENT_ID from env OR accepts --intent-id <id>
    - Accepts positional args mapping to the verb's signature kwargs
    - Builds the kwargs JSON via Python (avoids shell-quoting injection — panel F-10)
    - Pipes to `python -m agency.cli execute --code "..."`
    - Errors with clear messages on missing intent-id OR missing args
    - Supports `--` argument terminator (panel F-11)

    Inputs:
      - cap_name: capability name (becomes part of the wrapper filename)
      - verbs: {verb_name: {role, fn, inject}}
    Returns: {f"bin/agency-{cap_name}-{verb_name}": <bash content>} per verb.
    chain_next: pass to install.write(); install.write() sets +x mode.
    """
    out: dict[str, str] = {}
    for verb_name in sorted(verbs):
        spec = verbs[verb_name]
        fn = spec.get("fn")
        params_full = _user_params_full(fn, spec.get("inject", []))
        params = [name for name, _ann, _has_default in params_full]

        # Build the usage line + arg-count check + kwargs JSON pairs.
        # Spec 150 Slice 2 review (round 2): params with defaults are
        # OPTIONAL — the wrapper omits them when not supplied so the
        # verb's defaults apply. Required count is just the count of
        # params before the first default (Python defaults rule).
        required_count = sum(1 for _, _, hd in params_full if not hd)
        if params:
            # Usage: required positional then [optional] for the rest.
            usage_parts: list[str] = []
            for name, _ann, has_default in params_full:
                usage_parts.append(f"[{name}]" if has_default else f"<{name}>")
            usage = (f"agency-{cap_name}-{verb_name} [--intent-id ID] "
                     + " ".join(usage_parts))
            req_names = " ".join(
                n for n, _, hd in params_full if not hd)
            if required_count > 0:
                arg_check = (
                    f'if [ "${{#args[@]}}" -lt {required_count} ]; then\n'
                    f'  echo "error: expected at least {required_count} '
                    f'required arg(s) ({req_names}); got ${{#args[@]}}" >&2\n'
                    f'  exit 2\n'
                    f'fi'
                )
            else:
                # All user params optional — verb defaults handle the
                # zero-arg call from the bash surface.
                arg_check = ('# all positional args are optional; verb '
                             'defaults apply when omitted')
            # PR review round 8 (r_skill_emit_typed): coerce argv strings
            # to the verb's declared annotation. The coercion is
            # JSON-first-then-fallback so list-typed bash callers can
            # pass `axes=quality,security` AND JSON callers can pass
            # `axes='["quality","security"]'`.
            #
            # Spec 150 Slice 2 review (round 2): build the kwargs dict
            # incrementally so missing OPTIONAL params don't show up at
            # all (the verb's default applies). Required params come
            # first (no len check), optional after (conditional).
            pair_lines: list[str] = ['_kw = {"intent_id": sys.argv[1]}']
            for i, (p, ann, has_default) in enumerate(params_full):
                idx = i + 2
                ann_expr = _ann_repr(ann)
                pair = f'_kw["{p}"] = _coerce(sys.argv[{idx}], {ann_expr})'
                if has_default:
                    # Conditional: only include if the caller supplied it.
                    pair_lines.append(
                        f'if len(sys.argv) > {idx}: {pair}')
                else:
                    pair_lines.append(pair)
            pair_lines.append('print(json.dumps(_kw))')
            kwargs_block = "\n".join(pair_lines)
        else:
            usage = f"agency-{cap_name}-{verb_name} [--intent-id ID]"
            arg_check = ('# no positional args for this verb (only --intent-id required)')
            kwargs_block = ('_kw = {"intent_id": sys.argv[1]}\n'
                            'print(json.dumps(_kw))')

        brief = _first_sentence_brief(fn) if fn else "(no brief)"

        rendered = _BASH_WRAPPER_TEMPLATE.substitute(
            gen_version=str(GEN_VERSION),
            cap_name=cap_name,
            verb_name=verb_name,
            brief=brief,
            usage=usage,
            arg_check=arg_check,
            kwargs_block=kwargs_block,
        )
        out[f"bin/agency-{cap_name}-{verb_name}"] = rendered
    return out


def _capability_hash(cap, rule_version: int) -> str:
    """sha256 of capability shape + rule_version. Stable across runs.

    Hash inputs (in order):
    - cap.name
    - sorted verbs by name: (name, role, signature, docstring)
    - rule_version (so a template/lint bump invalidates everything)
    """
    parts = [cap.name]
    for verb_name in sorted(cap.verbs):
        spec = cap.verbs[verb_name]
        fn = spec.get("fn")
        role = spec.get("role", "")
        sig = str(inspect.signature(fn)) if fn else ""
        doc = (fn.__doc__ or "") if fn else ""
        parts.append(f"{verb_name}|{role}|{sig}|{doc}")
    parts.append(f"rule_version={rule_version}")
    blob = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
