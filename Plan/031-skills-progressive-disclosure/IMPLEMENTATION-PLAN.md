# Spec 031 — Skills as Progressive Disclosure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate `skills/<capability>/SKILL.md` + `skills/<capability>/references/<verb>.md` + `bin/agency-<capability>-<verb>` from each capability's declared `SkillDoc` so a fresh agent (Jules, future Claude) can use the MCP surface without reading plugin source.

**Architecture:** Each `CapabilityBase` subclass declares `skill_doc: SkillDoc` (rendering metadata) + optionally `walker_skills: WalkerSkills` (phase-graph schemas). `install.generate(engine)` iterates the registry, calls `skill_emit.emit_skill / emit_references / emit_bash_wrappers` per capability, gated by `lint_skill_doc` in block mode + an idempotency cache. New `skill_list` engine substrate + `skill` capability folder expose the walker over MCP.

**Tech Stack:** Python 3.11+, fastmcp, graphqlite, pytest. Standard agency-repo discipline: `python -m pytest -q` green between each task, one commit per task (RED + GREEN may share a commit when they land same-feature; major boundaries take their own commit).

---

## File Structure

**Phase 1 — Foundation (Spec + Core Extension + Lint + Templates + Doctrine)**
- New: `Plan/031-skills-progressive-disclosure/spec.md` — already written.
- Modify: `agency/capability.py` — `SkillDoc` + `WalkerSkills` dataclasses + `CapabilityBase` attrs.
- Modify: `agency/engine.py` — bootstrap-time `SkillDoc` validation.
- Modify: `agency/capabilities/plugin.py` — `lint_skill_doc` + `author_reference` helpers.
- Modify: `agency/templates.py` — `CAPABILITY_SKILL_MD`, `VERB_REFERENCE_MD`, `BASH_WRAPPER_SH`, `HELP_INDEX_MD`, `RULE_VERSION = 1`.
- New: `docs/vision/SKILL-CONTRACT.md` — the §16 five-obligation doctrine.
- New: `tests/test_skill_doc_validation.py` — bootstrap + lint rules.

**Phase 2 — Generation Pipeline (Emit + Cache + Install integration)**
- New: `agency/skill_emit.py` — `emit_skill / emit_references / emit_bash_wrappers / _capability_hash / _classify_tier`.
- New: `agency/cache.py` — `peek / commit` atomic JSON read/write.
- Modify: `agency/install.py` — `generate()` per-cap delegation + `--dry-run` flag + chmod handling.
- New: `tests/test_skill_emit.py` — per-emit unit tests.
- New: `tests/test_skill_cache_atomic.py` — TEST-3 atomic-kill survival.

**Phase 3 — MCP Wire Surface (skill_list substrate + skill capability folder)**
- Modify: `agency/engine.py` — `skill_list` substrate tool.
- New: `agency/capabilities/skill/__init__.py` — re-export.
- New: `agency/capabilities/skill/_main.py` — `current / submit / done` verbs.
- New: `agency/capabilities/skill/_walker.py` — graph-state recovery for `SkillRun`.
- New: `tests/test_skill_mcp_surface.py` — end-to-end via fastmcp Client.

**Phase 4 — Migration (capabilities declare skill_doc + walker_skills)**
- Modify: `agency/capabilities/reflect.py` — `skill_doc` (worked example, panel F-12).
- Modify: `agency/capabilities/{branch,workspace,dogfood,gate,skill_generator,subagent}.py` — `skill_doc` each (6 trivial).
- Modify: `agency/capabilities/develop.py` — `skill_doc` + `walker_skills` (lifts DEV_SKILLS).
- Modify: `agency/capabilities/plugin.py` — `skill_doc` + `walker_skills` (lifts SKILL_CREATION_SKILL + PLUGIN_DEV_SKILL).
- Modify: `agency/capabilities/delegate.py` — `skill_doc` + `walker_skills` (lifts _DISPATCH_DECISION_SKILL).
- Modify: `agency/capabilities/jules.py` — `skill_doc` + `walker_skills` (lifts JULES_SKILLS).

**Phase 5 — Cleanup + Discipline Test + PR**
- Remove: all hand-authored files under `skills/` (the 11+ pre-existing SKILL.md tree).
- Regenerate: `python -m agency.install` emits the new skills/ + bin/ files.
- New: `tests/test_skill_contract_e2e.py` — TEST-2 the Iron Law discipline test for reflect + jules + develop.
- Push + PR + status flip to `complete` on this spec.

---

## Phase 1 — Foundation

### Task 1.1: SkillDoc + WalkerSkills dataclasses

**Files:**
- Modify: `agency/capability.py` (insert after existing imports + before existing `CapabilityBase`)
- Test: `tests/test_skill_doc_validation.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_skill_doc_validation.py
"""Spec 031 §A — SkillDoc + WalkerSkills dataclasses + bootstrap validation."""
from agency.capability import SkillDoc, WalkerSkills, CapabilityBase


def test_skilldoc_fields_present():
    doc = SkillDoc(
        description="Use when X",
        overview="Y",
        triggers=["t1", "t2"],
        canonical_example="agency-foo-bar baz",
    )
    assert doc.description == "Use when X"
    assert doc.red_flags == []
    assert doc.required_subskills == []
    assert doc.verb_briefs == {}


def test_walkerskills_fields_present():
    ws = WalkerSkills(schemas={"foo": {"name": "foo", "kind": "discipline", "phases": []}})
    assert "foo" in ws.schemas


def test_capabilitybase_attrs_default_to_none():
    class _Cap(CapabilityBase):
        name = "test"
        home = "capability"
    assert _Cap.skill_doc is None
    assert _Cap.walker_skills is None
```

