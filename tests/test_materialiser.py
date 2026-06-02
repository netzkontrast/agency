"""Spec 032 §D — Ontology.materialise_schemas + materialise_templates.

Panel F-4: bi-temporal supersede on shape change, not destructive upsert.
"""
import json
import tempfile

import pytest

from agency.engine import Engine
from agency.ontology import Ontology, OntologyExtension


def test_materialise_schemas_records_one_node_per_entry():
    """Each ontology.schemas entry → one Schema node with id schema:<name>."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    # Add a test schema to the live ontology
    e.ontology.schemas["test-schema"] = ["foo", "bar"]
    try:
        mapping = e.ontology.materialise_schemas(e.memory)
        assert mapping["test-schema"] == "schema:test-schema"
        node = e.memory.recall("schema:test-schema")
        assert node is not None
        assert node["name"] == "test-schema"
        assert node["required"] == "foo,bar"
    finally:
        e.memory.close()


def test_materialise_schemas_idempotent_when_unchanged():
    """Re-running materialise on unchanged ontology is a no-op (no supersede)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.ontology.schemas["test-schema"] = ["foo", "bar"]
    try:
        m1 = e.ontology.materialise_schemas(e.memory)
        m2 = e.ontology.materialise_schemas(e.memory)
        # Same node id; no SUPERSEDED_BY edge added
        assert m1 == m2
        rows = e.memory.g.query(
            "MATCH (a)-[:SUPERSEDED_BY]->(b) WHERE a.id = 'schema:test-schema' RETURN b")
        assert rows == [], f"expected no supersede, got: {rows!r}"
    finally:
        e.memory.close()


def test_materialise_schemas_supersedes_on_required_list_change():
    """Changing the required list triggers a bi-temporal supersede (panel F-4)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.ontology.schemas["test-schema"] = ["foo", "bar"]
    try:
        e.ontology.materialise_schemas(e.memory)
        # Mutate the schema in the ontology
        e.ontology.schemas["test-schema"] = ["foo", "bar", "baz"]
        e.ontology.materialise_schemas(e.memory)
        # The SUPERSEDED_BY edge must exist now
        rows = e.memory.g.query(
            "MATCH (a)-[:SUPERSEDED_BY]->(b) WHERE a.id = 'schema:test-schema' RETURN b")
        assert len(rows) == 1, f"expected one supersede, got: {len(rows)}"
        # Latest recall returns the new version
        latest = e.memory.recall(rows[0]["b"]["properties"]["id"])
        assert latest["required"] == "foo,bar,baz"
    finally:
        e.memory.close()


def test_materialise_templates_records_one_node_per_entry():
    """Each ontology.templates entry → one Template node with id template:<name>."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.ontology.templates["greeting"] = "Hello $name!"
    try:
        mapping = e.ontology.materialise_templates(e.memory)
        assert mapping["greeting"] == "template:greeting"
        node = e.memory.recall("template:greeting")
        assert node["name"] == "greeting"
        assert node["body"] == "Hello $name!"
    finally:
        e.memory.close()


def test_materialise_templates_supersedes_on_body_change():
    """Changing a template body triggers bi-temporal supersede."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.ontology.templates["greeting"] = "Hello $name!"
    try:
        e.ontology.materialise_templates(e.memory)
        e.ontology.templates["greeting"] = "Hi $name!"
        e.ontology.materialise_templates(e.memory)
        rows = e.memory.g.query(
            "MATCH (a)-[:SUPERSEDED_BY]->(b) WHERE a.id = 'template:greeting' RETURN b")
        assert len(rows) == 1
        latest = e.memory.recall(rows[0]["b"]["properties"]["id"])
        assert latest["body"] == "Hi $name!"
    finally:
        e.memory.close()


def test_materialise_schemas_handles_draft07_shape():
    """Draft-07 dict shape: schema_json field carries the JSON string."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    draft07 = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "required": ["kind"],
        "properties": {"kind": {"type": "string"}},
    }
    e.ontology.schemas["draft07-schema"] = draft07
    try:
        e.ontology.materialise_schemas(e.memory)
        node = e.memory.recall("schema:draft07-schema")
        assert node["name"] == "draft07-schema"
        assert node["required"] == "kind"
        assert "schema_json" in node
        assert json.loads(node["schema_json"]) == draft07
    finally:
        e.memory.close()


def test_materialise_supersedes_on_shape_flip_simple_to_draft07():
    """Flipping a schema from simple list to draft-07 dict triggers supersede."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.ontology.schemas["shifty"] = ["foo"]
    try:
        e.ontology.materialise_schemas(e.memory)
        # Now flip to draft-07
        e.ontology.schemas["shifty"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "required": ["foo"],
            "properties": {"foo": {"type": "string"}},
        }
        e.ontology.materialise_schemas(e.memory)
        rows = e.memory.g.query(
            "MATCH (a)-[:SUPERSEDED_BY]->(b) WHERE a.id = 'schema:shifty' RETURN b")
        assert len(rows) == 1
        latest = e.memory.recall(rows[0]["b"]["properties"]["id"])
        assert "schema_json" in latest
    finally:
        e.memory.close()


def test_materialise_retroactive_coverage_of_plugin_kinds():
    """Spec 004 rolled in: ALL ontology.schemas entries get materialised,
    including the 5 legacy plugin kinds that arrive via OntologyExtension.schemas."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        mapping = e.ontology.materialise_schemas(e.memory)
        # The plugin capability ships 5 schemas via templates.REQUIRED
        expected_kinds = {"plugin-manifest", "skill-md", "command-md",
                          "marketplace-entry", "step-doc"}
        for kind in expected_kinds:
            assert kind in mapping, f"materialiser must cover legacy plugin kind {kind!r}"
            node = e.memory.recall(mapping[kind])
            assert node is not None, f"node for {kind!r} missing"
            assert node["name"] == kind
    finally:
        e.memory.close()
