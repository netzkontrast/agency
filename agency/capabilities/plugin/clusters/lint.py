"""Lint cluster — the authoring-doctrine rules as a polymorphic registry.

Spec 286 P3 OOP fix: the pre-split form spread each rule across THREE sites —
a ``_check_<rule>`` function, an entry in the ``_REMEDIATION`` dict, and a hand
wired call in ``lint_capability``. Adding a rule meant editing all three (an
OCP violation). Here every rule is ONE small class:

    class SomeRule(CapabilityLintRule):
        kind = "some_kind"
        severity = "block" | "soft"
        remediation = {"what":…, "steps":[…], "reference":…, "example"?:…}
        def check(self, target) -> list[dict]: ...

``lint_capability`` / ``lint_skill_doc`` / ``lint_surface`` iterate the rule
registries polymorphically — each rule contributes its findings AND owns its
remediation recipe. Adding a rule = add a class + append it to one list.

The findings + remediations produced are EQUIVALENT to the pre-split form
(same kinds, same messages, same severities, same accept-splitting). The
``# AGENCY-DRIFT: token-economy-budgets`` / ``accepted-warns`` tags are
preserved.
"""
from __future__ import annotations

import re
from pathlib import Path

from ....capability import CapabilityBase, verb
from ....capability import SkillDoc as _SkillDoc

# Spec 060 — kebab-case rule (mirrors _capability_loader._KEBAB_RE).
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

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

_SCAFFOLD_MARKER_RE = re.compile(r"^\s*#\s*agency-scaffold:")
_NET_IMPORTS = ("requests", "httpx", "urllib", "urllib3", "subprocess",
                "socket", "aiohttp")

_AGENT_INSTRUCTION_RE = re.compile(r"<!--\s*AGENT\s*:", re.IGNORECASE)
_WIRE_LEAK_RE = re.compile(r"Returns:\s*[`*~]*\s*\{\s*result\s*:", re.IGNORECASE)

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

# AGENCY-DRIFT: token-economy-budgets — the 6/12 budgets + the contract-tool set
#   are the canon-documented conventions (CAPABILITY-AUTHORING.md §Token-economy).
_WIRE_NAME_BUDGET = 6          # cl100k tokens for `capability_<cap>_<verb>`
_SURFACE_VERB_BUDGET = 12      # verbs per capability before sub-grouping
_CONTRACT_TOOLS = {"search", "get_schema", "execute"}

# Spec 092 G2 — names ALWAYS injected by Registry.invoke (never user-facing params).
_RESERVED_PARAMS = {"intent_id", "ctx", "memory"}

_ACCEPT_RE = re.compile(r"#\s*agency-accept-warn:\s*(\S+)\s*(.*)")


# ---------------------------------------------------------------------------
# Source-introspection helpers (shared across rules).
# ---------------------------------------------------------------------------

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


async def _tool_names(mcp):
    tools = await mcp._list_tools()
    return {t.name for t in tools}


# ---------------------------------------------------------------------------
# The polymorphic rule registry.
# ---------------------------------------------------------------------------

class LintRule:
    """Base for every authoring-doctrine rule.

    Each concrete rule declares its ``kind`` (the finding id), ``severity``
    (``"block"`` participates in the block-mode verdict; ``"soft"`` is WARN-only
    regardless of mode), and its ``remediation`` recipe (the HOW — what/steps/
    reference/example). ``check`` returns raw findings (``{verb, kind, msg,
    fix, …}``); the orchestrator enriches them with remediation + accept state.
    """
    kind: str = ""
    severity: str = "block"        # "block" | "soft"
    remediation: dict = {}

    def check(self, target) -> list[dict]:  # pragma: no cover - abstract
        raise NotImplementedError


class CapabilityLintRule(LintRule):
    """A rule whose ``check`` receives a ``_CapTarget`` (cap + its source path)."""


class RegistryLintRule(LintRule):
    """A rule whose ``check`` receives the live ``registry`` (cross-capability)."""


class _CapTarget:
    """The argument passed to every ``CapabilityLintRule.check`` — a capability
    plus its resolved source path (resolved once, shared across rules)."""

    def __init__(self, cap, source_path):
        self.cap = cap
        self.source_path = source_path


# ---- capability-level rules (block-severity unless marked soft) -----------

