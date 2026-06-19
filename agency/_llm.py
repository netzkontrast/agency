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

_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
_FREE_SUFFIX = ":free"
_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Preference-ranked list of known good free models used by `resolve_model()`
# when AGENCY_LLM_MODEL=auto.  The first model that appears in the live
# OpenRouter catalogue is selected; order reflects community usage prevalence
# (as of 2026-06, DeepSeek models dominate OpenRouter free-tier traffic).
_MODEL_PREFERENCE: list[str] = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-7b-instruct:free",
]
_URL = "https://openrouter.ai/api/v1/chat/completions"
_SYSTEM = ('You are a constrained decider. Choose EXACTLY ONE option and a confidence in '
           '[0,1]. Reply ONLY with JSON: {"choice": "<one option>", "confidence": <float>}.')


class LLMClient:
    def __init__(self, model: str | None = None):
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
