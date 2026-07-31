"""Spec 255 — preflight: derived metrics + dogfood-fed warnings.

The verdicts dict derives from the @preflight_phase registry (a 6th phase
auto-appears with zero preflight-module edits); phases are timed with no
hidden overhead; preflight stays graph-only (zero driver calls); a phase
that raises fails alone; recurring (phase, category) warnings mint exactly
one Spec-150 observation Reflection per cluster; readiness reports which
audits have substrate to bite on.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine
from agency.capabilities.novel._main import NovelCapability
from agency.capabilities.novel.clusters.preflight import (
    PREFLIGHT_BUDGET_MS, preflight_phase)


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 255", "preflight metrics", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _scene(e, iid, chapters: int = 1):
    nid = _invoke(e, iid, "create_novel", title="P", author="A")["novel_id"]
    sid = ""
    for i in range(1, chapters + 1):
        ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=i,
                     title=f"Ch{i}")["chapter_id"]
        sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"s{i}",
                      pov="first")["scene_id"]
    return nid, sid


class CountingDriver:
    """Any driver resolution during preflight is a doctrine breach."""

    calls = 0

    def __getattr__(self, name):
        def _bump(*a, **kw):
            CountingDriver.calls += 1
            return {}
        return _bump


def test_sixth_phase_auto_extends_the_verdicts() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)

    @preflight_phase("check_custom_drift")
    def _check_custom_drift(self, scene, chapter_id, novel_id):
        return {"verdict": {"passed": True}, "findings": []}

    NovelCapability.check_custom_drift = _check_custom_drift
    try:
        out = _invoke(e, iid, "preflight_report", scene_id=sid, debug=True)
        assert "check_custom_drift" in out["verdicts"]
        assert set(out["verdicts"]) == set(out["audit_verbs"])  # parity
        assert len(out["audit_verbs"]) == 6
        base = _invoke(e, iid, "preflight_report", scene_id=sid)
        assert base["audit_verb_set_hash"] == out["audit_verb_set_hash"]
    finally:
        del NovelCapability.check_custom_drift
    # removed phase auto-disappears — hash changes with the set
    after = _invoke(e, iid, "preflight_report", scene_id=sid, debug=True)
    assert "check_custom_drift" not in after["verdicts"]
    assert after["audit_verb_set_hash"] != out["audit_verb_set_hash"]
    e.memory.close()


def test_durations_timed_with_no_hidden_overhead() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid, chapters=40)          # the standard fixture
    out = _invoke(e, iid, "preflight_report", scene_id=sid)
    assert out["total_duration_ms"] < PREFLIGHT_BUDGET_MS
    per_phase = sum(v["duration_ms"] for v in out["verdicts"].values())
    assert out["total_duration_ms"] <= per_phase + 50   # epsilon
    assert not any(w.get("code") == "preflight_slow"
                   for w in out["warnings"])
    e.memory.close()


def test_budget_overrun_emits_preflight_slow_but_full_report() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    out = _invoke(e, iid, "preflight_report", scene_id=sid, budget_ms=-1)
    slow = [w for w in out["warnings"] if w.get("code") == "preflight_slow"]
    assert len(slow) == 1                        # surfaced, never truncated
    assert set(out["verdicts"]) == set(out["audit_verbs"])
    e.memory.close()


def test_preflight_is_graph_only_zero_driver_calls() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)
    CountingDriver.calls = 0
    for name in ("novel_state", "novel_format", "codex_match", "anthropic"):
        e.drivers.register(name, CountingDriver())
    _invoke(e, iid, "preflight_report", scene_id=sid)
    assert CountingDriver.calls == 0
    e.memory.close()


def test_raising_phase_fails_alone_others_continue() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sid = _scene(e, iid)

    @preflight_phase("check_explosive")
    def _check_explosive(self, scene, chapter_id, novel_id):
        raise RuntimeError("substrate hole")

    NovelCapability.check_explosive = _check_explosive
    try:
        out = _invoke(e, iid, "preflight_report", scene_id=sid)
        v = out["verdicts"]["check_explosive"]
        assert v["status"] == "fail"
        assert "substrate hole" in v["findings"][0]["reason"]
        # every OTHER registered phase still reported
        assert {"briefing_ready", "canon_clean", "reveal_clear",
                "r_rules_clean", "voice_ready"} <= set(out["verdicts"])
    finally:
        del NovelCapability.check_explosive
    e.memory.close()


def test_recurring_warning_mints_one_reflection_per_cluster() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "create_novel", title="R",
                  author="A")["novel_id"]
    sys_id = _invoke(e, iid, "create_character_system", novel_id=nid,
                     name="Kael")["system_id"]
    lex = _invoke(e, iid, "add_alter", system_id=sys_id, name="Lex",
                  category="anp", layer="layer-1")["alter_id"]
    _invoke(e, iid, "create_voice_profile", character_id=lex,
            sentence_avg_target=12.0)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="I")["chapter_id"]
    minted = []
    for i in range(3):     # same no_taboo warning on 3 scenes = a cluster
        sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"r{i}",
                      pov="first", pov_character_id=lex)["scene_id"]
        out = _invoke(e, iid, "preflight_report", scene_id=sid)
        minted.append(out["proposals_minted"])
    assert minted[0] == 0 and minted[1] == 0     # below threshold
    assert minted[2] >= 1                        # cluster reached N=3
    refl = [r for r in e.memory.find("Reflection")
            if r.get("kind") == "preflight-recurrence"]
    clusters = {r.get("cluster") for r in refl}
    assert any("no_taboo" in c for c in clusters)
    # idempotent — a 4th run never re-mints an already-reflected cluster
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug="r4",
                  pov="first", pov_character_id=lex)["scene_id"]
    _invoke(e, iid, "preflight_report", scene_id=sid)
    refl2 = [r for r in e.memory.find("Reflection")
             if r.get("kind") == "preflight-recurrence"
             and r.get("cluster") in clusters]
    assert len(refl2) == len(clusters)           # no duplicates
    e.memory.close()


def test_readiness_reports_wired_over_total() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, _ = _scene(e, iid)
    r0 = _invoke(e, iid, "preflight_readiness", novel_id=nid)
    assert r0["total"] == len(r0["phases"])
    unwired0 = {p["phase"] for p in r0["phases"] if not p["wired"]}
    assert "reveal_clear" in unwired0            # no RevealRule yet
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="the twin",
            tier="reader", may_know_from_chapter=9)
    r1 = _invoke(e, iid, "preflight_readiness", novel_id=nid)
    assert {p["phase"] for p in r1["phases"] if not p["wired"]} \
        < unwired0                               # strictly fewer unwired
    assert r1["readiness"] > r0["readiness"]
    assert _invoke(e, iid, "preflight_readiness",
                   novel_id="novel:nope") is None
    e.memory.close()