class StructuralRule(CapabilityLintRule):
    kind = "structural"
    remediation = {
        "what": "The capability is structurally malformed (missing name/home/verbs).",
        "steps": ["Add the missing class attribute(s); see the capability skeleton."],
        "reference": "Spec 016 + CAPABILITY-AUTHORING §Capability skeleton",
    }

    def check(self, target):
        """Hint #7: every @verb docstring carries Inputs:/Returns:/chain_next:."""
        cap = target.cap
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


class RoleTagRule(CapabilityLintRule):
    kind = "role_tag"
    remediation = {
        "what": "A transform-tagged verb's module imports a network/IO library.",
        "steps": ["Re-tag the verb `@verb(role='effect')` — the provenance moat relies on the tag."],
        "reference": "Spec 016 Hint #3 + CAPABILITY-AUTHORING §Role tags",
    }

    def check(self, target):
        """Hint #3: a transform verb whose MODULE imports a network/IO library
        is mis-tagged — should be `effect`. Conservative: scan the source for
        `import X` / `from X` for X in _NET_IMPORTS."""
        cap, source_path = target.cap, target.source_path
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


class RenderSliceRule(CapabilityLintRule):
    kind = "render_slice"
    remediation = {
        "what": "A verb's first-sentence brief is empty or > 120 chars.",
        "steps": ["Make the first sentence a ≤120-char gist; move detail to the body / Inputs/Returns."],
        "reference": "Spec 023 + CAPABILITY-AUTHORING §verb docstring contract",
    }

    def check(self, target):
        """Spec 023: brief is non-empty AND ≤120 chars; first sentence cleaves."""
        from agency.disclosure import parse_slices
        cap = target.cap
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


class ConsumerContractRule(CapabilityLintRule):
    kind = "consumer_contract"
    remediation = {
        "what": "The capability does not round-trip through the MCP tool list.",
        "steps": ["Fix the ontology fragment / verb signatures so build_mcp registers every verb."],
        "reference": "Spec 016 + the engine's _wire",
    }

    def check(self, target):
        """Codex R2 lesson: the cap must round-trip through mcp._list_tools().
        Build a throwaway in-memory engine + assert every verb registered."""
        import asyncio
        from agency.engine import Engine
        cap = target.cap
        try:
            # Spec 080 — this probe validates the cap's ontology + tool round-trip,
            # NOT its skill_doc (a separate concern). Bypass the bootstrap skill_doc
            # requirement so a clean-but-undocumented cap still round-trips here.
            e = Engine(":memory:", extra_capabilities=[cap], _require_skill_doc=False)
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


class TokenBudgetRule(CapabilityLintRule):
    kind = "token_budget"
    remediation = {
        "what": "A verb's brief slice exceeds the cl100k token budget.",
        "steps": ["Tighten the first sentence; split a two-clause sentence into two."],
        "reference": "Spec 023 + CAPABILITY-AUTHORING §verb docstring contract",
    }

    def __init__(self, max_per_verb: int = 20):
        self.max_per_verb = max_per_verb

    def check(self, target):
        """Spec 023 budget adapted: brief slice ≤ max_per_verb cl100k tokens
        per verb. Skips silently if tiktoken missing (non-dev install)."""
        try:
            import tiktoken
        except ImportError:
            return []
        enc = tiktoken.encoding_for_model("gpt-4")
        from agency.disclosure import parse_slices
        cap = target.cap
        out = []
        for verb_name, spec in cap.verbs.items():
            brief = parse_slices(spec.get("fn").__doc__ or "")["brief"]
            n = len(enc.encode(brief))
            if n > self.max_per_verb:
                out.append({
                    "verb": verb_name, "kind": "token_budget",
                    "msg": f"brief is {n} cl100k tokens; budget {self.max_per_verb}",
                    "fix": "tighten the first sentence",
                })
        return out


class WireShapeRule(CapabilityLintRule):
    kind = "wire_shape"
    remediation = {
        "what": "A verb's docstring describes the internal wrap, not the wire shape.",
        "steps": ["Document the unwrapped wire shape (strip the `{result: …}` envelope in the docstring)."],
        "reference": "Spec 019 + CAPABILITY-AUTHORING §Wire shape vs internal wrap",
    }

    def check(self, target):
        """Spec 019 §"Done When" — flag docstrings that describe the INTERNAL
        wrap on dict-wrapping verbs. ``Returns: {result: {…}}`` on a verb
        whose actual return is ``{"result": {…}}`` documents the envelope
        that the engine strips at the wire. Doc should describe the WIRE
        shape (the inner dict)."""
        cap = target.cap
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


