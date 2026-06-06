"""Spec 068 — tiered discovery.

CORE.md §Skills (Spec 072) mandates progressive disclosure at the DISCOVERY
layer: a cheap capability tier (≈14 lines: name + gist + verb-count) the agent
browses first, then drills into one capability via search/get_schema — instead of
a flat dump of all ~69 verbs. The tier is surfaced additively on `agency_welcome`
(the canonical first call); `capabilities` (names) stays for back-compat.
"""
from __future__ import annotations

import tiktoken

from agency.disclosure import parse_slices
from agency.engine import Engine, _capability_tier

_ENC = tiktoken.get_encoding("cl100k_base")


def test_capability_tier_shape():
    e = Engine(":memory:")
    try:
        tier = _capability_tier(e.registry)
        assert {t["name"] for t in tier} == set(e.registry.names())
        for t in tier:
            assert t["gist"] and isinstance(t["verbs"], int) and t["verbs"] >= 1
            assert "\n" not in t["gist"]  # one-line gist
    finally:
        e.memory.close()


def test_capability_tier_is_far_cheaper_than_the_flat_verb_dump():
    e = Engine(":memory:")
    try:
        tier = _capability_tier(e.registry)
        tier_str = "\n".join(f"- {t['name']} ({t['verbs']}): {t['gist']}" for t in tier)
        flat = "\n".join(
            f"- capability_{c}_{v}: {parse_slices(e.registry.get(c).verbs[v]['fn'].__doc__ or '')['brief'] or ''}"
            for c in e.registry.names() for v in e.registry.get(c).verbs)
    finally:
        e.memory.close()
    tier_tok, flat_tok = len(_ENC.encode(tier_str)), len(_ENC.encode(flat))
    # the capability tier is the cheap entry; the flat verb dump is the tax
    assert tier_tok < flat_tok / 3, f"tier={tier_tok} flat={flat_tok}"


def test_welcome_surfaces_the_tier_and_keeps_names_for_backcompat():
    # invoke the real welcome tool body via the engine's built MCP
    import asyncio
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=False)
        tools = asyncio.run(mcp._list_tools())
        welcome = next(t for t in tools if t.name == "agency_welcome")
        out = asyncio.run(welcome.run({}))
        payload = out.structured_content if hasattr(out, "structured_content") else out
    finally:
        e.memory.close()
    assert isinstance(payload.get("capabilities"), list)            # back-compat: names
    assert all(isinstance(c, str) for c in payload["capabilities"])
    tier = payload.get("capability_tier")
    assert isinstance(tier, list) and len(tier) == len(payload["capabilities"])
    assert {t["name"] for t in tier} == set(payload["capabilities"])