- [ ] **Step 2: Run; verify FAIL**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_doc_validation.py -v
```
Expected: `ImportError: cannot import name 'SkillDoc' from 'agency.capability'`

- [ ] **Step 3: Add the dataclasses + class attrs**

Open `/home/user/agency/agency/capability.py`. Add after the existing imports (after the `from .ontology import OntologyExtension` line):

```python
from typing import ClassVar


@dataclass
class SkillDoc:
    """Rendering metadata for the per-capability SKILL.md emission (Spec 031 §13).

    Single-responsibility: how this capability is documented to a fresh agent.
    No phase-graphs (those live on WalkerSkills); no verb impls (those are
    @verb methods on the capability class).
    """
    description: str                            # "Use when..." trigger-first, no workflow summary
    overview: str                               # 1-2 sentences: what this capability IS
    triggers: list[str]                         # 2-5 concrete symptom matches
    canonical_example: str                      # one-liner: bin/agency-<cap>-<verb> ... OR call_tool(...)
    red_flags: list[str] = field(default_factory=list)
    required_subskills: list[str] = field(default_factory=list)
    verb_briefs: dict[str, str] = field(default_factory=dict)


@dataclass
class WalkerSkills:
    """Phase-graph schemas this capability owns (Spec 031 §13).

    Single-responsibility: what skill-walks this capability provides.
    Schemas keep the existing dict shape ({name, kind, phases:[...]}).
    Merges into OntologyExtension.skills at engine bootstrap; OntologyExtension
    keeps the merge target unchanged for backwards compatibility.
    """
    schemas: dict[str, dict] = field(default_factory=dict)
```

Then in `class CapabilityBase`, add two class-level attributes right after the existing `ontology: OntologyExtension = OntologyExtension()` line:

```python
    # Spec 031 §13 — rendering metadata + walker schemas.
    # `skill_doc` is REQUIRED for any capability with >=1 verb (validated at
    # engine bootstrap); `walker_skills` is optional always.
    skill_doc: ClassVar["SkillDoc | None"] = None
    walker_skills: ClassVar["WalkerSkills | None"] = None
```

- [ ] **Step 4: Run; verify PASS**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_doc_validation.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Full suite still green**

```bash
cd /home/user/agency && python -m pytest -q
```
Expected: 333+ passed (no regressions).

- [ ] **Step 6: Commit**

```bash
cd /home/user/agency
git add agency/capability.py tests/test_skill_doc_validation.py
git commit -m "feat(capability): SkillDoc + WalkerSkills dataclasses (Spec 031 §A)"
```

---

### Task 1.2: Engine bootstrap validation

**Files:**
- Modify: `agency/engine.py` (insert after `for cap in list(discover()) ...` loop)
- Test: `tests/test_skill_doc_validation.py` (append)

- [ ] **Step 1: Append failing test**

```python
# tests/test_skill_doc_validation.py — APPEND

import pytest

from agency.capability import Capability
from agency.engine import Engine


def test_bootstrap_rejects_capability_with_verbs_but_no_skill_doc():
    """A capability declaring verbs must also declare a skill_doc."""
    bad = Capability(
        name="badcap", home="capability",
        verbs={"ping": {"role": "transform", "fn": lambda: {"result": "ok"}, "inject": []}},
    )
    with pytest.raises(ValueError) as ei:
        Engine(":memory:", extra_capabilities=[bad])
    msg = str(ei.value)
    assert "badcap" in msg
    assert "skill_doc" in msg


def test_bootstrap_allows_capability_without_verbs():
    """A capability with no verbs needs no skill_doc."""
    empty = Capability(name="emptycap", home="capability", verbs={})
    e = Engine(":memory:", extra_capabilities=[empty])
    try:
        assert "emptycap" in e.registry.names()
    finally:
        e.memory.close()
```

- [ ] **Step 2: Run; verify both FAIL**

Expected: the first fails because `Engine` doesn't validate today; the second may pass-by-accident.

- [ ] **Step 3: Add validation in `engine.py`**

Open `/home/user/agency/agency/engine.py`. In `Engine.__init__`, find the line that runs after the extend loop (right after `self.registry.ontology = self.ontology`). Add:

```python
        # Spec 031 §A — bootstrap-time skill_doc validation.
        # Any capability that declares verbs MUST declare a skill_doc; otherwise
        # the per-capability skill emit pipeline (Spec 031 Phase 2) cannot render
        # a SKILL.md for it. Fail loud at engine startup, not at install time.
        for cap_name in self.registry.names():
            cap = self.registry.get(cap_name)
            if cap.verbs and getattr(cap, "skill_doc", None) is None:
                raise ValueError(
                    f"capability {cap_name!r} declares verbs but no skill_doc — "
                    f"add `skill_doc = SkillDoc(description='Use when …', "
                    f"overview='…', triggers=[…], canonical_example='…')` to "
                    f"the capability class per Spec 031 §A. See "
                    f"agency/capabilities/reflect.py for the reference shape."
                )
```

**WARNING:** This will break the existing test suite because none of the shipped capabilities have a `skill_doc` yet. Phase 4 lands them; for Phase 1 we need an interim shim. Add this just before the validation loop:

```python
        # Phase-1 transition: until Phase 4 migration lands skill_doc on every
        # shipped capability, allow opt-in via AGENCY_SKILL_DOC_REQUIRED env.
        # Removed in Phase 5 once migration is complete.
        import os as _os
        if _os.environ.get("AGENCY_SKILL_DOC_REQUIRED", "").lower() == "true":
            for cap_name in self.registry.names():
                # (validation block as above)