class TemplateFolderRule(CapabilityLintRule):
    kind = "template_folder"
    remediation = {
        "what": "A declared template/schema folder is malformed.",
        "steps": ["Align the folder contents with the declared RenderTemplates/ArtefactSchemas."],
        "reference": "Spec 060 + CAPABILITY-AUTHORING §Where templates live",
    }

    def check(self, target):
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
        cap = target.cap
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


class ReservedParamRule(CapabilityLintRule):
    """Spec 092 G2 — the HARD half: a verb parameter named like a reserved
    injected param (crashes at signature build). No remediation recipe (the
    finding's own ``fix`` is the guidance; parity with the pre-split form,
    which carried no ``_REMEDIATION`` entry for the reserved kinds)."""
    kind = "reserved_param_name"
    remediation = {}        # intentionally empty — see docstring

    def check(self, target):
        return [f for f in _check_reserved_names(target.cap) if f.get("hard")]


class ReservedReturnKeyRule(CapabilityLintRule):
    """Spec 092 G2 — the SOFT half: a verb returning a non-dict under the
    reserved 'artefact' key (crashes the auto-artefact unwrap). No remediation
    recipe (parity with the pre-split form)."""
    kind = "reserved_return_key"
    severity = "soft"
    remediation = {}        # intentionally empty — see docstring

    def check(self, target):
        return [f for f in _check_reserved_names(target.cap) if not f.get("hard")]


# ---- capability-level SOFT (WARN-only) rules ------------------------------

class NodeIdGuardRule(CapabilityLintRule):
    kind = "node_id_guard"
    severity = "soft"
    remediation = {
        "what": "A verb reads a `<label>_id` param without verifying the node's label.",
        "steps": ["Use `memory.recall_typed(<param>, '<Label>')` instead of a bare recall/get_node."],
        "reference": "Spec 056 + CAPABILITY-AUTHORING §Node-id parameters",
        "example": "recall(research_id) → recall_typed(research_id, 'Research')",
    }

    def check(self, target):
        """Spec 056 (WARN): flag a verb that reads a ``<label>_id`` parameter via a
        bare ``recall(param)`` / ``get_node(param)`` WITHOUT verifying the node's
        label — the silent-anchor bug class (an intent id typo'd as a research id
        passes existence but anchors edges at the wrong endpoint). A verb passes when
        it uses ``recall_typed(param, Label)``, a Cypher ``MATCH (n:Label)``, or an
        explicit ``"Label" in labels`` check. Unknown id-prefixes skip (no guess).
        """
        import inspect
        cap = target.cap
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


class ReflectionLinkRule(CapabilityLintRule):
    kind = "reflection_link"
    severity = "soft"
    remediation = {
        "what": "A Reflection is recorded without both SERVES and OBSERVED_DURING edges.",
        "steps": ["Link the recorded id with BOTH `SERVES` and `OBSERVED_DURING` to the intent."],
        "reference": "Spec 058 + CAPABILITY-AUTHORING §Reflection write convention",
        "example": "ctx.link(rid, intent, 'SERVES'); ctx.link(rid, intent, 'OBSERVED_DURING')",
    }

    def check(self, target):
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
        cap = target.cap
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


class NameTokenBudgetRule(CapabilityLintRule):
    kind = "name_token_budget"
    severity = "soft"
    remediation = {
        "what": "A verb's wire name exceeds the cl100k token budget.",
        "steps": [
            "Shorten the verb name where it reads no worse (record_authoring_outcome → record_outcome).",
            "The prefix `capability_<cap>_` is the bulk of the cost; the bare code-mode "
            "alias is the real fix but is FastMCP-blocked (Spec 069 cancelled).",
            "If the wire form is being kept by design, accept it (this is a standing accept).",
        ],
        "reference": "Spec 049 audit + CORE §Naming (wire form kept)",
        "example": "capability_develop_record_authoring_outcome (8 tok) → record_outcome",
    }

    def __init__(self, budget: int = _WIRE_NAME_BUDGET):
        self.budget = budget

    def check(self, target):
        """Spec 067 (WARN): a verb whose wire name (`capability_<cap>_<verb>`) exceeds
        the cl100k token budget — the repeated discovery tax (GOALS #1; the bare
        code-mode alias in Spec 069 is the fix). Skips silently if tiktoken missing."""
        try:
            import tiktoken
        except ImportError:
            return []
        enc = tiktoken.get_encoding("cl100k_base")
        cap = target.cap
        out = []
        for verb_name in cap.verbs:
            wire = f"capability_{cap.name}_{verb_name}"
            n = len(enc.encode(wire))
            if n > self.budget:
                out.append({
                    "verb": verb_name, "kind": "name_token_budget",
                    "msg": f"wire name {wire!r} is {n} cl100k tokens (budget {self.budget})",
                    "fix": "shorten the verb name and/or expose a bare code-mode alias (Spec 069)",
                })
        return out


