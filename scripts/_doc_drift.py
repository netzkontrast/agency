"""Doc-drift detection core (importable) — Spec 054 hashing + Spec 389 derived fences.

`scripts/check-doc-drift` is a hyphenated shim that can't be imported; this module
holds the reusable logic so it is unit-testable.

The Spec 054 mechanism: a hand-written doc lists the source files it documents in a
``<!-- doc-source: … -->`` marker and stamps a ``<!-- doc-hash: … -->`` over their
bytes. A source change ⇒ hash mismatch ⇒ the doc is STALE and a human re-reads it.

Spec 389 narrows that hand-review surface: the mechanically-derivable fragments a
doc copies from code live in ``<!-- derived:<kind> -->`` fences (see
``scripts.derive_docs``). A stale doc is now triaged:

- ``stale_derived`` — its derived fences are out of date. AUTO-resolvable: run
  ``derive_docs --write-docs`` (or ``check-doc-drift --update``, which regenerates
  the fences before re-stamping). No hand prose edit needed.
- ``stale_prose`` — hash mismatch but the derived fences already match code, so the
  rot is in hand-written prose. Genuine hand-review (as before).

This keeps the derived pass from ever MASKING genuine prose drift, while shrinking
the hand-review surface to the fragments that truly need a human.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
from dataclasses import dataclass, field

_SOURCE_RE = re.compile(r"<!--\s*doc-source:\s*(.+?)\s*-->")
_HASH_RE = re.compile(r"<!--\s*doc-hash:\s*([0-9a-f]*)\s*-->")
_GENERATED_RE = re.compile(r"<!--\s*doc-generated-by:")


def _hash_sources(root: pathlib.Path, paths: list[str]) -> tuple[str, list[str]]:
    """Hash the concatenated bytes of the listed sources (sorted, deterministic).
    Returns (hex_digest[:16], missing_paths)."""
    h = hashlib.sha256()
    missing: list[str] = []
    for rel in sorted(paths):
        p = root / rel
        if not p.exists():
            missing.append(rel)
            continue
        h.update(rel.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16], missing


def _regenerate_fences(text: str) -> tuple[str, str | None]:
    """Regenerate any Spec 389 code-introspection fences in `text`. Returns
    (new_text, error). On a broken fence, returns (text, error-message) — the
    caller surfaces it without crashing the whole sweep. When `derive_docs` is
    unimportable (no agency on path), returns (text, None) — the integration
    degrades to plain hash drift."""
    try:
        from scripts.derive_docs import apply_doc_fences
    except Exception:                       # pragma: no cover - env guard
        return text, None
    try:
        return apply_doc_fences(text), None
    except ValueError as e:
        return text, str(e)


@dataclass
class DocDriftReport:
    ok: int = 0
    stale_prose: list[str] = field(default_factory=list)     # hand-review
    stale_derived: list[str] = field(default_factory=list)   # auto-resolvable
    unmarked: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    broken: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.stale_prose or self.stale_derived or self.broken)


def check_docs(docs_root: pathlib.Path, *, root: pathlib.Path | None = None,
               update: bool = False) -> DocDriftReport:
    """Scan ``docs_root/**/*.md``; classify each doc. ``root`` resolves
    ``doc-source`` paths (defaults to ``docs_root.parent`` — the repo root in
    production). When ``update`` is set: regenerate derived fences AND re-stamp
    the hash, so an auto-resolvable doc needs no hand edit."""
    root = root or docs_root.parent
    rep = DocDriftReport()
    for doc in sorted(docs_root.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        if _GENERATED_RE.search(text):
            continue
        m = _SOURCE_RE.search(text)
        rel = str(doc.relative_to(root)) if doc.is_relative_to(root) else str(doc)
        if not m:
            rep.unmarked.append(rel)
            continue
        sources = m.group(1).split()
        digest, missing = _hash_sources(root, sources)
        if missing:
            rep.stale_prose.append(f"{rel}  (missing source: {', '.join(missing)})")
            continue

        regenerated, fence_err = _regenerate_fences(text)
        if fence_err is not None:
            rep.broken.append(f"{rel}  ({fence_err})")
            continue
        derived_drift = regenerated != text

        hm = _HASH_RE.search(text)
        stamped = hm.group(1) if hm else ""
        if stamped == digest and not derived_drift:
            rep.ok += 1
            continue

        if update:
            text = regenerated                      # regenerate derived fences first
            hm = _HASH_RE.search(text)
            new = f"<!-- doc-hash: {digest} -->"
            if hm:
                text = text[:hm.start()] + new + text[hm.end():]
            else:                                   # insert after the doc-source line
                ms = _SOURCE_RE.search(text)
                text = text[:ms.end()] + "\n" + new + text[ms.end():]
            doc.write_text(text, encoding="utf-8")
            rep.updated.append(rel)
            continue

        # report mode — triage the staleness (Spec 389)
        if derived_drift:
            rep.stale_derived.append(
                f"{rel}  (derived fences stale — run `derive_docs --write-docs`)")
        else:
            rep.stale_prose.append(f"{rel}  (sources changed — review + re-stamp)")
    return rep
