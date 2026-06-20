"""Unified ``.agency/config.yaml`` — Spec 334 Slice 1 (resolver + registry).

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

try:  # frugal: yaml is a core dep (Spec 334); guard so import never hard-crashes.
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared dependency
    yaml = None


@dataclass(frozen=True)
class ConfigKey:
    """One config knob: its name, env-var alias, default, doc, and optional enum.
    ``secret`` keys are env-only — the scaffold writes a ``${env:VAR}`` reference,
    never the literal value (doctor reports presence)."""
    name: str
    env: str = ""
    default: Any = None
    doc: str = ""
    enum: tuple | None = None
    secret: bool = False


_REGISTRY: dict[str, list[ConfigKey]] = {}


def register_config_section(name: str, keys: list[ConfigKey]) -> None:
    """Register (or replace) a config section. Core + each capability call this."""
    _REGISTRY[name] = list(keys)


def registered_keys() -> list[str]:
    """Every registered key as ``section.name`` — the union = 'all agency config'."""
    return [f"{section}.{k.name}" for section, keys in _REGISTRY.items() for k in keys]


def secret_keys() -> list[str]:
    """Every registered secret key as ``section.name`` (env-only — never written
    literal). Computed live from the registry, not a frozen list (Goal 4)."""
    return [f"{section}.{k.name}"
            for section, keys in _REGISTRY.items() for k in keys if k.secret]


def register_dataclass_section(name: str, dataclass_type, *, doc: str = "") -> list:
    """Register a config section DERIVED from a dataclass's fields + declared
    scalar defaults — single source, no duplicated literals (Goal 4 + rule 2).
    The open-set proof: a capability surfaces its config in the unified file by
    pointing at its own dataclass. Returns the registered keys."""
    import dataclasses
    label = doc or f"{name} capability default"
    keys = [ConfigKey(name=f.name, default=f.default, doc=f"{label} ({f.name})")
            for f in dataclasses.fields(dataclass_type)
            if f.default is not dataclasses.MISSING
            and isinstance(f.default, (str, int, float, bool))]
    if keys:
        register_config_section(name, keys)
    return keys


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


_READ_CACHE: dict[str, tuple[float, dict]] = {}


def _read(path: str) -> dict:
    """Parsed YAML config (``{}`` if missing/corrupt). Memoized per-process keyed
    on ``(path, mtime)`` — config changes ~never within a process, but
    ``config_get`` is on the per-verb hot path (Spec 332 M2) and the doctor reads
    once per key, so a `stat` + dict reuse replaces an open + YAML parse each call.
    Returned dict is READ-ONLY (writers `config_set` copy before mutating)."""
    if not path or yaml is None:
        return {}
    try:
        mtime = os.path.getmtime(path)
    except OSError:                       # missing/unreadable → defaults
        return {}
    cached = _READ_CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data = data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):     # corrupt → fall through to defaults
        return {}
    _READ_CACHE[path] = (mtime, data)
    return data


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
    # Secrets are env-only: the file holds a ${env:VAR} REFERENCE, never a value,
    # so a secret resolves env → default — never the file placeholder (which would
    # leak the literal "${env:...}" string to a caller). Non-secrets read the file.
    if not key.secret:
        data = _read(path or _resolve_config_path())
        sec = data.get(section)
        if isinstance(sec, dict) and key.name in sec:
            return {"value": sec[key.name], "source": "file"}
    return {"value": key.default, "source": "default"}


def config_get(dotted: str, *, path: str | None = None) -> Any:
    """The resolved value (env > file > default)."""
    return config_resolve(dotted, path=path)["value"]


# ── Spec 334 Slice 6 — capability read-path unification helpers ────────────────
# A capability with its OWN richer config (nested file + multi-path fallback —
# novel/music) reads the unified file as a live but lowest-priority source via
# these. Centralised here so every cap shares one semantics (no per-cap drift).
def unified_or(section: str, field_name: str, fallback: Any) -> Any:
    """The unified-config value for ``section.field_name`` — ranked BELOW a cap's
    own file and ABOVE its literal default. Best-effort: an unregistered key
    (e.g. a list field) or any error returns ``fallback`` so the capability never
    breaks. ``config_get`` already returns the registered default (== the cap's
    dataclass default) when the file omits the key, so an absent unified value
    resolves byte-identically to the literal fallback."""
    try:
        return config_get(f"{section}.{field_name}")
    except Exception:
        return fallback


def unified_signature() -> tuple:
    """``(path, mtime)`` of the unified config file — a token a capability folds
    into its own mtime-keyed load cache so editing ``.agency/config.yaml``
    invalidates the cached load."""
    path = _resolve_config_path()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0.0
    return (path, mtime)


def config_set(dotted: str, value: Any, *, path: str | None = None) -> None:
    """Persist ``value`` for ``dotted`` to the config file (durable across
    processes). Secret keys are env-only — never written literal (the scaffold/
    report enforce this; so must the persist path, Spec 334 Q2)."""
    if yaml is None:  # pragma: no cover - yaml is a declared dependency
        raise RuntimeError("PyYAML is required for config_set")
    found = _lookup(dotted)
    if found is not None and found[1].secret:
        raise ValueError(f"refusing to persist secret {dotted!r} — secrets are "
                         f"env-only ({found[1].env or 'env var'}), never written to file")
    section, _, name = dotted.partition(".")
    target = path or _resolve_config_path()
    import copy
    data = copy.deepcopy(_read(target))   # never mutate the read-cache's dict
    data.setdefault(section, {})[name] = value
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    _READ_CACHE.pop(target, None)              # write invalidates the read-cache


# ── Spec 334 Slice 2 — the annotated scaffold generator ───────────────────────
_HEADER = (
    "# .agency/config.yaml — all agency config (Spec 334). Safe to edit.\n"
    "# Precedence: environment variable > this file > built-in default.\n"
    "# Generated by setup / `agency install`; re-running repairs missing keys\n"
    "# non-destructively (your edits and comments are preserved).\n"
)


def _yaml_scalar(val: Any) -> str:
    """Render ``val`` as a YAML-safe scalar: bare for simple tokens, JSON-quoted
    (valid YAML) for anything with special chars. Booleans → ``true``/``false``."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if val is None:
        return "null"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    if s and all(c.isalnum() or c in "_./-" for c in s):
        return s
    import json
    return json.dumps(s)                       # double-quoted → valid YAML scalar