class SurfaceSizeRule(CapabilityLintRule):
    kind = "surface_size"
    severity = "soft"
    remediation = {
        "what": "A capability carries more verbs than the budget.",
        "steps": [
            "Audit the capability's verbs for genuine near-duplicates (Spec 070).",
            "Collapse each near-duplicate pair behind ONE verb + a discriminating param.",
            "Alias-and-deprecate the old verb names (old → new+param for one minor).",
            "If the verbs are genuinely distinct, the surface is legitimately broad — "
            "accept with `# agency-accept-warn: surface_size <why>`.",
        ],
        "reference": "Spec 070 + CAPABILITY-AUTHORING §Token-economy budgets",
        "example": "jules.status + jules.status_all → jules.status(all=False)",
    }

    def __init__(self, max_verbs: int = _SURFACE_VERB_BUDGET):
        self.max_verbs = max_verbs

    def check(self, target):
        """Spec 067 (WARN): a capability carrying more than `max_verbs` verbs without
        sub-grouping — tiered discovery (Spec 068) or consolidation (Spec 070) is the
        answer (jules = 22 today)."""
        cap = target.cap
        n = len(cap.verbs)
        if n > self.max_verbs:
            return [{
                "verb": None, "kind": "surface_size",
                "msg": f"capability {cap.name!r} has {n} verbs (> {self.max_verbs})",
                "fix": "tier discovery (Spec 068) or collapse near-duplicate verbs (Spec 070)",
            }]
        return []


# ---- registry-level rules -------------------------------------------------

class BareNameUniqueRule(RegistryLintRule):
    """Emits two kinds: ``bare_name_collision`` + ``bare_name_contract_shadow``.
    ``kind`` names the primary; both share this rule's traversal."""
    kind = "bare_name_collision"
    remediation = {
        "what": "Two capabilities own the same bare verb name.",
        "steps": [
            "Pick a disambiguating bare form for one of them, OR keep the prefix.",
            "Only load-bearing if/when bare code-mode dispatch ships (deferred, Spec 069).",
        ],
        "reference": "Spec 049 §4 + Spec 069 (cancelled)",
        "example": "dogfood.note / reflect.note → keep prefixed, or dogfood.log_note",
    }

    def check(self, registry):
        """Spec 067 (WARN, registry-level): cross-capability bare-verb collisions +
        shadows of the code-mode contract tools. Gates the bare-name dispatch surface
        (Spec 069) — a bare alias can only ship when its name is unambiguous."""
        from collections import defaultdict
        by: dict[str, set] = defaultdict(set)
        for cap_name in registry.names():
            for v in registry.get(cap_name).verbs:
                by[v].add(cap_name)
        out = []
        for v, caps in sorted(by.items()):
            if len(caps) > 1:
                out.append({
                    "verb": v, "kind": "bare_name_collision",
                    "msg": f"bare verb {v!r} owned by {sorted(caps)} — ambiguous under bare dispatch",
                    "fix": "keep the prefix or pick a disambiguating bare form (Spec 069)",
                })
            if v in _CONTRACT_TOOLS:
                out.append({
                    "verb": v, "kind": "bare_name_contract_shadow",
                    "msg": f"bare verb {v!r} ({sorted(caps)}) shadows the code-mode contract tool {v!r}",
                    "fix": "rename the verb's bare alias so it can't shadow search/get_schema/execute (Spec 069)",
                })
        return out


