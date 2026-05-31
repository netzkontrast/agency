"""Spec 031 §E / Task 2.4 — atomic JSON cache for skill emit idempotency.

The cache lives at <cache_dir>/skill-cache.json — a single document mapping
capability name → {hash, files: [paths]}. install.generate(engine) consults
the cache before invoking the emit pipeline; if the capability's hash matches
the stored hash, the cached file list is reused (no regeneration).

Panel F-3 atomicity: commit writes to .tmp then os.replace's into place.
A kill between .tmp write and os.replace leaves the original file unchanged.
A corrupt .tmp left behind from a prior kill is harmless (it's a separate
file; cleanup is implicit on next successful commit).
"""
from __future__ import annotations

import json
import os
from pathlib import Path


CACHE_FILENAME = "skill-cache.json"
CACHE_VERSION = 1


def _cache_path(cache_dir) -> Path:
    return Path(cache_dir) / CACHE_FILENAME


def _read_cache(cache_dir) -> dict:
    """Load the cache document. Returns {version, capabilities: {...}}.

    On missing file: returns the empty shape.
    On corrupt JSON (partial write from kill): returns the empty shape;
    caller treats as a miss and regenerates.
    """
    path = _cache_path(cache_dir)
    if not path.exists():
        return {"version": CACHE_VERSION, "capabilities": {}}
    try:
        doc = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"version": CACHE_VERSION, "capabilities": {}}
    if not isinstance(doc, dict) or "capabilities" not in doc:
        return {"version": CACHE_VERSION, "capabilities": {}}
    return doc


def peek(cache_dir, cap_name: str, hash_: str) -> dict | None:
    """Return {hash, files} if cache has cap_name AT this hash; else None."""
    doc = _read_cache(cache_dir)
    entry = doc.get("capabilities", {}).get(cap_name)
    if not entry:
        return None
    if entry.get("hash") != hash_:
        return None
    return entry


def commit(cache_dir, cap_name: str, hash_: str, files: list[str]) -> None:
    """Atomically write {cap_name: {hash, files}} to skill-cache.json.

    Reads the current doc, merges in the new entry, writes to .tmp, then
    os.replace's into place. Atomic: a kill before os.replace leaves the
    original file unchanged.
    """
    path = _cache_path(cache_dir)
    tmp = path.with_suffix(".json.tmp")
    doc = _read_cache(cache_dir)
    doc["version"] = CACHE_VERSION  # ensure present
    doc.setdefault("capabilities", {})
    doc["capabilities"][cap_name] = {"hash": hash_, "files": list(files)}
    # Ensure dir exists
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    # Write to tmp first
    tmp.write_text(json.dumps(doc, indent=2, sort_keys=True))
    # Atomic rename
    os.replace(tmp, path)
