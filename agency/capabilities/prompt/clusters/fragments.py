"""prompt.fragments — Dramatica-as-prompt-fragments (Spec 129).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Each Dramatica ontology entry can carry a guidance fragment (second-person
agent imperative). Storage is hybrid: a vendored ``fragments.json`` ships the
bootstrap set; a per-project overlay
(``.agency/dramatica-fragments-overlay.yaml``) lets a workflow add or override
without editing the vendored file. ``register_fragment`` writes to the overlay.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from agency._overflow import budget_take
from agency.capability import verb
from agency.toolresult import ToolResult

from ._base import _approx_tokens


_FRAGMENTS_FILE = (Path(__file__).parent.parent.parent / "novel"
                   / "data" / "dramatica" / "fragments.json")
_DEFAULT_OVERLAY_PATH = ".agency/dramatica-fragments-overlay.yaml"


class FragmentsMixin:
    """Dramatica-as-prompt-fragments (Spec 129) — 3 verbs."""

    @verb(role="transform")
    def fragment(self, slug: str) -> ToolResult:
        """Look up a single Dramatica prompt fragment (transform).

        Inputs: slug (str — ontology id like ``th.main-character`` or any
                kind-prefix alias the novel cap's ``_resolve_term`` recognises).
        Returns: ``{slug, canonical_id, kind, text, tokens}`` OR
                 ``{slug, error: 'NO_FRAGMENT'}`` when no fragment is
                 authored for that entry yet.
        chain_next: ``prompt.fragments_for(scope)`` for multi-entry composition.
        """
        canonical_id, kind = _resolve_to_canonical(slug)
        if canonical_id is None:
            return ToolResult.success(data={
                "slug": slug, "error": "UNKNOWN_SLUG",
            })
        text = _load_fragments().get(canonical_id)
        if not text:
            return ToolResult.success(data={
                "slug": slug, "canonical_id": canonical_id, "kind": kind,
                "error": "NO_FRAGMENT",
            })
        return ToolResult.success(data={
            "slug": slug, "canonical_id": canonical_id, "kind": kind,
            "text": text, "tokens": _approx_tokens(text),
        })

    @verb(role="transform")
    def fragments_for(self, scope: dict,
                       max_tokens: int = 2000) -> ToolResult:
        """Compose multiple fragments for a storyform scope (transform).

        ``scope`` describes a slice of a storyform — any of these keys
        contributes a fragment lookup (order matters; earlier = higher
        priority when budget binds):
            throughline      → th.{mc|os|ic|rs}
            class_id         → class.{universe|physics|mind|psychology}
            concern_id       → type.{slug}
            problem_id       → element/variation lookup
            solution_id      → element/variation lookup
            crucial_element_id → element/variation lookup
            archetypes       → list[arc.*]; included in order

        Inputs: scope (dict), max_tokens (int — total budget).
        Returns: ``{fragments: [{slug, kind, text, tokens}], total_tokens,
                 truncated_at: int|None, skipped_no_fragment: [slug]}``.
        chain_next: feed ``fragments`` into the assembled brief
                    (Spec 127 ``prompt.assemble_scene_brief``).
        """
        order = [
            ("throughline", _throughline_slug),
            ("class_id", lambda v: v),
            ("concern_id", lambda v: v),
            ("crucial_element_id", lambda v: v),
            ("problem_id", lambda v: v),
            ("solution_id", lambda v: v),
        ]
        looked_up: list[tuple[str, str]] = []
        for key, transform in order:
            raw = scope.get(key)
            if raw:
                looked_up.append((key, transform(raw)))
        for arc in scope.get("archetypes") or []:
            looked_up.append(("archetype", arc))

        # Resolve every candidate to a fragment dict first (recording the
        # no-fragment skips), then let the shared budget_take loop perform
        # the priority-ordered, accumulate-and-stop-on-overshoot truncation
        # (Spec 286 P3 — the char-proxy lives in `_approx_tokens`, injected
        # as the per-item counter).
        skipped: list[str] = []
        candidates: list[dict] = []
        store = _load_fragments()
        for _key, slug in looked_up:
            canonical_id, kind = _resolve_to_canonical(slug)
            if canonical_id is None:
                skipped.append(slug)
                continue
            text = store.get(canonical_id)
            if not text:
                skipped.append(slug)
                continue
            candidates.append({
                "slug": slug, "canonical_id": canonical_id,
                "kind": kind, "text": text, "tokens": _approx_tokens(text),
            })
        fragments, over_budget = budget_take(
            candidates, lambda f: f["tokens"], max_tokens)
        total = sum(f["tokens"] for f in fragments)
        truncated_at: int | None = len(fragments) if over_budget else None
        return ToolResult.success(data={
            "fragments": fragments,
            "total_tokens": total,
            "truncated_at": truncated_at,
            "skipped_no_fragment": skipped,
        })

    @verb(role="effect")
    def register_fragment(self, slug: str, text: str,
                           overlay_path: str = "") -> ToolResult:
        """Write a fragment to the project overlay (effect; runtime-extensible).

        Inputs: slug (str — canonical or alias id), text (str — guidance
                body, ≤300 tokens recommended), overlay_path (str — defaults
                to ``.agency/dramatica-fragments-overlay.yaml``).
        Returns: ``{slug, canonical_id, kind, tokens, overlay_path}`` OR
                 ``{slug, error: 'UNKNOWN_SLUG'}``.
        chain_next: ``prompt.fragment(slug)`` to verify the round-trip.
        """
        canonical_id, kind = _resolve_to_canonical(slug)
        if canonical_id is None:
            return ToolResult.success(data={
                "slug": slug,
                "error": "UNKNOWN_SLUG",
            })
        path = overlay_path or _DEFAULT_OVERLAY_PATH
        _write_overlay_fragment(path, canonical_id, text)
        # Invalidate the loader cache so the next read sees the write.
        _load_fragments.cache_clear()
        return ToolResult.success(data={
            "slug": slug, "canonical_id": canonical_id, "kind": kind,
            "tokens": _approx_tokens(text),
            "overlay_path": path,
        })


# ─────────────────────────── Spec 129 fragment loader ───────────────────────────


@lru_cache(maxsize=1)
def _load_fragments() -> dict:
    """Merged store: vendored bootstrap + per-project overlay (overlay wins)."""
    base: dict = {}
    if _FRAGMENTS_FILE.is_file():
        raw = json.loads(_FRAGMENTS_FILE.read_text())
        base = dict(raw.get("fragments") or {})
    overlay = _load_overlay(_DEFAULT_OVERLAY_PATH)
    base.update(overlay)
    return base


def _load_overlay(path: str) -> dict:
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        return {}
    text = p.read_text()
    # Tiny YAML subset: top-level `id: "text"` lines (one per line) OR
    # full PyYAML when available.
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
        return {k: str(v) for k, v in loaded.items()
                if isinstance(k, str) and v is not None}
    except ImportError:
        pass
    out: dict = {}
    for ln in text.splitlines():
        ln = ln.split("#", 1)[0].rstrip()
        if not ln or ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if val:
            out[key.strip()] = val
    return out


def _write_overlay_fragment(path: str, canonical_id: str, text: str) -> None:
    """Append-or-replace a single fragment in the overlay file."""
    p = Path(os.path.expanduser(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_overlay(path)
    existing[canonical_id] = text
    # Write back as one-line-per-entry; PyYAML when available for safety.
    try:
        import yaml  # type: ignore
        p.write_text(yaml.safe_dump(existing, allow_unicode=True))
    except ImportError:
        lines = []
        for k, v in existing.items():
            safe = str(v).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{k}: "{safe}"')
        p.write_text("\n".join(lines) + "\n")


# ────────────── ontology resolution (re-uses novel cap's helper) ──────────────

def _resolve_to_canonical(slug: str) -> tuple[str | None, str | None]:
    """Resolve a slug to (canonical_ontology_id, kind) via the novel cap's
    ``_resolve_term``. Returns ``(None, None)`` when no entry matches.
    Cross-cap import is acceptable: the Dramatica ontology IS the substrate
    Spec 129 composes against (novel owns the data; prompt presents it)."""
    from agency.capabilities.novel._main import _resolve_term
    entry, _exact = _resolve_term(slug)
    if entry is None:
        return None, None
    return entry.get("id"), entry.get("kind")


def _throughline_slug(value: str) -> str:
    """Normalise common throughline aliases to canonical ontology ids.

    Caller short forms (``mc``, ``os``, ``ic``, ``rs``) map to the
    Dramatica canonical ids (``throughline.main``, ``throughline.objective``,
    ``throughline.influence``, ``throughline.relationship``). Pass-through
    for values that already look canonical."""
    alias = {
        "mc": "throughline.main",
        "os": "throughline.objective",
        "ic": "throughline.influence",
        "rs": "throughline.relationship",
    }
    return alias.get(value.lower(), value)