class SkillNameParityRule(RegistryLintRule):
    kind = "skill_name_parity"
    remediation = {
        "what": "An ontology.skills key has no matching SKILL.md folder (the two surfaces diverge).",
        "steps": [
            "Choose ONE canonical name per skill across both surfaces (Spec 071).",
            "Alias the old name for one minor (walker + marketplace lookup).",
        ],
        "reference": "Spec 071 + CORE §Skills (one name per skill)",
        "example": "ontology `tdd` ↔ folder `test-driven-development` → reconcile",
    }

    def check(self, registry):
        """Spec 067 (WARN, registry-level): an `ontology.skills` key with no matching
        `skills/<key>/SKILL.md` folder — the two skill surfaces diverge (Spec 071,
        e.g. `tdd` ↔ `test-driven-development`). Folder-only skills (marketplace docs
        without a walkable template) are NOT flagged."""
        import glob
        import os
        onto_obj = getattr(registry, "ontology", None)
        onto = set(getattr(onto_obj, "skills", {}) or {}) if onto_obj is not None else set()
        folders = {os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")}
        out = []
        for key in sorted(onto - folders):
            out.append({
                "verb": None, "kind": "skill_name_parity",
                "msg": f"ontology skill {key!r} has no matching skills/{key}/SKILL.md folder",
                "fix": "reconcile the name across both skill surfaces (Spec 071)",
            })
        return out


# ---- the registries -------------------------------------------------------
# Adding a rule = add a class above + append it here. lint_capability /
# lint_surface iterate these polymorphically; no other site changes.

# Block-severity capability rules (participate in the block-mode verdict).
_CAPABILITY_BLOCK_RULES: list[CapabilityLintRule] = [
    StructuralRule(),
    RoleTagRule(),
    RenderSliceRule(),
    ConsumerContractRule(),
    TokenBudgetRule(),
    WireShapeRule(),
    TemplateFolderRule(),
    ReservedParamRule(),          # Spec 092 G2 hard
]

# Soft (WARN-only) capability rules — never block, even in block mode.
_CAPABILITY_SOFT_RULES: list[CapabilityLintRule] = [
    NodeIdGuardRule(),
    ReflectionLinkRule(),
    NameTokenBudgetRule(),
    SurfaceSizeRule(),
    ReservedReturnKeyRule(),      # Spec 092 G2 soft
]

# Registry-level (cross-capability) rules.
_REGISTRY_RULES: list[RegistryLintRule] = [
    BareNameUniqueRule(),
    SkillNameParityRule(),
]

# The single source of remediation recipes, derived from the rule classes
# (every kind a rule can emit → its recipe). BareNameUniqueRule emits two
# kinds; the second (contract_shadow) carries its own recipe here.
# AGENCY-DRIFT: accepted-warns — keep the reasons (below) current.
_EXTRA_REMEDIATION = {
    "bare_name_contract_shadow": {
        "what": "A bare verb name shadows a code-mode contract tool.",
        "steps": ["Rename the verb's bare alias so it can't shadow search/get_schema/execute."],
        "reference": "Spec 049 §4 + CORE §Naming",
        "example": "reflect.search → reflect.find_notes (under a bare-name surface)",
    },
}


def _build_remediation() -> dict:
    out: dict = {}
    for rule in (_CAPABILITY_BLOCK_RULES + _CAPABILITY_SOFT_RULES + _REGISTRY_RULES):
        if rule.kind and rule.remediation:
            out[rule.kind] = dict(rule.remediation)
    out.update(_EXTRA_REMEDIATION)
    return out


# Back-compat alias — the per-rule rework recipe, single source. Built from the
# rule classes so a new rule's recipe ships with the rule (OCP).
_REMEDIATION = _build_remediation()


# Standing accepts — WARNs the project has DECIDED to keep, with the reason
# (so the open-WARN set is genuine work). Per-site `# agency-accept-warn:` markers
# add to this. AGENCY-DRIFT: accepted-warns — keep the reasons current.
_STANDING_ACCEPTS = {
    "name_token_budget": "wire form kept (CORE §Naming); bare alias FastMCP-blocked — Spec 069 cancelled",
    "bare_name_collision": "wire names are unique; bare dispatch deferred — Spec 069 cancelled",
    "bare_name_contract_shadow": "wire form keeps reflect.search disambiguated — Spec 069 cancelled",
    "skill_name_parity": "tracked divergence; reconciliation deferred to Spec 071",
}


# ---------------------------------------------------------------------------
# Spec 092 G2 reserved-name check (shared by the two reserved rules).
# ---------------------------------------------------------------------------

def _check_reserved_names(cap) -> list[dict]:
    """Spec 092 G2 — author-time guards for the two reserved-name collisions that each
    crash at runtime: a verb PARAMETER named like a reserved injected param, and a verb
    that RETURNS a string under the key ``artefact`` (which the Registry auto-records as
    an Artefact props dict). Returns findings (param = hard; return-key = soft WARN)."""
    import ast
    import inspect
    import textwrap

    findings: list[dict] = []
    for vname, spec in cap.verbs.items():
        fn = spec.get("fn")
        method = getattr(fn, "__capability_method__", fn)
        inject = set(spec.get("inject", []))
        try:
            params = list(inspect.signature(method).parameters)
        except (TypeError, ValueError):
            params = []
        for pname in params:
            if pname == "self" or pname in inject:
                continue
            if pname in _RESERVED_PARAMS:
                findings.append({
                    "verb": vname, "kind": "reserved_param_name", "hard": True,
                    "msg": f"verb {vname!r} declares a parameter named {pname!r}, which "
                           f"collides with the reserved injected param (duplicate parameter "
                           f"name at signature build).",
                    "fix": f"rename it; read the serving value ambiently via self.ctx.{pname} "
                           f"instead of taking it as a parameter."})
        # best-effort AST: a Return dict literal with an 'artefact' key whose value is a
        # bare literal/name (not a dict/call) collides with the auto-artefact-record.
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
        except (OSError, TypeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)):
                continue
            for key, val in zip(node.value.keys, node.value.values):
                if (isinstance(key, ast.Constant) and key.value == "artefact"
                        and not isinstance(val, (ast.Dict, ast.Call))):
                    findings.append({
                        "verb": vname, "kind": "reserved_return_key", "hard": False,
                        "msg": f"verb {vname!r} returns key 'artefact' with a non-dict value; "
                               f"the Registry auto-records result['artefact'] as Artefact "
                               f"props (dict) — a string/id here crashes the unwrap.",
                        "fix": "use a different key (e.g. 'artefact_id') for an id; reserve "
                               "'artefact' for an artefact props dict."})
    return findings


