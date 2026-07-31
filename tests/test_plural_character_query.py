"""Spec 248 — plural-character graph queries.

Phobia cycles + co-front occurrences as pure edge walks; results carry alter
IDs, never labels (recognition discipline holds across queries); max-pair
membership is computed from the live matrix, never pinned; empty matrices are
legal, self-loops are signal.
"""
from __future__ import annotations

import inspect
import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 248", "plural queries", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _system(e, iid, n=3):
    nid = _invoke(e, iid, "create_novel", title="KP", author="A")["novel_id"]
    sys_id = _invoke(e, iid, "create_character_system", novel_id=nid,
                     name="Kael")["system_id"]
    names = ["Lex", "Nyx", "Echo", "Sonder"][:n]
    cats = ["anp", "ep", "special", "mirror"]
    alters = [_invoke(e, iid, "add_alter", system_id=sys_id, name=nm,
                      category=cats[i], layer="layer-1")["alter_id"]
              for i, nm in enumerate(names)]
    return nid, sys_id, alters


def test_empty_matrix_returns_empty_cycleset() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sys_id, _ = _system(e, iid)
    out = _invoke(e, iid, "query_phobia_cycles", system_id=sys_id)
    assert out["cycles"] == []                    # legal, not an error


def test_cycle_detected_with_weight_and_ids_only() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sys_id, (a, b, c) = _system(e, iid, n=3)
    _invoke(e, iid, "record_alter_conflict", alter_a=a, alter_b=b,
            vector="anp-ep", intensity="max")
    _invoke(e, iid, "record_alter_conflict", alter_a=b, alter_b=c,
            vector="ep-ep", intensity="friction")
    _invoke(e, iid, "record_alter_conflict", alter_a=c, alter_b=a,
            vector="mirror", intensity="ambivalent")
    out = _invoke(e, iid, "query_phobia_cycles", system_id=sys_id)
    assert len(out["cycles"]) == 1
    cyc = out["cycles"][0]
    assert cyc["length"] == 3
    assert set(cyc["alter_ids"]) == {a, b, c}
    assert 0 < cyc["weight"] <= 1.0
    # recognition discipline: ids, never names
    assert all(x.startswith(("alter:", "node:")) or ":" in x
               for x in cyc["alter_ids"])
    assert "Lex" not in str(out)


def test_co_front_max_pair_is_computed_not_pinned() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, sys_id, (a, b, c) = _system(e, iid, n=3)
    _invoke(e, iid, "record_alter_conflict", alter_a=a, alter_b=b,
            vector="anp-ep", intensity="friction")
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="Ch")["chapter_id"]
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug="s",
                  pov="first", pov_character_id=a)["scene_id"]
    e.memory.update(sid, {"cast": b})
    # friction is currently the system max → the pair IS a max-pair
    out = _invoke(e, iid, "query_co_front", system_id=sys_id,
                  pair_kind="max")
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["violates_canon"] is True
    # a HIGHER-weight edge elsewhere demotes the friction pair (computed!)
    _invoke(e, iid, "record_alter_conflict", alter_a=b, alter_b=c,
            vector="ep-ep", intensity="max")
    out2 = _invoke(e, iid, "query_co_front", system_id=sys_id,
                   pair_kind="max")
    assert out2["occurrences"] == []              # a-b no longer max
    # but adjacent still sees the conflict edge, any sees the pair
    assert len(_invoke(e, iid, "query_co_front", system_id=sys_id,
                       pair_kind="adjacent")["occurrences"]) == 1
    assert len(_invoke(e, iid, "query_co_front", system_id=sys_id,
                       pair_kind="any")["occurrences"]) == 1


def test_queries_are_pure_edge_walks_no_dormant_edge_scan() -> None:
    """The CLAUDE.md dormant-edge audit as a standing test: the cycle query
    traverses PHOBIA_OF via ctx.neighbors — no find('Alter') + foreign-key
    filter in its source."""
    from agency.capabilities.novel.clusters.plural import PluralMixin
    src = inspect.getsource(PluralMixin.query_phobia_cycles)
    assert 'neighbors' in src and '"PHOBIA_OF"' in src
    assert 'find("Alter")' not in src
