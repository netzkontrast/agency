"""The plugin-development capability — everything needed to develop a good plugin:
skill creation (TDD-for-docs, with the CSO rules enforced as compute) and
plugin/marketplace authoring, in the agency capability model.

A REAL capability (template rendering + rule-checking is real compute — it
mutates nothing external), role-tagged:

- `scaffold` (act)         — generate a Claude Code plugin manifest (`.claude-plugin/plugin.json`).
- `author_skill` (act)     — the *skill creator*: emit a SKILL.md (frontmatter + body).
- `author_command` (act)   — emit a slash-command markdown file.
- `marketplace_entry` (act)— emit a marketplace.json plugin entry.
- `step_doc` (act)         — prestructure one chain step's resulting document.
- `lint_skill` (transform) — the EXECUTABLE port of the writing-skills CSO rules:
                             validate a skill's name + description against the
                             "Use when…", hyphen-only-name, third-person, and
                             length rules. Judgment-as-code.
- `help` (transform)       — map the engine's capabilities (macroskills) to their
                             verbs (the harness-in-harness micro-skills): the
                             discovery surface a Claude Code plugin exposes as `help`.

Each `act` verb returns an `artefact` so the Registry records a PRODUCES edge —
the authored document is provenance, edged to the intent it SERVES.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Spec 060 — kebab-case rule (mirrors _capability_loader._KEBAB_RE).
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...capability import SkillDoc as _SkillDoc
from ...ontology import OntologyExtension
from ... import templates

DEFAULT_TOOLS = "  - Read\n  - Write\n  - Edit"
# kebab-case per the Agent Skills spec: lowercase letters/numbers/hyphens, no
# leading/trailing hyphen, no consecutive hyphens.
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_FIRST_PERSON = re.compile(r"\b(I|I'll|I'm|my|me|we|we'll)\b", re.IGNORECASE)

_WORKFLOW_SUMMARY_PATTERNS = (
    re.compile(r"\bstep\s+\d", re.I),
    re.compile(r"\bfirst\b.*?\bthen\b", re.I | re.S),
    re.compile(r"\b\d+[.)]\s", re.M),
)

_TRIGGER_PROCEDURAL_VERBS = re.compile(
    r"^\s*(call|create|run|step|then|first|generate|build|write|invoke)\b",
    re.I,
)


def scaffold(name: str, version: str, description: str) -> dict:
    body = json.dumps(templates.manifest_obj(name, version, description), indent=2)
    return {"result": body, "artefact": {
        "kind": "plugin-manifest", "name": name, "version": version,
        "description": description, "body": body}}


def author_skill(name: str, description: str, body: str,
                 allowed_tools: str = DEFAULT_TOOLS, title: str | None = None) -> dict:
    # C1 (Codex review 6059c74 / templates.py:51) — same class of bug as the
    # description-escape fix: a name carrying a newline or YAML indicator chars
    # would inject frontmatter keys before lint_skill caught it. Defense in
    # depth — CSO kebab-case lint runs after, but the SKILL.md artefact must
    # never be rendered invalid in the first place.
    rendered = templates.SKILL_MD.substitute(
        name=templates._yaml_scalar(name),
        description=templates._yaml_scalar(description), body=body,
        allowed_tools=allowed_tools, title=title or name)
    return {"result": rendered, "artefact": {
        "kind": "skill-md", "name": name, "description": description, "body": rendered}}


def author_command(name: str, description: str, body: str) -> dict:
    rendered = templates.COMMAND_MD.substitute(
        description=templates._yaml_scalar(description), body=body)
    return {"result": rendered, "artefact": {
        "kind": "command-md", "name": name, "description": description, "body": rendered}}


def marketplace_entry(name: str, version: str, description: str, source: str) -> dict:
    body = json.dumps(templates.marketplace_obj(name, version, description, source), indent=2)
    return {"result": body, "artefact": {
        "kind": "marketplace-entry", "name": name, "version": version,
        "description": description, "source": source, "body": body}}


def step_doc(step: str, output: str, status: str = "done",
             inputs: str = "", notes: str = "") -> dict:
    rendered = templates.STEP_DOC.substitute(
        step=step, output=output, status=status, inputs=inputs, notes=notes)
    return {"result": rendered, "artefact": {
        "kind": "step-doc", "step": step, "output": output, "body": rendered}}


def lint_skill(name: str, description: str) -> dict:
    """The writing-skills CSO rules + the Agent Skills spec limits, as enforceable
    compute. Returns the violations a baseline-tested human reviewer would flag —
    judgment ported (kebab-case ≤64 name; ≤1024 description; 'Use when…';
    third-person)."""
    v: list[str] = []
    if not _NAME_RE.match(name or ""):
        v.append("name must be kebab-case (lowercase letters, numbers, hyphens; "
                 "no leading/trailing or consecutive hyphen)")
    if len(name or "") > 64:
        v.append("name exceeds 64 chars")
    if not (description or "").lower().startswith("use when"):
        v.append("description must start with 'Use when…' (triggering conditions)")
    if _FIRST_PERSON.search(description or ""):
        v.append("description must be third person (no first-person pronouns)")
    if len(description or "") > 1024:
        v.append("description exceeds the 1024-char spec limit")
    elif len(description or "") > 500:
        v.append("description should be under 500 chars")
    return {"ok": not v, "violations": v}


def lint_skill_doc(cap_name: str, doc: "_SkillDoc", verbs: dict) -> dict:
    """Validate a SkillDoc against the Spec 031 §B contract.

    Returns {ok: bool, violations: [{rule, message}]}.
    """
    v: list[dict] = []
    desc = (doc.description or "").strip()
    if not desc.lower().startswith("use when"):
        v.append({"rule": "description-trigger-first",
                  "message": "description must start with 'Use when…'"})
    for pat in _WORKFLOW_SUMMARY_PATTERNS:
        if pat.search(desc):
            v.append({"rule": "description-no-workflow-summary",
                      "message": (f"description matches workflow-summary "
                                  f"pattern {pat.pattern!r}; describe triggers, "
                                  f"not steps")})
            break
    overview = (doc.overview or "").strip()
    for pat in _WORKFLOW_SUMMARY_PATTERNS:
        if pat.search(overview):
            v.append({"rule": "overview-no-workflow-summary",
                      "message": (f"overview matches workflow-summary pattern "
                                  f"{pat.pattern!r}")})
            break
    triggers = list(doc.triggers or [])
    for i, t in enumerate(triggers):
        first_8 = " ".join(t.split()[:8])
        if _TRIGGER_PROCEDURAL_VERBS.search(first_8):
            v.append({"rule": "triggers-named-symptoms",
                      "message": (f"trigger {i!r} starts with a procedural verb "
                                  f"({first_8!r}); name the symptom, not the action")})
    if not (2 <= len(triggers) <= 5):
        v.append({"rule": "triggers-count",
                  "message": f"triggers list has {len(triggers)} items; want 2-5"})
    canonical_verbs = set(verbs)
    if not any(f"capability_{cap_name}_{vb}" in (doc.canonical_example or "")
               or f"agency-{cap_name}-{vb}" in (doc.canonical_example or "")
               for vb in canonical_verbs):
        v.append({"rule": "example-uses-real-verb",
                  "message": (f"canonical_example does not reference any verb of "
                              f"capability {cap_name!r} (have: "
                              f"{sorted(canonical_verbs)!r})")})
    if len(canonical_verbs) >= 3 and not doc.red_flags:
        v.append({"rule": "red-flags-required",
                  "message": (f"capability {cap_name!r} ships "
                              f"{len(canonical_verbs)} verbs; red_flags MUST "
                              f"have >=1 item")})
    for rf in (doc.red_flags or []):
        if "→" not in rf and " - " not in rf:
            v.append({"rule": "red-flags-format",
                      "message": (f"red_flag {rf[:40]!r}... missing "
                                  f"'<symptom> → <counter>' delimiter (use ' → ' "
                                  f"or ' - ')")})
    for vb_name in (doc.verb_briefs or {}):
        if vb_name not in canonical_verbs:
            v.append({"rule": "verb-briefs-resolve",
                      "message": (f"verb_briefs key {vb_name!r} is not a verb of "
                                  f"capability {cap_name!r}")})
    return {"ok": not v, "violations": v}


# ---- Spec 016 P4 / Plan/024 PR-A — lint_capability ------------------------

_SCAFFOLD_MARKER_RE = __import__("re").compile(r"^\s*#\s*agency-scaffold:")
_NET_IMPORTS = ("requests", "httpx", "urllib", "urllib3", "subprocess",
                "socket", "aiohttp")


def _capability_source_path(cap):
    """Find the source file backing a Capability. Used to read the
    scaffold marker + scan for mis-tagged transform/effect imports.

    `_wrap_method` (agency/capability.py) attaches `__capability_cls__`
    to every wrapped verb fn so we can find the original class — the fn
    itself is a closure inside capability.py and would otherwise hide
    the user's source file."""
    import inspect
    for spec in cap.verbs.values():
        fn = spec.get("fn")
        if fn is None:
            continue
        # Spec 016 P4: prefer the exposed class pointer; fall back to
        # naive lookup for functional-form capabilities (no class wrap).
        target = getattr(fn, "__capability_cls__", None) or fn
        try:
            path = inspect.getsourcefile(target)
            if path:
                return path
        except (TypeError, OSError):
            continue
    return None


