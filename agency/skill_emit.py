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

# Engine-injected params: these are NOT user-facing args in the wrapper.
_INJECTED_PARAMS = frozenset({"ctx", "client", "vcs", "memory", "caps"})


def _ann_repr(annotation) -> str:
    """Render an inspect.Parameter annotation as a Python expression the
    bash wrapper's embedded code can evaluate at call time.

    `int`, `bool`, `float`, `str` → bare class name (assumes the wrapper
    imports them — `__builtins__` always has these). Container types
    (`list`, `dict`, `list[str]`, `dict[str, int]`) → ``list`` / ``dict``
    because runtime coercion only needs the top-level container.
    Anything else (missing annotation, callable, Union, …) → ``str`` (the
    raw argv string is safe — verbs decide how to handle).

    Spec 060 round 9 — when the verb's module uses ``from __future__
    import annotations``, inspect.signature returns the annotation as a
    string (`'int'`, `'list[str]'`, …) instead of the type object. Match
    those string forms before falling through to the runtime-type path.
    """
    if annotation is inspect.Parameter.empty:
        return "str"
    # Postponed-annotation string form: peel the typing-parametrised
    # decoration and match on the bare head.
    if isinstance(annotation, str):
        head = annotation.split("[", 1)[0].strip()
        if head in ("int", "bool", "float", "str", "list", "dict"):
            return head
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
        out[f"skills/{cap_name}/references/{verb_name}.md"] = rendered
    return out


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
    if fn is None:
        return []
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return []
    excluded = _INJECTED_PARAMS | set(inject_list or []) | {"intent_id", "agent_id"}
    return [(p.name, p.annotation)
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
        params_with_annotations = _user_params_with_annotations(
            fn, spec.get("inject", []))
        params = [name for name, _ann in params_with_annotations]

        # Build the usage line + arg-count check + kwargs JSON pairs
        if params:
            usage = (f"agency-{cap_name}-{verb_name} [--intent-id ID] "
                     + " ".join(f"<{p}>" for p in params))
            arg_check = (
                f'if [ "${{#args[@]}}" -lt {len(params)} ]; then\n'
                f'  echo "error: expected {len(params)} arg(s) ({" ".join(params)}); '
                f'got ${{#args[@]}}" >&2\n'
                f'  exit 2\n'
                f'fi'
            )
            # PR review round 8 (r_skill_emit_typed): coerce argv strings
            # to the verb's declared annotation. Without this, `analyze.run
            # axes=quality,security` arrives as the string "quality,security"
            # and `list(axes)` splits it into characters; `dogfood.render
            # max_tokens=2000` arrives as "2000" and numeric arithmetic
            # fails. The coercion is JSON-first-then-fallback: try
            # `json.loads(raw)`; on success, accept the result iff it
            # matches the annotation's runtime type; on failure, fall back
            # to the raw string (str-annotated params stay verbatim).
            kwargs_pairs = ', '.join(
                ['"intent_id": sys.argv[1]'] +
                [f'"{p}": _coerce(sys.argv[{i+2}], {_ann_repr(ann)})'
                 for i, (p, ann) in enumerate(params_with_annotations)]
            )
        else:
            usage = f"agency-{cap_name}-{verb_name} [--intent-id ID]"
            arg_check = ('# no positional args for this verb (only --intent-id required)')
            kwargs_pairs = '"intent_id": sys.argv[1]'

        brief = _first_sentence_brief(fn) if fn else "(no brief)"

        rendered = _BASH_WRAPPER_TEMPLATE.substitute(
            gen_version=str(GEN_VERSION),
            cap_name=cap_name,
            verb_name=verb_name,
            brief=brief,
            usage=usage,
            arg_check=arg_check,
            kwargs_pairs=kwargs_pairs,
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
