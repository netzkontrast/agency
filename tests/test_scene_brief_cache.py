"""Spec 237 — scene-brief cache discipline.

Sections render stability-descending; the brief splits into a byte-stable
prefix (frozen + semi) and a volatile suffix; prompt == prefix + suffix
byte-exact; a scene-state edit changes only the suffix; the breakpoint is
emitted only above the 1024-token floor (cache_ineligible below, brief
intact); a driver without cache_control support degrades to
cache_unsupported; a mocked driver only reports a cache hit when the second
call's prefix bytes are IDENTICAL — the end-to-end stability proof.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine
from agency.capabilities.prompt.clusters.assembly import (
    CACHE_MIN_PREFIX_TOKENS, STABILITY_RANK)


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 237", "brief cache", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, cap, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return r


def _scene(e, iid, storyform_body: str = ""):
    nid = _invoke(e, iid, "novel", "create_novel", title="C",
                  author="A")["novel_id"]
    ch = _invoke(e, iid, "novel", "create_chapter", novel_id=nid, number=1,
                 title="I")["chapter_id"]
    sid = _invoke(e, iid, "novel", "create_scene", chapter_id=ch, slug="s1",
                  pov="third-limited")["scene_id"]
    if storyform_body:
        _invoke(e, iid, "novel", "create_storyform", novel_id=nid,
                body=storyform_body)
    return nid, sid


def _brief(e, iid, sid, **kw):
    return _invoke(e, iid, "prompt", "assemble_scene_brief",
                   scene_id=sid, **kw)


def test_stability_descending_and_prompt_equals_prefix_plus_suffix() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    out = _brief(e, iid, sid)
    ranks = [STABILITY_RANK[m["stability"]] for m in out["sections_meta"]]
    assert ranks == sorted(ranks, reverse=True)   # never re-ascends
    assert out["prompt"] == out["prefix"] + out["suffix"]   # byte-exact
    assert out["prefix_tokens"] + out["suffix_tokens"] == out["total_tokens"]
    # byte offsets index the full prompt correctly
    raw = out["prompt"].encode("utf-8")
    for m in out["sections_meta"]:
        assert raw[m["byte_offset"]:m["byte_offset"] + 3] == b"## "
    e.memory.close()


def test_prefix_byte_stable_across_volatile_only_edits() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    briefs = [_brief(e, iid, sid) for _ in range(3)]
    # scene-STATE edit (cast + body are volatile inputs)
    e.memory.update(sid, {"cast": "Juna, Kael"})
    _invoke(e, iid, "novel", "integrate_scene_body", scene_id=sid,
            body="The bridge held. Kael counted the rivets.")
    briefs += [_brief(e, iid, sid) for _ in range(2)]
    prefixes = {b["prefix"] for b in briefs}
    assert len(prefixes) == 1                     # 5 calls, ONE prefix
    assert briefs[0]["suffix"] != briefs[-1]["suffix"]   # suffix moved
    e.memory.close()


def test_breakpoint_only_above_floor_else_cache_ineligible() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    small = _brief(e, iid, sid)                  # default 1024-token floor
    assert small["prefix_tokens"] < CACHE_MIN_PREFIX_TOKENS
    assert small["cache"]["min_prefix_tokens"] == CACHE_MIN_PREFIX_TOKENS
    assert small["cache"]["eligible"] is False
    assert small["cache"]["code"] == "cache_ineligible"
    assert small["cache"]["breakpoint_offset"] is None
    assert small["prompt"]                       # brief still returned
    # the floor is a documented tunable — a driver with a lower floor
    # makes the SAME prefix eligible (relation, not a pinned size)
    low = _brief(e, iid, sid, cache_floor_tokens=10)
    assert low["prefix_tokens"] >= 10
    assert low["cache"]["eligible"] is True
    assert low["cache"]["breakpoint_offset"] \
        == len(low["prefix"].encode("utf-8"))
    e.memory.close()


class FakeAnthropicDriver:
    """Counts tokens 1:1 per word; caches on prefix BYTES — a cache hit is
    only reported when the prefix is byte-identical to the cached one."""

    supports_cache_control = True

    def __init__(self):
        self._cached_prefix: bytes | None = None

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def invoke_with_cache(self, prefix: str, suffix: str) -> dict:
        blob = prefix.encode("utf-8")
        hit = blob == self._cached_prefix
        self._cached_prefix = blob
        return {"cache_read_input_tokens":
                self.count_tokens(prefix) if hit else 0}


def test_second_call_hits_the_cache_on_a_mocked_driver() -> None:
    e = _fresh()
    iid = _iid(e)
    drv = FakeAnthropicDriver()
    e.drivers.register("anthropic", drv)
    _, sid = _scene(e, iid)
    b1 = _brief(e, iid, sid, cache_floor_tokens=10)
    assert b1["cache"]["eligible"] is True
    assert drv.invoke_with_cache(b1["prefix"], b1["suffix"])[
        "cache_read_input_tokens"] == 0          # cold
    e.memory.update(sid, {"cast": "Juna"})       # volatile-only edit
    b2 = _brief(e, iid, sid, cache_floor_tokens=10)
    read = drv.invoke_with_cache(b2["prefix"], b2["suffix"])[
        "cache_read_input_tokens"]
    assert read >= b2["prefix_tokens"] * 0.9     # hit, tokenizer-tolerant
    # Spec 201: driver counted, not hand-summed
    assert b2["total_tokens"] == drv.count_tokens(b2["prefix"]) \
        + drv.count_tokens(b2["suffix"])
    e.memory.close()


def test_driver_without_cache_support_degrades_gracefully() -> None:
    e = _fresh()
    iid = _iid(e)

    class NoCacheDriver(FakeAnthropicDriver):
        supports_cache_control = False

    e.drivers.register("anthropic", NoCacheDriver())
    _, sid = _scene(e, iid)
    out = _brief(e, iid, sid, cache_floor_tokens=10)
    assert out["cache"]["code"] == "cache_unsupported"
    assert out["cache"]["breakpoint_offset"] is None
    assert out["prompt"]                         # brief intact
    e.memory.close()


def test_legacy_contract_untouched() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    out = _brief(e, iid, sid, max_tokens=10000, section_budget=2000)
    for k in ("prompt", "sections", "token_count", "sources", "brief_id"):
        assert k in out
    assert {"storyform", "pov_card", "scene_cast", "world_rules",
            "continuity", "foreshadowing", "voice_constraints"} \
        <= set(out["sections"])
    missing = _brief(e, iid, "scene:none")
    assert missing.get("error") == "NOT_FOUND"
    e.memory.close()
