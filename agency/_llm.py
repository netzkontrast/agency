"""Spec 092 G3 / Spec 331 — the LLM-decider boundary (an ``llm`` Driver on the
Spec-002 registry).

A constrained classifier the engine uses where a small judgement is needed without an
autonomous agent — today `intent.suggests`'s ``llm_select`` Matcher and
`delegate.dispatch_decision`'s optional S12 LLM tie-breaker. The single typed method is
``decide(prompt, options) -> {choice, confidence}``.

**Backend: OpenRouter** (https://openrouter.ai) — OpenAI-wire-compatible, reached over
``httpx`` (a core dependency), so this needs **no extra SDK**. It is lazy: the default
never touches the network until a verb asks for a decision, and ``decide`` raises a clear
error when ``OPENROUTER_API_KEY`` is unset (the ``llm_select`` Matcher is then skipped —
pattern/verb_code Matchers are unaffected).

Only **free** OpenRouter models are used.  Free models carry a ``:free`` suffix in their
model ID (e.g. ``meta-llama/llama-3.3-70b-instruct:free``).  The engine enforces this
at construction time so a misconfigured ``AGENCY_LLM_MODEL`` never silently incurs cost.

The model is ``AGENCY_LLM_MODEL`` (default
``meta-llama/llama-3.3-70b-instruct:free``).  Set ``AGENCY_LLM_MODEL=auto`` to
dynamically query the OpenRouter ``/api/v1/models`` endpoint and pick the most
preferred available free model (see ``_MODEL_PREFERENCE`` ranking below). The request
pins ``temperature: 0`` and a strict ``response_format: json_schema`` so the reply is
forced to ``{"choice": <one option>, "confidence": <float>}``; parsing is tolerant
(fence-strip + brace-extract) so a model that ignores strict schema still works.

API key and any other secrets are loaded from a ``.env`` file by the entry-point modules
(``__main__.py`` / ``cli.py``) via ``python-dotenv`` before this module is used.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
_FREE_SUFFIX = ":free"
_MODELS_URL = "https://openrouter.ai/api/v1/models"


# ── Spec 338 — use-case-tagged model registry ────────────────────────────────
@dataclass(frozen=True)
class ModelProfile:
    """One free OpenRouter model + the use-cases it serves. ``flags`` (e.g.
    ``context_length``) are HYDRATED from live OpenRouter model info, never
    hand-frozen (rule 8); the built-in registry carries only id/use_cases/
    priority. ``general`` is the catch-all every model declares."""
    id: str
    use_cases: tuple[str, ...]
    priority: int = 100
    flags: dict = field(default_factory=dict)


# Built-in default registry — priority-ordered (lower wins). Overridable by a
# ``models:`` block in ``.agency/config.yaml`` (load_registry). The flat
# `_MODEL_PREFERENCE` used by `resolve_model()` is DERIVED from this (single
# source — no drift between the two).
_DEFAULT_REGISTRY: tuple[ModelProfile, ...] = (
    ModelProfile("deepseek/deepseek-r1:free", ("reasoning", "decision", "general"), 10),
    ModelProfile("deepseek/deepseek-chat-v3-0324:free", ("decision", "general"), 20),
    ModelProfile("qwen/qwen3-coder:free", ("code", "general"), 25),
    ModelProfile("meta-llama/llama-3.3-70b-instruct:free", ("prose", "general"), 30),
    ModelProfile("google/gemma-3-27b-it:free", ("prose", "general"), 40),
    ModelProfile("mistralai/mistral-7b-instruct:free", ("general",), 50),
)

# Preference-ranked free-model list for `resolve_model()` (AGENCY_LLM_MODEL=auto)
# — DERIVED from the registry so there is one source of truth.
_MODEL_PREFERENCE: list[str] = [p.id for p in sorted(_DEFAULT_REGISTRY,
                                                     key=lambda p: p.priority)]


def default_registry() -> tuple[ModelProfile, ...]:
    """The built-in registry (read-only)."""
    return _DEFAULT_REGISTRY


def load_registry(config: dict | None) -> tuple[ModelProfile, ...]:
    """Build a registry from a ``{"models": [{id, use_cases, priority, flags}]}``
    config block; an absent / malformed block falls back to the built-in default
    (fail-closed, Spec 058). Each model defaults to the ``general`` use-case."""
    models = (config or {}).get("models")
    if not isinstance(models, list):
        return _DEFAULT_REGISTRY
    out: list[ModelProfile] = []
    for m in models:
        if not isinstance(m, dict) or not m.get("id"):
            continue
        out.append(ModelProfile(
            id=str(m["id"]),
            use_cases=tuple(m.get("use_cases") or ("general",)),
            priority=int(m.get("priority", 100)),
            flags=dict(m.get("flags") or {}),
        ))
    return tuple(out) or _DEFAULT_REGISTRY


def select_model(use_case: str, *, registry: tuple[ModelProfile, ...] | None = None,
                 live_ids: set[str] | None = None, model: str | None = None,
                 default: str = _DEFAULT_MODEL) -> str:
    """Pick the highest-priority free model serving ``use_case``, restricted to
    ``live_ids`` when supplied. Resolution: explicit ``model`` (must be ``:free``)
    → use-case pick → ``general`` pick → ``default``. Never raises except on a
    non-free explicit override (cost-safety)."""
    if model:
        if not model.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"explicit model must be a free OpenRouter model "
                f"(end with '{_FREE_SUFFIX}', got {model!r})")
        return model
    reg = registry if registry is not None else _DEFAULT_REGISTRY

    def _first(cands: list[ModelProfile]) -> str | None:
        for p in sorted(cands, key=lambda p: p.priority):
            if live_ids is None or p.id in live_ids:
                return p.id
        return None

    return (_first([p for p in reg if use_case in p.use_cases])
            or _first([p for p in reg if "general" in p.use_cases])
            or default)


@dataclass(frozen=True)
class GenerationResult:
    """Spec 338 — the typed plain-text generation return."""
    text: str
    model: str
    backend: str            # "openrouter"
    finish_reason: str


_URL = "https://openrouter.ai/api/v1/chat/completions"
_SYSTEM = ('You are a constrained decider. Choose EXACTLY ONE option and a confidence in '
           '[0,1]. Reply ONLY with JSON: {"choice": "<one option>", "confidence": <float>}.')


class LLMClient:
    def __init__(self, model: str | None = None, *, use_case: str = "general",
                 require: str | None = None,
                 registry: tuple[ModelProfile, ...] | None = None,
                 client=None):
        raw = model or os.environ.get("AGENCY_LLM_MODEL") or _DEFAULT_MODEL
        if raw == "auto":
            resolved = self.resolve_model()
        else:
            resolved = raw
        if not resolved.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"AGENCY_LLM_MODEL must be a free OpenRouter model "
                f"(model ID must end with '{_FREE_SUFFIX}', got {resolved!r}). "
                f"Set AGENCY_LLM_MODEL=auto to auto-discover, browse free models at "
                f"https://openrouter.ai/models?order=pricing-asc "
                f"or leave AGENCY_LLM_MODEL unset to use the default ({_DEFAULT_MODEL})."
            )
        self.model = resolved
        # Spec 338 — driver flags + use-case registry.
        self.use_case = use_case
        self.require = require
        self._registry = registry if registry is not None else _DEFAULT_REGISTRY
        self._client = client                # injectable OpenRouter SDK (tests)
        self._model_pinned = model is not None

    def generate(self, prompt: str, *, use_case: str | None = None,
                 system: str | None = None, max_tokens: int = 1024,
                 model: str | None = None) -> GenerationResult:
        """Spec 338 — plain-text free generation. The model is selected by
        ``use_case`` from the registry (explicit ``model`` wins; must be
        ``:free``). Returns a typed :class:`GenerationResult`."""
        uc = use_case or self.use_case
        chosen = select_model(
            uc, registry=self._registry,
            model=model or (self.model if self._model_pinned else None))
        text, finish = self._send(prompt, chosen, system, max_tokens)
        return GenerationResult(text=text, model=chosen, backend="openrouter",
                                finish_reason=finish)

    def _send(self, prompt: str, model: str, system: str | None,
              max_tokens: int) -> tuple[str, str]:
        client = self._client if self._client is not None else self._sdk()
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.send(model=model, messages=messages,
                                max_tokens=max_tokens)
        choice = resp.choices[0]
        return (getattr(choice.message, "content", "") or "",
                getattr(choice, "finish_reason", "") or "")

    def _sdk(self):                                   # pragma: no cover - network
        import openrouter
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY required for generation — get one at "
                "https://openrouter.ai/keys")
        return openrouter.OpenRouter(
            api_key=key, http_referer="https://github.com/netzkontrast/agency",
            x_open_router_title="agency")

    def backend(self) -> str:
        """The live backend name (what ``agency_doctor`` reports) — never the key."""
        return "openrouter" if os.environ.get("OPENROUTER_API_KEY") else "none"

    # ------------------------------------------------------------------
    # Free model discovery (Spec 331)
    # ------------------------------------------------------------------

    @classmethod
    def list_free_models(cls, api_key: str | None = None) -> list[dict]:
        """Query ``/api/v1/models`` and return models available at zero cost.

        A model is considered free when its ID ends with ``:free`` OR when
        both ``pricing.prompt`` and ``pricing.completion`` are ``"0"``.
        Returns a list of ``{id, name, context_length}`` dicts, ordered as
        they appear in the OpenRouter catalogue (most recently added first).
        An API key is optional — the public endpoint is accessible without
        one, though authenticated requests may see more models.
        """
        import httpx
        key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        headers = {
            "HTTP-Referer": "https://github.com/netzkontrast/agency",
            "X-Title": "agency",
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"
        resp = httpx.get(_MODELS_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        models: list[dict] = []
        for m in resp.json().get("data", []):
            mid = m.get("id", "")
            # Strict: only include models whose IDs end with :free so they
            # pass the decide() enforcement without special-casing.
            if mid.endswith(_FREE_SUFFIX):
                models.append({
                    "id": mid,
                    "name": m.get("name", mid),
                    "context_length": m.get("context_length", 0),
                })
        return models

    @classmethod
    def resolve_model(cls, api_key: str | None = None) -> str:
        """Pick the most-preferred available free model from the live catalogue.

        Walks ``_MODEL_PREFERENCE`` in order and returns the first model whose
        ID appears in the OpenRouter free-model list.  Falls back to
        ``_DEFAULT_MODEL`` when the API is unreachable or no preference matches.
        """
        try:
            live_ids = {m["id"] for m in cls.list_free_models(api_key=api_key)}
            for preferred in _MODEL_PREFERENCE:
                if preferred in live_ids:
                    return preferred
        except Exception:
            pass
        return _DEFAULT_MODEL

    # ------------------------------------------------------------------
    # Core decide() interface
    # ------------------------------------------------------------------

    def decide(self, prompt: str, options: list[str], model: str | None = None,
               system: str | None = None) -> dict:
        """Choose EXACTLY ONE of ``options``. Returns ``{choice, confidence}``; tolerant
        of a malformed reply (degrades to a mentioned option, else the first / conf 0).

        ``system`` overrides the default ``_SYSTEM`` prompt for this call only — pass a
        domain-specific system prompt to improve routing quality for specialised decisions
        (e.g. the S12 dispatch tie-breaker in ``delegate.dispatch_decision``).
        """
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "LLM driver needs OPENROUTER_API_KEY — get one at https://openrouter.ai/keys "
                "(set AGENCY_LLM_MODEL to choose a free model or 'auto' to discover; "
                f"default {_DEFAULT_MODEL}).")
        use_model = model or self.model
        if not use_model.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"Per-call model override must also be a free OpenRouter model "
                f"(must end with '{_FREE_SUFFIX}', got {use_model!r})."
            )
        return self._parse(self._chat(key, prompt, options, use_model, system=system), options)

    def _chat(self, key, prompt, options, model,              # pragma: no cover - network
              system: str | None = None):
        import httpx
        body = {
            "model": model, "temperature": 0, "max_tokens": 64,
            "messages": [{"role": "system", "content": system or _SYSTEM},
                         {"role": "user", "content": f"{prompt}\n\nOptions: {options}"}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "decision", "strict": True, "schema": {
                    "type": "object", "additionalProperties": False,
                    "required": ["choice", "confidence"],
                    "properties": {"choice": {"type": "string", "enum": list(options)},
                                   "confidence": {"type": "number"}}}}},
        }
        resp = httpx.post(
            _URL, timeout=30, json=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/netzkontrast/agency",
                     "X-Title": "agency"})
        resp.raise_for_status()                              # 401/402/429/4xx/5xx
        return resp.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _parse(text: str, options: list[str]) -> dict:
        stripped = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(),
                          flags=re.MULTILINE).strip()
        data: dict = {}
        try:
            data = json.loads(stripped)
        except Exception:
            match = re.search(r"\{.*\}", stripped, re.DOTALL)   # first {...} block
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = {}
        choice, conf = data.get("choice"), data.get("confidence", 0.0)
        if choice in options:
            return {"choice": choice, "confidence": float(conf)}
        low = (text or "").lower()                              # tolerant: option in raw text
        for opt in options:
            if opt.lower() in low:
                return {"choice": opt, "confidence": float(conf) if conf else 0.5}
        return {"choice": options[0] if options else "", "confidence": 0.0}


# ── Spec 338 — the single plain-text generator-selection rule ─────────────────
def _dep_missing(msg: str) -> RuntimeError:
    from .toolresult import Codes
    e = RuntimeError(f"{Codes.DEPENDENCY_MISSING}: {msg}")
    e.code = Codes.DEPENDENCY_MISSING                           # typed (Spec 151)
    return e


def select_text_generator(drivers, *, env=None, require: str | None = None):
    """The SOLE provider-selection rule for plain-text generation (Spec 338).

    Returns ``(name, driver)``: ``"llm"`` (OpenRouter) when ``OPENROUTER_API_KEY``
    is set — the owner directive wins even when ``ANTHROPIC_API_KEY`` is also set;
    ``"anthropic"`` when ``require == "anthropic"`` (the explicit quality/feature
    escape), the ``AGENCY_GENERATE=anthropic`` override is active, or only the
    Anthropic key is present; else a typed ``Codes.DEPENDENCY_MISSING``. NEVER a
    silent paid fallback — a free failure is the caller's cue to re-invoke with
    ``require="anthropic"`` (the barbell)."""
    env = env if env is not None else os.environ
    has_or = bool(env.get("OPENROUTER_API_KEY"))
    has_an = bool(env.get("ANTHROPIC_API_KEY"))
    force_an = (require == "anthropic"
                or env.get("AGENCY_GENERATE", "").strip().lower() == "anthropic")
    if force_an:
        if not has_an:
            raise _dep_missing(
                "Anthropic generation requested but ANTHROPIC_API_KEY is unset")
        return ("anthropic", drivers.get("anthropic"))
    if has_or:
        return ("llm", drivers.get("llm"))
    if has_an:
        return ("anthropic", drivers.get("anthropic"))
    raise _dep_missing(
        "no generation key — set OPENROUTER_API_KEY (free, preferred) "
        "or ANTHROPIC_API_KEY")


def _openrouter_models() -> dict:                     # pragma: no cover - network
    """Live free-model catalogue from the OpenRouter SDK → ``{id: flags}``.
    Hydrates the registry's ``flags`` (context_length, supported_parameters)
    from live model info — derived, never hand-frozen (rule 8). Best-effort:
    a fetch failure leaves the built-in registry unflagged."""
    import openrouter
    key = os.environ.get("OPENROUTER_API_KEY")
    sdk = openrouter.OpenRouter(
        api_key=key or None,
        http_referer="https://github.com/netzkontrast/agency",
        x_open_router_title="agency")
    out: dict = {}
    for m in (sdk.models.list(max_price=0).data or []):
        mid = getattr(m, "id", "")
        if mid.endswith(_FREE_SUFFIX):
            out[mid] = {
                "context_length": getattr(m, "context_length", 0),
                "supported_parameters": list(
                    getattr(m, "supported_parameters", []) or []),
            }
    return out