```

Adjust the validation block to be inside this `if`.

- [ ] **Step 4: Run targeted tests with the env var set**

```bash
cd /home/user/agency && AGENCY_SKILL_DOC_REQUIRED=true python -m pytest tests/test_skill_doc_validation.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Run full suite WITHOUT the env var**

```bash
cd /home/user/agency && python -m pytest -q
```
Expected: 333+ passed (no regressions because the shim defaults to off).

- [ ] **Step 6: Commit**

```bash
cd /home/user/agency
git add agency/engine.py tests/test_skill_doc_validation.py
git commit -m "feat(engine): bootstrap-time skill_doc validation (Spec 031 §A, gated)"
```

---

### Task 1.3: `plugin.lint_skill_doc` — the 9 rule families

**Files:**
- Modify: `agency/capabilities/plugin.py` (insert after `lint_skill`)
- Test: `tests/test_skill_doc_validation.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# tests/test_skill_doc_validation.py — APPEND

from agency.capability import SkillDoc
from agency.capabilities.plugin import lint_skill_doc


def _verbs(*names):
    return {n: {"role": "transform", "fn": lambda: None, "inject": []} for n in names}


def test_lint_passes_clean_skilldoc():
    doc = SkillDoc(
        description="Use when capturing a cross-session insight tagged by scope.",
        overview="Reflect is the cross-session memory layer.",
        triggers=["you learned something a later session shouldn't re-learn",
                  "you want a doctrine observation alongside a code change"],
        canonical_example="agency-reflect-note --intent-id $IID 'observation' 'X → Y'",
        red_flags=["narrative form → re-note in <symptom> → <counter> shape"],
        verb_briefs={"note": "record one"},
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert out["ok"], out["violations"]


def test_lint_rejects_description_without_use_when():
    doc = SkillDoc(
        description="Records a reflection node.",
        overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "description-trigger-first" for v in out["violations"])


def test_lint_rejects_workflow_summary_in_description():
    doc = SkillDoc(
        description="Use when you want to first call X, then Y, then Z.",
        overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "description-no-workflow-summary" for v in out["violations"])


def test_lint_rejects_triggers_with_procedural_verbs():
    doc = SkillDoc(
        description="Use when capturing insights.",
        overview="x",
        triggers=["call reflect.note", "create a reflection"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "triggers-named-symptoms" for v in out["violations"])


def test_lint_rejects_triggers_count_outside_2_5():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["only-one"],
        canonical_example="agency-reflect-note 'x' 'y'",
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "triggers-count" for v in out["violations"])


def test_lint_rejects_example_not_referencing_real_verb():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-foo-bar 'x' 'y'",  # 'bar' isn't a verb of reflect
    )
    out = lint_skill_doc("reflect", doc, _verbs("note", "recall"))
    assert not out["ok"]
    assert any(v["rule"] == "example-uses-real-verb" for v in out["violations"])


def test_lint_requires_red_flags_when_3plus_verbs():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
        red_flags=[],
    )
    out = lint_skill_doc("reflect", doc, _verbs("note", "recall", "search"))
    assert not out["ok"]
    assert any(v["rule"] == "red-flags-required" for v in out["violations"])


def test_lint_rejects_verb_briefs_with_unknown_verb():
    doc = SkillDoc(
        description="Use when X.", overview="x",
        triggers=["a", "b"],
        canonical_example="agency-reflect-note 'x' 'y'",
        verb_briefs={"note": "record one", "phantom": "does not exist"},
    )
    out = lint_skill_doc("reflect", doc, _verbs("note"))
    assert not out["ok"]
    assert any(v["rule"] == "verb-briefs-resolve" for v in out["violations"])
```

- [ ] **Step 2: Run; verify all 8 FAIL**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_doc_validation.py -v
```
Expected: 8 of the new tests fail with `ImportError: cannot import name 'lint_skill_doc'`.

- [ ] **Step 3: Add `lint_skill_doc` to plugin.py**

Open `/home/user/agency/agency/capabilities/plugin.py`. Add at the top (with the other regexes):

```python
_WORKFLOW_SUMMARY_PATTERNS = (
    re.compile(r"\bstep\s+\d", re.I),
    re.compile(r"\bfirst\b.*?\bthen\b", re.I | re.S),
    re.compile(r"\b\d+[.)]\s", re.M),
)

