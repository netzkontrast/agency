# agency-scaffold: v1
"""music config — Spec 115 production-binding config layer.

Loads `.agency/music-config.yaml` (per-project) with optional fallbacks at
`~/.agency-music/config.yaml` (user-global) and `$AGENCY_MUSIC_HOME/config.yaml`
(env override). Mirrors bitwize's `~/.bitwize-music/config.yaml` shape so a
bitwize user can point `AGENCY_MUSIC_HOME` at their existing dir and it
just works.

Resolution order (first hit wins):
1. `.agency/music-config.yaml` (CWD-relative)
2. `~/.agency-music/config.yaml`
3. `$AGENCY_MUSIC_HOME/config.yaml`
4. Built-in defaults (the `MusicConfig.defaults()` factory)

YAML parsing is optional — falls back to a minimal handrolled subset parser
(supports `key: value` + 2-level nesting + lists) when `pyyaml` isn't
installed. Production users install `pip install agency[music-production]`
to get the real PyYAML for richer YAML files.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_CONTENT_ROOT = "~/music-projects"

# Spec 117 — the default config written when a fresh repo has none yet.
# Mirrors the bitwize-music config shape; empty artist + the generic
# content_root are the "fill me in" defaults a fresh user edits.
_DEFAULT_CONFIG_REL = ".agency/music-config.yaml"
DEFAULT_CONFIG_YAML = """\
# agency music — production config (auto-generated default, Spec 117).
# Bind a project by editing `artist.name` + `paths.content_root`, then run
# any music verb. Mirrors the bitwize-music `~/.bitwize-music/config.yaml` shape.
artist:
  name: ""

paths:
  content_root: "~/music-projects"
  # audio_root / documents_root / overrides / ideas_file default under content_root

db:
  backend: sqlite
  path: ".agency/music.db"

generation:
  additional_genres: []

sheet_music:
  enabled: true
  page_size: "letter"