def _render_section(section: str, keys: list[ConfigKey]) -> str:
    """One annotated YAML section: a key per line at its default + a ``#`` comment.
    Secret keys render a ``${env:VAR}`` reference, never the literal value."""
    lines = [f"{section}:"]
    for k in keys:
        value = f"${{env:{k.env or 'UNSET'}}}" if k.secret else k.default
        comment = k.doc
        if k.enum:
            comment = f"{comment} ({'|'.join(map(str, k.enum))})".strip()
        if k.env and not k.secret:
            comment = f"{comment} [env: {k.env}]".strip()
        line = f"  {k.name}: {_yaml_scalar(value)}"
        if comment:
            line += f"  # {comment}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _ensure_all_registered() -> None:
    """Register every config section before reading the UNION. Config registers via
    import side-effect, but the modules that hold it are imported lazily: ``_frugal``
    by the M1 hook handlers, and each capability's ``config`` submodule only when a
    config-reading verb runs (NOT at capability discovery). So a scaffold/report —
    which needs the whole set — must pull them in. Globs ``capabilities/*/config.py``
    so a new drop-in capability is included with no edit here (open-set; no frozen
    list — Spec 054). Best-effort: one bad import never breaks scaffold/report."""
    try:
        from . import _frugal  # noqa: F401 — core discipline section
    except Exception:
        pass
    try:
        import importlib
        import pkgutil
        from . import capabilities as _caps
        for mod in pkgutil.iter_modules(_caps.__path__):
            try:
                importlib.import_module(f"{_caps.__name__}.{mod.name}.config")
            except Exception:
                continue                  # no config.py (or its import failed) → skip
    except Exception:
        pass