def _has_scaffold_marker(source_path):
    """Marker = first non-blank line of the file is `# agency-scaffold: …`.
    Read it version-agnostically: any prefix triggers block mode."""
    if not source_path:
        return False
    try:
        with open(source_path) as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                return bool(_SCAFFOLD_MARKER_RE.match(stripped))
    except OSError:
        return False
    return False


def _check_structural(cap):
    """Hint #7: every @verb docstring carries Inputs:/Returns:/chain_next:."""
    out = []
    for verb_name, spec in cap.verbs.items():
        doc = (spec.get("fn").__doc__ or "")
        missing = [m for m in ("Inputs:", "Returns:", "chain_next:") if m not in doc]
        if missing:
            out.append({
                "verb": verb_name, "kind": "structural",
                "msg": f"docstring missing markers: {', '.join(missing)}",
                "fix": "add `Inputs:`, `Returns:`, `chain_next:` lines per CAPABILITY-AUTHORING.md",
            })
    return out


def _check_role_tag(cap, source_path):
    """Hint #3: a transform verb whose MODULE imports a network/IO library
    is mis-tagged — should be `effect`. Conservative: scan the source for
    `import X` / `from X` for X in _NET_IMPORTS."""
    if not source_path:
        return []
    try:
        src = open(source_path).read()
    except OSError:
        return []
    flagged_imports = []
    for imp in _NET_IMPORTS:
        if f"import {imp}" in src or f"from {imp}" in src:
            flagged_imports.append(imp)
    if not flagged_imports:
        return []
    out = []
    for verb_name, spec in cap.verbs.items():
        if spec.get("role") == "transform":
            out.append({
                "verb": verb_name, "kind": "role_tag",
                "msg": f"transform role but module imports {flagged_imports!r} (network/IO)",
                "fix": "re-tag as @verb(role='effect') — the provenance moat relies on the tag",
            })
    return out


