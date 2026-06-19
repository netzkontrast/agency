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

from agency._capture import keep_full
from agency._overflow import budget_take
from agency.capability import verb
from agency.toolresult import ToolResult, Codes

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
        candidates = [
            {"slug": e["slug"], "name": e["name"],
             "complexity_tier": e["complexity_tier"],
             "tokens": _approx_tokens(e.get("template", ""))}
            for e in _user_frameworks()
            if e.get("intent_category") == intent
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
    def route_framework(self, draft: str, intent_hint: str = "",
                        top: int = 1) -> ToolResult:
        """Route a free-text ``draft`` to the ONE right framework (effect).

        Two-level routing (Spec 305): (1) detect the ``intent_category`` by
        matching ``draft`` against the vendored category signals + each
        framework's ``discriminators`` (DERIVED from the library, not a
        hardcoded keyword table); (2) within that category, rank candidates by
        discriminator + token overlap. **Token-efficient — returns ONE
        framework plus ≤ 1 alt, never the whole library.** Records a
        ``Recommendation`` node SERVING the intent (298 parity).

        Trigger vocabulary — which words route to which intent (a SUMMARY so you
        can phrase a draft or pick an ``intent_hint``; the live, authoritative
        signals live in ``data/frameworks.json`` → ``intent_signals`` +
        per-framework ``discriminators``):

        - **recover**  ← "reverse engineer", "recover prompt", "what prompt produced"
        - **clarify**  ← "not sure what I need", "help me figure out", "interview me"
        - **create**   ← "write", "create", "draft", "generate", "build", "design"
        - **transform**← "rewrite", "refactor", "improve", "summarize", "convert"
        - **reason**   ← "calculate", "solve", "analyze", "compare options", "should I"
        - **critique** ← "review", "stress test", "find flaws", "risks", "what could go wrong"
        - **agentic**  ← "use tools", "search and", "run code", "query a database"

        When a draft is ambiguous or the words straddle two intents, pass
        ``intent_hint`` to pin the category; the discriminators then pick the
        framework within it.

        Inputs: draft (str — the rough prompt/goal), intent_hint (str —
                override category detection), top (int — how many ALTERNATES to
                return beyond the best; ``top=1`` ⇒ best + ≤ 1 alt).
        Returns: ``{intent, framework: {slug, name, complexity_tier},
                 alts: [...], rationale, scaffold}``.
        chain_next: ``prompt.render(framework_slug, fields)`` to fill it.
        """
        store = _load_frameworks()
        intent = (intent_hint if intent_hint in _user_intents()
                  else _detect_category(draft))
        ranked = _rank_in_category(draft, intent)
        if not ranked:
            return ToolResult.success(data={
                "intent": intent, "framework": None, "alts": [],
                "rationale": f"no framework matched intent '{intent}'",
                "scaffold": "",
            })
        best = ranked[0]
        entry = store[best["slug"]]
        alts = [{"slug": r["slug"], "name": store[r["slug"]]["name"]}
                for r in ranked[1:max(1, top) + 1]][:max(0, top)]
        self.ctx.record_and_serve("Recommendation", {
            "request": keep_full(draft, label="prompt request"), "capability": "prompt",
        })
        rationale = (f"intent '{intent}' → {entry['name']}: "
                     f"{entry.get('when_to_use', '') or entry['full_name']}")[:200]
        return ToolResult.success(data={
            "intent": intent,
            "framework": {"slug": entry["slug"], "name": entry["name"],
                          "complexity_tier": entry["complexity_tier"]},
            "alts": alts,
            "rationale": rationale,
            "scaffold": entry.get("template", ""),
        })

    @verb(role="act")
    def render(self, framework_slug: str, fields: dict,
               max_tokens: int = 2000) -> ToolResult:
        """Fill a framework's template with ``fields`` → a PromptInstance (act).

        Renders one ``COMPONENT: value`` line per framework component (the
        slots derived from the template), filling from ``fields`` (matched by
        component name, case-insensitive) and marking unfilled slots ``[TODO]``.
        Honors ``max_tokens`` (refuses an over-budget body — the ``engineer``
        gate). Records a ``PromptInstance`` + a ``FILLS_FRAMEWORK`` edge to a
        lazily-recorded ``PromptFramework`` node (304 — nodes appear only on
        use; declare-an-edge ⇒ traverse-it).

        Inputs: framework_slug (str), fields (dict — component→value),
                max_tokens (int).
        Returns: ``{result, artefact: {kind, framework_slug, rendered_body,
                 instance_id, approx_tokens}}`` OR ``{error}``.
        chain_next: ``prompt.evaluate(body, target='user-prompt')`` to score it.
        """
        entry = _load_frameworks().get(framework_slug)
        if entry is None:
            return ToolResult.success(data={
                "framework_slug": framework_slug, "error": "NO_FRAMEWORK"})
        body = _fill_template(entry, fields or {})
        tokens = _approx_tokens(body)
        if tokens > max_tokens:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"rendered prompt {tokens} tokens > budget {max_tokens}; "
                f"trim fields or raise max_tokens")
        fw_node = self._framework_node(entry)
        instance_id = self.ctx.record_and_serve("PromptInstance", {
            "builder_kind": f"framework:{framework_slug}", "rendered_body": body,
        })
        self.ctx.link(instance_id, fw_node, "FILLS_FRAMEWORK")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "prompt-instance",
                         "framework_slug": framework_slug,
                         "rendered_body": body,
                         "instance_id": instance_id,
                         "approx_tokens": tokens},
        })

    def _framework_node(self, entry: dict) -> str:
        """Lazily record (or find) the PromptFramework node for ``entry`` (Q1:
        nodes record only when a framework is actually used)."""
        existing = self.ctx.query_nodes("PromptFramework", {"slug": entry["slug"]})
        if existing:
            return existing[0]["id"]
        return self.ctx.record("PromptFramework", {
            "slug": entry["slug"], "name": entry["name"],
            "intent_category": entry["intent_category"],
            "complexity_tier": entry["complexity_tier"],
            "audience": entry.get("audience", "user"),
        })

    @verb(role="effect")
    def register_framework(self, slug: str, payload: dict,
                           overlay_path: str = "") -> ToolResult:
        """Write a custom framework to the project overlay (effect; extensible).

        Inputs: slug (str), payload (dict — at minimum ``template``; any of
                name/intent_category/complexity_tier/audience/components/
                when_to_use/discriminators override the vendored defaults).
                ``intent_category``/``complexity_tier``/``audience`` must be
                valid ontology enum values (validated HERE so a bad overlay
                fails fast, not later at ``render`` time when the
                ``PromptFramework`` node is recorded).
                overlay_path (str — defaults to the project overlay).
        Returns: ``{slug, name, intent_category, audience, overlay_path}`` OR
                 ``{slug, error: 'INVALID_ARGUMENT', invalid: {...}}`` when the
                 template is missing or an enum field is out of range.
        chain_next: ``prompt.framework(slug)`` to verify the round-trip.
        """
        if not isinstance(payload, dict) or not payload.get("template"):
            return ToolResult.success(data={
                "slug": slug, "error": "INVALID_ARGUMENT"})
        entry = _normalise_framework(slug, payload)
        invalid = _invalid_enum_fields(entry)
        if invalid:
            return ToolResult.success(data={
                "slug": slug, "error": "INVALID_ARGUMENT", "invalid": invalid})
        path = overlay_path or _DEFAULT_FW_OVERLAY_PATH
        _write_overlay_framework(path, slug, entry)
        _load_frameworks.cache_clear()
        return ToolResult.success(data={
            "slug": slug, "name": entry["name"],
            "intent_category": entry["intent_category"],
            "audience": entry["audience"],
            "overlay_path": path,
        })


