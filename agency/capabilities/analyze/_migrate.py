"""Spec 385 — one-time brooks-lint → agency quality migration (pure helpers).

A project mid-stream on the brooks-lint plugin has two sidecar files: a
``.brooks-lint.yaml`` config and a ``.brooks-lint-history.json`` trend. These
pure functions map them onto agency's unified surfaces — the ``quality:`` config
block (Spec 381 §2) + ``QualityRun`` history nodes (Spec 381 §3) — so the
importer verbs (analyze.migrate_quality_*) stay thin. No I/O, no graph writes.
"""
from __future__ import annotations

from ..._frontmatter import frontmatter_hash

# brooks `.brooks-lint.yaml` keys that map 1:1 onto the unified `quality:` block
# (Spec 381 §2). `suppress` is split out (→ Suppression nodes, §4); the rest ride.
_QUALITY_KEYS = ("disable", "focus", "severity", "ignore", "strictness",
                 "custom_risks")


def map_brooks_config(raw: dict) -> tuple[dict, list]:
    """Map a parsed ``.brooks-lint.yaml`` onto ``(quality_block, suppress_entries)``.

    1:1 for disable/focus/severity/ignore/strictness/custom_risks (empty values
    dropped so the merge stays minimal); ``suppress`` is returned separately
    because it becomes ``Suppression`` graph nodes, not config (Spec 381 §4)."""
    raw = raw or {}
    quality = {k: raw[k] for k in _QUALITY_KEYS
               if raw.get(k) not in (None, [], {}, "")}
    suppress = list(raw.get("suppress") or [])
    return quality, suppress


def history_key(rec: dict) -> str:
    """Stable content hash of a ``.brooks-lint-history.json`` record — the
    idempotency key so a re-import never duplicates (keep-both, Spec 292).
    Delegates to the canonical content-hash (``_frontmatter.frontmatter_hash``) —
    the dict-shaped twin already used for Artefact fingerprints."""
    return frontmatter_hash(rec)


def normalize_record(rec: dict) -> dict:
    """A ``.brooks-lint-history.json`` record → ``QualityRun`` props. brooks shape
    (``common.md`` History Tracking): ``{date, mode, score,
    findings:{critical,warning,suggestion}, scope}``. ``recorded_at`` carries the
    original date (the trend is preserved by inserting oldest-first, so the
    bi-temporal ``vfrom`` order matches); ``migrated_key`` is the dedup anchor."""
    f = rec.get("findings") or {}
    return {
        "mode": str(rec.get("mode", "review")),
        "scope": str(rec.get("scope", "")),
        "score": int(rec.get("score", 0) or 0),
        "critical": int(f.get("critical", 0) or 0),
        "warning": int(f.get("warning", 0) or 0),
        "suggestion": int(f.get("suggestion", 0) or 0),
        "status": "complete",
        "recorded_at": str(rec.get("date", "")),
        "migrated_key": history_key(rec),
    }