def _check_render_slice(cap):
    """Spec 023: brief is non-empty AND ≤120 chars; first sentence cleaves."""
    from agency.disclosure import parse_slices
    out = []
    for verb_name, spec in cap.verbs.items():
        doc = (spec.get("fn").__doc__ or "")
        brief = parse_slices(doc)["brief"]
        if not brief:
            out.append({
                "verb": verb_name, "kind": "render_slice",
                "msg": "first-sentence brief is empty (no docstring or unparseable)",
                "fix": "add a one-sentence gist as the first line; see CAPABILITY-AUTHORING.md §verb docstring contract",
            })
        elif len(brief) > 120:
            out.append({
                "verb": verb_name, "kind": "render_slice",
                "msg": f"brief is {len(brief)} chars; must be ≤120 (token-budget gate)",
                "fix": "tighten the first sentence; move detail to body / Inputs/Returns markers",
            })
    return out


def _check_consumer_contract(cap):
    """Codex R2 lesson: the cap must round-trip through mcp._list_tools().
    Build a throwaway in-memory engine + assert every verb registered."""
    import asyncio
    from agency.engine import Engine
    try:
        e = Engine(":memory:", extra_capabilities=[cap])
    except Exception as exc:  # ontology collision, etc.
        return [{"verb": None, "kind": "consumer_contract",
                 "msg": f"Engine refused to load capability: {exc}",
                 "fix": "check ontology fragment for collision with core or another cap"}]
    try:
        try:
            mcp = e.build_mcp(codemode=False)
        except Exception as exc:
            return [{"verb": None, "kind": "consumer_contract",
                     "msg": f"build_mcp failed: {exc}",
                     "fix": "verb signatures must be FastMCP-compatible"}]
        tool_names = asyncio.run(_tool_names(mcp))
    finally:
        e.memory.close()
    out = []
    for verb_name in cap.verbs:
        expected = f"capability_{cap.name}_{verb_name}"
        if expected not in tool_names:
            out.append({
                "verb": verb_name, "kind": "consumer_contract",
                "msg": f"{expected!r} did not register as an MCP tool",
                "fix": "verb signature must not collide with reserved kwargs; check FastMCP errors",
            })
    return out