_TRIGGER_PROCEDURAL_VERBS = re.compile(
    r"^\s*(call|create|run|step|then|first|generate|build|write|invoke)\b",
    re.I,
)
```

Then add the function (after the existing `lint_skill` function):

```python
def lint_skill_doc(cap_name: str, doc, verbs: dict) -> dict:
    """Validate a SkillDoc against the Spec 031 §B contract.

    Returns {ok: bool, violations: [{rule, message}]}.
    """
    v: list = []
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
```

- [ ] **Step 4: Run; verify all PASS**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_doc_validation.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Full suite green**

```bash
cd /home/user/agency && python -m pytest -q
```
Expected: 333+ passed.

- [ ] **Step 6: Commit**

```bash
cd /home/user/agency
git add agency/capabilities/plugin.py tests/test_skill_doc_validation.py
git commit -m "feat(plugin): lint_skill_doc — 9 rule families (Spec 031 §B)"
```

---

### Task 1.4: ⚠️ DEFERRED to Spec 032 — Templates (CAPABILITY_SKILL_MD, VERB_REFERENCE_MD, BASH_WRAPPER_SH, HELP_INDEX_MD)

**Status (2026-05-31):** This task is DEFERRED per the Spec 032 spec-panel coordination (panel finding F-1). Rather than landing Python `Template` constants here that Spec 032 immediately migrates to files in `agency/render/`, Spec 032 lands them as files from the start. The 4 templates this task would have added live as:
- `agency/render/capability-skill.md`
- `agency/render/verb-reference.md`
- `agency/render/bash-wrapper.sh`
- `agency/render/help-index.md`

See `Plan/032-templates-schemas-oop-extensions/IMPLEMENTATION-PLAN.md` Task 1.2 for the file-based emission.

The `RULE_VERSION: int = 1` constant referenced here ALSO defers to Spec 032 — it lives alongside the loader (`agency/_capability_loader.py`) since it participates in the capability hash for cache invalidation. Spec 032 ships it there.

**Skip this task. Resume Spec 031 at Task 1.5.**

### (Original Task 1.4 content — for historical reference)

**Files:**
- Modify: `agency/templates.py` (append after existing templates)
- Test: `tests/test_skill_emit.py` (create — minimal smoke test for now)

- [ ] **Step 1: Write a minimal failing smoke test**

```python
# tests/test_skill_emit.py
"""Spec 031 §C — template existence smoke test (full emit covered in Phase 2)."""
from agency.templates import (
    CAPABILITY_SKILL_MD, VERB_REFERENCE_MD, BASH_WRAPPER_SH, HELP_INDEX_MD,
    RULE_VERSION,
)


def test_templates_exist():
    assert CAPABILITY_SKILL_MD is not None
    assert VERB_REFERENCE_MD is not None
    assert BASH_WRAPPER_SH is not None
    assert HELP_INDEX_MD is not None
    assert isinstance(RULE_VERSION, int)
    assert RULE_VERSION >= 1


def test_capability_skill_md_render_minimal():
    rendered = CAPABILITY_SKILL_MD.substitute(
        gen_version=str(RULE_VERSION),
        cap_name="foo",
        description="Use when X",
        overview="Foo does Y.",
        triggers_bulleted="- a\n- b",
        verb_table="| `bar` | act | brief | [details](references/bar.md) |",
        canonical_example="agency-foo-bar 'x'",
        red_flags_bulleted="- rationalization → counter",
        required_subskills_block="",
    )
    assert "name: foo" in rendered
    assert "Use when X" in rendered
    assert "agency-generated: v" in rendered
```

- [ ] **Step 2: Run; verify FAIL**

Expected: `ImportError: cannot import name 'CAPABILITY_SKILL_MD' from 'agency.templates'`.

- [ ] **Step 3: Append templates to `templates.py`**

Open `/home/user/agency/agency/templates.py`. Append:

```python
# Spec 031 §C — templates for the per-capability SKILL.md emission pipeline.
# RULE_VERSION participates in the capability hash; bump it when a template
# shape changes so the install cache (cache.py) regenerates everything.
RULE_VERSION: int = 1


CAPABILITY_SKILL_MD = Template(
    "<!-- agency-generated: v$gen_version -->\n"
    "---\n"
    "name: $cap_name\n"
    "description: $description\n"
    "allowed-tools:\n"
    "  - mcp__plugin_agency_agency__search\n"
    "  - mcp__plugin_agency_agency__get_schema\n"
    "  - mcp__plugin_agency_agency__execute\n"
    "  - Bash\n"
    "---\n"
    "\n"
    "# $cap_name capability\n"
    "\n"
    "$overview\n"
    "\n"
    "## When to use\n"
    "\n"
    "$triggers_bulleted\n"
    "\n"
    "## Verbs\n"
    "\n"
    "| Verb | Role | Brief | Reference |\n"
    "|------|------|-------|-----------|\n"
    "$verb_table\n"
    "\n"
    "## Example\n"
    "\n"
    "```bash\n"
    "$canonical_example\n"
    "```\n"
    "\n"
    "## Red flags — stop and re-read this skill\n"
    "\n"
    "$red_flags_bulleted\n"
    "$required_subskills_block"
)


VERB_REFERENCE_MD = Template(
    "<!-- agency-generated: v$gen_version -->\n"
    "# $verb_full_name\n"
    "\n"
    "$brief\n"
    "\n"
    "## Inputs\n"
    "\n"
    "$inputs_table\n"
    "\n"
    "## Returns\n"
    "\n"
    "$returns\n"
    "\n"
    "## Chain-next\n"
    "\n"
    "$chain_next\n"
    "\n"
    "## Details\n"
    "\n"
    "$body\n"
    "\n"
    "## Example\n"
    "\n"
    "```bash\n"
    "$bash_example\n"
    "```\n"
)