def config_scaffold(path: str | None = None) -> str:
    """Generate / repair ``.agency/config.yaml`` — every registered section at its
    defaults with per-key comments. Idempotent + **non-destructive**: a present
    section is never rewritten (user edits + comments survive); only **missing**
    sections are appended. Returns the path written.

    # frugal: section-granular merge — a NEW section appears, but a key added to
    # an EXISTING section is not back-filled into the file (config_get still
    # resolves its default). Upgrade to per-key insertion if a section's key set
    # grows in place and the file must list it; comment-preserving round-trip
    # would then want ruamel.yaml over the bare-pyyaml read used here.
    """
    _ensure_all_registered()
    target = path or _resolve_config_path()
    existing_text = ""
    if os.path.exists(target):
        with open(target, encoding="utf-8") as f:
            existing_text = f.read()
    # Parse the existing text directly (one parse). If it's non-empty but CORRUPT
    # YAML, repair must NOT blind-append sections — that yields a doubly-broken
    # file. Leave it untouched and let the caller/doctor surface the parse error.
    if existing_text.strip():
        try:
            parsed = yaml.safe_load(existing_text) if yaml is not None else {}
        except yaml.YAMLError:
            return target                      # corrupt — don't worsen it
        present = parsed if isinstance(parsed, dict) else {}
    else:
        present = {}
    appended = [_render_section(section, keys)
                for section, keys in _REGISTRY.items() if section not in present]
    if not appended and existing_text:
        return target                          # nothing missing → no rewrite (keeps
        #                                        the read-cache + file mtime stable)
    out = existing_text if existing_text.strip() else _HEADER
    if appended:
        if out and not out.endswith("\n"):
            out += "\n"
        out += "\n".join(appended)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(out)
    _READ_CACHE.pop(target, None)              # write invalidates the read-cache
    return target


# ── Spec 334 Slice 4 — doctor report + validation ─────────────────────────────
def config_report(*, path: str | None = None) -> dict:
    """Every registered key → ``{value, source}`` (env / file / default), so doctor
    can explain *why* a value is what it is. Secret keys are redacted to presence
    (``value`` is ``"set"``/``"unset"`` — the literal is never reported)."""
    _ensure_all_registered()
    secrets = set(secret_keys())
    out: dict = {}
    for dotted in registered_keys():
        r = config_resolve(dotted, path=path)
        if dotted in secrets:
            present = r["source"] == "env" and bool(r["value"])
            out[dotted] = {"value": "set" if present else "unset", "source": r["source"]}
        else:
            out[dotted] = {"value": r["value"], "source": r["source"]}
    return out


def config_validate(*, path: str | None = None) -> list[str]:
    """Config-health issues (empty = clean): a registered key resolving outside
    its declared ``enum``, and a key present in the file that no section
    registered (typo / stale). Each message names the key + the repair."""
    _ensure_all_registered()
    issues: list[str] = []
    for section, keys in _REGISTRY.items():
        for k in keys:
            if not k.enum:
                continue
            val = config_resolve(f"{section}.{k.name}", path=path)["value"]
            if val not in k.enum:
                issues.append(
                    f"config {section}.{k.name}={val!r} is invalid (expected "
                    f"{'|'.join(map(str, k.enum))}) — fix .agency/config.yaml or "
                    f"run `agency-doctor --write-config` to regenerate missing keys")
    registered = set(registered_keys())
    for section, sec in (_read(path or _resolve_config_path()) or {}).items():
        if isinstance(sec, dict):
            for name in sec:
                if f"{section}.{name}" not in registered:
                    issues.append(
                        f"config {section}.{name} in .agency/config.yaml is not a "
                        f"registered key (typo or stale?)")
    return issues


# ── core section (always registered) ──────────────────────────────────────────
register_config_section("core", [
    ConfigKey("db_path", "AGENCY_DB", ".agency/session.db",
              "central bi-temporal graph DB (Spec 020)"),
    ConfigKey("embedder", "AGENCY_EMBEDDER", "tfidf",
              "recall embedder backend", enum=("tfidf", "bge")),
    ConfigKey("token_backend", "AGENCY_TOKEN_BACKEND", "tiktoken",
              "token-count backend (anthropic|tiktoken|proxy)"),
])

# Secrets are env-only — the scaffold writes a ${env:VAR} reference, doctor
# reports presence, config_set never persists the literal (Spec 334 Q2).
register_config_section("secrets", [
    ConfigKey("jules_api_key", "JULES_API_KEY", "",
              "Jules remote-agent API key", secret=True),
    ConfigKey("anthropic_api_key", "ANTHROPIC_API_KEY", "",
              "Anthropic API key", secret=True),
])
