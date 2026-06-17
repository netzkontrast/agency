"""prompt.frameworks — the 27-framework library, first-class (Spec 304).

prompt-architect (ckelsoe, MIT) ships 27 research-backed prompt-engineering
frameworks across 7 intent categories. Structurally each is a *metaprompt
template*: a named-slot skeleton you fill to produce a better prompt. Spec 304
reimplements that library as graph-native agency substrate — the SAME storage
model as Spec 129's Dramatica fragments: a vendored ``data/frameworks.json`` as
the source of truth + a per-project overlay
(``.agency/prompt-frameworks-overlay.yaml``) that adds/overrides without editing
the vendored file. ``register_framework`` writes to the overlay.

Attribution lives in ``references/frameworks/NOTICE.md`` + each entry's
``source_ref``; the reference prose is preserved verbatim for human readers
under ``references/frameworks/*.md`` (NOT parsed at runtime — routing reads the
JSON).
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


_FRAMEWORKS_FILE = Path(__file__).parent.parent / "data" / "frameworks.json"
_DEFAULT_FW_OVERLAY_PATH = ".agency/prompt-frameworks-overlay.yaml"

# The presentation fields a single-framework lookup returns (held out of the
# wire payload: the per-framework routing ``discriminators`` + ``audience``,
# which routing — not a caller filling a template — consumes).
_FRAMEWORK_VIEW = (
    "slug", "name", "full_name", "intent_category", "complexity_tier",
    "components", "template", "when_to_use",
)


class FrameworksMixin:
    """The 27-framework library (Spec 304) — 3 verbs."""

    @verb(role="transform")
    def framework(self, slug: str) -> ToolResult:
        """Look up a single prompt-engineering framework by slug (transform).

        Inputs: slug (str — e.g. ``co-star``, ``ape``, ``rise-ie``).
        Returns: ``{slug, name, intent_category, complexity_tier, components,
                 template, when_to_use, tokens}`` OR
                 ``{slug, error: 'NO_FRAMEWORK'}`` when no framework carries
                 that slug.
        chain_next: ``prompt.render(slug, fields)`` to fill its template.
        """
        entry = _load_frameworks().get(slug)
        if entry is None:
            return ToolResult.success(data={"slug": slug, "error": "NO_FRAMEWORK"})
        view = {k: entry.get(k) for k in _FRAMEWORK_VIEW}
        view["tokens"] = _approx_tokens(entry.get("template", ""))
        return ToolResult.success(data=view)

    @verb(role="transform")
    def frameworks_for(self, intent: str,
                       max_tokens: int = 2000) -> ToolResult:
        """Budget-aware candidate list for a known intent category (transform).

        Returns the user-facing frameworks whose ``intent_category`` matches
        ``intent``, in library order, accumulating template tokens until
        ``max_tokens`` binds (the shared ``budget_take`` truncation — 129
        parity). Functional frameworks (``audience='functional'``, Spec 306)
        are held out — they are never user-prompt picks.

        Inputs: intent (str — one of recover/clarify/create/transform/reason/
                critique/agentic), max_tokens (int — total budget).
        Returns: ``{intent, frameworks: [{slug, name, complexity_tier,
                 tokens}], total_tokens, truncated_at: int|None}``.
        chain_next: ``prompt.route_framework`` to pick ONE (305); or
                    ``prompt.render(slug, fields)``.
        """
        store = _load_frameworks()
        candidates = [
            {"slug": e["slug"], "name": e["name"],
             "complexity_tier": e["complexity_tier"],
             "tokens": _approx_tokens(e.get("template", ""))}
            for e in store.values()
            if e.get("audience", "user") == "user"
            and e.get("intent_category") == intent
        ]
        taken, over_budget = budget_take(
            candidates, lambda f: f["tokens"], max_tokens)
        total = sum(f["tokens"] for f in taken)
        truncated_at = len(taken) if over_budget else None
        return ToolResult.success(data={
            "intent": intent,
            "frameworks": taken,
            "total_tokens": total,
            "truncated_at": truncated_at,
        })

    @verb(role="effect")
    def register_framework(self, slug: str, payload: dict,
                           overlay_path: str = "") -> ToolResult:
        """Write a custom framework to the project overlay (effect; extensible).

        Inputs: slug (str), payload (dict — at minimum ``template``; any of
                name/intent_category/complexity_tier/audience/components/
                when_to_use/discriminators override the vendored defaults),
                overlay_path (str — defaults to the project overlay).
        Returns: ``{slug, name, intent_category, audience, overlay_path}`` OR
                 ``{slug, error: 'INVALID_ARGUMENT'}`` when no template is given.
        chain_next: ``prompt.framework(slug)`` to verify the round-trip.
        """
        if not isinstance(payload, dict) or not payload.get("template"):
            return ToolResult.success(data={
                "slug": slug, "error": "INVALID_ARGUMENT"})
        entry = _normalise_framework(slug, payload)
        path = overlay_path or _DEFAULT_FW_OVERLAY_PATH
        _write_overlay_framework(path, slug, entry)
        _load_frameworks.cache_clear()
        return ToolResult.success(data={
            "slug": slug, "name": entry["name"],
            "intent_category": entry["intent_category"],
            "audience": entry["audience"],
            "overlay_path": path,
        })


# ─────────────────────────── framework loader (Spec 304 / 129 parity) ───────


def _normalise_framework(slug: str, payload: dict) -> dict:
    """Coerce a partial overlay payload into a full framework entry, filling
    sensible defaults so downstream readers stay total."""
    return {
        "slug": slug,
        "name": payload.get("name", slug),
        "full_name": payload.get("full_name", payload.get("name", slug)),
        "intent_category": payload.get("intent_category", "create"),
        "complexity_tier": payload.get("complexity_tier", "medium"),
        "audience": payload.get("audience", "user"),
        "components": list(payload.get("components", []) or []),
        "template": payload.get("template", ""),
        "discriminators": list(payload.get("discriminators", []) or []),
        "when_to_use": payload.get("when_to_use", ""),
        "source_ref": payload.get("source_ref", f"overlay:{slug}"),
    }


@lru_cache(maxsize=1)
def _load_frameworks() -> dict:
    """Merged store keyed by slug: vendored bootstrap + overlay (overlay wins)."""
    base: dict = {}
    if _FRAMEWORKS_FILE.is_file():
        raw = json.loads(_FRAMEWORKS_FILE.read_text())
        for entry in raw.get("frameworks") or []:
            base[entry["slug"]] = entry
    for slug, entry in _load_fw_overlay(_DEFAULT_FW_OVERLAY_PATH).items():
        base[slug] = entry
    return base


@lru_cache(maxsize=1)
def _load_intent_signals() -> dict:
    """Category-level routing keywords vendored alongside the frameworks
    (Spec 305 first-level routing). Slug→keyword data, not a magic table."""
    if _FRAMEWORKS_FILE.is_file():
        raw = json.loads(_FRAMEWORKS_FILE.read_text())
        return dict(raw.get("intent_signals") or {})
    return {}


def _load_fw_overlay(path: str) -> dict:
    """Read the per-project overlay → ``{slug: full_entry}``. The overlay is a
    YAML/JSON mapping of slug → payload; each payload is normalised."""
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        return {}
    text = p.read_text()
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
    except ImportError:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return {}
    out: dict = {}
    if isinstance(loaded, dict):
        for slug, payload in loaded.items():
            if isinstance(payload, dict):
                out[str(slug)] = _normalise_framework(str(slug), payload)
    return out


def _write_overlay_framework(path: str, slug: str, entry: dict) -> None:
    """Append-or-replace a single framework in the overlay file."""
    p = Path(os.path.expanduser(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if p.is_file():
        text = p.read_text()
        try:
            import yaml  # type: ignore
            existing = yaml.safe_load(text) or {}
        except ImportError:
            try:
                existing = json.loads(text)
            except json.JSONDecodeError:
                existing = {}
    if not isinstance(existing, dict):
        existing = {}
    existing[slug] = entry
    try:
        import yaml  # type: ignore
        p.write_text(yaml.safe_dump(existing, allow_unicode=True, sort_keys=True))
    except ImportError:
        p.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