BASH_WRAPPER_SH = Template(
    "#!/usr/bin/env bash\n"
    "# agency-generated: v$gen_version — capability_${cap_name}_${verb_name}\n"
    "# $brief\n"
    "# Usage: $usage\n"
    "set -euo pipefail\n"
    "\n"
    "iid=\"$${AGENCY_INTENT_ID:-}\"\n"
    "args=()\n"
    "while [ $$# -gt 0 ]; do\n"
    "  case \"$$1\" in\n"
    "    --intent-id) iid=\"$$2\"; shift 2;;\n"
    "    --) shift; args+=(\"$$@\"); break;;\n"
    "    *) args+=(\"$$1\"); shift;;\n"
    "  esac\n"
    "done\n"
    "\n"
    "if [ -z \"$$iid\" ]; then\n"
    "  echo \"error: --intent-id or AGENCY_INTENT_ID required\" >&2\n"
    "  exit 1\n"
    "fi\n"
    "\n"
    "$arg_check\n"
    "\n"
    "kwargs=$$(python3 -c '\n"
    "import json, sys\n"
    "print(json.dumps({$kwargs_pairs}))\n"
    "' \"$$iid\" \"$${args[@]}\") || { echo \"error: failed to build kwargs JSON\" >&2; exit 3; }\n"
    "\n"
    "exec python -m agency.cli execute --code \"\n"
    "import json\n"
    "return await call_tool('capability_${cap_name}_${verb_name}', json.loads(r'''$${kwargs}'''))\n"
    "\"\n"
)


HELP_INDEX_MD = Template(
    "<!-- agency-generated: v$gen_version -->\n"
    "---\n"
    "name: help\n"
    "description: Use when you arrived in a repo with the agency plugin and need the capability index without reading source.\n"
    "allowed-tools:\n"
    "  - mcp__plugin_agency_agency__search\n"
    "  - mcp__plugin_agency_agency__get_schema\n"
    "  - mcp__plugin_agency_agency__execute\n"
    "---\n"
    "\n"
    "# agency — capability index\n"
    "\n"
    "$intro\n"
    "\n"
    "**Onboarding:** `agency_welcome` is your first call. See `quickstart.md` for the full first-call sequence.\n"
    "\n"
    "## Capabilities\n"
    "\n"
    "$capability_links\n"
)
```

Note the `$$` escapes — `string.Template` treats `$$` as a literal `$`, which we need for bash `$1` / `${args[@]}` / `$IID` etc.

- [ ] **Step 4: Run; verify PASS**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_emit.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Full suite green**

```bash
cd /home/user/agency && python -m pytest -q
```
Expected: 333+ passed.

- [ ] **Step 6: Commit**

```bash
cd /home/user/agency
git add agency/templates.py tests/test_skill_emit.py
git commit -m "feat(templates): CAPABILITY_SKILL_MD / VERB_REFERENCE_MD / BASH_WRAPPER_SH / HELP_INDEX_MD (Spec 031 §C)"
```

---

### Task 1.5: SKILL-CONTRACT.md doctrine doc

**Files:**
- Create: `docs/vision/SKILL-CONTRACT.md`

- [ ] **Step 1: Create the doctrine doc**

```bash
mkdir -p /home/user/agency/docs/vision
```

Write `/home/user/agency/docs/vision/SKILL-CONTRACT.md` with the §16 doctrine content (the five obligations: WHEN to call, WHICH verb, WHAT it mutates, HOW to recover, WHERE to fetch heavy reference). Lift verbatim from Spec 031 spec.md §"What a skill MUST expose".

- [ ] **Step 2: Cross-link from CORE.md**

Open `/home/user/agency/docs/vision/CORE.md`. Find the Skills/Lifecycle section. Append a line:

```markdown
See [SKILL-CONTRACT.md](SKILL-CONTRACT.md) for the five-obligation contract every generated SKILL.md must satisfy (Spec 031).
```

- [ ] **Step 3: Verify doctrine-doc tests still pass**

```bash
cd /home/user/agency && python -m pytest tests/test_doctrine_docs.py -v
```
Expected: 9 passed (existing tests don't yet cover this doc).

- [ ] **Step 4: Commit**

```bash
cd /home/user/agency
git add docs/vision/SKILL-CONTRACT.md docs/vision/CORE.md
git commit -m "docs: SKILL-CONTRACT.md — the 5 obligations every generated SKILL.md exposes (Spec 031 §L)"
```

---

### Phase 1 checkpoint

After Task 1.5: push the branch, optionally open a draft PR for Phase 1 review. Phase 1 adds infrastructure with no visible behavior change (no skills generated yet).

```bash
cd /home/user/agency
git push -u origin <branch-name>
# Optionally: gh pr create --draft --title "Spec 031 Phase 1 — foundation" --body "..."
```

---

## Phase 2 — Generation Pipeline

### Task 2.1: `_capability_hash` + `_classify_tier`

**Files:**
- Create: `agency/skill_emit.py`
- Test: `tests/test_skill_emit.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# tests/test_skill_emit.py — APPEND

from agency.capability import Capability
from agency.skill_emit import _capability_hash, _classify_tier


def test_capability_hash_stable_across_runs():
    cap = Capability(
        name="x", home="capability",
        verbs={"a": {"role": "transform", "fn": lambda: None, "inject": []}})
    h1 = _capability_hash(cap, rule_version=1)
    h2 = _capability_hash(cap, rule_version=1)
    assert h1 == h2 and len(h1) == 64  # sha256 hex


def test_capability_hash_changes_on_rule_version_bump():
    cap = Capability(
        name="x", home="capability",
        verbs={"a": {"role": "transform", "fn": lambda: None, "inject": []}})
    h1 = _capability_hash(cap, rule_version=1)
    h2 = _capability_hash(cap, rule_version=2)
    assert h1 != h2


def test_classify_tier_full_markers_is_tier_a():
    def fn_a():
        """Brief.

        Inputs: x (str)
        Returns: dict
        chain_next: foo
        """
    assert _classify_tier(fn_a) == "A"


def test_classify_tier_missing_marker_is_tier_b():
    def fn_b():
        """Brief only — no Inputs:/Returns:/chain_next: markers."""
    assert _classify_tier(fn_b) == "B"