# ---------------------------------------------------------------------------
# Remediation enrichment + accept mechanism (Spec 074).
# ---------------------------------------------------------------------------

def _with_remediation(finding: dict) -> dict:
    """Spec 074 — enrich a finding with its rework recipe (additive; the existing
    {verb, kind, msg, fix} keys are preserved)."""
    rem = _REMEDIATION.get(finding.get("kind"), {})
    out = {**finding,
           "severity": finding.get("severity", "warn"),
           "steps": rem.get("steps", []),
           "reference": rem.get("reference", "")}
    if rem.get("example"):
        out["example"] = rem["example"]
    return out


def _accepted_kinds(source_text: str = "") -> dict:
    """The accepted-WARN kinds → reason: the standing set plus any
    `# agency-accept-warn: <kind> <reason>` markers in `source_text`."""
    acc = dict(_STANDING_ACCEPTS)
    for m in _ACCEPT_RE.finditer(source_text or ""):
        acc[m.group(1)] = m.group(2).strip() or "accepted at site"
    return acc


def _split_accepted(findings: list, accepts: dict):
    """Enrich + split findings into (open, accepted). Accepted findings carry an
    `accept_reason` and severity='accepted'; open findings stay WARN."""
    open_f, accepted_f = [], []
    for f in findings:
        f = _with_remediation(f)
        reason = accepts.get(f["kind"])
        if reason:
            accepted_f.append({**f, "severity": "accepted", "accept_reason": reason})
        else:
            open_f.append(f)
    return open_f, accepted_f


# ---------------------------------------------------------------------------
# Skill-doc / skill linting (not capability-graph rules — distinct inputs).
# ---------------------------------------------------------------------------

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


# Spec 377 — the Tier-B render placeholder that must never reach disk (373 Slice 3
# kills its generation; this blocks it if it ever slips into a committed skill).
_TIER_B_STUB = "(Tier B"


