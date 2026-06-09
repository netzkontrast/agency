"""Spec 103 hybrid rows 12+13 — NCP appreciation + narrative_function validation.

Closes goal criterion 1: 463 canonical appreciations + 144 canonical
narrative_functions enums validate via two hybrid verbs.

- validate_appreciations(ncp) — walks every appreciation field across
  the NCP body, asserts each value belongs to the canonical_appreciation
  enum (463 values). Returns {passed, violations: [{path, value}]}.
- validate_narrative_functions(ncp) — walks every narrative_function
  field; asserts each value belongs to canonical_narrative_function
  (144 values). Returns same shape.

Both verbs read the vendored ncp-schema-v1.3.0.json at module-level
(lru-cached), then walk the NCP body recursively collecting values
at every matching field-name path.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agency.engine import Engine

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "novel"


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "ncp validation") -> str:
    iid = e.intent.capture(purpose, "ncp coverage", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.ncp.json").read_text())


# ─────────────────────── registration ───────────────────────


def test_registers_two_ncp_validators() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert {"validate_appreciations", "validate_narrative_functions"} <= set(cap.verbs)
    e.memory.close()


# ─────────────────────── validate_appreciations ───────────────────────


def test_validate_appreciations_passes_good_work() -> None:
    """good_work.ncp.json doesn't carry rich appreciation/narrative_function
    fields (it's a storyform-shape fixture), so the empty-walk PASSES."""
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("good_work")
    data, _ = _invoke(e, iid, "validate_appreciations", ncp=ncp)
    assert data["passed"] is True
    assert data["violations"] == []
    e.memory.close()


def test_validate_appreciations_canonical_set_size_463() -> None:
    """The canonical set lookup must surface the documented 463 values
    (per NCP v1.3.0 spec). This is a goal-criterion invariant."""
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "validate_appreciations", ncp={})
    assert data["canonical_size"] == 463
    e.memory.close()


def test_validate_appreciations_flags_invalid_value() -> None:
    """An NCP with an appreciation field carrying a non-canonical value
    must surface the violation with its path."""
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = {
        "story": {
            "narratives": [{
                "subtext": {
                    "perspectives": [{
                        "appreciation": "NOT-A-REAL-APPRECIATION",
                    }],
                }
            }]
        }
    }
    data, _ = _invoke(e, iid, "validate_appreciations", ncp=ncp)
    assert data["passed"] is False
    assert any(v["value"] == "NOT-A-REAL-APPRECIATION"
               for v in data["violations"])
    e.memory.close()


def test_validate_appreciations_accepts_canonical_value() -> None:
    """An NCP carrying a real canonical-appreciation value passes."""
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = {
        "story": {
            "narratives": [{
                "subtext": {
                    "perspectives": [{"appreciation": "Argument Approach"}],
                }
            }]
        }
    }
    data, _ = _invoke(e, iid, "validate_appreciations", ncp=ncp)
    assert data["passed"] is True
    e.memory.close()


# ─────────────────────── validate_narrative_functions ───────────────────────


def test_validate_narrative_functions_passes_good_work() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("good_work")
    data, _ = _invoke(e, iid, "validate_narrative_functions", ncp=ncp)
    assert data["passed"] is True
    e.memory.close()


def test_validate_narrative_functions_canonical_set_size_144() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "validate_narrative_functions", ncp={})
    assert data["canonical_size"] == 144
    e.memory.close()


def test_validate_narrative_functions_flags_invalid() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = {
        "story": {
            "narratives": [{
                "subtext": {
                    "elements": [{
                        "narrative_function": "BOGUS-FUNCTION-NAME",
                    }],
                }
            }]
        }
    }
    data, _ = _invoke(e, iid, "validate_narrative_functions", ncp=ncp)
    assert data["passed"] is False
    assert any(v["value"] == "BOGUS-FUNCTION-NAME"
               for v in data["violations"])
    e.memory.close()


def test_validate_narrative_functions_accepts_canonical_value() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = {
        "story": {
            "narratives": [{
                "subtext": {
                    "elements": [{"narrative_function": "Acceptance"}],
                }
            }]
        }
    }
    data, _ = _invoke(e, iid, "validate_narrative_functions", ncp=ncp)
    assert data["passed"] is True
    e.memory.close()