def test_classify_tier_terminal_chain_next_counts_as_a():
    def fn_t():
        """Brief.

        Inputs: x
        Returns: y
        chain_next: (terminal)
        """
    assert _classify_tier(fn_t) == "A"
```

- [ ] **Step 2: Run; verify FAIL**

Expected: `ModuleNotFoundError: No module named 'agency.skill_emit'`.

- [ ] **Step 3: Create `agency/skill_emit.py` with both helpers**

```python
# agency/skill_emit.py
"""Spec 031 §D — per-capability skill emission pipeline.

Public surface:
  emit_skill(cap_name, doc, verbs) -> {path: content}
  emit_references(cap_name, verbs) -> {path: content for each Tier-A verb}
  emit_bash_wrappers(cap_name, verbs) -> {path: content for each verb}

Helpers:
  _capability_hash(cap, rule_version) -> sha256 hex (idempotency cache key)
  _classify_tier(verb_fn) -> "A" | "B" (per §5 Gherkin)
"""
from __future__ import annotations

import hashlib
import inspect
import re


_TERMINAL_CHAIN_NEXT = re.compile(r"^\s*\(?(terminal|none)\)?\s*$", re.I)


def _capability_hash(cap, rule_version: int) -> str:
    """sha256 of capability shape + rule_version. Stable across runs."""
    parts = [cap.name]
    for verb_name in sorted(cap.verbs):
        spec = cap.verbs[verb_name]
        fn = spec.get("fn")
        sig = str(inspect.signature(fn)) if fn else ""
        doc = (fn.__doc__ or "") if fn else ""
        parts.append(f"{verb_name}|{spec.get('role')}|{sig}|{doc}")
    parts.append(f"rule_version={rule_version}")
    blob = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _classify_tier(verb_fn) -> str:
    """Tier A iff all three Spec 016 structural markers present + non-empty
    (with terminal chain_next counted as A per §5 Gherkin). Else Tier B."""
    doc = (verb_fn.__doc__ or "")
    from agency.render import parse_slices
    slices = parse_slices(doc)
    inputs = slices.get("inputs", "").strip()
    returns = slices.get("returns", "").strip()
    chain_next = slices.get("chain_next", "").strip()
    if not inputs or not returns:
        return "B"
    if not chain_next:
        return "B"
    # Terminal-by-design counts as A
    return "A"
```

- [ ] **Step 4: Run; verify PASS**

```bash
cd /home/user/agency && python -m pytest tests/test_skill_emit.py -v
```
Expected: 5 passed (the 2 from Task 1.4 + 5 new = 7 total; verify all pass).

- [ ] **Step 5: Commit**

```bash
cd /home/user/agency
git add agency/skill_emit.py tests/test_skill_emit.py
git commit -m "feat(skill_emit): _capability_hash + _classify_tier (Spec 031 §D)"
```

---

### Task 2.2: `emit_skill(cap_name, doc, verbs)`

(See spec.md §D Done When. The implementation reads `doc` + iterates `verbs`, renders `CAPABILITY_SKILL_MD` with the verb table + Tier B anchors, runs `lint_skill_doc` PRE-emit, returns the {path: content} dict.)

- [ ] **Step 1: Write failing test (round-trip: emit + lint clean)**

```python
# tests/test_skill_emit.py — APPEND
from agency.capability import SkillDoc
from agency.skill_emit import emit_skill


def test_emit_skill_renders_clean_skill_md():
    doc = SkillDoc(
        description="Use when capturing a cross-session insight tagged by scope.",
        overview="Reflect is the cross-session memory layer.",
        triggers=["you learned something the next session shouldn't re-learn",
                  "you want a doctrine observation alongside a code change"],
        canonical_example="agency-reflect-note --intent-id $IID 'observation' 'X → Y'",
        red_flags=["narrative form → re-note in <symptom> → <counter> shape"],
        verb_briefs={"note": "record one"},
    )
    def note_fn():
        """Record a scope-tagged Reflection.

        Inputs: scope (str), text (str)
        Returns: {result: <id>}
        chain_next: capability_reflect_recall
        """
    verbs = {"note": {"role": "act", "fn": note_fn, "inject": []}}
    out = emit_skill("reflect", doc, verbs)
    assert "skills/reflect/SKILL.md" in out
    body = out["skills/reflect/SKILL.md"]
    assert body.startswith("<!-- agency-generated: v")
    assert "name: reflect" in body
    assert "[details](references/note.md)" in body
```

- [ ] **Step 2: Run; verify FAIL** — `ImportError` or `AssertionError`.

- [ ] **Step 3: Implement `emit_skill` in `agency/skill_emit.py`**

```python
# Append to agency/skill_emit.py

from agency.templates import CAPABILITY_SKILL_MD, RULE_VERSION


def emit_skill(cap_name: str, doc, verbs: dict) -> dict:
    """Render skills/<cap_name>/SKILL.md from the SkillDoc + verb registry.

    Runs lint_skill_doc PRE-emit; raises ValueError with structured violations
    on failure (no file ever lands with a failing lint).
    """
    from agency.capabilities.plugin import lint_skill_doc
    lint = lint_skill_doc(cap_name, doc, verbs)
    if not lint["ok"]:
        msgs = "; ".join(f"{v['rule']}: {v['message']}" for v in lint["violations"])
        raise ValueError(f"emit_skill({cap_name}): SkillDoc lint failed — {msgs}")

    # Verb table — Tier A linked, Tier B anchor
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

    rendered = CAPABILITY_SKILL_MD.substitute(
        gen_version=str(RULE_VERSION),
        cap_name=cap_name,
        description=doc.description,
        overview=doc.overview,
        triggers_bulleted="\n".join(f"- {t}" for t in doc.triggers),
        verb_table="\n".join(table_rows),
        canonical_example=doc.canonical_example,
        red_flags_bulleted="\n".join(f"- {r}" for r in (doc.red_flags or [])) or "- (none documented)",
        required_subskills_block=("\n## Required sub-skills\n\n" +
                                  "\n".join(f"- **REQUIRED SUB-SKILL:** {s}"
                                            for s in doc.required_subskills)
                                  if doc.required_subskills else ""),
    )
    if tier_b_anchors:
        rendered += "\n" + "\n\n".join(tier_b_anchors) + "\n"
    return {f"skills/{cap_name}/SKILL.md": rendered}


