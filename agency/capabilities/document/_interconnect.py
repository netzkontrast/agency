# agency-scaffold: v1
"""graph<->markdown interconnect (Spec 292).

The premise flip: markdown files are no longer a one-way *rendered view* of
the graph — they are an editable PEER surface that round-trips back into it.

Mechanism (keep-both, bi-temporal, stable anchor):

- A participating ``.md`` file carries a stable ANCHOR on its first line::

      <!-- agency-node: document:abc12345 -->

  reusing the existing HTML-comment marker convention (cf. ``doc-source``).

- The anchor names a stable ``Document`` node (the file's identity). Every
  ingest/render appends an append-only ``DocRevision`` (tagged ``source`` =
  ``graph`` | ``file``) linked ``REVISION_OF`` the Document. NOTHING is
  overwritten — the graph-authored and file-authored versions coexist;
  latest-by-``recorded_at`` wins on read, the rest is retained history.

This module is pure text/hash helpers; graph writes live in the verbs.
"""
from __future__ import annotations

import hashlib
import re

# `# AGENCY-DRIFT: doc-interconnect anchor` — the anchor regex/format is read
# by ingest (parse) AND render (stamp); keep both sites in sync.
_ANCHOR_RE = re.compile(r"<!--\s*agency-node:\s*(\S+)\s*-->")
_ANCHOR_LINE_RE = re.compile(r"^[ \t]*<!--\s*agency-node:\s*\S+\s*-->[ \t]*\n?",
                             re.MULTILINE)


def content_sha(text: str) -> str:
    """16-hex content hash of the document BODY (anchor-independent).

    Matches ``_index_repo.content_sha``'s 16-char width so the two
    interconnect hashes read alike.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def extract_anchor(raw: str) -> tuple[str | None, str]:
    """Split a raw markdown string into ``(anchor_node_id | None, body)``.

    The body is the file content with the anchor line removed, so the
    content hash is stable across (re-)stamping.
    """
    m = _ANCHOR_RE.search(raw)
    node_id = m.group(1) if m else None
    body = _ANCHOR_LINE_RE.sub("", raw, count=1).lstrip("\n") if node_id else raw
    return node_id, body


def parse_frontmatter(body: str) -> dict:
    """Parse a leading ``---\\n…\\n---`` YAML frontmatter block; ``{}`` if absent
    or unparseable. The convergence layer reads a Document's declared fields
    here to validate them against its bound Schema (CONFORMS_TO)."""
    if not body.startswith("---\n"):
        return {}
    end = body.find("\n---", 4)
    if end == -1:
        return {}
    try:
        import yaml
        loaded = yaml.safe_load(body[4:end])
    except Exception:                                           # noqa: BLE001
        return {}
    return loaded if isinstance(loaded, dict) else {}


def stamp_anchor(body: str, node_id: str) -> str:
    """Return ``body`` with the anchor for ``node_id`` on its first line.

    Idempotent — an existing anchor (any id) is replaced, not duplicated.
    """
    stripped = _ANCHOR_LINE_RE.sub("", body, count=1).lstrip("\n")
    return f"<!-- agency-node: {node_id} -->\n{stripped}"
