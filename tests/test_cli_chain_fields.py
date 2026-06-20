import pytest
from click.testing import CliRunner
import json
import yaml
import tempfile
import os
from agency.cli import cli
from agency._typed_shapes_wave1_part2 import ChainStep

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def intent_id(runner):
    """Create a fresh intent for tests that need one."""
    res = runner.invoke(cli, [
        "intent",
        "--purpose", "test intent",
        "--deliverable", "test output",
        "--acceptance", "exit 0",
    ])
    assert res.exit_code == 0, f"intent creation failed: {res.output}"
    return json.loads(res.output)["intent_id"]

def test_fields_projection_on_auto_verb(runner):
    """Test that generated verbs accept and respect --fields."""
    res = runner.invoke(cli, ["welcome", "--fields", "capabilities"])
    assert res.exit_code == 0
    parsed = json.loads(res.output)
    assert "capabilities" in parsed
    assert "schema_version" not in parsed

def test_fields_projection_on_auto_verb_with_intent(runner, intent_id):
    """Test that a true dynamically generated verb respects --fields when intent_id is passed."""
    res = runner.invoke(cli, ["analyze", "graph", "--intent-id", intent_id, "--fields", "census"])
    assert res.exit_code == 0
    parsed = json.loads(res.output)
    assert "census" in parsed
    assert "nodes" not in parsed

def test_chain_parsing_and_invariants():
    """Test that the ChainStep dataclass enforces invariants."""
    step = ChainStep(cap="analyze", verb="graph", args={})
    assert step.cap == "analyze"

    with pytest.raises(ValueError, match="ChainStep.cap must be non-empty"):
        ChainStep(cap="", verb="graph", args={})

    with pytest.raises(ValueError, match="ChainStep.verb must be non-empty"):
        ChainStep(cap="analyze", verb="", args={})

    with pytest.raises(ValueError, match="ChainStep.args must be a dictionary"):
        ChainStep(cap="analyze", verb="graph", args="not_a_dict")

def test_chain_execution_single_session_and_substitution(runner, intent_id, tmp_path):
    """Test that a chain executes correctly with interpolation and fields filtering."""
    yaml_content = f"""
- cap: discover
  verb: status
  args:
    intent_id: "{intent_id}"
  save_as: result
  fields:
    - nodes
- cap: analyze
  verb: graph
  args:
    intent_id: "{intent_id}"
    node_type: "${{result.nodes.0}}"
  fields:
    - census
    """
    chain_file = tmp_path / "plan.yaml"
    chain_file.write_text(yaml_content)

    res = runner.invoke(cli, ["--chain", str(chain_file)])
    assert res.exit_code == 0
    parsed = json.loads(res.output)

    assert "census" in parsed
    assert "nodes" not in parsed

def test_chain_unknown_ref(runner, intent_id, tmp_path):
    """Test that chain returns CHAIN_UNKNOWN_REF on unresolvable interpolation."""
    yaml_content = f"""
- cap: analyze
  verb: graph
  args:
    intent_id: "{intent_id}"
    scope: "${{missing.field}}"
    """
    chain_file = tmp_path / "plan.yaml"
    chain_file.write_text(yaml_content)

    res = runner.invoke(cli, ["--chain", str(chain_file)])
    assert res.exit_code == 1
    parsed = json.loads(res.output)
    assert parsed.get("error") == "Codes.CHAIN_UNKNOWN_REF"
