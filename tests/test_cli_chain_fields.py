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

def test_fields_projection_on_auto_verb(runner):
    """Test that generated verbs accept and respect --fields."""
    res = runner.invoke(cli, ["welcome", "--fields", "capabilities"])
    assert res.exit_code == 0
    parsed = json.loads(res.output)
    assert "capabilities" in parsed
    assert "schema_version" not in parsed

def test_fields_projection_on_auto_verb_with_intent(runner):
    """Test that a true dynamically generated verb respects --fields when intent_id is passed."""
    res = runner.invoke(cli, ["analyze", "graph", "--intent-id", "intent:892308ec", "--fields", "census"])
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

def test_chain_execution_single_session_and_substitution(runner, tmp_path):
    """Test that a chain executes correctly with interpolation and fields filtering."""
    yaml_content = """
- cap: discover
  verb: status
  args:
    intent_id: "intent:892308ec"
  save_as: result
  fields:
    - nodes
- cap: analyze
  verb: graph
  args:
    intent_id: "intent:892308ec"
    node_type: "${result.nodes.0}"
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

def test_chain_unknown_ref(runner, tmp_path):
    """Test that chain returns CHAIN_UNKNOWN_REF on unresolvable interpolation."""
    yaml_content = """
- cap: analyze
  verb: graph
  args:
    intent_id: "intent:892308ec"
    scope: "${missing.field}"
    """
    chain_file = tmp_path / "plan.yaml"
    chain_file.write_text(yaml_content)

    res = runner.invoke(cli, ["--chain", str(chain_file)])
    assert res.exit_code == 1
    parsed = json.loads(res.output)
    assert parsed.get("error") == "Codes.CHAIN_UNKNOWN_REF"
