"""Spec 092 G3 — the LLM-decider boundary (an ``llm`` Driver on the Spec-002 registry).

A constrained classifier the engine uses where a small judgement is needed without an
autonomous agent — today `intent.suggests`'s ``llm_select`` Matcher; later the agentic
pressure-test deciders (Spec 011). The single typed method is
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
``meta-llama/llama-3.3-70b-instruct:free``). The request pins
``temperature: 0`` and a strict ``response_format: json_schema`` so the reply is forced to
``{"choice": <one option>, "confidence": <float>}``; parsing is tolerant (fence-strip +
brace-extract) so a model that ignores strict schema still works.

API key and any other secrets are loaded from a ``.env`` file by the entry-point modules
(``__main__.py`` / ``cli.py``) via ``python-dotenv`` before this module is used.
"""
from __future__ import annotations

import json
import os
import re

_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
_FREE_SUFFIX = ":free"
_URL = "https://openrouter.ai/api/v1/chat/completions"
_SYSTEM = ('You are a constrained decider. Choose EXACTLY ONE option and a confidence in '
           '[0,1]. Reply ONLY with JSON: {"choice": "<one option>", "confidence": <float>}.')


class LLMClient:
    def __init__(self, model: str | None = None):
        resolved = model or os.environ.get("AGENCY_LLM_MODEL", _DEFAULT_MODEL)
        if not resolved.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"AGENCY_LLM_MODEL must be a free OpenRouter model "
                f"(model ID must end with '{_FREE_SUFFIX}', got {resolved!r}). "
                f"Browse free models at https://openrouter.ai/models?order=pricing-asc "
                f"or leave AGENCY_LLM_MODEL unset to use the default ({_DEFAULT_MODEL})."
            )
        self.model = resolved

    def backend(self) -> str:
        """The live backend name (what ``agency_doctor`` reports) — never the key."""
        return "openrouter" if os.environ.get("OPENROUTER_API_KEY") else "none"

    def decide(self, prompt: str, options: list[str], model: str | None = None) -> dict:
        """Choose EXACTLY ONE of ``options``. Returns ``{choice, confidence}``; tolerant
        of a malformed reply (degrades to a mentioned option, else the first / conf 0)."""
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "LLM driver needs OPENROUTER_API_KEY — get one at https://openrouter.ai/keys "
                "(set AGENCY_LLM_MODEL to choose a free model; default "
                f"{_DEFAULT_MODEL}).")
        use_model = model or self.model
        if not use_model.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"Per-call model override must also be a free OpenRouter model "
                f"(must end with '{_FREE_SUFFIX}', got {use_model!r})."
            )
        return self._parse(self._chat(key, prompt, options, use_model), options)

    def _chat(self, key, prompt, options, model):            # pragma: no cover - network
        import httpx
        body = {
            "model": model, "temperature": 0, "max_tokens": 64,
            "messages": [{"role": "system", "content": _SYSTEM},
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