def lint_skill_schema(skill: dict, verbs_index: dict | None = None) -> dict:
    """Spec 377 — strict lint over a 371 Skill dict (a committed `skill.yaml`,
    a pillar, or a rendered skill), beyond the SkillDoc shape `lint_skill_doc`
    checks. Makes a thin / stub / non-self-contained skill FAIL where it used to
    pass.

    Rules:
    - ``schema`` — `parse_skill` validates structure AND per-type completeness
      (a typed skill MUST carry its R15 required core); a failure short-circuits
      (the typed checks below need a parsed skill).
    - ``description-trigger-first`` (R1) — the description is a 'Use when…' trigger.
    - ``phase-self-contained`` (A1) — every phase carries non-empty `instructions`.
    - ``no-stub`` — no `(Tier B…)` placeholder text anywhere in the skill.
    - ``verb-resolves`` — a phase's `invoke` binding names a LIVE verb (pass
      ``verbs_index={cap: {verb, …}}``; the loose advisory `verbs` list is NOT
      strictly resolved — it legitimately names skills/methods, not just verbs).

    Returns ``{ok, violations: [{rule, message}]}``."""
    from ...._skill_parse import parse_skill

    res = parse_skill(skill)
    if not res.ok:
        return {"ok": False, "violations": [
            {"rule": "schema", "message": f"{res.code}: {res.message}"}]}
    sk = res.value
    v: list[dict] = []
    desc = (sk.description or "").strip()
    if desc and not desc.lower().startswith("use when"):
        v.append({"rule": "description-trigger-first",
                  "message": "description must start with 'Use when…' (R1)"})
    for p in sk.phases:
        if not (p.instructions or "").strip():
            v.append({"rule": "phase-self-contained",
                      "message": (f"phase {p.name!r} has empty `instructions` — a "
                                  f"self-contained skill spells out each phase (A1)")})
    import json as _json
    if _TIER_B_STUB in _json.dumps(skill):
        v.append({"rule": "no-stub",
                  "message": f"skill carries a {_TIER_B_STUB}…) stub placeholder"})
    if verbs_index is not None:
        for p in sk.phases:
            if p.invoke is None:
                continue
            cap, vb = p.invoke
            if cap in verbs_index and vb not in verbs_index[cap]:
                v.append({"rule": "verb-resolves",
                          "message": (f"phase {p.name!r} invokes {cap}.{vb} — "
                                      f"not a verb of capability {cap!r}")})
    return {"ok": not v, "violations": v}


def partition_discipline_lint(disciplines: dict, verbs_index: dict) -> dict:
    """Spec 378 Slice 4 — the graduated discipline gate. Lints every discipline and
    partitions it by whether it has OPTED INTO the self-contained contract:

    - ``clean``   — self-contained (every phase has `instructions`) AND passes lint.
    - ``blocked`` — self-contained but FAILS another rule (no-stub / verb-resolves /
                    schema): a regression on a migrated discipline — fail the gate.
    - ``warned``  — not yet self-contained (the migration tail): surfaced, not fatal,
                    until its capability is migrated (then it auto-joins the gate).

    `disciplines`: ``{name: skill_dict}``. Returns ``{ok, clean, warned, blocked}``
    where ``ok = not blocked`` (a filled discipline must stay compliant; an unfilled
    one only warns). The set self-WIDENS — a discipline joins the block set the
    moment its phases gain instructions, no manual list."""
    clean: list[str] = []
    warned: list[dict] = []
    blocked: list[dict] = []
    for name in sorted(disciplines):
        skill = disciplines[name]
        phases = skill.get("phases", [])
        compliant = bool(phases) and all(
            (p.get("instructions") or "").strip() for p in phases)
        res = lint_skill_schema(skill, verbs_index=verbs_index)
        if res["ok"]:
            clean.append(name)
        elif compliant:
            blocked.append({"name": name, "violations": res["violations"]})
        else:
            warned.append({"name": name, "violations": res["violations"]})
    return {"ok": not blocked, "clean": clean, "warned": warned, "blocked": blocked}


# ---------------------------------------------------------------------------
# The orchestrators — iterate the rule registries polymorphically.
# ---------------------------------------------------------------------------

def lint_capability(cap) -> dict:
    """Run the rule families against `cap` (a Capability instance).

    Mode dispatch: if the capability's source file carries the
    `# agency-scaffold: …` marker on its first non-blank line → BLOCK
    mode (violations are real errors, ok=False). Otherwise WARN mode
    (legacy grandfathering — violations move to warnings, ok=True).

    Spec 056 — soft rules are WARN-ONLY (regardless of mode) during their
    migration window: they surface as warnings even in block mode so a
    scaffold-marked capability isn't broken before the audit completes.

    Returns: {ok, violations, warnings, skipped, mode}."""
    source_path = _capability_source_path(cap)
    mode = "block" if _has_scaffold_marker(source_path) else "warn"
    target = _CapTarget(cap, source_path)

    # Polymorphic dispatch over the rule registries.
    all_findings: list[dict] = []
    for rule in _CAPABILITY_BLOCK_RULES:
        all_findings.extend(rule.check(target))
    soft_findings: list[dict] = []
    for rule in _CAPABILITY_SOFT_RULES:
        soft_findings.extend(rule.check(target))

    # Spec 074 — enrich with remediation; split soft WARNs into open vs accepted
    # (standing accepts + per-site `# agency-accept-warn:` markers in the source).
    src_text = ""
    if source_path:
        try:
            src_text = open(source_path, encoding="utf-8").read()
        except OSError:
            pass
    soft_open, soft_accepted = _split_accepted(soft_findings, _accepted_kinds(src_text))
    hard = [_with_remediation(f) for f in all_findings]
    if mode == "block":
        return {"ok": not all_findings, "violations": hard,
                "warnings": soft_open, "accepted": soft_accepted, "skipped": 0, "mode": mode}
    # warn mode — findings move to warnings; ok always True
    return {"ok": True, "violations": [], "warnings": hard + soft_open,
            "accepted": soft_accepted, "skipped": 0, "mode": mode}


