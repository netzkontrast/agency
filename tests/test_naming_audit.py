"""Spec 049 — naming & token-economy audit reproducibility guard.

These assertions PIN the exact figures published in
`Plan/049-…/naming-audit-report.md` (the 2026-06-06 snapshot) against the live
registry, so any change to the verb/skill surface FAILS this test and forces the
report (and these numbers) to be updated in lock-step — that is the whole point
of a reproducibility guard (PR #23 review: loose lower bounds let the report go
stale). The follow-up rename spec (066) updates this snapshot when it drops the
`capability_<cap>_` prefix.
"""
from __future__ import annotations

import asyncio
import glob
import os
import re
from collections import defaultdict

import tiktoken

from agency.capabilities.plugin._main import _tool_names
from agency.disclosure import parse_slices
from agency.engine import Engine

_ENC = tiktoken.get_encoding("cl100k_base")
_SUBSTRATE = {"agency_welcome", "agency_install", "agency_doctor",
              "intent_bootstrap", "lifecycle_gate", "memory_graph_provenance"}
_CONTRACT = {"search", "get_schema", "execute"}

# --- the published snapshot (keep in sync with naming-audit-report.md) ---------
SNAP_VERB_COUNT = 70   # +1 lint_explain (Spec 074)
SNAP_SKILL_COUNT = 19
SNAP_WIRE_TOK = 317
SNAP_BARE_TOK = 112
SNAP_PREFIX_TAX = 205        # = WIRE - BARE
SNAP_PAYLOAD_WIRE = 1503
SNAP_PAYLOAD_BARE = 1290
SNAP_SUBSTRATE_TOK = 18
SNAP_SKILL_TOK = 59
SNAP_ONTOLOGY_SKILL_COUNT = 21
SNAP_ONTOLOGY_SKILL_TOK = 67
SNAP_COLLISIONS = {"note": ["dogfood", "reflect"],
                   "render": ["document", "dogfood"],
                   "verify": ["jules", "research"]}


def _tk(s: str) -> int:
    return len(_ENC.encode(s))


def _verbs():
    e = Engine(":memory:")
    try:
        return [(cap, v, parse_slices(e.registry.get(cap).verbs[v]["fn"].__doc__ or "")["brief"] or "")
                for cap in e.registry.names() for v in e.registry.get(cap).verbs]
    finally:
        e.memory.close()


def _live_substrate():
    """The non-contract, non-`capability_` tools actually registered on the built
    MCP surface — so the snapshot guards against `@mcp.tool` drift, not a constant."""
    e = Engine(":memory:")
    try:
        names = asyncio.run(_tool_names(e.build_mcp(codemode=False)))
        return {n for n in names if not n.startswith("capability_") and n not in _CONTRACT}
    finally:
        e.memory.close()


def test_substrate_snapshot():
    # derive from the LIVE MCP surface, then pin the set + token total
    assert _live_substrate() == _SUBSTRATE, "substrate @mcp.tool surface changed — update the audit"
    assert sum(_tk(s) for s in _SUBSTRATE) == SNAP_SUBSTRATE_TOK
    assert sum(_tk(s) for s in _CONTRACT) == 4  # the code-mode contract stays


def test_verb_prefix_tax_snapshot():
    verbs = _verbs()
    assert len(verbs) == SNAP_VERB_COUNT, "verb surface changed — update the audit report + snapshot"
    wire = [f"capability_{cap}_{v}" for cap, v, _ in verbs]
    bare = [v for _, v, _ in verbs]
    assert all(w.startswith("capability_") for w in wire)
    assert sum(_tk(w) for w in wire) == SNAP_WIRE_TOK
    assert sum(_tk(b) for b in bare) == SNAP_BARE_TOK
    assert sum(_tk(w) for w in wire) - sum(_tk(b) for b in bare) == SNAP_PREFIX_TAX


def test_synthetic_name_brief_corpus_snapshot():
    # NOTE: a SYNTHETIC `- <name>: <brief>` corpus (models the search payload's
    # name-controllable slice — see report §2). It is NOT the live search tool's
    # formatted output; the delta (prefixed vs bare) is the point and the live
    # tool can't yield it (no bare-name registry exists).
    verbs = _verbs()
    pw = "\n".join(f"- capability_{cap}_{v}: {b}" for cap, v, b in verbs)
    pb = "\n".join(f"- {v}: {b}" for _, v, b in verbs)
    assert _tk(pw) == SNAP_PAYLOAD_WIRE
    assert _tk(pb) == SNAP_PAYLOAD_BARE


def test_ontology_skill_surface_snapshot():
    # The SECOND skill surface (walkable Lifecycle templates), distinct from the
    # SKILL.md folders — derived live from the ontology so it guards against drift.
    e = Engine(":memory:")
    try:
        keys = list(e.ontology.skills.keys())
    finally:
        e.memory.close()
    assert len(keys) == SNAP_ONTOLOGY_SKILL_COUNT
    assert sum(_tk(k) for k in keys) == SNAP_ONTOLOGY_SKILL_TOK


def test_bare_name_collision_set_is_complete():
    # Guards report §4: the COMPLETE cross-capability verb-name collision set.
    by = defaultdict(set)
    for cap, v, _ in _verbs():
        by[v].add(cap)
    collisions = {v: sorted(cs) for v, cs in by.items() if len(cs) > 1}
    assert collisions == SNAP_COLLISIONS
    # the contract-shadow the report calls out
    assert "search" in {v for _, v, _ in _verbs()}  # reflect.search shadows the `search` contract tool


def test_skill_names_are_canonical_kebab():
    kebab = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    skills = [os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")]
    assert len(skills) == SNAP_SKILL_COUNT
    assert all(kebab.match(s) for s in skills)
    assert sum(_tk(s) for s in skills) == SNAP_SKILL_TOK  # pin the published 59-tok corpus


def test_audit_report_exists_and_states_the_headline():
    text = open("Plan/049-naming-and-token-economy/naming-audit-report.md").read()
    flat = " ".join(text.lower().split())  # normalise markdown line wraps
    assert "capability_<cap>_" in text and "KEEP" in text and "ALIAS-AND-RENAME" in text
    # the corrected premise + complete collision set must be present
    assert "no existing bare alias" in flat
    for name in SNAP_COLLISIONS:
        assert f"`{name}`" in text
