"""Acceptance — Spec 385: brooks-lint sidecars → agency quality surface.

Two one-time importers carry an existing brooks-lint user's state across the port:
`.brooks-lint.yaml` → the unified `quality:` config block + `Suppression` nodes,
and `.brooks-lint-history.json` → back-dated `QualityRun` nodes (trend preserved).
Both are non-destructive (keep-both, Spec 292) and idempotent.
"""
from __future__ import annotations

import json

import yaml

from conftest import invoke


def test_config_migrates_to_quality_block_non_destructively(engine, iid, tmp_path,
                                                            monkeypatch):
    brooks = tmp_path / ".brooks-lint.yaml"
    brooks.write_text(yaml.safe_dump({
        "strictness": "legacy-friendly", "disable": ["T5"],
        "severity": {"R1": "suggestion"},
        "suppress": [{"risk": "R3", "glob": "src/util.py"}]}), encoding="utf-8")
    out = tmp_path / ".agency" / "config.yaml"
    monkeypatch.setenv("AGENCY_CONFIG", str(out))

    r, _ = invoke(engine, iid, "analyze", "migrate_quality_config",
                  config_path=str(brooks))
    assert r["migrated"] is True, r

    cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert cfg["quality"]["strictness"] == "legacy-friendly"
    assert "T5" in cfg["quality"]["disable"]
    assert brooks.exists(), "keep-both — the legacy .brooks-lint.yaml must remain"
    # a suppress entry becomes a Suppression node (read by the score, Spec 381 §4)
    sup = [s for s in engine.memory.find("Suppression") if s.get("risk") == "R3"]
    assert sup and sup[0].get("glob") == "src/util.py", sup


def test_config_merge_preserves_other_sections(engine, iid, tmp_path, monkeypatch):
    out = tmp_path / ".agency" / "config.yaml"
    out.parent.mkdir(parents=True)
    out.write_text(yaml.safe_dump({"frugal": {"level": "full"}}), encoding="utf-8")
    brooks = tmp_path / ".brooks-lint.yaml"
    brooks.write_text(yaml.safe_dump({"strictness": "strict"}), encoding="utf-8")
    monkeypatch.setenv("AGENCY_CONFIG", str(out))

    invoke(engine, iid, "analyze", "migrate_quality_config", config_path=str(brooks))
    cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert cfg["frugal"]["level"] == "full", "merge clobbered an unrelated section"
    assert cfg["quality"]["strictness"] == "strict"


def test_history_migrates_backdated_and_idempotent(engine, iid, tmp_path):
    hist = tmp_path / ".brooks-lint-history.json"
    records = [
        {"date": "2026-01-01", "mode": "review", "score": 70,
         "findings": {"critical": 2, "warning": 1, "suggestion": 0}, "scope": "a"},
        {"date": "2026-02-01", "mode": "review", "score": 80,
         "findings": {"critical": 1, "warning": 1, "suggestion": 1}, "scope": "a"},
        {"date": "2026-03-01", "mode": "review", "score": 90,
         "findings": {"critical": 0, "warning": 1, "suggestion": 2}, "scope": "a"},
    ]
    hist.write_text(json.dumps(records), encoding="utf-8")

    r, _ = invoke(engine, iid, "analyze", "migrate_quality_history",
                  history_path=str(hist))
    assert r["imported"] == 3, r
    runs = [q for q in engine.memory.find("QualityRun") if q.get("migrated_key")]
    assert len(runs) == 3
    assert {q.get("recorded_at") for q in runs} == {
        "2026-01-01", "2026-02-01", "2026-03-01"}

    # idempotent — re-running imports nothing new (content-hash dedup)
    r2, _ = invoke(engine, iid, "analyze", "migrate_quality_history",
                   history_path=str(hist))
    assert r2["imported"] == 0 and r2["skipped"] == 3, r2


def test_missing_sidecars_degrade_gracefully(engine, iid, tmp_path):
    rc, _ = invoke(engine, iid, "analyze", "migrate_quality_config",
                   config_path=str(tmp_path / "nope.yaml"))
    rh, _ = invoke(engine, iid, "analyze", "migrate_quality_history",
                   history_path=str(tmp_path / "nope.json"))
    assert rc["migrated"] is False and rh["migrated"] is False