async def _tool_names(mcp):
    tools = await mcp._list_tools()
    return {t.name for t in tools}


def _verb_wraps_dict(member) -> bool:
    """Spec 019 heuristic: walk a verb's source for ``return {"result":
    <expr>}`` where ``<expr>`` is a dict-literal / dict-comp. That's
    the dict-on-dict wrap pattern where the engine unwraps the
    ``result`` key at the wire — so the docstring's ``Returns:`` line
    must describe the INNER shape, not the wrapped envelope.

    Returns False for verbs that don't wrap at all (return rich dicts
    directly like ``jules.dispatch``) and for verbs that wrap a scalar
    (the engine re-wraps non-dict outputs into ``{result: <scalar>}``
    so the wire shape IS ``{result: <scalar>}`` — docstring is correct
    to say so)."""
    import ast
    import inspect
    try:
        src = inspect.getsource(member)
    except (OSError, TypeError):
        return False
    # Dedent so the indented method src parses standalone.
    src = inspect.cleandoc("\n" + src)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        v = node.value
        if not isinstance(v, ast.Dict):
            continue
        # exactly one key, and it's the literal "result"
        if len(v.keys) != 1:
            continue
        k = v.keys[0]
        if not (isinstance(k, ast.Constant) and k.value == "result"):
            continue
        # the value behind result must itself be a dict literal/comp
        inner = v.values[0]
        if isinstance(inner, (ast.Dict, ast.DictComp)):
            return True
    return False


_WIRE_LEAK_RE = re.compile(r"Returns:\s*[`*~]*\s*\{\s*result\s*:", re.IGNORECASE)


def _check_wire_shape(cap):
    """Spec 019 §"Done When" — flag docstrings that describe the INTERNAL
    wrap on dict-wrapping verbs. ``Returns: {result: {…}}`` on a verb
    whose actual return is ``{"result": {…}}`` documents the envelope
    that the engine strips at the wire. Doc should describe the WIRE
    shape (the inner dict)."""
    out = []
    for verb_name, spec in cap.verbs.items():
        fn = spec.get("fn")
        member = getattr(fn, "__capability_method__", None)
        if member is None:
            continue
        if not _verb_wraps_dict(member):
            continue
        doc = (fn.__doc__ or "")
        if _WIRE_LEAK_RE.search(doc):
            out.append({
                "verb": verb_name, "kind": "wire_shape",
                "msg": ("docstring `Returns:` describes the internal "
                        "`{result: {...}}` wrap; engine strips it at the "
                        "wire. Describe the inner dict shape only."),
                "fix": "rewrite the `Returns:` line to name the inner "
                       "dict's top-level keys (no `result` envelope).",
            })
    return out


_AGENT_INSTRUCTION_RE = re.compile(r"<!--\s*AGENT\s*:", re.IGNORECASE)


