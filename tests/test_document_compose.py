"""Spec 394 — document.compose: deterministic template scaffold + sampled sections.

The template+sample MIX in one verb: a deterministic `render`/`explain` scaffold
plus named sections whose bodies come from an MCP `ctx.host.sample` call grounded
in that scaffold. Degrades honestly (Spec 391) when no host is bound — the section
becomes a placeholder that PRESERVES its prompt (rule 9), never a hard failure.
"""
from __future__ import annotations

import tempfile

from agency._host_bridge import bind_host_context, reset_host_context
from agency.engine import Engine


class _FakeSamplingResult:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeHost:
    """A sampling-capable Context that echoes a marker + the grounding it saw."""

    def __init__(self) -> None:
        self.seen: list = []

    async def sample(self, messages, **kwargs):
        self.seen.append((messages, kwargs))
        return _FakeSamplingResult("SAMPLED-PROSE about the real catalogue")


def _confirmed_intent(eng):
    iid = eng.intent.capture("p", "d", "a")
    eng.intent.confirm(iid)
    return iid


def _compose(eng, iid, **kw):
    return eng.registry.invoke(eng.memory, iid, "document", "compose", **kw)[0]


def test_compose_mixes_scaffold_with_sampled_sections():
    eng = Engine(":memory:")
    eng.sampling_enabled = True
    host = _FakeHost()
    token = bind_host_context(host)
    try:
        iid = _confirmed_intent(eng)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        res = _compose(eng, iid, scope="capability-catalogue",
                       sections=[{"heading": "Why it matters",
                                  "prompt": "Explain why the catalogue matters."}],
                       apply_path=path)
        assert res.get("degraded") is False, res
        body = open(path, encoding="utf-8").read()
        # deterministic scaffold present (the catalogue lists capabilities)…
        assert "document" in body
        # …AND the sampled section heading + body are folded in.
        assert "## Why it matters" in body
        assert "SAMPLED-PROSE" in body
        # grounding: the host saw the scaffold as context, not a bare prompt.
        assert host.seen, "the host was actually sampled"
        ground = str(host.seen[0])
        assert "Why it matters" in ground or "catalogue" in ground.lower()
    finally:
        reset_host_context(token)
        eng.memory.close()


def test_compose_degrades_and_preserves_the_prompt_without_a_host():
    eng = Engine(":memory:")                     # no host bound → can_sample() False
    try:
        iid = _confirmed_intent(eng)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        res = _compose(eng, iid, scope="capability-catalogue",
                       sections=[{"heading": "Caveats",
                                  "prompt": "List the known caveats C1..C14."}],
                       apply_path=path)
        assert res.get("degraded") is True, res
        assert res.get("action") in ("created", "revised"), res
        body = open(path, encoding="utf-8").read()
        assert "## Caveats" in body
        # rule 9 — the captured intent (the section prompt) is PRESERVED, not dropped.
        assert "List the known caveats C1..C14." in body
    finally:
        eng.memory.close()


def test_compose_round_trips_as_a_keep_both_document():
    eng = Engine(":memory:")
    try:
        iid = _confirmed_intent(eng)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        first = _compose(eng, iid, scope="capability-catalogue",
                         sections=[{"heading": "Note", "prompt": "x"}],
                         apply_path=path)
        did = first["document_id"]
        revs = eng.registry.invoke(eng.memory, iid, "document", "revisions",
                                   document_id=did)[0]
        assert revs["count"] >= 1, revs
        # idempotent: re-composing identical content appends no new revision.
        again = _compose(eng, iid, scope="capability-catalogue",
                         sections=[{"heading": "Note", "prompt": "x"}],
                         apply_path=path)
        assert again["action"] == "unchanged", again
    finally:
        eng.memory.close()
