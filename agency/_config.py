"""Unified ``.agency/config.yaml`` — Spec 328 Slice 1 (resolver + registry).

A single home for all agency config. A key resolves **env var → config.yaml →
built-in default** (the same precedence shape as ``_db_path.resolve_db_path``).
Capabilities ``register_config_section`` their own keys, so the live set is the
union of all registered config — no frozen audit (Goal 4). ``config_set``
persists a value to the file.

Slice 1 is the resolver/registry/precedence. The annotated, comment-preserving
scaffold generator + doctor validation are later slices.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:  # frugal: yaml is a core dep (Spec 328); guard so import never hard-crashes.
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared dependency
    yaml = None


@dataclass(frozen=True)
class ConfigKey:
    """One config knob: its name, env-var alias, default, doc, and optional enum."""
    name: str
    env: str = ""
    default: Any = None
    doc: str = ""
    enum: tuple | None = None


_REGISTRY: dict[str, list[ConfigKey]] = {}


def register_config_section(name: str, keys: list[ConfigKey]) -> None:
    """Register (or replace) a config section. Core + each capability call this."""
    _REGISTRY[name] = list(keys)


def registered_keys() -> list[str]:
    """Every registered key as ``section.name`` — the union = 'all agency config'."""
    return [f"{section}.{k.name}" for section, keys in _REGISTRY.items() for k in keys]


def _lookup(dotted: str) -> tuple[str, ConfigKey] | None:
    section, _, name = dotted.partition(".")
    for k in _REGISTRY.get(section, []):
        if k.name == name:
            return section, k
    return None


def _resolve_config_path() -> str:
    """``AGENCY_CONFIG`` env → ``$CWD/.agency/config.yaml`` (mirrors _db_path)."""
    return os.environ.get("AGENCY_CONFIG") or os.path.join(
        os.getcwd(), ".agency", "config.yaml")


def _read(path: str) -> dict:
    if not path or yaml is None or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):  # corrupt/unreadable → fall through to defaults
        return {}


def config_resolve(dotted: str, *, path: str | None = None) -> dict:
    """Resolve a registered key to ``{"value", "source"}`` where source is one of
    ``env`` / ``file`` / ``default`` (so doctor can explain *why* a value is what
    it is). Raises ``KeyError`` for an unregistered key."""
    found = _lookup(dotted)
    if found is None:
        raise KeyError(f"unregistered config key: {dotted!r}")
    section, key = found
    if key.env and os.environ.get(key.env) is not None:
        return {"value": os.environ[key.env], "source": "env"}
    data = _read(path or _resolve_config_path())
    sec = data.get(section)
    if isinstance(sec, dict) and key.name in sec:
        return {"value": sec[key.name], "source": "file"}
    return {"value": key.default, "source": "default"}


def config_get(dotted: str, *, path: str | None = None) -> Any:
    """The resolved value (env > file > default)."""
    return config_resolve(dotted, path=path)["value"]


def config_set(dotted: str, value: Any, *, path: str | None = None) -> None:
    """Persist ``value`` for ``dotted`` to the config file (durable across
    processes). Slice 2 adds comment-preserving round-trip + scaffold rendering."""
    if yaml is None:  # pragma: no cover - yaml is a declared dependency
        raise RuntimeError("PyYAML is required for config_set")
    section, _, name = dotted.partition(".")
    target = path or _resolve_config_path()
    data = _read(target)
    data.setdefault(section, {})[name] = value
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


# ── core section (always registered) ──────────────────────────────────────────
register_config_section("core", [
    ConfigKey("db_path", "AGENCY_DB", ".agency/session.db",
              "central bi-temporal graph DB (Spec 020)"),
    ConfigKey("embedder", "AGENCY_EMBEDDER", "tfidf",
              "recall embedder backend", enum=("tfidf", "bge")),
    ConfigKey("token_backend", "AGENCY_TOKEN_BACKEND", "tiktoken",
              "token-count backend (anthropic|tiktoken|proxy)"),
])
