"""Spec 032 §H — engine-owned templates load from agency/render/ files."""
from pathlib import Path

from agency.templates import SKILL_MD, COMMAND_MD, STEP_DOC


def test_render_folder_files_exist():
    render = Path(__file__).parent.parent / "agency" / "render"
    assert render.is_dir()
    for name in ("capability-skill.md", "verb-reference.md", "bash-wrapper.sh",
                 "help-index.md", "skill-md.tpl", "command-md.tpl", "step-doc.md"):
        assert (render / name).exists(), f"missing {name}"


def test_skill_md_template_loads_from_file():
    rendered = SKILL_MD.substitute(name="x", description="Use when y",
                                   allowed_tools="  - Read",
                                   title="x", body="hello")
    assert "name: x" in rendered
    assert "hello" in rendered


def test_command_md_template_loads_from_file():
    rendered = COMMAND_MD.substitute(description="Use when y", body="hello body")
    assert "Use when y" in rendered
    assert "hello body" in rendered


def test_step_doc_template_loads_from_file():
    rendered = STEP_DOC.substitute(step="my-step", output="my-output",
                                   status="done", inputs="i", notes="n")
    assert "my-step" in rendered or "my-output" in rendered
