"""Spec 143 — Kohärenz-Protokoll deep prompt fragments.

Six fragment families vendored in kp-fragments.yaml; fragments_for_scope maps
KP scope keys to slugs under the 2000-token budget; compose_drafting_brief is
the LLM-side scene composition; overlay isolation keeps non-KP novels clean.
The lint contract (slug regex · family set · ≤300 tokens) is a standing test.
"""
from __future__ import annotations

import re
import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 143", "kp fragments", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, cap, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return r


# ── the lint contract, standing (spec §Fragment lint extension) ───────────────

def test_yaml_lint_slug_family_and_token_cap() -> None:
    from agency._tokens import count_tokens
    from agency.capabilities.prompt.clusters.fragments import (
        KP_FAMILIES, _load_kp_fragments)
    store = _load_kp_fragments()
    assert len(store) >= 50                       # the six families in full
    slug_re = re.compile(r"^kp\.[a-z]+(\.[a-z0-9-]+)+$")
    families_seen = set()
    for slug, entry in store.items():
        assert slug_re.match(slug), slug
        assert entry["family"] in KP_FAMILIES, (slug, entry["family"])
        families_seen.add(entry["family"])
        assert entry["text"]
        # ≤300 cl100k tokens per fragment (char/4 proxy tolerated)
        try:
            n = count_tokens(entry["text"]).count
        except Exception:
            n = len(entry["text"]) // 4
        assert n <= 300, (slug, n)
    assert families_seen == KP_FAMILIES


# ── overlay isolation ─────────────────────────────────────────────────────────

def test_non_kp_novel_sees_no_fragments() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _invoke(e, iid, "prompt", "fragments_for_scope",
                  scope={"mode_block": "choral"})
    assert out["kp_active"] is False and out["fragments"] == []


def test_character_system_activates_overlay() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "novel", "create_novel", title="KP",
                  author="A")["novel_id"]
    _invoke(e, iid, "novel", "create_character_system", novel_id=nid,
            name="Kael")
    out = _invoke(e, iid, "prompt", "fragments_for_scope",
                  scope={"mode_block": "choral"})
    assert out["kp_active"] is True
    assert out["fragments"][0]["slug"] == "kp.mode.choral"


# ── one golden composition per family ─────────────────────────────────────────

def test_golden_compositions_per_family() -> None:
    e = _fresh()
    iid = _iid(e)
    goldens = [
        ({"kp": True, "alter_id": ""}, None),                  # placeholder
        ({"kp": True, "family": "plurality"}, "kp.alter.anp"),
        ({"kp": True, "routing_mode": "soft",
          "transition_kind": "operative"}, "kp.route.soft"),
        ({"kp": True, "mode_block": "vortex-still",
          "genre_accent": "literary-sf"}, "kp.mode.vortex-still"),
        ({"kp": True, "audience_tier": "reader", "veil": "maintain",
          "reveal_channels": ["glitch", "log"]}, "kp.tier.reader"),
        ({"kp": True, "r_rule_ids": ["R-5", "R-7"],
          "predicate_kind": "mutual-exclusion"},
         "kp.rule.r5-hot-polarity"),
        ({"kp": True, "family": "synthesis"}, "kp.synthesis.philosophical"),
    ]
    for scope, expected in goldens[1:]:
        out = _invoke(e, iid, "prompt", "fragments_for_scope", scope=scope)
        slugs = [f["slug"] for f in out["fragments"]]
        assert expected in slugs, (scope, slugs)
        assert out["total_tokens"] <= 2000
        assert out["skipped_no_fragment"] == [], (scope, out)


def test_alter_scope_prefers_function_over_category() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "novel", "create_novel", title="KP",
                  author="A")["novel_id"]
    sys_id = _invoke(e, iid, "novel", "create_character_system",
                     novel_id=nid, name="Kael")["system_id"]
    nyx = _invoke(e, iid, "novel", "add_alter", system_id=sys_id,
                  name="Nyx", category="ep", layer="layer-2",
                  function="Fight")["alter_id"]
    out = _invoke(e, iid, "prompt", "fragments_for_scope",
                  scope={"alter_id": nyx})
    slugs = [f["slug"] for f in out["fragments"]]
    assert slugs[0] == "kp.alter.fight"          # function beats category
    assert "kp.alter.ep" in slugs


# ── the scene-level composer ──────────────────────────────────────────────────

def test_compose_drafting_brief_reads_the_graph() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "novel", "create_novel", title="KP",
                  author="A")["novel_id"]
    sys_id = _invoke(e, iid, "novel", "create_character_system",
                     novel_id=nid, name="Kael")["system_id"]
    alter = _invoke(e, iid, "novel", "add_alter", system_id=sys_id,
                    name="Lex", category="anp", layer="layer-1",
                    function="Rationalist")["alter_id"]
    ch = _invoke(e, iid, "novel", "create_chapter", novel_id=nid, number=2,
                 title="Ch 2")["chapter_id"]
    _invoke(e, iid, "novel", "define_mode_block", novel_id=nid,
            label="Akt I", mode="linear-introspective", from_chapter=1,
            to_chapter=12, genre_accent="philosophical-horror")
    _invoke(e, iid, "novel", "register_project_rule", novel_id=nid,
            rule_id="R-5", name="polarity", severity="critical",
            predicate_kind="mutual-exclusion",
            params={"set_a": ["a"], "set_b": ["b"]})
    _invoke(e, iid, "novel", "set_reveal_rule", novel_id=nid, fact="f",
            tier="reader", may_know_from_chapter=13, channel="glitch")
    sid = _invoke(e, iid, "novel", "create_scene", chapter_id=ch, slug="s",
                  pov="first", pov_character_id=alter)["scene_id"]
    out = _invoke(e, iid, "prompt", "compose_drafting_brief", scene_id=sid)
    assert out["brief"]
    src = set(out["sources"])
    assert {"kp.alter.rationalist", "kp.mode.linear-introspective",
            "kp.genre.philosophical-horror", "kp.channel.glitch",
            "kp.rule.r5-hot-polarity"} <= src
    assert out["total_tokens"] <= 2000