# ─────────────────────────── routing + render (Spec 305) ────────────────────
# Reuses Spec 298 (recommend)'s tokenizer — the shared scoring substrate; this
# slice owns only the framework-specific candidate shaping (Open Q1).
from agency.capabilities.recommend._main import _tokens  # noqa: E402


def _user_intents() -> set[str]:
    """The intent categories that carry at least one user-facing framework."""
    return {e["intent_category"] for e in _user_frameworks()}


def _detect_category(draft: str) -> str:
    """First-level routing: score each intent category by substring hits of its
    vendored signals + member-framework discriminators against ``draft``.
    Falls back to ``create`` (the most common) when nothing matches — upstream
    parity."""
    low = draft.lower()
    signals = _load_intent_signals()
    # Aggregate per-category discriminators from the library (derived, rule 8);
    # the agg keys ARE the user intent categories.
    agg: dict[str, list[str]] = {}
    for e in _user_frameworks():
        agg.setdefault(e["intent_category"], []).extend(e.get("discriminators", []))
    scores = {
        cat: sum(1 for kw in list(signals.get(cat, [])) + discs
                 if kw and kw.lower() in low)
        for cat, discs in agg.items()
    }
    # Deterministic tie-break: highest score, ties broken by category name —
    # so the same draft always routes the same way regardless of dict order.
    best = max(scores, key=lambda c: (scores[c], c)) if scores else "create"
    return best if scores.get(best, 0) > 0 else "create"


