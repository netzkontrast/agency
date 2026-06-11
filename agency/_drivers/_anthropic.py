"""Spec 147 — the canonical AnthropicDriver boundary (Slice 1: inference surface).

ONE typed surface every verb that needs LLM inference (thinking, prompt-composition,
the dogfood-classifier, scene-writer, …) wires through, so the engine stops doing it
"lossy-in-chat" (Spec 110) or via one-off shims (Spec 026's pending llm_select). The
defaults come from the ``claude-api`` skill: ``model="claude-opus-4-8"``, adaptive
thinking, ``output_config.format`` for structured outputs, and typed ``stop_reason`` /
error handling so a refusal or rate-limit never crashes the engine.

Mirrors the Spec 092 G3 ``LLMClient`` pattern — lazy, key-gated, degrades cleanly, and
reports a ``backend()`` for ``agency_doctor`` (never the key). The ``anthropic`` SDK is
imported lazily inside ``_sdk()`` so this module imports with no extra installed; tests
inject a fake client.

**Slice 1** ships the inference surface (``complete`` / ``count_tokens`` / typed errors
/ readiness). The Managed-Agents bridge (``dispatch_session``) is **Slice 2** — it raises
a clear deferred error today. See ``Plan/147-anthropic-driver-boundary/spec.md``.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

_DEFAULT_MODEL = "claude-opus-4-8"
# Above this, the claude-api skill requires streaming (idle connections drop). Slice 1
# `complete` is non-streaming; callers wanting larger output use a future `stream()`.
_NONSTREAM_MAX_TOKENS = 16000


class DriverError(Exception):
    """Typed driver failure. ``code`` is one of the class constants below; ``detail``
    carries structured context (e.g. a refusal ``category``). The wrapping verb maps
    this to a ToolResult failure (Spec 059/151 Codes) — the engine never crashes."""

    REFUSAL = "refusal"
    RATE_LIMITED = "rate_limited"
    OVERLOADED = "overloaded"
    BAD_REQUEST = "bad_request"
    TIMEOUT = "timeout"
    AUTH_FAILED = "auth_failed"
    NETWORK = "network"

    def __init__(self, code: str, message: str = "", detail: dict | None = None):
        self.code = code
        self.detail = detail or {}
        super().__init__(f"{code}: {message}" if message else code)


@dataclass
class Completion:
    """The success result of ``complete``. ``parsed`` is populated only when an
    ``output_schema`` was supplied and the text parsed as JSON."""

    text: str
    stop_reason: str
    usage: dict = field(default_factory=dict)
    model: str = _DEFAULT_MODEL
    request_id: str = ""
    parsed: dict | None = None


# anthropic SDK exception class-names → typed codes (matched by name so the SDK need
# not be installed for the mapping to compile).
_EXC_NAME_MAP = {
    "RateLimitError": DriverError.RATE_LIMITED,
    "OverloadedError": DriverError.OVERLOADED,
    "BadRequestError": DriverError.BAD_REQUEST,
    "AuthenticationError": DriverError.AUTH_FAILED,
    "PermissionDeniedError": DriverError.AUTH_FAILED,
    "APITimeoutError": DriverError.TIMEOUT,
    "APIConnectionError": DriverError.NETWORK,
}
_STATUS_MAP = {
    400: DriverError.BAD_REQUEST, 401: DriverError.AUTH_FAILED,
    403: DriverError.AUTH_FAILED, 408: DriverError.TIMEOUT,
    429: DriverError.RATE_LIMITED, 529: DriverError.OVERLOADED,
}


class AnthropicDriver:
    def __init__(self, model: str | None = None, client=None):
        self.model = model or os.environ.get("AGENCY_ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self._client = client                          # injectable for tests

    # ── reporting (never the key) ────────────────────────────────────────────
    def backend(self) -> str:
        """The live backend name ``agency_doctor`` reports — ``anthropic`` when a key
        (or an injected client) is present, else ``none``."""
        if self._client is not None or os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        return "none"

    def readiness(self) -> dict:
        """Structured readiness for ``agency_doctor`` (Spec 170). Slice 1:
        Managed-Agents is not yet capable."""
        return {
            "api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "model_id_resolved": self.model,
            "managed_agents_capable": False,           # Slice 2
        }

    # ── inference surface ────────────────────────────────────────────────────
    def complete(self, messages, system: str = "", output_schema: dict | None = None,
                 effort: str = "high", model: str | None = None,
                 max_tokens: int = _NONSTREAM_MAX_TOKENS) -> Completion:
        """One non-streaming completion with the claude-api defaults (adaptive
        thinking + effort). Returns a typed ``Completion``; raises ``DriverError`` on
        refusal / rate-limit / overload / auth / network. ``output_schema`` adds
        ``output_config.format`` (structured outputs) and parses the JSON reply."""
        if max_tokens > _NONSTREAM_MAX_TOKENS:
            raise DriverError(
                DriverError.BAD_REQUEST,
                f"max_tokens={max_tokens} > {_NONSTREAM_MAX_TOKENS}; use stream() "
                "(claude-api skill: non-streaming risks idle-connection timeout)")
        client = self._sdk()
        output_config: dict = {"effort": effort}
        if output_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": output_schema}
        params: dict = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "thinking": {"type": "adaptive"},
            "output_config": output_config,
        }
        if system:
            params["system"] = system
        try:
            resp = client.messages.create(**params)
        except DriverError:
            raise
        except Exception as exc:                       # SDK / network failure
            raise self._classify(exc) from exc
        return self._to_completion(resp, output_schema)

    def count_tokens(self, messages, model: str | None = None) -> int:
        """Authoritative token count for the model (claude-api skill: never tiktoken
        for Claude — it undercounts by ~15-20%). Returns ``input_tokens``."""
        client = self._sdk()
        try:
            resp = client.messages.count_tokens(model=model or self.model,
                                                messages=messages)
        except DriverError:
            raise
        except Exception as exc:
            raise self._classify(exc) from exc
        return int(getattr(resp, "input_tokens", 0))

    def dispatch_session(self, agent_id: str, env_id: str, kickoff: str):
        """Managed-Agents bridge — **Slice 2**. References a pre-created Agent
        (create-once doctrine) and streams events back as MonitorEvents (Spec 021).
        Deferred today; see ``Plan/147-anthropic-driver-boundary/spec.md``."""
        raise DriverError(
            DriverError.BAD_REQUEST,
            "Managed-Agents bridge is Slice 2 — not yet implemented (Spec 147)")

    # ── internals ────────────────────────────────────────────────────────────
    def _sdk(self):
        if self._client is not None:
            return self._client
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise DriverError(
                DriverError.AUTH_FAILED,
                "AnthropicDriver needs ANTHROPIC_API_KEY (or an injected client) — "
                "install the [anthropic] extra + set the key")
        try:
            import anthropic                           # lazy; pragma: no cover - needs SDK
        except ImportError as exc:                     # pragma: no cover - needs SDK
            raise DriverError(
                DriverError.BAD_REQUEST,
                "the `anthropic` SDK is not installed — `pip install -e .[anthropic]`"
            ) from exc
        self._client = anthropic.Anthropic()           # pragma: no cover - needs SDK
        return self._client

    def _to_completion(self, resp, output_schema) -> Completion:
        stop = getattr(resp, "stop_reason", "end_turn")
        if stop == "refusal":
            details = getattr(resp, "stop_details", None)
            category = getattr(details, "category", None) if details else None
            raise DriverError(DriverError.REFUSAL, "model refused for safety",
                              {"category": category})
        text = "".join(
            getattr(b, "text", "") for b in getattr(resp, "content", [])
            if getattr(b, "type", None) == "text")
        parsed = None
        if output_schema is not None and text:
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = None
        return Completion(
            text=text, stop_reason=stop, usage=self._usage(resp),
            model=getattr(resp, "model", self.model),
            request_id=getattr(resp, "_request_id", "") or "", parsed=parsed)

    @staticmethod
    def _usage(resp) -> dict:
        u = getattr(resp, "usage", None)
        if u is None:
            return {}
        return {k: getattr(u, k) for k in (
            "input_tokens", "output_tokens",
            "cache_read_input_tokens", "cache_creation_input_tokens")
            if getattr(u, k, None) is not None}

    @staticmethod
    def _classify(exc: Exception) -> DriverError:
        code = _EXC_NAME_MAP.get(type(exc).__name__)
        if code is None:
            status = getattr(exc, "status_code", None)
            if status is not None:
                code = _STATUS_MAP.get(int(status), DriverError.NETWORK)
        return DriverError(code or DriverError.NETWORK, str(exc))
