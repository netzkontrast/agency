"""dogfood.lifecycle — spec lifecycle queries: status, listing, and code refs.

Specs move through a lifecycle (drafted → partial → shipped → archived).
The Plan/ directory is the live surface for drafted/partial specs; shipped
specs are deleted from disk and preserved in the git archive branch
``archive/plan-specs-pre-cleanup``.

These verbs make the lifecycle queryable via the agency surface so the
Plan folder is a first-class, machine-readable lifecycle artefact.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ....capability import verb


_SPEC_DIR_RE = re.compile(r"^(\d{3})-(.+)$")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_SPEC_REF_RE = re.compile(r"#\s*Spec\s+(\d{1,3})\b")
_ARCHIVE_BRANCH = "archive/plan-specs-pre-cleanup"

# Normalize raw frontmatter status values to canonical lifecycle stages.
# Frontmatter is hand-maintained so capitalisation and phrasing varies.
_STATUS_NORM: dict[str, str] = {}
for _raw, _canon in [
    ("draft",       "drafted"),
    ("drafted",     "drafted"),
    ("partial",     "partial"),
    ("implementing","partial"),
    ("in-progress", "partial"),
    ("shipped",     "shipped"),
    ("done",        "shipped"),
    ("complete",    "shipped"),
    ("closed",      "closed"),
    ("superseded",  "closed"),
    ("deferred",    "deferred"),
]:
    _STATUS_NORM[_raw] = _canon


def _read_frontmatter(path: str) -> dict[str, Any]:
    """Parse YAML-ish frontmatter (key: value lines) from a spec.md."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip().strip('"')
    return result


def _normalize_status(raw: str) -> str:
    """Canonicalize a raw frontmatter status string."""
    key = raw.lower().split()[0] if raw else "drafted"
    return _STATUS_NORM.get(key, raw.lower())


