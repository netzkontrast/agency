"""Spec 049 — naming & token-economy audit reproducibility guard.

These assertions recompute the audit's headline figures from the LIVE registry
so `Plan/049-…/naming-audit-report.md` can't silently drift from reality. They
encode the CURRENT (pre-rename) baseline; the follow-up rename spec (066) updates
them when it drops the `capability_<cap>_` prefix — which is the intended signal.
"""
from __future__ import annotations

import glob
import os
import re

import tiktoken

from agency.disclosure import parse_slices
from agency.engine import Engine

_ENC = tiktoken.get_encoding("cl100k_base")
_SUBSTRATE = {"agency_welcome", "agency_install", "agency_doctor",
              "intent_bootstrap", "lifecycle_gate", "memory_graph_provenance"}
_CONTRACT = {"search", "get_schema", "execute"}


def _tk(s: str) -> int:
    return len(_ENC.encode(s))


def _verbs():
    e = Engine(":memory:")
    try:
        out = []
        for cap in e.registry.names():
            c = e.registry.get(cap)
            for v, spec in c.verbs.items():
                brief = parse_slices(spec["fn"].__doc__ or "")["brief"] or ""
                out.append((cap, v, brief))
        return out
    finally:
        e.memory.close()


def test_substrate_tools_are_short():
    # The 6 substrate tools are already 2-5 tokens; renaming saves ~10 tok total
    # (small) — the report's basis for ALIAS-AND-RENAME, not RENAME-HARD.
    assert sum(_tk(s) for s in _SUBSTRATE) <= 20
    assert sum(_tk(s) for s in _CONTRACT) <= 6  # the code-mode contract stays


def test_capability_prefix_is_the_dominant_tax():
    verbs = _verbs()
    wire = [f"capability_{cap}_{v}" for cap, v, _ in verbs]
    bare = [v for _, v, _ in verbs]
    assert all(w.startswith("capability_") for w in wire)
    prefix_tax = sum(_tk(w) for w in wire) - sum(_tk(b) for b in bare)
    # the prefix is pure repetition; the report documents ~202 tok at audit time
    assert prefix_tax > 150
    # bare corpus is far smaller than the wire corpus (the rename's leverage)
    assert sum(_tk(w) for w in wire) > 2.5 * sum(_tk(b) for b in bare)


def test_full_search_payload_delta_is_material():
    verbs = _verbs()
    pw = "\n".join(f"- capability_{cap}_{v}: {b}" for cap, v, b in verbs)
    pb = "\n".join(f"- {v}: {b}" for _, v, b in verbs)
    delta = _tk(pw) - _tk(pb)
    # dropping the prefix saves a material slice of the discovery payload
    assert delta > 150


def test_skill_names_are_canonical_kebab():
    kebab = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    skills = [os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")]
    assert skills, "no skills found"
    assert all(kebab.match(s) for s in skills)


def test_audit_report_exists_and_states_the_headline():
    report = "Plan/049-naming-and-token-economy/naming-audit-report.md"
    assert os.path.exists(report)
    text = open(report).read()
    assert "capability_<cap>_" in text and "KEEP" in text and "ALIAS-AND-RENAME" in text
