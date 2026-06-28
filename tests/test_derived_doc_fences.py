"""Spec 389 — derived fences for hand-authored reference docs.

Extends the Spec 149 `<!-- derived:<id> -->` fence engine with code-introspection
fence kinds that regenerate from the LIVE engine — so the mechanically-derivable
fragments of a hand doc (the `SUBSTRATE_TOOLS` roster, a capability's verb list,
the driver-boundary set) stop rotting on every refactor. The expected values are
COMPUTED from the live source (rule 8 — no pinned counts).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.derive_docs import (
    apply_doc_fences,
    doc_fence_ids,
    doc_has_derived_drift,
    render_capability_verbs,
    render_driver_boundaries,
    render_substrate_tools,
)

_REPO = Path(__file__).resolve().parents[1]
_OVERVIEW = _REPO / "docs" / "vision" / "reference" / "overview.md"


# ── the three code-introspection renderers derive from live source ────────────

def test_substrate_tools_render_matches_live() -> None:
    from agency._substrate_tools import SUBSTRATE_TOOLS
    live = [t.name for t in SUBSTRATE_TOOLS]
    out = render_substrate_tools()
    for name in live:
        assert f"`{name}`" in out, f"{name} missing from substrate-tools fence"
    assert f"**{len(live)}**" in out          # count derived from live, not pinned


def test_driver_boundaries_render_matches_live() -> None:
    import tempfile
    from agency.engine import Engine
    live = sorted(Engine(tempfile.mktemp(suffix=".db"),
                         _require_skill_doc=False).drivers.names())
    out = render_driver_boundaries()
    for name in live:
        assert f"`{name}`" in out
    assert f"**{len(live)}**" in out


def test_capability_verbs_render_matches_live() -> None:
    import tempfile
    from agency.engine import Engine
    e = Engine(tempfile.mktemp(suffix=".db"), _require_skill_doc=False)
    verbs = sorted(e.registry.get("reflect").verbs.keys())
    out = render_capability_verbs("reflect")
    for v in verbs:
        assert f"`{v}`" in out
    assert f"**{len(verbs)}**" in out


# ── fence application: rewrite, idempotent, prose-preserving ──────────────────

_PROSE_BEFORE = "Intro prose that must survive byte-for-byte.\n\n"
_PROSE_AFTER = "\nTrailing prose that must survive byte-for-byte.\n"


def _doc(fence_id: str, inner: str) -> str:
    return (f"{_PROSE_BEFORE}<!-- derived:{fence_id} -->\n{inner}"
            f"<!-- /derived:{fence_id} -->{_PROSE_AFTER}")


def test_apply_doc_fences_rewrites_stale_and_is_idempotent() -> None:
    doc = _doc("substrate-tools", "STALE — out of date list\n")
    once = apply_doc_fences(doc)
    assert "STALE" not in once
    assert render_substrate_tools().strip() in once
    assert apply_doc_fences(once) == once          # idempotent
    assert once.startswith(_PROSE_BEFORE) and once.endswith(_PROSE_AFTER)


def test_apply_doc_fences_no_fence_is_identity() -> None:
    plain = "Just prose, no fences here.\n"
    assert apply_doc_fences(plain) == plain


def test_capability_verbs_fence_parametrized() -> None:
    doc = _doc("capability-verbs:reflect", "old\n")
    out = apply_doc_fences(doc)
    assert "`note`" in out and "`recall`" in out


def test_unclosed_doc_fence_raises_broken() -> None:
    from agency.toolresult import Codes
    broken = f"{_PROSE_BEFORE}<!-- derived:substrate-tools -->\nno close marker\n"
    with pytest.raises(ValueError) as exc:
        apply_doc_fences(broken)
    assert getattr(exc.value, "code", "") == Codes.DERIVE_FENCE_BROKEN


# ── the drift discriminator: derived-zone drift vs prose drift ────────────────

def test_doc_has_derived_drift_true_when_fence_stale() -> None:
    assert doc_has_derived_drift(_doc("substrate-tools", "STALE\n")) is True


def test_doc_has_derived_drift_false_when_fence_current() -> None:
    current = apply_doc_fences(_doc("substrate-tools", "x\n"))
    assert doc_has_derived_drift(current) is False


def test_doc_has_derived_drift_false_without_fence() -> None:
    assert doc_has_derived_drift("prose only, source may have changed\n") is False


def test_doc_fence_ids_finds_open_markers_only() -> None:
    doc = _doc("substrate-tools", "x\n") + _doc("driver-boundaries", "y\n")
    ids = doc_fence_ids(doc)
    assert ids == ["substrate-tools", "driver-boundaries"]


# ── the proof + standing guard: overview.md's fence stays in sync ─────────────

def test_overview_has_substrate_tools_fence() -> None:
    text = _OVERVIEW.read_text(encoding="utf-8")
    assert "<!-- derived:substrate-tools -->" in text, \
        "overview.md must opt its substrate-tools list into a derived fence (Spec 389)"


def test_overview_substrate_fence_in_sync_with_live() -> None:
    text = _OVERVIEW.read_text(encoding="utf-8")
    assert not doc_has_derived_drift(text), (
        "overview.md derived fences are stale — run "
        "`python -m scripts.derive_docs --write-docs`")


# ── derive_docs_pass over a docs tree ─────────────────────────────────────────

def test_derive_docs_pass_writes_stale_fence(tmp_path) -> None:
    from scripts.derive_docs import derive_docs_pass
    doc = tmp_path / "d.md"
    doc.write_text(_doc("substrate-tools", "STALE\n"), encoding="utf-8")
    (tmp_path / "nofence.md").write_text("plain prose\n", encoding="utf-8")
    changed, broken = derive_docs_pass(tmp_path, write=True)
    assert broken == []
    assert doc in changed
    assert not doc_has_derived_drift(doc.read_text(encoding="utf-8"))  # now in sync
    # a second pass is a no-op (idempotent)
    changed2, _ = derive_docs_pass(tmp_path, write=True)
    assert changed2 == []


def test_derive_docs_pass_reports_broken_fence(tmp_path) -> None:
    from scripts.derive_docs import derive_docs_pass
    (tmp_path / "b.md").write_text(
        "<!-- derived:substrate-tools -->\nno close\n", encoding="utf-8")
    changed, broken = derive_docs_pass(tmp_path, write=True)
    assert changed == [] and len(broken) == 1


# ── check-doc-drift triage: derived (auto) vs prose (hand-review) ─────────────

def _drift_doc(tmp_path, *, fence_inner: str, source_bytes: bytes = b"v1"):
    """A tmp docs tree: one source file + a doc that doc-sources it and carries a
    substrate-tools fence. Returns (docs_root, root, doc_path)."""
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    (root / "src.py").write_bytes(source_bytes)
    doc = docs / "d.md"
    doc.write_text(
        "<!-- doc-source: src.py -->\n<!-- doc-hash: 0 -->\n\n"
        f"<!-- derived:substrate-tools -->\n{fence_inner}"
        "<!-- /derived:substrate-tools -->\n", encoding="utf-8")
    return docs, root, doc


def test_check_docs_classifies_stale_derived_as_auto(tmp_path) -> None:
    from scripts._doc_drift import _hash_sources, check_docs
    docs, root, doc = _drift_doc(tmp_path, fence_inner="STALE list\n")
    # stamp the CORRECT source hash by hand (so the source is "in sync"), leaving
    # the fence stale — isolates derived drift from prose drift.
    digest, _ = _hash_sources(root, ["src.py"])
    doc.write_text(doc.read_text(encoding="utf-8").replace(
        "<!-- doc-hash: 0 -->", f"<!-- doc-hash: {digest} -->"), encoding="utf-8")
    rep = check_docs(docs, root=root)
    assert len(rep.stale_derived) == 1 and not rep.stale_prose


def test_check_docs_update_regenerates_fence_and_restamps(tmp_path) -> None:
    from scripts._doc_drift import check_docs
    docs, root, doc = _drift_doc(tmp_path, fence_inner="STALE list\n")
    check_docs(docs, root=root, update=True)          # regen fence + stamp
    assert not doc_has_derived_drift(doc.read_text(encoding="utf-8"))
    assert check_docs(docs, root=root).ok == 1        # now fully in sync


def test_check_docs_prose_drift_stays_hand_review(tmp_path) -> None:
    from scripts._doc_drift import check_docs
    docs, root, doc = _drift_doc(tmp_path, fence_inner=render_substrate_tools())
    check_docs(docs, root=root, update=True)          # stamp with fence current
    (root / "src.py").write_bytes(b"v2 - a listed source changed")  # prose-side rot
    rep = check_docs(docs, root=root)
    assert len(rep.stale_prose) == 1 and not rep.stale_derived


def test_check_docs_unclosed_fence_is_broken(tmp_path) -> None:
    from scripts._doc_drift import check_docs
    root = tmp_path
    docs = root / "docs"
    docs.mkdir()
    (root / "src.py").write_bytes(b"v1")
    (docs / "d.md").write_text(
        "<!-- doc-source: src.py -->\n<!-- doc-hash: 0 -->\n\n"
        "<!-- derived:substrate-tools -->\nno close marker\n", encoding="utf-8")
    rep = check_docs(docs, root=root)
    assert len(rep.broken) == 1
