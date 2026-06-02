"""Spec 032 §C — Memory.validate_schema_draft07 (panel F-3 second method)."""
import json
import tempfile

import pytest

from agency.engine import Engine


def _engine_with_node(props: dict, schema_props: dict):
    """Build an engine, record one Schema + one Node, return (engine, intent_id,
    node_id, schema_id)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture_and_confirm("test", "test", "test")
    # The schema node — recorded with whatever shape the test provides
    schema_id = e.memory.record("Schema", schema_props)
    # A test node — use the Artefact label since it has loose schema
    node_id = e.memory.record("Artefact", props)
    return e, iid, node_id, schema_id


def test_validate_schema_draft07_passes_for_valid_node():
    """A node with all required fields against a draft-07 schema returns True."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "required": ["kind", "name"],
        "properties": {"kind": {"type": "string"}, "name": {"type": "string"}},
    }
    e, _, node_id, schema_id = _engine_with_node(
        props={"kind": "test", "name": "foo"},
        # Schema node carries name + required (CSV) + schema_json (JSON string)
        schema_props={"name": "test-schema",
                      "required": "kind,name",
                      "schema_json": json.dumps(schema)},
    )
    try:
        assert e.memory.validate_schema_draft07(node_id, schema_id) is True
    finally:
        e.memory.close()


def test_validate_schema_draft07_fails_for_missing_required_field():
    """Missing required field → False (not raise)."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "required": ["kind", "name"],
        "properties": {"kind": {"type": "string"}, "name": {"type": "string"}},
    }
    e, _, node_id, schema_id = _engine_with_node(
        props={"kind": "test"},  # missing 'name'
        schema_props={"name": "test-schema",
                      "required": "kind,name",
                      "schema_json": json.dumps(schema)},
    )
    try:
        assert e.memory.validate_schema_draft07(node_id, schema_id) is False
    finally:
        e.memory.close()


def test_validate_schema_draft07_raises_when_schema_lacks_schema_json():
    """Calling draft07 method against a simple-shape Schema node (no
    schema_json field) raises RuntimeError — wrong tool for the shape."""
    e, _, node_id, schema_id = _engine_with_node(
        props={"kind": "test"},
        # Simple shape — no schema_json field
        schema_props={"name": "simple-schema", "required": "kind"},
    )
    try:
        with pytest.raises(RuntimeError) as ei:
            e.memory.validate_schema_draft07(node_id, schema_id)
        assert "schema_json" in str(ei.value).lower() or "draft-07" in str(ei.value).lower()
    finally:
        e.memory.close()


def test_validate_schema_draft07_returns_false_for_missing_nodes():
    """Same defensive shape as existing validate_schema: returns False if
    the node or schema does not exist (rather than raising)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        assert e.memory.validate_schema_draft07("nonexistent", "also:nonexistent") is False
    finally:
        e.memory.close()


def test_validate_schema_draft07_fails_for_wrong_type():
    """Draft-07 type checking: a node with 'kind' as int when schema says
    string returns False."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "required": ["kind"],
        "properties": {"kind": {"type": "string"}},
    }
    e, _, node_id, schema_id = _engine_with_node(
        props={"kind": 42},  # wrong type
        schema_props={"name": "typed-schema",
                      "required": "kind",
                      "schema_json": json.dumps(schema)},
    )
    try:
        assert e.memory.validate_schema_draft07(node_id, schema_id) is False
    finally:
        e.memory.close()


def test_validate_schema_simple_path_unchanged():
    """Sanity: the existing validate_schema method still works on simple
    shape schemas (no schema_json needed)."""
    e, _, node_id, schema_id = _engine_with_node(
        props={"kind": "test", "name": "foo"},
        schema_props={"name": "simple-schema", "required": "kind,name"},
    )
    try:
        assert e.memory.validate_schema(node_id, schema_id) is True
        # missing field → False
        node2_id = e.memory.record("Artefact", {"kind": "only-kind"})
        assert e.memory.validate_schema(node2_id, schema_id) is False
    finally:
        e.memory.close()