def _rank_in_category(draft: str, intent: str) -> list[dict]:
    """Second-level routing: rank the category's user frameworks by
    discriminator substring hits + token overlap against ``draft``."""
    toks = _tokens(draft)
    low = draft.lower()
    ranked = []
    for e in _user_frameworks():
        if e["intent_category"] != intent:
            continue
        discs = e.get("discriminators", [])
        disc_hits = sum(1 for d in discs if d and d.lower() in low)
        overlap = len(toks & _tokens(" ".join(discs) + " " + e.get("when_to_use", "")))
        ranked.append({"slug": e["slug"], "score": disc_hits * 2 + overlap})
    # Stable order: score desc, then library order (slug) for determinism.
    ranked.sort(key=lambda r: (-r["score"], r["slug"]))
    return ranked


def _fill_template(entry: dict, fields: dict) -> str:
    """Fill a framework's component slots from ``fields`` (matched by component
    name, case-insensitive; first word as a fallback key). Unfilled → [TODO]."""
    lowered = {str(k).lower(): v for k, v in fields.items()}
    lines = []
    for comp in entry.get("components", []) or []:
        key = comp.lower()
        val = (lowered.get(key)
               or lowered.get(key.split()[0] if key.split() else key))
        lines.append(f"{comp.upper()}: {val}" if val else f"{comp.upper()}: [TODO]")
    if not lines:  # frameworks with no parsed components fall back to template
        return entry.get("template", "")
    return "\n\n".join(lines)


# ─────────────────────────── framework loader (Spec 304 / 129 parity) ───────


def _invalid_enum_fields(entry: dict) -> dict:
    """Enum fields of a framework entry whose value is out of ontology range —
    ``{field: bad_value}``. Empty dict ⇒ valid. Lets ``register_framework``
    reject a bad overlay at write time instead of crashing at ``render`` time
    (when the ``PromptFramework`` node would fail the enum check)."""
    from ..ontology import AUDIENCE, COMPLEXITY_TIER, INTENT_CATEGORY
    checks = {
        "intent_category": INTENT_CATEGORY,
        "complexity_tier": COMPLEXITY_TIER,
        "audience": AUDIENCE,
    }
    return {f: entry[f] for f, allowed in checks.items()
            if entry.get(f) not in allowed}


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
def _load_raw() -> dict:
    """Parse the vendored ``frameworks.json`` once (frameworks + intent_signals).
    Both the framework store and the intent-signal map derive from this single
    cached read, so the file is parsed once per session no matter who asks."""
    if _FRAMEWORKS_FILE.is_file():
        return json.loads(_FRAMEWORKS_FILE.read_text())
    return {}


@lru_cache(maxsize=1)
def _load_frameworks() -> dict:
    """Merged store keyed by slug: vendored bootstrap + overlay (overlay wins)."""
    base = {e["slug"]: e for e in _load_raw().get("frameworks") or []}
    base.update(_load_fw_overlay(_DEFAULT_FW_OVERLAY_PATH))
    return base


def _load_intent_signals() -> dict:
    """Category-level routing keywords vendored alongside the frameworks
    (Spec 305 first-level routing). Slug→keyword data, not a magic table."""
    return dict(_load_raw().get("intent_signals") or {})


def _user_frameworks() -> list[dict]:
    """The user-facing frameworks. The functional family (Spec 306,
    ``audience=functional``) is held out of routing HERE, in one place, so a new
    routing reader cannot forget the filter (altitude: the filter is
    infrastructure, not per-call policy)."""
    return [e for e in _load_frameworks().values()
            if e.get("audience", "user") == "user"]


def _read_mapping(text: str) -> dict:
    """Parse a YAML (preferred) or JSON mapping; ``{}`` on parse failure. Shared
    by both overlay read paths (load + write-merge)."""
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text) or {}
    except ImportError:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return {}
    return loaded if isinstance(loaded, dict) else {}


def _load_fw_overlay(path: str) -> dict:
    """Read the per-project overlay → ``{slug: full_entry}``. The overlay is a
    YAML/JSON mapping of slug → payload; each payload is normalised."""
    p = Path(os.path.expanduser(path))
    if not p.is_file():
        return {}
    return {str(slug): _normalise_framework(str(slug), payload)
            for slug, payload in _read_mapping(p.read_text()).items()
            if isinstance(payload, dict)}


def _write_overlay_framework(path: str, slug: str, entry: dict) -> None:
    """Append-or-replace a single framework in the overlay file."""
    p = Path(os.path.expanduser(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_mapping(p.read_text()) if p.is_file() else {}
    existing[slug] = entry
    try:
        import yaml  # type: ignore
        p.write_text(yaml.safe_dump(existing, allow_unicode=True, sort_keys=True))
    except ImportError:
        p.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
