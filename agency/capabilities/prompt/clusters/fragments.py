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
# Spec 143 — the Kohärenz-Protokoll deep-fragment overlay (six families).
_KP_FRAGMENTS_FILE = (Path(__file__).parent.parent.parent / "novel"
                      / "data" / "kp-fragments.yaml")
KP_FAMILIES = {"plurality", "klein-c", "mode-block", "reveal", "r-rule",
               "synthesis"}


@lru_cache(maxsize=1)
def _load_kp_fragments() -> dict:
    """slug → {text, family} from the vendored KP overlay (Spec 143)."""
    import yaml
    raw = yaml.safe_load(_KP_FRAGMENTS_FILE.read_text(encoding="utf-8")) or {}
    out: dict[str, dict] = {}
    for f in raw.get("fragments", []) or []:
        slug = f.get("slug", "")
        if slug:
            out[slug] = {"text": str(f.get("text", "")).strip(),
                         "family": f.get("family", "")}
    return out


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

    def _kp_active(self, scope: dict) -> bool:
        """Overlay isolation (Spec 143): KP fragments load only when the graph
        carries a CharacterSystem/StoryformSet, or the scope opts in
        explicitly (family / kp key). Non-KP novels see only Dramatica."""
        if scope.get("family") in KP_FAMILIES or scope.get("kp"):
            return True
        return bool(self.ctx.find("CharacterSystem")
                    or self.ctx.find("StoryformSet"))

    @verb(role="transform")
    def fragments_for_scope(self, scope: dict,
                            max_tokens: int = 2000) -> ToolResult:
        """Compose KP fragments for a drafting scope (transform; Spec 143).

        KP scope keys (all optional; earlier = higher priority when the
        budget binds): mode_block, genre_accent, audience_tier, routing_mode,
        transition_kind, predicate_kind, veil (maintain|leak-via-glitch|
        payoff), reveal_channels (list), alter_id (Alter node → category +
        function fragments), r_rule_ids (list — registered R-rule handles),
        family (whole-family pull), kp (bool opt-in).

        Inputs: scope (dict), max_tokens (total budget, ≤2000 default).
        Returns: ``{fragments: [{slug, kind, text, tokens, family}],
                 total_tokens, truncated_at, skipped_no_fragment}``.
        chain_next: ``prompt.compose_drafting_brief(scene_id)`` for the
                    scene-level composition.
        """
        store = _load_kp_fragments()
        if not self._kp_active(scope):
            return ToolResult.success(data={
                "fragments": [], "total_tokens": 0, "truncated_at": None,
                "skipped_no_fragment": [], "kp_active": False})
        slugs: list[str] = []
        # highest-specificity first: the alter beats its archetype beats mode
        alter_id = scope.get("alter_id")
        if alter_id:
            alter = self.ctx.recall(alter_id) or {}
            fn = str(alter.get("function", "")).strip().lower()
            if fn and f"kp.alter.{fn}" in store:
                slugs.append(f"kp.alter.{fn}")
            cat = alter.get("category", "")
            if cat:
                slugs.append(f"kp.alter.{cat}")
        for key, prefix in (("routing_mode", "kp.route."),
                            ("transition_kind", "kp.transition."),
                            ("mode_block", "kp.mode."),
                            ("genre_accent", "kp.genre."),
                            ("audience_tier", "kp.tier."),
                            ("veil", "kp.veil."),
                            ("predicate_kind", "kp.predicate.")):
            v = scope.get(key)
            if v:
                slugs.append(prefix + str(v).strip().lower()
                             .replace(" ", "-"))
        for ch in scope.get("reveal_channels") or []:
            slugs.append(f"kp.channel.{str(ch).strip().lower()}")
        for rid in scope.get("r_rule_ids") or []:
            key = str(rid).strip().lower().replace("-", "")
            hit = next((slug for slug in store
                        if slug.startswith(f"kp.rule.{key}-")
                        or slug.startswith(f"kp.rule.{key}.")), None)
            slugs.append(hit or f"kp.rule.{key}")
        fam = scope.get("family")
        if fam:
            slugs.extend(sorted(sl for sl, f in store.items()
                                if f["family"] == fam))
        seen: set[str] = set()
        skipped: list[str] = []
        candidates: list[dict] = []
        for slug in slugs:
            if slug in seen:
                continue
            seen.add(slug)
            entry = store.get(slug)
            if entry is None:
                skipped.append(slug)
                continue
            candidates.append({"slug": slug, "kind": "kp-fragment",
                               "family": entry["family"],
                               "text": entry["text"],
                               "tokens": _approx_tokens(entry["text"])})
        fragments, over = budget_take(candidates, lambda f: f["tokens"],
                                      max_tokens)
        return ToolResult.success(data={
            "fragments": fragments,
            "total_tokens": sum(f["tokens"] for f in fragments),
            "truncated_at": len(fragments) if over else None,
            "skipped_no_fragment": skipped, "kp_active": True})

    @verb(role="transform")
    def compose_drafting_brief(self, scene_id: str,
                               max_tokens: int = 2000) -> ToolResult:
        """Compose the LLM-side drafting brief for ONE scene (transform;
        Spec 143) — the prompt counterpart of Spec 127's graph-side
        ``assemble_scene_brief``. Reads the scene's mode-block, routing,
        fronting alter, reveal channels and R-rules from the graph, pulls
        the matching KP fragments, and returns ONE newline-joined brief.

        Inputs: scene_id, max_tokens.
        Returns: ``{brief, sources: [slug], total_tokens}``.
        chain_next: feed ``brief`` as the system prompt of the scene draft.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.success(data={
                "scene_id": scene_id, "error": "NOT_FOUND"})
        chapter = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = chapter.get("novel", "")
        number = int(chapter.get("number", 0))
        block = next((b for b in self.ctx.find("ModeBlock")
                      if b.get("novel") == novel_id
                      and int(b.get("from_chapter", 0)) <= number
                      <= int(b.get("to_chapter", 0))), None) or {}
        rules = [r.get("rule_id", "") for r in self.ctx.find("ProjectRule")
                 if r.get("novel") == novel_id]
        channels = sorted({r.get("channel", "")
                           for r in self.ctx.find("RevealRule")
                           if r.get("novel") == novel_id
                           and r.get("channel")})
        scope = {"kp": True,
                 "mode_block": block.get("mode", ""),
                 "genre_accent": block.get("genre_accent", ""),
                 "routing_mode": scene.get("route_mode", ""),
                 "alter_id": scene.get("pov_character_id", ""),
                 "reveal_channels": channels,
                 "r_rule_ids": rules}
        res = self.fragments_for_scope(
            {k: v for k, v in scope.items() if v}, max_tokens=max_tokens)
        frags = res.data["fragments"] if res.ok else []
        return ToolResult.success(data={
            "brief": "\n\n".join(f["text"] for f in frags),
            "sources": [f["slug"] for f in frags],
            "total_tokens": sum(f["tokens"] for f in frags)})

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