def _check_template_folder(cap):
    """Spec 060 — templates must instruct agents.

    When a capability declares `render_templates = RenderTemplates(
    folder=...)`, three invariants apply:
      1. The folder must exist on disk.
      2. Filename stems must be kebab-case (already enforced by the
         loader; this rule pre-flags it at lint time).
      3. Every template file's body must carry at least one
         ``<!-- AGENT: ... -->`` instruction block — the doctrine bar
         that separates per-cap templates (with agent instructions)
         from engine-owned templates in `agency/render/` (pure
         rendering).

    Returns lint findings (kind='template_folder'). Empty when the cap
    has no `render_templates` declaration (the default — back-compat).
    """
    rt = getattr(cap, "render_templates", None)
    if rt is None:
        return []
    out = []
    folder = Path(rt.folder)
    if not folder.is_dir():
        out.append({
            "kind": "template_folder",
            "verb": "<capability>",
            "msg": f"render_templates folder does not exist: {folder}",
            "fix": "create the folder and add at least one template "
                   "with an `<!-- AGENT: ... -->` block",
        })
        return out
    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue
        stem = entry.stem
        if not _KEBAB_RE.match(stem):
            out.append({
                "kind": "template_folder",
                "verb": entry.name,
                "msg": f"template filename stem must be kebab-case: {entry.name}",
                "fix": f"rename {entry.name} so the stem matches "
                       f"^[a-z0-9]+(-[a-z0-9]+)*$",
            })
        try:
            body = entry.read_text(encoding="utf-8")
        except OSError:
            continue
        if not _AGENT_INSTRUCTION_RE.search(body):
            out.append({
                "kind": "template_folder",
                "verb": entry.name,
                "msg": f"template {entry.name} has no `<!-- AGENT: ... -->` "
                       f"instruction block (Spec 060 doctrine)",
                "fix": "add at least one `<!-- AGENT: <imperative> -->` "
                       "block instructing the reader what to do",
            })
    return out


def _check_token_budget(cap, max_per_verb=20):
    """Spec 023 budget adapted: brief slice ≤ max_per_verb cl100k tokens
    per verb. Skips silently if tiktoken missing (non-dev install)."""
    try:
        import tiktoken
    except ImportError:
        return []
    enc = tiktoken.encoding_for_model("gpt-4")
    from agency.disclosure import parse_slices
    out = []
    for verb_name, spec in cap.verbs.items():
        brief = parse_slices(spec.get("fn").__doc__ or "")["brief"]
        n = len(enc.encode(brief))
        if n > max_per_verb:
            out.append({
                "verb": verb_name, "kind": "token_budget",
                "msg": f"brief is {n} cl100k tokens; budget {max_per_verb}",
                "fix": "tighten the first sentence",
            })
    return out


# Spec 056 — irregular `<prefix>_id` → expected node label. Unknown prefixes
# skip the rule (no guess). Grows alongside the verbs that introduce new types.
_NODE_ID_LABELS = {
    "research": "Research",
    "intent": "Intent",
    "parent_intent": "Intent",
    "for_intent": "Intent",
    "root_intent": "Intent",
    "lifecycle": "Lifecycle",
}


def _check_node_id_guards(cap):
    """Spec 056 (WARN): flag a verb that reads a ``<label>_id`` parameter via a
    bare ``recall(param)`` / ``get_node(param)`` WITHOUT verifying the node's
    label — the silent-anchor bug class (an intent id typo'd as a research id
    passes existence but anchors edges at the wrong endpoint). A verb passes when
    it uses ``recall_typed(param, Label)``, a Cypher ``MATCH (n:Label)``, or an
    explicit ``"Label" in labels`` check. Unknown id-prefixes skip (no guess).
    """
    import inspect
    out = []
    for verb_name, spec in cap.verbs.items():
        # Class-form verbs expose a wrapper as `fn`; the real method (with the
        # user-facing source + signature) hangs off `__capability_method__`.
        fn = getattr(spec.get("fn"), "__capability_method__", spec.get("fn"))
        try:
            src = inspect.getsource(fn)
            params = inspect.signature(fn).parameters
        except (OSError, TypeError, ValueError):
            continue
        for pname in params:
            m = re.match(r"^(.+)_id$", pname)
            if not m:
                continue
            label = _NODE_ID_LABELS.get(m.group(1))
            if not label:
                continue
            reads_bare = f"recall({pname})" in src or f"get_node({pname})" in src
            if not reads_bare:
                continue
            guarded = (f"recall_typed({pname}" in src
                       or f'"{label}"' in src or f"'{label}'" in src
                       or f":{label})" in src)
            if not guarded:
                out.append({
                    "verb": verb_name, "kind": "node_id_guard",
                    "msg": f"reads {pname!r} via bare recall/get_node without a "
                           f"{label}-label check",
                    "fix": f"use memory.recall_typed({pname}, {label!r}) — Spec 056",
                })
    return out


