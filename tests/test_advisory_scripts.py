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
    # G6 — every Shipped spec's Followup cites test files that exist on disk
    cf = _load("check_followup", "scripts/check-followup")
    assert cf.main(quiet=True) == 0


def test_check_doc_drift_marked_docs_in_sync():
    # G5/doc-drift — every marked doc's sources match its stamped hash
    cdd = _load("check_doc_drift", "scripts/check-doc-drift")
    assert cdd.check(update=False, strict=False) == 0
