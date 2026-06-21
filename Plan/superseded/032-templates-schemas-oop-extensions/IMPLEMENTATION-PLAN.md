# Spec 032 — Templates & Schemas as OOP Capability Extensions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ArtefactSchemas` + `RenderTemplates` first-class OOP extensions on `CapabilityBase` (parallel to Spec 031's `SkillDoc` + `WalkerSkills`), backed by per-capability `templates/` + `schemas/` folders, with an engine bootstrap loader + bi-temporal materialiser that records `Schema`/`Template` nodes for production validation.

**Architecture:** Four new dataclasses on `agency/capability.py` (`TemplateDoc`, `SchemaDoc`, `RenderTemplates`, `ArtefactSchemas`). New loader at `agency/_capability_loader.py` (path-safe, lint-clean, kebab-case rule). New `agency/render/` folder for engine-owned templates (was: Python `Template` constants in `templates.py`). New materialiser methods on `Ontology`. Two `Memory` schema-validation methods (simple + draft-07). Engine bootstrap orchestrates: extend → load folders → resolve mixed-mode → lint → memory → materialise.

**Tech Stack:** Python 3.11+, stdlib only (no jinja2/yaml; uses `json` + `string.Template` + `pathlib.Path`). Existing `jsonschema` extra (Spec 010 `[novel]`) optional for draft-07.

---

## Phases overview (each independently PR-able)

| Phase | Tasks | Independent PR? | What lands |
|---|---|---|---|
| **1 — Foundation** | 1.1–1.4 | Yes | Four new dataclasses + path-safe loader + agency/render/ files migrated from in-Python constants |
| **2 — Materialiser** | 2.1–2.3 | Yes | `Ontology.materialise_schemas/templates` with bi-temporal supersede + `Memory.validate_schema_draft07` + Spec 004 retroactive coverage |
| **3 — Loader integration** | 3.1–3.3 | Yes | `_capability_loader.load_capability_folders` + Engine bootstrap call + mixed-mode resolution table + unified `AGENCY_BOOTSTRAP_LINT` gate |
| **4 — Migration** | 4.1–4.4 | Yes | reflect / jules / delegate / plugin capabilities migrated to file-based form per F-6 5-step recipe |
| **5 — SKILL.md sections + tests + PR** | 5.1–5.4 | Yes | Generated SKILL.md gains Templates/Schemas sections; extended TEST-2 (F-15); status flip + PR |

---

## File Structure (summary; full list in spec.md `affects:`)

**New:**
- `agency/_capability_loader.py` — discovers + loads + lints per-cap folders
- `agency/render/` — engine-owned template files (was Python constants)
- `agency/render/{capability-skill,verb-reference,help-index}.md` + `bash-wrapper.sh` + `skill-md.tpl` + `command-md.tpl` + `step-doc.md`
- `agency/capabilities/{reflect,jules,plugin}/` — folder migrations (each contains `_main.py`, `templates/`, `schemas/`)
- `tests/test_capability_loader.py`, `tests/test_materialiser.py`, `tests/test_mixed_mode_compat.py`, `tests/test_path_safety.py`

**Modified:**
- `agency/capability.py` — 4 new dataclasses + 2 `ClassVar` attrs
- `agency/engine.py` — bootstrap pipeline extension
- `agency/ontology.py` — materialiser methods
- `agency/memory.py` — `validate_schema_draft07`
- `agency/install.py` — load templates from `agency/render/` (not in-Python constants)
- `agency/templates.py` — KEPT but only as helpers (`manifest_obj`, `marketplace_obj`, `_yaml_scalar`); Template constants removed

---

## Phase 1 — Foundation

### Task 1.1: Four new dataclasses (`agency/capability.py`)

**Files:** Modify `agency/capability.py`; create `tests/test_oop_extensions_dataclasses.py`.

- [ ] **Step 1: Write the failing test:**

