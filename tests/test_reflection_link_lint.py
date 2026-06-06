"""Spec 058 — reflection-link convention as a lint rule.

A verb that records a Reflection must link it with BOTH SERVES (provenance) and
OBSERVED_DURING (the intent-scoped reflection view). `_check_reflection_links`
(WARN) flags a write missing either edge.
"""
from __future__ import annotations

import types

from agency.capabilities.plugin._main import _check_reflection_links
from agency.engine import Engine


def _verb_both(self):
    rid = self.ctx.record("Reflection", {"scope": "observation", "text": "x"})
    self.ctx.link(rid, self.ctx.intent_id, "SERVES")
    self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
    return rid


def _verb_serves_only(self):
    rid = self.ctx.record("Reflection", {"scope": "observation", "text": "x"})
    self.ctx.link(rid, self.ctx.intent_id, "SERVES")
    return rid


def _verb_observed_only(self):
    rid = self.ctx.record("Reflection", {"scope": "observation", "text": "x"})
    self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
    return rid


def _verb_no_reflection(self):
    aid = self.ctx.record("Artefact", {"kind": "x"})
    self.ctx.link(aid, self.ctx.intent_id, "SERVES")
    return aid


def _verb_skip_marker(self):
    # a deliberate cross-intent reflection opts out of the edge check
    rid = self.ctx.record("Reflection", {"scope": "observation"})  # agency-skip-link-check: cross-intent
    self.ctx.link(rid, self.ctx.intent_id, "SERVES")
    return rid


def _cap(**fns):
    return types.SimpleNamespace(verbs={n: {"fn": f, "role": "act"} for n, f in fns.items()})


def test_both_edges_passes():
    assert _check_reflection_links(_cap(v=_verb_both)) == []


def test_serves_only_warns_missing_observed_during():
    findings = _check_reflection_links(_cap(v=_verb_serves_only))
    assert len(findings) == 1
    assert findings[0]["kind"] == "reflection_link"
    assert "OBSERVED_DURING" in findings[0]["msg"]


def test_observed_only_warns_missing_serves():
    findings = _check_reflection_links(_cap(v=_verb_observed_only))
    assert len(findings) == 1
    assert "SERVES" in findings[0]["msg"]


def test_non_reflection_verb_is_silent():
    assert _check_reflection_links(_cap(v=_verb_no_reflection)) == []


def test_skip_marker_opts_out():
    assert _check_reflection_links(_cap(v=_verb_skip_marker)) == []


def test_live_registry_has_no_reflection_link_gaps():
    # Regression: every Reflection-writing verb in the shipped registry links
    # BOTH edges (the audit migrated analyze.improve/cleanup + develop).
    e = Engine(":memory:")
    try:
        gaps = [(n, x["verb"]) for n in e.registry.names()
                for x in _check_reflection_links(e.registry.get(n))]
    finally:
        e.memory.close()
    assert gaps == []
