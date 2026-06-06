"""Spec 056 — type-safe node-id discipline.

`Memory.recall_typed(id, label)` returns props only when the node exists AND
carries the label; the `_check_node_id_guards` lint rule (WARN) flags verbs that
read a `<label>_id` param via a bare recall/get_node without a label check.
"""
from __future__ import annotations

import tempfile
import types

from agency.capabilities.plugin._main import _check_node_id_guards
from agency.engine import Engine


# --- recall_typed --------------------------------------------------------------

def _mem():
    return Engine(tempfile.mktemp(suffix=".db")).memory


def test_recall_typed_matching_label_returns_props():
    m = _mem()
    try:
        aid = m.record("Artefact", {"kind": "scenario"})
        props = m.recall_typed(aid, "Artefact")
        assert props is not None and props["kind"] == "scenario"
    finally:
        m.close()


def test_recall_typed_wrong_label_returns_none():
    m = _mem()
    try:
        aid = m.record("Artefact", {"kind": "scenario"})
        assert m.recall_typed(aid, "Research") is None
    finally:
        m.close()


def test_recall_typed_missing_node_returns_none():
    m = _mem()
    try:
        assert m.recall_typed("intent:does-not-exist", "Intent") is None
    finally:
        m.close()


def test_recall_typed_empty_id_returns_none():
    m = _mem()
    try:
        assert m.recall_typed("", "Intent") is None
        assert m.recall_typed(None, "Intent") is None
    finally:
        m.close()


def test_recall_typed_returns_a_copy():
    m = _mem()
    try:
        aid = m.record("Artefact", {"kind": "scenario"})
        props = m.recall_typed(aid, "Artefact")
        props["kind"] = "MUTATED"
        again = m.recall_typed(aid, "Artefact")
        assert again["kind"] == "scenario"  # mutation didn't leak into the graph
    finally:
        m.close()


# --- _check_node_id_guards lint rule ------------------------------------------

def _verb_bare_recall(self, research_id: str):
    node = memory.recall(research_id)  # noqa: F821 — synthetic anti-pattern
    return node


def _verb_recall_typed(self, research_id: str):
    node = memory.recall_typed(research_id, "Research")  # noqa: F821
    return node


def _verb_match_label(self, lifecycle_id: str):
    # a Cypher MATCH on the label is an accepted guard form
    return g.query("MATCH (l:Lifecycle) WHERE l.id = $x RETURN l", {"x": lifecycle_id})  # noqa: F821


def _verb_no_id_param(self, path: str):
    return path


def _verb_unknown_prefix(self, widget_id: str):
    return memory.recall(widget_id)  # noqa: F821 — prefix not in the label table → skip


def _cap(**fns):
    return types.SimpleNamespace(verbs={n: {"fn": f, "role": "act"} for n, f in fns.items()})


def test_lint_flags_bare_recall_without_label():
    findings = _check_node_id_guards(_cap(specialist=_verb_bare_recall))
    assert any(f["kind"] == "node_id_guard" and f["verb"] == "specialist" for f in findings)


def test_lint_passes_recall_typed():
    assert _check_node_id_guards(_cap(specialist=_verb_recall_typed)) == []


def test_lint_passes_cypher_match_on_label():
    assert _check_node_id_guards(_cap(check=_verb_match_label)) == []


def test_lint_silent_on_no_id_param():
    assert _check_node_id_guards(_cap(plain=_verb_no_id_param)) == []


def test_lint_skips_unknown_prefix():
    # widget_id has no entry in the label table → the rule skips (no guess)
    assert _check_node_id_guards(_cap(w=_verb_unknown_prefix)) == []