```python
# tests/test_oop_extensions_dataclasses.py
"""Spec 032 §A — TemplateDoc / SchemaDoc / RenderTemplates / ArtefactSchemas."""
from pathlib import Path

from agency.capability import (
    TemplateDoc, SchemaDoc, RenderTemplates, ArtefactSchemas, CapabilityBase,
)


def test_template_doc_fields():
    td = TemplateDoc(
        description="Use when rendering a note",
        canonical_example="ctx.render('foo', x='y')",
    )
    assert td.description == "Use when rendering a note"


def test_schema_doc_fields():
    sd = SchemaDoc(
        description="Use when validating a foo",
        canonical_example="memory.validate_schema(id, 'schema:foo')",
    )
    assert sd.description == "Use when validating a foo"


def test_render_templates_holds_folder_and_docs_dict():
    rt = RenderTemplates(folder=Path("/tmp/templates"), docs={
        "foo": TemplateDoc(description="Use when X", canonical_example="..."),
    })
    assert rt.folder == Path("/tmp/templates")
    assert "foo" in rt.docs


def test_artefact_schemas_holds_folder_and_docs_dict():
    asch = ArtefactSchemas(folder=Path("/tmp/schemas"), docs={})
    assert asch.folder == Path("/tmp/schemas")
    assert asch.docs == {}


def test_render_templates_from_module_classmethod(tmp_path):
    fake_module_file = tmp_path / "fake_main.py"
    fake_module_file.write_text("# stub")
    (tmp_path / "templates").mkdir()
    rt = RenderTemplates.from_module(str(fake_module_file), "templates")
    assert rt.folder == tmp_path / "templates"
    assert rt.docs == {}


def test_artefact_schemas_from_module_classmethod(tmp_path):
    fake_module_file = tmp_path / "fake_main.py"
    fake_module_file.write_text("# stub")
    (tmp_path / "schemas").mkdir()
    asch = ArtefactSchemas.from_module(str(fake_module_file), "schemas")
    assert asch.folder == tmp_path / "schemas"


def test_capabilitybase_attrs_default_to_none():
    class _Cap(CapabilityBase):
        name = "test"
    assert _Cap.render_templates is None
    assert _Cap.artefact_schemas is None
```

- [ ] **Step 2: Run; verify FAIL** — `ImportError`.

- [ ] **Step 3: Add dataclasses to `agency/capability.py`**

Insert after the existing `SkillDoc` / `WalkerSkills` dataclasses (which Spec 031 Task 1.1 added):

```python
from pathlib import Path
import inspect as _inspect


@dataclass
class TemplateDoc:
    """Rendering metadata for ONE template the capability ships (Spec 032 §A).

    Drives one row in the SKILL.md ## Templates table generated by Spec 031's
    install pipeline. A capability with templates that need NO documentation
    can ship them without a TemplateDoc — they'll appear with the filename
    as the only hint.
    """
    description: str
    canonical_example: str


@dataclass
class SchemaDoc:
    """Rendering metadata for ONE schema the capability ships (Spec 032 §A).

    Drives one row in the SKILL.md ## Schemas table. Same shape + purpose as
    TemplateDoc.
    """
    description: str
    canonical_example: str


@dataclass
class RenderTemplates:
    """The capability's owned templates (Spec 032 §A).

    `folder` is the absolute path to the capability's templates/ folder.
    Use the `from_module` classmethod to resolve it relative to the
    capability module's __file__ (avoids `Path(__file__).parent` boilerplate
    and packaging issues — panel F-7).

    `docs` is a dict mapping filename stem to TemplateDoc. Templates without
    a matching doc still load + materialise as Template nodes; they just
    appear without rendering metadata in the SKILL.md table.
    """
    folder: Path
    docs: dict[str, "TemplateDoc"] = field(default_factory=dict)

    @classmethod
    def from_module(cls, module_file: str, subfolder: str = "templates",
                    docs: Optional[dict] = None) -> "RenderTemplates":
        """Resolve folder relative to the capability module's __file__."""
        return cls(folder=Path(module_file).parent / subfolder,
                   docs=docs or {})


@dataclass
class ArtefactSchemas:
    """The capability's owned schemas (Spec 032 §A).

    Same shape as RenderTemplates but for schemas/ folder + SchemaDoc dict.
    """
    folder: Path
    docs: dict[str, "SchemaDoc"] = field(default_factory=dict)

    @classmethod
    def from_module(cls, module_file: str, subfolder: str = "schemas",
                    docs: Optional[dict] = None) -> "ArtefactSchemas":
        """Resolve folder relative to the capability module's __file__."""
        return cls(folder=Path(module_file).parent / subfolder,
                   docs=docs or {})
```

Then in `class CapabilityBase`, add two `ClassVar` attributes after the existing Spec 031 ones:

```python
    # Spec 032 §A — template + schema file-based extensions.
    render_templates: ClassVar[Optional[RenderTemplates]] = None
    artefact_schemas: ClassVar[Optional[ArtefactSchemas]] = None
```

- [ ] **Step 4: Run; verify all 7 tests PASS.**
- [ ] **Step 5: Full suite green** — `python -m pytest -q`.
- [ ] **Step 6: Commit:**