def _is_record_reflection(call) -> bool:
    import ast
    f = call.func
    return (isinstance(f, ast.Attribute) and f.attr == "record"
            and bool(call.args)
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == "Reflection")


def _link_edges(call) -> set:
    """String-constant edge names passed to a `.link(...)` call."""
    import ast
    if not (isinstance(call.func, ast.Attribute) and call.func.attr == "link"):
        return set()
    return {a.value for a in call.args
            if isinstance(a, ast.Constant) and isinstance(a.value, str)}


def _check_reflection_links(cap):
    """Spec 058 (WARN): a verb that records a ``Reflection`` MUST link it with
    BOTH ``SERVES`` (provenance — surfaces in ``Memory.provenance``) AND
    ``OBSERVED_DURING`` (the intent-scoped reflection view used by
    ``document.render(scope='reflections')`` + the repo-index recent-activity
    filter). Missing either edge writes a node invisible to half its consumers.

    AST walk: capture each ``<obj>.record("Reflection", …)`` assignment target,
    then require both ``link(<var>, …, "SERVES")`` and ``…"OBSERVED_DURING"`` on
    that var. Reflections recorded via a dynamic label variable skip (no
    false-fire). A line carrying ``# agency-skip-link-check`` opts out.
    """
    import ast
    import inspect
    import textwrap
    out = []
    for verb_name, spec in cap.verbs.items():
        # Resolve the real method behind the class-form wrapper (see above).
        fn = getattr(spec.get("fn"), "__capability_method__", spec.get("fn"))
        try:
            src = textwrap.dedent(inspect.getsource(fn))
            tree = ast.parse(src)
        except (OSError, TypeError, SyntaxError, ValueError):
            continue
        if "# agency-skip-link-check" in src:
            continue
        reflection_vars: set[str] = set()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                    and _is_record_reflection(node.value)):
                reflection_vars |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        if not reflection_vars:
            continue
        edges_by_var: dict[str, set] = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and node.args
                    and isinstance(node.args[0], ast.Name)):
                e = _link_edges(node)
                if e:
                    edges_by_var.setdefault(node.args[0].id, set()).update(e)
        for var in reflection_vars:
            have = edges_by_var.get(var, set())
            for required in ("SERVES", "OBSERVED_DURING"):
                if required not in have:
                    out.append({
                        "verb": verb_name, "kind": "reflection_link",
                        "msg": f"records a Reflection ({var!r}) but never links it {required}",
                        "fix": f"add link({var}, <intent>, {required!r}) — both edges "
                               f"required (Spec 058)",
                    })
    return out


def lint_capability(cap) -> dict:
    """Run the rule families against `cap` (a Capability instance).

    Mode dispatch: if the capability's source file carries the
    `# agency-scaffold: …` marker on its first non-blank line → BLOCK
    mode (violations are real errors, ok=False). Otherwise WARN mode
    (legacy grandfathering — violations move to warnings, ok=True).

    Spec 056 — `_check_node_id_guards` is a WARN-ONLY soft rule (regardless of
    mode) during its migration window: it surfaces as warnings even in block
    mode so a scaffold-marked capability isn't broken before the audit completes.

    Returns: {ok, violations, warnings, skipped, mode}."""
    source_path = _capability_source_path(cap)
    mode = "block" if _has_scaffold_marker(source_path) else "warn"
    all_findings = (
        _check_structural(cap)
        + _check_role_tag(cap, source_path)
        + _check_render_slice(cap)
        + _check_consumer_contract(cap)
        + _check_token_budget(cap)
        + _check_wire_shape(cap)
        + _check_template_folder(cap)
    )
    # WARN-only soft rules — never block, even in block mode (migration windows).
    soft_findings = _check_node_id_guards(cap) + _check_reflection_links(cap)
    if mode == "block":
        return {"ok": not all_findings, "violations": all_findings,
                "warnings": soft_findings, "skipped": 0, "mode": mode}
    # warn mode — findings move to warnings; ok always True
    return {"ok": True, "violations": [], "warnings": all_findings + soft_findings,
            "skipped": 0, "mode": mode}