def lint_surface(registry) -> dict:
    """Spec 067 — the registry-level (cross-capability) WARN rules: bare-name
    uniqueness + skill-surface parity. Spec 074 — findings carry remediation +
    split into open `warnings` vs `accepted` (recorded-reason WARNs).

    Returns: ``{ok: True, warnings: [...], accepted: [...], mode: 'warn'}``.
    """
    findings: list[dict] = []
    for rule in _REGISTRY_RULES:
        findings.extend(rule.check(registry))
    open_f, accepted_f = _split_accepted(findings, _accepted_kinds())
    return {"ok": True, "warnings": open_f, "accepted": accepted_f, "mode": "warn"}


def lint_explain(rule: str) -> dict:
    """The wire-shape payload for the `lint_explain` verb (Spec 074)."""
    rem = _REMEDIATION.get(rule)
    if not rem:
        return {"result": {"error": f"no remediation recipe for rule {rule!r}",
                           "known": sorted(_REMEDIATION)}}
    return {"result": {"kind": rule, **rem}}


class LintMixin(CapabilityBase):
    """Verbs that LINT skills + capabilities against the authoring doctrine."""

    @verb(role="transform")
    def lint_skill(self, name: str, description: str) -> dict:
        """Lint a skill description against the CSO + length rules.

        Inputs: name (slug), description (the SKILL.md description field).
        Returns: ``{ok, violations}``.
        chain_next: fix violations + re-lint OR write the skill if ``ok=True``.
        """
        return lint_skill(name, description)

    @verb(role="transform")
    def lint_skill_schema(self, skill: dict) -> dict:
        """Strict per-type + self-containment + no-stub + verb-resolves lint over a
        371 Skill dict (Spec 377) — beyond the SkillDoc shape ``lint_skill`` checks.

        Inputs: skill (a Skill dict — name, kind, type?, description?, phases?, …).
        Returns: ``{ok, violations: [{rule, message}]}``.
        chain_next: fix the flagged sections + re-lint; ``install.generate`` /
                    ``check-drift`` gate on this (graduated warn→block, Slice 2).
        """
        verbs_index = {c: set(self.ctx.registry.get(c).verbs)
                       for c in self.ctx.registry.names()}
        return lint_skill_schema(skill, verbs_index=verbs_index)

    @verb(role="transform")
    def lint_disciplines(self) -> dict:
        """The graduated discipline gate (Spec 378 Slice 4): strict-lint every
        registered discipline, partitioned into clean / warned (the migration tail)
        / blocked (a self-contained discipline that regressed).

        Inputs: none.
        Returns: ``{ok, clean: [name], warned: [{name, violations}],
                 blocked: [{name, violations}]}`` — ``ok`` is False iff a
                 self-contained discipline fails the contract.
        chain_next: fix any ``blocked`` discipline; fill a ``warned`` one's phase
                    instructions to move it into the gate.
        """
        from ...skills._main import _all_skills
        skills = _all_skills(self.ctx.registry)
        disciplines = {n: m["_schema"] for n, m in skills.items()
                       if m["kind"] == "discipline"}
        verbs_index = {c: set(self.ctx.registry.get(c).verbs)
                       for c in self.ctx.registry.names()}
        return partition_discipline_lint(disciplines, verbs_index)

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
    def lint_explain(self, rule: str) -> dict:
        """Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it.

        Inputs: rule (the finding ``kind``, e.g. 'surface_size', 'reflection_link').
        Returns: ``{kind, what, steps, reference, example?}`` (wire shape); or
                 ``{error, known}`` when the rule kind is unrecognised.
        chain_next: apply the ``steps``, then re-run ``plugin.lint_capability``.
        """
        return lint_explain(rule)