```
git add agency/capability.py tests/test_oop_extensions_dataclasses.py
git commit -m "feat(capability): TemplateDoc + SchemaDoc + RenderTemplates + ArtefactSchemas dataclasses (Spec 032 §A)"
```

---

### Task 1.2: `agency/render/` folder population — migrate Python Template constants to files

**Files:** Create `agency/render/__init__.py`, `agency/render/*.md|.tpl|.sh`; modify `agency/install.py` to load from files; modify `agency/templates.py` to remove Template constants.

**Note (panel F-1 coordination):** Spec 031 Task 1.4 added Python `Template` constants (`CAPABILITY_SKILL_MD`, etc.) to `agency/templates.py`. Spec 032 lands them as FILES in `agency/render/`. The transition steps below assume Task 1.4 has NOT yet landed those constants — if Task 1.4 did land them, this task DELETES them from `templates.py` and writes the file equivalents.

- [ ] **Step 1: Create the render folder + empty marker:**

```bash
mkdir -p /home/user/agency/agency/render
touch /home/user/agency/agency/render/__init__.py
```

- [ ] **Step 2: Write the file equivalents.** For each existing Python `Template` constant (in `agency/templates.py` if it landed via Spec 031 Task 1.4, OR per Spec 031 design §14), extract the template body string and write it to `agency/render/<name>.md` (or `.tpl` / `.sh` per the design).

Specifically:
- `agency/render/capability-skill.md` ← body of `CAPABILITY_SKILL_MD`
- `agency/render/verb-reference.md` ← body of `VERB_REFERENCE_MD`
- `agency/render/bash-wrapper.sh` ← body of `BASH_WRAPPER_SH`
- `agency/render/help-index.md` ← body of `HELP_INDEX_MD`
- `agency/render/skill-md.tpl` ← body of existing `templates.SKILL_MD`
- `agency/render/command-md.tpl` ← body of existing `templates.COMMAND_MD`
- `agency/render/step-doc.md` ← body of existing `templates.STEP_DOC`

(Full bodies are in Spec 031 §14 + the existing `agency/templates.py` source.)

- [ ] **Step 3: Update `agency/install.py` + `agency/capabilities/plugin.py` consumers** to load from files:

Replace `from agency.templates import SKILL_MD` patterns with:

```python
from pathlib import Path
from string import Template

_RENDER_DIR = Path(__file__).parent / "render"

def _load_render_template(name: str) -> Template:
    """Load a template body from agency/render/<name> as a string.Template."""
    path = _RENDER_DIR / name
    return Template(path.read_text())

SKILL_MD = _load_render_template("skill-md.tpl")
COMMAND_MD = _load_render_template("command-md.tpl")
# ... etc.
```

(Could also be a one-time module-init pass that loads all of them; design choice — keep the names available at module level for back-compat.)

