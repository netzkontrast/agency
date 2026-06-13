"""Spec 283 (+ minimal Spec 278) — frontmatter emit / parse / hash.

The render substrate writes each graph entity to a markdown file carrying a
YAML-ish frontmatter block (the node id + key fields, so a re-render is
byte-identical and `parse` reconstructs the slice). Stdlib-only, matching the
`key: "value"` shape the novel production driver already uses — when Spec 278
lands its richer schema-per-kind discipline extends this helper rather than
replacing it.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, dict)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"))
    return f'"{v}"'


def _unscalar(val: str) -> Any:
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1]
    if val in ("true", "false"):
        return val == "true"
    # bare (unquoted) integer — emit writes ints unquoted, so round-trip them.
    if val and (val.lstrip("-")).isdigit():
        return int(val)
    if val and (val[0] in "[{"):
        try:
            return json.loads(val)
        except ValueError:
            pass
    return val


def emit(frontmatter: dict[str, Any], body: str = "") -> str:
    """Render a frontmatter block + body. Key order is preserved (dict order),
    so a stable frontmatter dict yields byte-identical output."""
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f"{k}: {_scalar(v)}")
    lines.append("---")
    block = "\n".join(lines)
    return f"{block}\n\n{body}\n" if body else f"{block}\n"


def parse(text: str) -> tuple[dict, str]:
    """Inverse of `emit` — returns ``(frontmatter, body)``. No frontmatter →
    ``({}, text)``."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm: dict = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        ln = lines[i]
        i += 1
        if not ln.strip() or ":" not in ln or ln[:1] in (" ", "\t"):
            continue
        key, _, raw = ln.partition(":")
        fm[key.strip()] = _unscalar(raw.strip())
    body = "\n".join(lines[i + 1:]).strip("\n") if i < len(lines) else ""
    return fm, body


def frontmatter_hash(frontmatter: dict) -> str:
    """Stable short hash of the frontmatter — the Artefact's content
    fingerprint (an unchanged node re-renders to the same hash)."""
    blob = json.dumps(frontmatter, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