def _first_sentence_brief(fn) -> str:
    if not fn or not fn.__doc__:
        return "(no docstring)"
    from agency.render import parse_slices
    return parse_slices(fn.__doc__)["brief"] or "(no brief)"


def _render_tier_b_anchor(verb_name: str, fn, brief: str) -> str:
    sig = str(inspect.signature(fn)) if fn else "()"
    return (f"## {verb_name}\n\n{brief}\n\n"
            f"Parameters: `{sig}`.\n\n"
            f"_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; "
            f"reference is in-skill only. Add markers to upgrade to a separate references/{verb_name}.md.)_")
```

- [ ] **Step 4: Run; verify PASS**

- [ ] **Step 5: Commit**

```bash
cd /home/user/agency
git add agency/skill_emit.py tests/test_skill_emit.py
git commit -m "feat(skill_emit): emit_skill renders SKILL.md with Tier A links + Tier B anchors (Spec 031 §D)"
```

---

### Task 2.3 — Task 2.6: emit_references, emit_bash_wrappers, cache.py atomic, install.generate integration

(Tasks 2.3–2.6 follow the same RED → GREEN → commit pattern as 2.1–2.2. Detailed steps below in the same shape. Each is a separate commit.)

- **Task 2.3**: `emit_references(cap_name, verbs)` — iterates verbs, picks Tier-A, renders `VERB_REFERENCE_MD` per verb, returns `{path: content}`. Tier-B verbs skip (their content lives in `emit_skill` anchors).
- **Task 2.4**: `emit_bash_wrappers(cap_name, verbs)` — iterates verbs, renders `BASH_WRAPPER_SH` per verb with positional-arg mapping from `inspect.signature`. Returns `{path: content}` for `bin/agency-<cap>-<verb>`.
- **Task 2.5**: `cache.py` — `peek` + `commit` with atomic `tmp` + `os.replace`. Includes TEST-3 (`test_skill_cache_atomic.py`) that simulates interrupted commit and verifies `peek` returns None.
- **Task 2.6**: `install.generate(engine)` integration — per-cap iteration, cache check, emit pipeline, cache commit. Plus `install.main(argv)` `--dry-run` flag and `chmod +x` on `bin/agency-*` with RO-mount warning fallback (per §8a failure-modes table).

Each task: 6 steps (write failing test, run RED, implement, run GREEN, full suite, commit). See Task 1.3 for the exact step template — apply the same shape.

---

### Phase 2 checkpoint

After Task 2.6: `python -m agency.install --dry-run` prints the would-write file list with lint results; `python -m agency.install` writes the files to disk. Phase 2 ends with the generator working end-to-end against a single test capability (no shipped capability has a `skill_doc` yet — that's Phase 4).

```bash
cd /home/user/agency
git push
```

---

## Phase 3 — MCP Wire Surface

### Task 3.1: `skill_list` substrate tool in `engine.py`

(RED test in `tests/test_skill_mcp_surface.py`: call `skill_list({})` on a fastmcp `Client`; assert payload shape `{skills, total}` and a known skill is present. GREEN: register in `engine.build_mcp` after `agency_doctor`. Commit.)

### Task 3.2: `skill/` capability folder — `__init__.py` + `_main.py` with three verbs

(RED: dispatch fastmcp `Client.call_tool("capability_skill_current", {"name": "x", "intent_id": "..."})` and assert the payload shape. GREEN: implement `SkillCapability(CapabilityBase)` with `current` / `submit` / `done` verbs. Commit.)

### Task 3.3: `_walker.py` graph state recovery

(RED test: write a Phase node to a graph via raw `memory.record`, then call `SkillCapability.current(name=...)` and verify it returns the NEXT phase, not phase 1. GREEN: implement `resume(memory, intent_id, skill_schema) → SkillRun` per spec.md §H. Commit.)

### Task 3.4: `SkillCapability.skill_doc` (eat its own dogfood)

(Add `skill_doc = SkillDoc(...)` to `SkillCapability`. The walker capability documents itself per the same contract every other capability must. Commit.)

### Phase 3 checkpoint

After Task 3.4: any MCP client can call `skill_list` for discovery + `capability_skill_current / submit / done` to walk. Independent of Phase 2 — Phase 3 works without per-cap SKILL.md files (it walks the dict-shape schemas already in `OntologyExtension.skills`).

```bash
cd /home/user/agency
git push
```

---

## Phase 4 — Migration

### Task 4.1: `reflect.py` — the worked example

(Add `skill_doc` per spec.md §21. Run `python -m agency.install --dry-run` and verify `skills/reflect/SKILL.md` would render clean. Run `lint_skill_doc("reflect", ReflectCapability.skill_doc, ReflectCapability.verbs())` and verify `ok=True`. Commit.)

### Task 4.2: Trivial migration — branch, workspace, dogfood, gate, skill_generator, subagent

(Each gets a `skill_doc` declaration in its `.py` file. 6 capabilities × ~30 lines each ≈ 180 lines. Each capability is one commit (granular history) OR all six in one commit (faster review) — author's choice. Verify each capability's `skill_doc` passes lint.)

### Task 4.3: develop.py — `skill_doc` + `walker_skills` (lift `DEV_SKILLS`)

(Add `walker_skills = WalkerSkills(schemas=dict(DEV_SKILLS))` on `DevelopCapability`; keep `DEV_SKILLS` as a module-level dict for backwards compat with existing imports. Add `skill_doc`. Commit.)

### Task 4.4: plugin.py — `skill_doc` + `walker_skills` (lift SKILL_CREATION_SKILL + PLUGIN_DEV_SKILL)

(Similar to 4.3 but lifts two skill dicts. Commit.)

### Task 4.5: delegate.py + jules.py — `skill_doc` + `walker_skills`

(Two heavy capabilities. `delegate` lifts `_DISPATCH_DECISION_SKILL`; `jules` lifts the 6 schemas from `_jules_skills.py` into `walker_skills.schemas`. Commit each separately.)

### Phase 4 checkpoint

After Task 4.5: every shipped capability has `skill_doc`. Set `AGENCY_SKILL_DOC_REQUIRED=true` and the full test suite still passes (the bootstrap-validation gate from Task 1.2 is now satisfied). Remove the `if _os.environ.get(...)` shim from `engine.py` — validation runs unconditionally.

```bash
cd /home/user/agency
git push
```

---

## Phase 5 — Cleanup + Discipline Test + PR

### Task 5.1: Remove hand-authored `skills/` files

```bash
cd /home/user/agency
git rm -r skills/authoring-capabilities skills/brainstorming skills/code-review \
       skills/help skills/plugin-development skills/skill-creation \
       skills/spec-panel