- [ ] **Step 4: Delete the Template constants from `agency/templates.py`** (keep helpers — `manifest_obj`, `marketplace_obj`, `_yaml_scalar`, `REQUIRED` if it's still referenced by un-migrated capabilities).

- [ ] **Step 5: Write smoke tests:**

```python
# tests/test_render_folder.py
"""Spec 032 §H — engine-owned templates load from agency/render/ files."""
from pathlib import Path

from agency.templates import SKILL_MD, COMMAND_MD  # or wherever they re-export


def test_skill_md_template_loads_from_file():
    rendered = SKILL_MD.substitute(name="x", description="Use when y",
                                   allowed_tools="  - Read",
                                   title="x", body="hello")
    assert "name: x" in rendered
    assert "hello" in rendered


def test_render_folder_files_exist():
    render = Path(__file__).parent.parent / "agency" / "render"
    assert render.is_dir()
    for name in ("capability-skill.md", "verb-reference.md", "bash-wrapper.sh",
                 "help-index.md", "skill-md.tpl", "command-md.tpl", "step-doc.md"):
        assert (render / name).exists(), f"missing {name}"
```

- [ ] **Step 6: Run; verify all pass + full suite still green.**

- [ ] **Step 7: Commit:**

```
git add agency/render/ agency/install.py agency/templates.py agency/capabilities/plugin.py tests/test_render_folder.py
git commit -m "feat(render): migrate engine-owned templates to agency/render/ files (Spec 032 §H)"
```

---

### Task 1.3: Path-safe loader scaffolding (`agency/_capability_loader.py`)

(RED test in `tests/test_capability_loader.py`: load templates+schemas from a synthetic capability folder; verify path safety. GREEN: implement `load_capability_folders(cap)` per spec §B. Commit.)

**Key contract:** `load_capability_folders(cap) → (templates_dict, schemas_dict)` where:
- Returns empty dicts if `cap.render_templates is None` AND `cap.artefact_schemas is None`.
- Walks `cap.render_templates.folder` for `*.md|.tpl|.sh`; each filename stem becomes a key, content becomes a `string.Template`.
- Walks `cap.artefact_schemas.folder` for `*.json`; each filename stem becomes a key, content becomes parsed JSON (dict).
- **Path-safety check (F-9):** every loaded file's `os.path.realpath` MUST start with `os.path.realpath(cap_folder)`. Rejects `..` traversal AND escaping symlinks.
- **Kebab-case rule (NFR-5 / spec.md §B):** filename stem MUST match `^[a-z0-9]+(-[a-z0-9]+)*$`.
- **Empty-folder rule (F-11):** declaring `render_templates` with zero matching files raises `ValueError`.

### Task 1.4: Path-safety tests (`tests/test_path_safety.py`)

(Explicit symlink-escape test: create a synthetic cap folder, symlink a file to `/etc/passwd`, verify loader raises. Plus the `..` traversal test. Commit.)

---

## Phase 2 — Materialiser

### Task 2.1: `Memory.validate_schema_draft07`

(RED test: record a Schema node with draft-07 shape (`schema_json` field present); call `validate_schema_draft07(node, schema_id)`; verify it dispatches to `jsonschema.Draft7Validator` AND raises clear error when `schema_json` field is absent. GREEN: implement in `memory.py`. Commit.)

### Task 2.2: `Ontology.materialise_schemas` + `materialise_templates`

(RED test in `tests/test_materialiser.py`: set up `ontology.schemas = {"foo": ["a","b"]}`; call `materialise_schemas(memory)`; verify a Schema node exists at `schema:foo` with `required="a,b"`. Then change the schema entry to `{"required": ["a","b","c"]}`; re-materialise; verify a NEW node version was recorded via `SUPERSEDED_BY` (bi-temporal — panel F-4). Same for templates. GREEN: implement methods on `Ontology`. Commit.)

### Task 2.3: Retroactive coverage (Spec 004 rolled in)

(Verify materialiser also records Schema nodes for the 5 legacy plugin kinds (`plugin-manifest`, `skill-md`, `command-md`, `marketplace-entry`, `step-doc`) that come in via `OntologyExtension.schemas` dict path. No code change needed — the materialiser iterates the merged ontology regardless of source. Test asserts. Commit.)

---

## Phase 3 — Loader integration

### Task 3.1: `Engine.__init__` bootstrap pipeline extension

(Add `load_capability_folders(cap)` call inside the existing extend loop. Merge results into `ontology.{templates,schemas}` per the mixed-mode resolution table §F. After `Memory(...)` is constructed, call the materialisers. Tests: full bootstrap round-trip for a synthetic capability with both folders. Commit.)

### Task 3.2: Mixed-mode resolution table (`tests/test_mixed_mode_compat.py`)

(4 tests, one per row of the §F table:
- dict-only → loads from dict, no warning
- file-only → loads from file, no warning
- equal-mixed → DeprecationWarning, file wins
- divergent-mixed → InstallError, no engine instance returned

GREEN: implement the resolution logic inside `_capability_loader.load_capability_folders` (or in the engine's merge step). Commit.)

### Task 3.3: Unified `AGENCY_BOOTSTRAP_LINT` env var (F-10)

(Replace Spec 031's `AGENCY_SKILL_DOC_REQUIRED` with three-valued `AGENCY_BOOTSTRAP_LINT ∈ {strict, warn, off}`. All bootstrap lint families honor it. Strict aborts; warn emits warning; off skips. Update Spec 031 tests' monkeypatch.setenv calls to use the new name. Commit. Optional: keep `AGENCY_SKILL_DOC_REQUIRED` as a soft-deprecated alias that maps to `strict` when truthy.)

---

## Phase 4 — Capability migrations (F-6 5-step recipe per cap)

### Task 4.1: reflect (worked example proof)

(Migrate per the spec.md §"Worked example: reflect migration recipe". Folder migration first (mini-Spec-028 for reflect alone), then `templates/reflection-note.md` + `schemas/reflection.json` + `_main.py` SkillDoc+RenderTemplates+ArtefactSchemas declarations. Run `AGENCY_BOOTSTRAP_LINT=strict` + verify clean. Commit.)

### Task 4.2: jules (Spec 004 jules-session target)

(Folder migration + `schemas/jules-session.json` per Spec 004 §reduction/jules-session. `jules.dispatch` records the full required field set + links `VALIDATES_AGAINST schema:jules-session`. Existing test_agency.py assertions on the artefact sub-dict shape updated. Commit.)

### Task 4.3: delegate (Spec 004 reduction target)

(`schemas/reduction.json`. `delegate.join` records full reduction artefact `{parent_intent, children, summary}` + VALIDATES_AGAINST link. Commit.)

### Task 4.4: plugin (5 historic kinds)

(Folder migration + 5 schemas in `schemas/`. Removes `schemas=dict(templates.REQUIRED)` from `plugin_ontology`; replaces with `artefact_schemas = ArtefactSchemas.from_module(...)`. Updates SKILL_CREATION_SKILL etc. references if needed. Commit.)

---

## Phase 5 — SKILL.md sections + Extended TEST-2 + PR

### Task 5.1: SKILL.md `## Schemas` + `## Templates` sections

(Update `CAPABILITY_SKILL_MD` (now at `agency/render/capability-skill.md`) to add the two new sections per spec.md §G. Update Spec 031 emit pipeline (`agency/skill_emit.py`) to populate them from `cap.artefact_schemas.docs` + `cap.render_templates.docs`. Commit.)

### Task 5.2: Extended TEST-2 (F-15) — discipline test

(`tests/test_skill_contract_e2e_with_files.py` — subagent reads only `skills/reflect/SKILL.md` + `schemas/reflection.json` + `templates/reflection-note.md`. Task: construct ctx.render + validate_schema round-trip. Pass iff both succeed WITHOUT source reads of `agency/capabilities/reflect/_main.py`. Commit.)

### Task 5.3: Sunset documentation

(Update `OntologyExtension.__doc__` in `agency/ontology.py` to note the v2 (Spec 04x) removal of `schemas`/`templates` fields. Adds a clear deprecation timeline. Commit.)

### Task 5.4: Status flip + push + PR

- [ ] Update `Plan/superseded/032-templates-schemas-oop-extensions/spec.md` frontmatter: `status: complete` with changelog block.
- [ ] Update `Plan/superseded/004-template-schema-coverage/spec.md` frontmatter: `status: superseded` referencing Spec 032.
- [ ] Run full suite one more time.
- [ ] Push + open PR.

---

## Self-Review

**Spec coverage:**
- §A dataclasses → Task 1.1
- §B loader → Task 1.3
- §C schema-shape detection + validate_schema_draft07 → Tasks 1.3 (detection) + 2.1 (draft07 method)
- §D materialiser (Spec 004 rolled in) → Tasks 2.2 + 2.3
- §E engine bootstrap pipeline → Tasks 3.1 + 3.3 (lint gate generalization)
- §F mixed-mode resolution table → Task 3.2
- §G SKILL.md sections → Task 5.1
- §H agency/render/ folder migration → Task 1.2
- §I capability migrations → Tasks 4.1–4.4
- §J tests → Tasks 1.4 + 2.2 + 3.2 + 5.2

All 5 immediate panel findings (F-1, F-2, F-3, F-4, F-9) folded into the task descriptions above. Short-term findings (F-6 migration recipe, F-7 from_module, F-10 unified env, F-11 empty-folder rule, F-14 loader module placement) also baked into Phase 1+3 task descriptions.

**Placeholder scan:** Tasks 1.3, 1.4, 2.1, 2.2, 2.3, 3.x, 4.x, 5.x are abbreviated to the Task 1.1 / 1.2 shape (the implementer expands them per the explicit RED→GREEN→commit template at execution time).

**Type consistency:** `TemplateDoc`, `SchemaDoc`, `RenderTemplates`, `ArtefactSchemas`, `RenderTemplates.from_module`, `ArtefactSchemas.from_module`, `load_capability_folders`, `materialise_schemas`, `materialise_templates`, `validate_schema_draft07`, `AGENCY_BOOTSTRAP_LINT` — names consistent across tasks.

---

## Execution choice

**Plan complete and saved to `Plan/superseded/032-templates-schemas-oop-extensions/`. Two execution options:**

1. **Subagent-Driven (recommended)** — One implementer subagent per task; spec+code reviewers after each; ~20 dispatches total.
2. **Inline Execution** — Run tasks in this session via `superpowers:executing-plans`; faster but heavier on context.

**Which approach?**