"""


def _expand(p: str) -> str:
    return os.path.expanduser(os.path.expandvars(p))


def _mtime(p: str) -> float:
    """Cheap stat — 0.0 when missing; used as cache invalidation token."""
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0.0


# Module-level mtime-keyed cache for MusicConfig.load (Spec 116 efficiency
# review): every config-touching verb calls load(), and engine bootstrap
# touches it 2-3× per session. The cache key is (paths-tuple, mtime-tuple)
# so a real config edit invalidates without engine restart.
_LOAD_CACHE: dict[tuple, "MusicConfig"] = {}


def _parse_yaml(text: str) -> dict:
    """Try PyYAML first; fall back to a minimal subset parser.

    The minimal parser supports the bitwize-shape config used here:
    - `key: value` pairs (strings, numbers, bools)
    - 2-level nesting via 2-space indent
    - empty values become None
    - lines starting with `#` or whitespace-then-`#` are comments
    """
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
            current_key = key.strip()
            v = value.strip()
            out[current_key] = _coerce(v) if v else {}
    return out


def _coerce(v: str):
    if v in ("true", "True", "yes"):
        return True
    if v in ("false", "False", "no"):
        return False
    if v in ("null", "None", ""):
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v.strip("\"'")


@dataclass
class MusicConfig:
    """Music production-binding config — Spec 115.

    Attributes match the bitwize shape (Spec 115 §"Config schema"). All
    paths are post-expansion (no `~` or `$HOME` left in them).
    """
    artist_name: str = ""
    content_root: str = _DEFAULT_CONTENT_ROOT
    audio_root: str = ""
    documents_root: str = ""
    overrides: str = ""
    ideas_file: str = ""
    db_backend: str = "sqlite"
    db_path: str = ".agency/music.db"
    additional_genres: list = field(default_factory=list)
    sheet_music_enabled: bool = True
    sheet_music_page_size: str = "letter"

    @classmethod
    def defaults(cls) -> "MusicConfig":
        cfg = cls()
        cfg._fill_path_defaults()
        return cfg

    @classmethod
    def load(cls, search_paths: list[str] | None = None) -> "MusicConfig":
        """Load config from the first hit in the search-path list.

        Default search order (first hit wins):
          1. `./.agency/music-config.yaml`
          2. `~/.agency-music/config.yaml`
          3. `$AGENCY_MUSIC_HOME/config.yaml`
          4. defaults

        Result is mtime-cached: re-calling on the same file (no mtime change)
        returns the same `MusicConfig` instance instead of re-parsing YAML.
        Mtime invalidation handles edits-in-place without engine restart.
        """
        paths = (tuple(search_paths) if search_paths is not None
                 else tuple(cls._default_search_paths()))
        # Build a cache key keyed by paths + per-path mtime (mtime=0 if missing).
        signature = tuple((p, _mtime(_expand(p))) for p in paths)
        cached = _LOAD_CACHE.get(signature)
        if cached is not None:
            return cached
        cfg = cls._load_uncached(paths)
        _LOAD_CACHE[signature] = cfg
        return cfg

    @classmethod
    def _load_uncached(cls, paths: tuple[str, ...]) -> "MusicConfig":
        for path in paths:
            p = Path(_expand(path))
            if p.is_file():
                return cls._from_dict(_parse_yaml(p.read_text()))
        return cls.defaults()

    @classmethod
    def _default_search_paths(cls) -> list[str]:
        out = [".agency/music-config.yaml",
               "~/.agency-music/config.yaml"]
        env = os.environ.get("AGENCY_MUSIC_HOME", "")
        if env:
            out.append(f"{env.rstrip('/')}/config.yaml")
        return out

    @classmethod
    def config_file_exists(cls, search_paths: list[str] | None = None) -> bool:
        """True when any search-path config file is present (Spec 117).

        The bootstrap predicate: a fresh repo has none, so `bootstrap()`
        writes a default; an existing project has one, so bootstrap is a no-op.
        """
        paths = (search_paths if search_paths is not None
                 else cls._default_search_paths())
        return any(Path(_expand(p)).is_file() for p in paths)

    @classmethod
    def bootstrap(cls, *, write_config: bool = True, make_dirs: bool = True,
                  config_path: str = _DEFAULT_CONFIG_REL) -> "MusicConfig":
        """Default-config + fresh-repo bootstrap (Spec 117).

        Idempotent "set up if not done yet": when NO music config exists on any
        search path, write a default ``.agency/music-config.yaml`` so a fresh
        repo is ready to edit, then (optionally) create the ``content_root`` so
        the FileStateDriver has a home to write into. A no-op when a config
        already exists — an existing project keeps its bindings. Returns the
        loaded `MusicConfig`.

        Driven lazily by the music capability's auto-wiring (set up drivers —
        and their config — only when a verb needs them).
        """
        if write_config and not cls.config_file_exists():
            dest = Path(_expand(config_path))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(DEFAULT_CONFIG_YAML)
            _LOAD_CACHE.clear()      # invalidate so load() sees the new file
        cfg = cls.load()
        if make_dirs:
            try:
                Path(_expand(cfg.content_root)).mkdir(parents=True, exist_ok=True)
            except OSError:
                pass                 # best-effort; FileStateDriver also mkdirs on write
        return cfg

    @classmethod
    def _from_dict(cls, d: dict) -> "MusicConfig":
        artist = d.get("artist") or {}
        paths = d.get("paths") or {}
        db = d.get("db") or {}
        gen = d.get("generation") or {}
        sheet = d.get("sheet_music") or {}
        cfg = cls(
            artist_name=artist.get("name") or "",
            content_root=_expand(paths.get("content_root") or _DEFAULT_CONTENT_ROOT),
            audio_root=_expand(paths.get("audio_root") or ""),
            documents_root=_expand(paths.get("documents_root") or ""),
            overrides=_expand(paths.get("overrides") or ""),
            ideas_file=_expand(paths.get("ideas_file") or ""),
            db_backend=(db.get("backend") or "sqlite"),
            db_path=_expand(db.get("path") or ".agency/music.db"),
            additional_genres=list(gen.get("additional_genres") or []),
            sheet_music_enabled=bool(sheet.get("enabled", True)),
            sheet_music_page_size=str(sheet.get("page_size") or "letter"),
        )
        cfg._fill_path_defaults()
        return cfg

    def _fill_path_defaults(self) -> None:
        root = _expand(self.content_root) if self.content_root else _expand(_DEFAULT_CONTENT_ROOT)
        self.content_root = root
        if not self.audio_root:
            self.audio_root = f"{root}/audio"
        if not self.documents_root:
            self.documents_root = f"{root}/documents"
        if not self.overrides:
            self.overrides = f"{root}/overrides"
        if not self.ideas_file:
            self.ideas_file = f"{root}/IDEAS.md"

    def as_dict(self) -> dict:
        """Bitwize-shape rendering for `get_config` verb returns."""
        return {
            "artist": {"name": self.artist_name},
            "paths": {
                "content_root": self.content_root,
                "audio_root": self.audio_root,
                "documents_root": self.documents_root,
                "overrides": self.overrides,
                "ideas_file": self.ideas_file,
            },
            "db": {"backend": self.db_backend, "path": self.db_path},
            "generation": {"additional_genres": list(self.additional_genres)},
            "sheet_music": {
                "enabled": self.sheet_music_enabled,
                "page_size": self.sheet_music_page_size,
            },
        }
