"""novel config — Spec 121 production-binding config layer.

Mirrors `agency/capabilities/music/config.py`: per-project
`.agency/novel-config.yaml`, global fallback, env override; mtime-cached
4-level resolution; minimal handrolled YAML parser when PyYAML missing;
`bootstrap()` writes default + creates content_root on first run.

Resolution order (first hit wins):
1. `.agency/novel-config.yaml` (CWD-relative)
2. `~/.agency-novel/config.yaml`
3. `$AGENCY_NOVEL_HOME/config.yaml`
4. Built-in defaults (`NovelConfig.defaults()`)

Prior-spec-010 disk layout: `works/{author}/works/{genre}/{slug}/`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_CONTENT_ROOT = "~/novel-projects"

# The default-config written when a fresh repo has none yet.
_DEFAULT_CONFIG_REL = ".agency/novel-config.yaml"
DEFAULT_CONFIG_YAML = """\
# agency novel — production config (auto-generated default, Spec 121).
# Bind a project by editing `author.name` + `paths.content_root`, then run
# any novel verb that needs disk I/O.
author:
  name: ""

paths:
  content_root: "~/novel-projects"
  # ideas_file defaults under content_root

defaults:
  genre: "novel"
  target_word_count: 80000

db:
  backend: sqlite
  path: ".agency/novel.db"
"""


def _expand(p: str) -> str:
    return os.path.expanduser(os.path.expandvars(p))


def _mtime(p: str) -> float:
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0.0


_LOAD_CACHE: dict[tuple, "NovelConfig"] = {}


def _parse_yaml(text: str) -> dict:
    """PyYAML first; minimal handrolled subset parser as fallback."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        pass
    out: dict = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  ") and current_key:
            inner_key, _, value = line.strip().partition(":")
            out.setdefault(current_key, {})[inner_key.strip()] = _coerce(value.strip())
        else:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                out[key] = _coerce(value)
            else:
                current_key = key
                out[key] = {}
    return out


def _coerce(v: str):
    if v == "":
        return None
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if v.startswith(("'", '"')) and v.endswith(v[0]):
        return v[1:-1]
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


@dataclass
class NovelConfig:
    """Novel production-binding config — Spec 121.

    All paths are post-expansion (no `~` or `$HOME` left in them).
    """
    author_name: str = ""
    content_root: str = _DEFAULT_CONTENT_ROOT
    ideas_file: str = ""
    default_genre: str = "novel"
    default_target_word_count: int = 80000
    db_backend: str = "sqlite"
    db_path: str = ".agency/novel.db"

    @classmethod
    def defaults(cls) -> "NovelConfig":
        cfg = cls()
        cfg._fill_path_defaults()
        return cfg

    @classmethod
    def load(cls, search_paths: list[str] | None = None) -> "NovelConfig":
        """Load config from the first hit; mtime-cached for in-process reuse."""
        paths = (tuple(search_paths) if search_paths is not None
                 else tuple(cls._default_search_paths()))
        signature = tuple((p, _mtime(_expand(p))) for p in paths)
        cached = _LOAD_CACHE.get(signature)
        if cached is not None:
            return cached
        cfg = cls._load_uncached(paths)
        _LOAD_CACHE[signature] = cfg
        return cfg

    @classmethod
    def _load_uncached(cls, paths: tuple[str, ...]) -> "NovelConfig":
        for path in paths:
            p = Path(_expand(path))
            if p.is_file():
                return cls._from_dict(_parse_yaml(p.read_text()))
        return cls.defaults()

    @classmethod
    def _default_search_paths(cls) -> list[str]:
        out = [".agency/novel-config.yaml",
               "~/.agency-novel/config.yaml"]
        env = os.environ.get("AGENCY_NOVEL_HOME", "")
        if env:
            out.append(f"{env.rstrip('/')}/config.yaml")
        return out

    @classmethod
    def config_file_exists(cls, search_paths: list[str] | None = None) -> bool:
        paths = (search_paths if search_paths is not None
                 else cls._default_search_paths())
        return any(Path(_expand(p)).is_file() for p in paths)

    @classmethod
    def bootstrap(cls, *, write_config: bool = True, make_dirs: bool = True,
                  config_path: str = _DEFAULT_CONFIG_REL) -> "NovelConfig":
        """Idempotent fresh-repo bootstrap (mirrors MusicConfig.bootstrap).

        No-op when a config already exists; otherwise writes the default
        `.agency/novel-config.yaml` so a fresh repo is ready to edit, then
        creates the content_root so FileNovelStateDriver has a home.
        """
        if write_config and not cls.config_file_exists():
            dest = Path(_expand(config_path))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(DEFAULT_CONFIG_YAML)
        cfg = cls.load()
        if make_dirs:
            Path(cfg.content_root).expanduser().mkdir(parents=True,
                                                      exist_ok=True)
        return cfg

    @classmethod
    def _from_dict(cls, d: dict) -> "NovelConfig":
        cfg = cls()
        author = d.get("author") or {}
        paths = d.get("paths") or {}
        defaults = d.get("defaults") or {}
        db = d.get("db") or {}
        cfg.author_name = author.get("name", "") or ""
        cfg.content_root = _expand(
            paths.get("content_root") or _DEFAULT_CONTENT_ROOT)
        cfg.ideas_file = _expand(paths.get("ideas_file") or "")
        cfg.default_genre = defaults.get("genre", "novel") or "novel"
        cfg.default_target_word_count = int(
            defaults.get("target_word_count", 80000) or 80000)
        cfg.db_backend = db.get("backend", "sqlite") or "sqlite"
        cfg.db_path = db.get("path", ".agency/novel.db") or ".agency/novel.db"
        cfg._fill_path_defaults()
        return cfg

    def _fill_path_defaults(self) -> None:
        self.content_root = _expand(self.content_root)
        if not self.ideas_file:
            self.ideas_file = str(
                Path(self.content_root) / "IDEAS.md")


# Spec 328 Slice 5 — open-set proof: surface novel's config in the unified
# .agency/config.yaml (derived from the dataclass — single source, no literals).
# The live value is resolved by the novel capability (.agency/novel-config.yaml /
# AGENCY_NOVEL_HOME); full read-path unification is a tracked follow-up.
try:  # best-effort — config registration must never break the capability import
    from ... import _config as _agency_config
    _agency_config.register_dataclass_section(
        "novel", NovelConfig, doc="novel default — resolved by the novel capability")
except Exception:  # pragma: no cover - registration is best-effort
    pass
