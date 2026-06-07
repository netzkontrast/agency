"""Spec 092 G5/G6 — the advisory drift scripts run clean on the repo."""
import importlib.util
import pathlib
from importlib.machinery import SourceFileLoader

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name, rel):
    # the scripts have no .py extension — load via an explicit source loader
    loader = SourceFileLoader(name, str(ROOT / rel))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def test_check_followup_every_shipped_spec_is_grounded():
    # G6 — every Shipped spec's Followup cites tests that EXIST (a ref the spec documents
    # as intentionally absent/superseded/not-yet-written is skipped, not flagged). Now
    # that the false-positives are fixed this is an accurate grounding gate; the CI step
    # stays advisory (continue-on-error) for the log report.
    cf = _load("check_followup", "scripts/check-followup")
    assert cf.main(quiet=True) == 0


def test_check_doc_drift_runs_without_crashing():
    # G5 — doc-drift is ADVISORY (the CI step is continue-on-error); the suite only
    # asserts the script runs + returns a clean exit code, NOT that every doc is in sync
    # (a stale hash is a re-stamp nudge, not a test failure — that would couple every
    # doc-source-touching PR to a re-stamp in the same commit).
    cdd = _load("check_doc_drift", "scripts/check-doc-drift")
    assert cdd.check(update=False, strict=False) in (0, 1)