def help_map(caps: dict) -> dict:
    """Map macroskills (capabilities) -> micro-skills (verbs). `caps` is the live
    registry view `{capability: [verb, ...]}`; the engine INJECTS it (the `inject`
    convention) so this verb stays pure. Returns a tiny doc + the structured map
    (token-efficient delta) under one `result` payload."""
    ordered = {k: sorted(caps[k]) for k in sorted(caps)}
    lines = ["# agency — capabilities (macroskills) and their verbs (micro-skills)", ""]
    for name, verbs in ordered.items():
        lines.append(f"- **{name}** — {', '.join(verbs)}")
    lines += [
        "",
        "## Discovery",
        "",
        "There is no separate 'remember to use the skill' layer — discovery IS the contract:",
        "",
        "- `search` finds a capability/verb or a discipline by symptom;",
        "- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);",
        "- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).",
        "",
        "Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until",
        "confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's",
        "heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS",
        "the recorded walk, so there is nothing extra to remember.",
    ]
    return {"result": {"doc": "\n".join(lines) + "\n", "map": ordered}}


# --- this capability's OWN ontology fragment (merged onto the core by the engine).
# The plugin-dev node types, its template-schemas, and its two skills live HERE,
# with the capability that owns them — not hard-wired into the core ontology.

# skill creation as TDD-for-docs. The Iron Law — "NO SKILL WITHOUT A FAILING TEST
# FIRST" — is ENFORCED by phase ordering: GREEN (authoring)
# is unreachable until RED produced its baseline. RED → GREEN → lint → REFACTOR →
# deploy(hard gate); GREEN + lint are bound to REAL verbs.
SKILL_CREATION_SKILL = {
    "name": "skill-creation",
    "kind": "authoring",
    "phases": [
        {"index": 1, "name": "red-baseline",
         "produces": ["baseline", "rationalizations"]},
        {"index": 2, "name": "green-author", "produces": ["skill_md"],
         "invoke": {"capability": "plugin", "verb": "author_skill"},
         "inputs": ["name", "description", "body"]},
        {"index": 3, "name": "lint", "produces": ["lint"],
         "invoke": {"capability": "plugin", "verb": "lint_skill"},
         "inputs": ["name", "description"]},
        {"index": 4, "name": "refactor",
         "produces": ["rationalization_table", "red_flags"]},
        {"index": 5, "name": "deploy", "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

# the complete plugin-authoring chain: each phase emits a prestructured document.
PLUGIN_DEV_SKILL = {
    "name": "plugin-dev",
    "kind": "authoring",
    "phases": [
        {"index": 1, "name": "manifest", "produces": ["manifest"],
         "invoke": {"capability": "plugin", "verb": "scaffold"},
         "inputs": ["name", "version", "description"]},
        {"index": 2, "name": "skill", "produces": ["skill_md"],
         "invoke": {"capability": "plugin", "verb": "author_skill"},
         "inputs": ["name", "description", "body"]},
        {"index": 3, "name": "command", "produces": ["command_md"],
         "invoke": {"capability": "plugin", "verb": "author_command"},
         "inputs": ["name", "description", "body"]},
        {"index": 4, "name": "marketplace", "produces": ["entry"],
         "invoke": {"capability": "plugin", "verb": "marketplace_entry"},
         "inputs": ["name", "version", "description", "source"]},
        {"index": 5, "name": "confirm", "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

plugin_ontology = OntologyExtension(
    nodes={
        "Plugin":  ["name", "version", "description"],   # a Claude Code plugin manifest
        "Command": ["name", "description"],              # a slash command
    },
    skills={"skill-creation": SKILL_CREATION_SKILL, "plugin-dev": PLUGIN_DEV_SKILL},
    # Spec 060 — schemas migrated from `templates.REQUIRED` Python dict
    # to file-based `plugin/schemas/*.json` declarations. The engine's
    # `load_capability_folders` discovers them at bootstrap and merges
    # them into this OntologyExtension's `schemas` dict before
    # `Ontology.extend` runs.
)

class PluginCapability(CapabilityBase):
    name = "plugin"
    home = "capability"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = plugin_ontology

    # the act verbs are pure template renders (module functions above); the class
    # methods are thin verb wrappers so the capability is authored in the class form.
    @verb(role="act")
    def scaffold(self, name: str, version: str, description: str) -> dict:
        """Render the plugin scaffold (plugin.json + .mcp.json).

        Inputs: name (plugin slug), version (semver), description (str).
        Returns: ``{result: {plugin_json, mcp_json}}``.
        chain_next: write the rendered files; commit; install.
        """
        return scaffold(name, version, description)

    @verb(role="act")
    def author_skill(self, name: str, description: str, body: str) -> dict:
        """Render a CSO-compliant SKILL.md.

        Inputs: name (skill slug), description (trigger phrase), body (markdown).
        Returns: ``{result: <skill_md_str>}``.
        chain_next: ``plugin.lint_skill(name=, description=)`` then write.
        """
        return author_skill(name, description, body)

    @verb(role="act")
    def author_command(self, name: str, description: str, body: str) -> dict:
        """Render a slash-command markdown stub.

        Inputs: name (command name), description (str), body (markdown).
        Returns: ``{result: <command_md_str>}``.
        chain_next: write to ``commands/<name>.md``.
        """
        return author_command(name, description, body)

    @verb(role="act")
    def marketplace_entry(self, name: str, version: str, description: str, source: str) -> dict:
        """Render a marketplace.json entry.

        Inputs: name (plugin slug), version (semver), description (str),
                source (git URL or local path).
        Returns: ``{result: <entry_dict>}``.
        chain_next: merge into ``.claude-plugin/marketplace.json``.
        """
        return marketplace_entry(name, version, description, source)

    @verb(role="act")
    def step_doc(self, step: str, output: str, status: str = "done",
                 inputs: str = "", notes: str = "") -> dict:
        """Render a step-doc markdown block (audit trail entry).

        Inputs: step (title), output (deliverable), status (done|partial|skip),
                inputs (str, optional), notes (str, optional).
        Returns: ``{result: <markdown_str>}``.
        chain_next: append to the working step-doc file.
        """
        return step_doc(step, output, status, inputs, notes)

    @verb(role="transform")
    def lint_skill(self, name: str, description: str) -> dict:
        """Lint a skill description against the CSO + length rules.

        Inputs: name (slug), description (the SKILL.md description field).
        Returns: ``{ok, violations}``.
        chain_next: fix violations + re-lint OR write the skill if ``ok=True``.
        """
        return lint_skill(name, description)

    @verb(role="transform")
    def lint_capability(self, name: str) -> dict:
        """Lint a capability against Hint #7 structural + role-tag + render-slice rules.

        Inputs: name (capability name registered in ``ctx.registry``).
        Returns: ``{ok, violations, warnings, skipped, mode}``.
        chain_next: fix violations + re-lint; ``mode=block`` is fatal.
        """
        cap = self.ctx.registry.get(name)
        return lint_capability(cap)

    @verb(role="transform")
    def help(self) -> dict:
        """Map the engine's capabilities (macroskills) to their verbs — via ctx.registry.

        Inputs: none.
        Returns: ``{result: {<cap>: [<verb>, …]}}``.
        chain_next: ``search('<keyword>')`` or ``get_schema(name=)`` for details.
        """
        caps = {n: list(self.ctx.registry.get(n).verbs) for n in self.ctx.registry.names()}
        return help_map(caps)
