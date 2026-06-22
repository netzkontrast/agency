"""Acceptance — Spec 383 Slice 2b: the brooks JUDGMENT corpus (`-m wet`).

The decidable risks have a paired fixture corpus (quality_corpus.feature). This is
its counterpart for the NINE judgment-only risks (R2/R3/R6 + T1–T6) — the ones a
scanner can't decide, that the LLM review-chain pass produces. Each fixture is a
known-bad snippet that a competent reviewer SHOULD flag with that risk; the test
runs a REAL review (`analyze.review`, mode="sweep") and asserts the risk is flagged.

These need a live inference backend, so the module skips unless ANTHROPIC_API_KEY or
OPENROUTER_API_KEY is set — they no-op in the default keyless CI and run in a
dedicated `pytest -m wet` job with a key. The COVERAGE invariant (every judgment-only
risk has a fixture) is derived + checked keyless in test_quality_chain.py.
"""
from __future__ import annotations

import os

import pytest

from conftest import invoke

# Known-bad fixtures, one per judgment-only risk (smell-evocative, compact). The
# keys are decay-risk codes; the coverage invariant (test_quality_chain.py) asserts
# this dict covers exactly the judgment-only set DERIVED from the registry (rule 8).
JUDGMENT_FIXTURES: dict[str, str] = {
    # R2 Change Propagation — Feature Envy: a method using another class's data
    # far more than its own (a change to Account ripples into Statement).
    "R2": '''
class Account:
    def __init__(self, balance, overdraft, currency, owner):
        self.balance = balance
        self.overdraft = overdraft
        self.currency = currency
        self.owner = owner

class Statement:
    def summarize(self, account):
        # uses Account's data exclusively, none of its own — envy
        avail = account.balance + account.overdraft
        return f"{account.owner}: {avail} {account.currency} ({account.balance})"
''',
    # R3 Knowledge Duplication — the same tax rule expressed in two places.
    "R3": '''
def price_with_tax(net):
    return net + net * 0.19          # 19% VAT, here

def invoice_total(items):
    net = sum(items)
    return net + net * 0.19          # 19% VAT, duplicated decision
''',
    # R6 Domain Model Distortion — an anemic data bag + the domain rule stranded
    # in a utility (behaviour that belongs on Order lives in OrderUtils).
    "R6": '''
class Order:
    def __init__(self, lines, status):
        self.lines = lines
        self.status = status         # pure data, no behaviour

class OrderUtils:
    @staticmethod
    def can_ship(order):
        # the shipping rule belongs on Order, not a utility bag
        return order.status == "paid" and len(order.lines) > 0
''',
    # T1 Test Obscurity — vague name, no assertion messages, intent unclear.
    "T1": '''
def test_1():
    r = process([1, 2, 3])
    assert r
    assert r[0] == 1
    assert len(r) == 3
''',
    # T2 Test Brittleness — coupled to a private implementation detail that a
    # safe refactor would break, not to observable behaviour.
    "T2": '''
def test_uses_private_state():
    svc = Service()
    svc.handle("x")
    assert svc._cache["x"]._node.dirty is True     # reaches into privates
    assert svc._internal_calls == 1
''',
    # T3 Test Duplication — the same scenario asserted again and again with
    # copy-pasted setup that should be a shared fixture/parametrization.
    "T3": '''
def test_add_a():
    c = Calc(); c.add(1); c.add(2); assert c.total == 3
def test_add_b():
    c = Calc(); c.add(1); c.add(2); assert c.total == 3
def test_add_c():
    c = Calc(); c.add(1); c.add(2); assert c.total == 3
''',
    # T4 Mock Abuse — mock setup dwarfs the test; asserts only that a mock was
    # called, verifying interaction not behaviour.
    "T4": '''
def test_saves_user():
    repo = Mock(); logger = Mock(); clock = Mock(); mailer = Mock()
    repo.find.return_value = Mock(id=1, name="a", active=True)
    clock.now.return_value = 0
    mailer.send.return_value = True
    svc = UserService(repo, logger, clock, mailer)
    svc.save("a")
    repo.save.assert_called_once()          # only that a mock was called
''',
    # T5 Coverage Illusion — public behaviour shipped with a test that exercises
    # only the trivial path, leaving the real branch unverified.
    "T5": '''
def divide(a, b):
    if b == 0:
        raise ValueError("no")     # the branch that matters
    return a / b

def test_divide():
    assert divide(6, 2) == 3        # never tests the b == 0 branch
''',
    # T6 Architecture Mismatch — the unit can't be tested in isolation because a
    # hard-wired dependency blocks the seam (constructs its own DB/clock).
    "T6": '''
import sqlite3, time
class Report:
    def build(self):
        conn = sqlite3.connect("/var/app/prod.db")    # no seam — hard-wired
        ts = time.time()                              # real clock, untestable
        return conn.execute("select 1").fetchone(), ts
''',
}


def _has_backend() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY"))


pytestmark = [
    pytest.mark.wet,
    pytest.mark.skipif(not _has_backend(),
                       reason="brooks judgment corpus needs a live inference backend "
                              "(set ANTHROPIC_API_KEY or OPENROUTER_API_KEY)"),
]


@pytest.mark.parametrize("code", sorted(JUDGMENT_FIXTURES))
def test_judgment_flags_known_bad(engine, iid, tmp_path, code):
    """A real review over a known-bad fixture flags the expected judgment risk."""
    (tmp_path / "m.py").write_text(JUDGMENT_FIXTURES[code], encoding="utf-8")
    r, _ = invoke(engine, iid, "analyze", "review", path=str(tmp_path), mode="sweep")
    flagged = {f.get("risk_code") for f in r.get("findings", [])}
    assert code in flagged, (
        f"judgment did not flag {code}; got {sorted(c for c in flagged if c)}")