def _next_step_from_followup(path: str) -> str:
    """Extract the first non-empty line from the Followup section."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    m = re.search(r"##\s+Followup[^\n]*\n(.*?)(?:\n##|\Z)", text, re.DOTALL)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = line.strip().lstrip("-•*").strip()
        if line and not line.startswith("#"):
            return line[:200]
    return ""


def _list_plan_dirs(plan_dir: str = "Plan") -> list[tuple[str, str, str]]:
    """Return (spec_id, slug, spec_path) for every NNN-slug dir with a spec.md."""
    results = []
    try:
        entries = sorted(os.listdir(plan_dir))
    except OSError:
        return results
    for entry in entries:
        m = _SPEC_DIR_RE.match(entry)
        if not m:
            continue
        spec_path = os.path.join(plan_dir, entry, "spec.md")
        if os.path.isfile(spec_path):
            results.append((m.group(1), m.group(2), spec_path))
    return results


def _archive_path_for(spec_id: str) -> str | None:
    """Return the spec path from the archive index, or None if not found.

    Reads ``Plan/_archive/index.json`` first (committed — always available,
    even in CI shallow clones), then falls back to ``git ls-tree`` on the
    archive branch for any entries not yet in the index.
    """
    import json
    index_path = Path("Plan/_archive/index.json")
    try:
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        if spec_id in idx:
            return idx[spec_id]
    except Exception:
        pass
    # Fallback: git archive branch (works in full clones / local dev).
    try:
        out = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", _ARCHIVE_BRANCH, "--", "Plan/"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        for line in out.stdout.splitlines():
            parts = line.split("/")
            if (len(parts) == 3 and parts[0] == "Plan"
                    and parts[1].startswith(f"{spec_id}-")
                    and parts[2] == "spec.md"):
                return line
    except Exception:
        pass
    return None


class LifecycleMixin:
    """Spec lifecycle read-verbs (transform) — status, listing, code refs."""

    @verb(role="transform")
    def spec_status(self, spec_id: str) -> dict:
        """Return the lifecycle status of a spec by its 3-digit id.

        Checks the live Plan/ directory first; falls back to the git archive
        branch for shipped specs; returns ``{"status": "unknown"}`` if the
        spec is not found anywhere.

        :param spec_id: 3-digit spec number as a string, e.g. ``"146"``.
        """
        if not spec_id or not spec_id.strip().isdigit():
            return {"status": "unknown", "spec_id": spec_id, "error": "invalid spec_id"}
        sid = spec_id.strip().zfill(3)

        # Check live Plan/ directory
        matches = sorted(glob.glob(f"Plan/{sid}-*/spec.md"))
        if matches:
            path = matches[0]
            slug_dir = Path(path).parent.name
            slug = slug_dir.split("-", 1)[1] if "-" in slug_dir else slug_dir
            fm = _read_frontmatter(path)
            next_step = _next_step_from_followup(path)
            return {
                "spec_id": sid,
                "slug": slug,
                "status": _normalize_status(fm.get("status", "drafted")),
                "status_raw": fm.get("status", ""),
                "on_disk": True,
                "path": path,
                "next_step": next_step,
            }

        # Not on disk — check archive branch (shipped/closed)
        archived = _archive_path_for(sid)
        if archived:
            slug_dir = archived.split("/")[1]
            slug = slug_dir.split("-", 1)[1] if "-" in slug_dir else slug_dir
            return {
                "spec_id": sid,
                "slug": slug,
                "status": "shipped",
                "on_disk": False,
                "path": archived,
                "archive_branch": _ARCHIVE_BRANCH,
                "next_step": "",
            }

        return {"status": "unknown", "spec_id": sid, "on_disk": False}

    @verb(role="transform")
    def specs(self, status: str = "", plan_dir: str = "Plan") -> dict:
        """List specs from the Plan/ directory, optionally filtered by status.

        Walks every ``Plan/NNN-slug/spec.md`` on disk, reads the frontmatter
        status field, and returns a structured list.  Shipped specs (no Plan
        dir on disk) are not included unless you also query the archive branch
        explicitly via ``spec_status``.

        :param status: Filter to this status value (``drafted``, ``partial``,
            ``shipped``).  Empty string returns all on-disk specs.
        :param plan_dir: Root of the Plan directory (default ``"Plan"``).
        """
        entries = []
        for spec_id, slug, path in _list_plan_dirs(plan_dir):
            fm = _read_frontmatter(path)
            s = _normalize_status(fm.get("status", "drafted"))
            if status and s != status:
                continue
            next_step = _next_step_from_followup(path)
            entries.append({
                "spec_id": spec_id,
                "slug":    slug,
                "status":  s,
                "path":    path,
                "next_step": next_step,
            })
        return {"specs": entries, "count": len(entries), "filter": status or "all"}

    @verb(role="transform")
    def spec_refs(self, spec_id: str, search_root: str = "agency") -> dict:
        """Find all ``# Spec NNN`` inline references to a spec in the codebase.

        Scans Python source files under ``search_root`` for the pattern
        ``# Spec NNN`` (case-insensitive).  Returns file paths, line numbers,
        and the matching line text so callers can navigate to the reference.

        :param spec_id: 3-digit spec number, e.g. ``"150"``.
        :param search_root: Directory to scan (default ``"agency"``).
        """
        if not spec_id or not spec_id.strip().isdigit():
            return {"refs": [], "count": 0, "spec_id": spec_id,
                    "error": "invalid spec_id"}
        sid = spec_id.strip().lstrip("0") or "0"  # normalise "046" → "46"
        target = re.compile(rf"#\s*Spec\s+0*{re.escape(sid)}\b", re.IGNORECASE)
        refs = []
        for py_path in sorted(glob.glob(f"{search_root}/**/*.py", recursive=True)):
            if "__pycache__" in py_path:
                continue
            try:
                for lineno, line in enumerate(
                        Path(py_path).read_text(encoding="utf-8",
                                                errors="replace").splitlines(),
                        start=1):
                    if target.search(line):
                        refs.append({
                            "file": py_path,
                            "line": lineno,
                            "text": line.strip(),
                        })
            except OSError:
                continue
        return {"refs": refs, "count": len(refs), "spec_id": spec_id.zfill(3)}
