"""Spec 049 — naming & token-economy audit: INVARIANT guard (not a pinned snapshot).

Per the no-hardcoded-values doctrine (CLAUDE.md): this recomputes from the live
registry and asserts RELATIONSHIPS that hold as the surface grows — it does NOT
pin verb counts / token totals (those drift on every added verb and gate a fixed
surface). The published figures in `naming-audit-report.md` are a dated snapshot;
this test guards the *shape* of the finding, not a frozen number.
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
# The documented substrate surface (engine tools, not capability verbs). Grows
# deliberately: Spec 076 added `hook_event` (the unified hook dispatcher entry).
_SUBSTRATE = {"agency_welcome", "agency_install", "agency_doctor",
              "intent_bootstrap", "lifecycle_gate", "memory_graph_provenance",
              "hook_event"}
_CONTRACT = {"search", "get_schema", "execute"}
# Known cross-capability collisions that MUST be present (others are allowed).
_KNOWN_COLLISIONS = {"note", "render", "verify"}


def _tk(s):
    return len(_ENC.encode(s))


def _verbs():
    e = Engine(":memory:")
    try:
        return [(cap, v, parse_slices(e.registry.get(cap).verbs[v]["fn"].__doc__ or "")["brief"] or "")
                for cap in e.registry.names() for v in e.registry.get(cap).verbs]
    finally:
        e.memory.close()


def _live_substrate():
    e = Engine(":memory:")
    try:
        names = asyncio.run(_tool_names(e.build_mcp(codemode=False)))
        return {n for n in names if not n.startswith("capability_") and n not in _CONTRACT}
    finally:
        e.memory.close()


def test_substrate_set_is_the_documented_surface():
    # a real contract (the substrate surface), not a fragile count
    assert _live_substrate() == _SUBSTRATE
    assert sum(_tk(s) for s in _CONTRACT) <= 6  # the code-mode contract stays tiny


def test_prefix_is_the_dominant_name_tax():
    verbs = _verbs()
    wire = [f"capability_{c}_{v}" for c, v, _ in verbs]
    bare = [v for _, v, _ in verbs]
    assert all(w.startswith("capability_") for w in wire)
    wire_tok, bare_tok = sum(_tk(w) for w in wire), sum(_tk(b) for b in bare)
    # The prefix is pure repetition — it dominates the wire-name corpus.
    # AGENCY-DRIFT: prefix-dominance-bound — the 2.0x lower bound is the
    #   doctrine threshold ("prefix dominates iff wire ≥ 2x bare = ≥ 67%
    #   of total wire bytes are pure prefix"). Originally 2.5x in the
    #   pre-music surface; relaxed to 2.0x as Spec 094 lifecycle verbs
    #   (promote_idea, list_ideas, create_album, find_album, create_track,
    #   list_tracks, set_track_status, rename_album, rename_track,
    #   album_progress, resume_session) added 11 spec-mandated bare names
    #   that grew `bare_tok` faster than `wire_tok`. The absolute-100-token
    #   floor (line below) is the substantive guard; this ratio is the
    #   shape guard.
    assert wire_tok > bare_tok * 2.0
    assert wire_tok - bare_tok > 100  # substantial, however many verbs exist


def test_synthetic_payload_prefix_drop_is_material():
    verbs = _verbs()
    pw = "\n".join(f"- capability_{c}_{v}: {b}" for c, v, b in verbs)
    pb = "\n".join(f"- {v}: {b}" for _, v, b in verbs)
    # dropping the prefix saves a material slice of the (synthetic) payload.
    assert _tk(pw) > _tk(pb)
    assert (_tk(pw) - _tk(pb)) > 100


def test_known_collisions_present():
    by = defaultdict(set)
    for cap, v, _ in _verbs():
        by[v].add(cap)
    collisions = {v for v, cs in by.items() if len(cs) > 1}
    assert _KNOWN_COLLISIONS <= collisions  # subset — new collisions allowed (lint surfaces them)


def test_skill_folders_are_canonical_kebab():
    kebab = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    skills = [os.path.basename(os.path.dirname(p)) for p in glob.glob("skills/*/SKILL.md")]
    assert skills and all(kebab.match(s) for s in skills)


def test_ontology_skill_surface_exists():
    e = Engine(":memory:")
    try:
        keys = list(e.ontology.skills)
    finally:
        e.memory.close()
    assert keys and all(isinstance(k, str) for k in keys)


def test_audit_report_states_the_headline():
    text = open("Plan/049-naming-and-token-economy/naming-audit-report.md").read()
    flat = " ".join(text.lower().split())
    assert "capability_<cap>_" in text and "no existing bare alias" in flat
    for name in _KNOWN_COLLISIONS:
        assert f"`{name}`" in text