# ... whichever exist
git commit -m "chore(skills): remove hand-authored SKILL.md tree (Spec 031 §J — generator owns the namespace)"
```

### Task 5.2: Regenerate install artifacts

```bash
cd /home/user/agency
python -m agency.install
git status   # observe the new skills/<cap>/SKILL.md tree + bin/ wrappers
git add skills/ bin/ .agency/skill-cache.json
git commit -m "chore: regenerate skills/ + bin/ from per-capability SkillDoc (Spec 031 §F)"
```

### Task 5.3: TEST-2 — the Iron Law discipline test

(Write `tests/test_skill_contract_e2e.py`. Dispatch a subagent with `tools=[Read]` and a sandboxed copy of `skills/reflect/`. Task: construct the correct `call_tool("capability_reflect_note", {...})` payload. Forbid reads outside `skills/reflect/`. Assert the constructed call has the right verb name + all required params + correct types. Repeat for `jules` and `develop` capabilities. Three tests in one file. Commit.)

### Task 5.4: Status flip + push + PR

- [ ] Update `Plan/031-skills-progressive-disclosure/spec.md` frontmatter: `status: complete` with a changelog block listing the implementing commit SHAs (Spec 016 pattern).

- [ ] Run the full suite one more time:

```bash
cd /home/user/agency && python -m pytest -q
```
Expected: 333 + N new tests passed.

- [ ] Push + open PR:

```bash
cd /home/user/agency
git push -u origin <branch-name>
# Use mcp__github__create_pull_request as we did for Spec 029/030
```

---

## Self-Review

**Spec coverage:**
- §A Capability core extension → Tasks 1.1 + 1.2
- §B lint_skill_doc → Task 1.3
- §C Templates → Task 1.4
- §D Emit pipeline → Tasks 2.1, 2.2, 2.3, 2.4
- §E Cache → Task 2.5 + TEST-3
- §F Install integration → Task 2.6
- §G skill_list substrate → Task 3.1
- §H skill capability folder → Tasks 3.2, 3.3, 3.4
- §I Migration → Tasks 4.1–4.5
- §J Cleanup → Tasks 5.1 + 5.2
- §K TEST-2 → Task 5.3
- §L Doctrine doc → Task 1.5
- All 8 panel findings → folded into the relevant tasks (Tasks 1.3 has F-2; 2.1 has F-1 paths; 2.5 has F-3 atomic; 1.1+1.3 has F-8 split; 5.3 has F-4; 4.1 has F-12; 2.1 has F-6 Gherkin via `_classify_tier`; 2.2 has F-7 budget enforcement in emit_skill region check).

**Placeholder scan:** Tasks 2.3–2.6 are abbreviated (use the Task 1.3 step template — 6 explicit steps). Tasks 3.1–3.4 + 4.2–4.5 + 5.3 follow the same pattern. The implementer at execution time MUST expand these into bite-sized steps per the Task 1.3 shape, NOT skip the RED step.

**Type consistency:** `SkillDoc` field names, `WalkerSkills.schemas`, `RULE_VERSION`, `emit_skill / emit_references / emit_bash_wrappers / _capability_hash / _classify_tier` signatures match across tasks.

---

## Execution choice

**Plan complete and saved to `Plan/031-skills-progressive-disclosure/`. Two execution options:**

1. **Subagent-Driven (recommended for size)** — Dispatch one subagent per phase (or even per task). Fresh context per task; review between tasks. Slower per task but bulletproof against context drift.
2. **Inline Execution** — Run the tasks in this session via `superpowers:executing-plans`. Batch execution with checkpoints between phases. Faster but heavier on context.

**Which approach?**
