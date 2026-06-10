"""novel production drivers — Spec 121.

Disk-writing StateDriver bound to the bitwize prior-spec-010 layout:

    {content_root}/
    └── works/{author}/works/{genre}/{slug}/
        ├── work.md                 (rendered from templates/work.md)
        ├── premise.md              (rendered from templates/premise.md)
        ├── dramatica.md            (rendered from templates/dramatica.md)
        ├── ncp.json                (NCP v1.3.0 payload, optional)
        ├── chapters/
        │   └── NN-slug.md          (rendered from templates/chapter.md)
        └── scenes/
            └── NN-slug.md          (rendered from templates/scene.md)

`production_drivers(cfg)` returns a driver bundle symmetric to music's
`production_drivers`, so the novel capability's lazy auto-wiring (Spec 121
`_require_drv`) registers it on first miss.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import NovelConfig
from ._slug import slugify


class FileNovelStateDriver:
    """Disk-writing StateDriver for the novel capability.

    Production usage::

        cfg = NovelConfig.load()
        engine = Engine(drivers=production_drivers(cfg))

    Render fidelity (Spec 117 F3/F4/F5 lessons applied from day one):
    - Templates substituted with {{author_slug}}, {{work_slug}}, {{work_title}},
      {{genre_slug}}, {{created}} (F3 — body field substitution)
    - `status:` lives in frontmatter as the single source of truth
      (F4 — no sidecar .meta.json)
    - The default `status: draft` matches what create_novel records on
      the graph node (F5 — template status matches verb's initial state)
    """

    def __init__(self, config: NovelConfig | None = None,
                 templates_dir: str | None = None) -> None:
        self.config = config or NovelConfig.defaults()
        if templates_dir:
            self._templates_dir = Path(templates_dir)
        else:
            self._templates_dir = Path(__file__).parent / "templates"

    # ── path helpers ──
    def _content_root(self) -> Path:
        return Path(self.config.content_root).expanduser()

    def _work_root(self, author: str, genre: str, slug: str) -> Path:
        return (self._content_root() / "works" / slugify(author)
                / "works" / slugify(genre) / slugify(slug))

    def _render_template(self, name: str, fields: dict) -> str:
        tpl = self._templates_dir / f"{name}.md"
        if not tpl.is_file():
            return ""
        body = tpl.read_text(encoding="utf-8")
        for k, v in fields.items():
            body = body.replace("{{" + k + "}}", str(v))
        return body

    # ── frontmatter helpers (mirrors music's stdlib-only pattern) ──
    @staticmethod
    def _parse_frontmatter(text: str) -> dict:
        if not text.startswith("---"):
            return {}
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        out: dict = {}
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            if not ln or ln[0] in (" ", "\t") or ln.lstrip().startswith("#"):
                continue
            if ":" not in ln:
                continue
            key, _, raw = ln.partition(":")
            val = raw.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                val = val[1:-1]
            out[key.strip()] = val
        return out

    @staticmethod
    def _set_frontmatter_field(text: str, field: str, value: str) -> str:
        new_line = f'{field}: "{value}"'
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return text
        close_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                close_idx = i
                break
        if close_idx is None:
            return text
        nl = "\n"
        for i in range(1, close_idx):
            stripped = lines[i].lstrip()
            if lines[i][:1] in (" ", "\t"):
                continue
            if stripped.startswith(f"{field}:"):
                eol = nl if lines[i].endswith("\n") else ""
                lines[i] = new_line + eol
                return "".join(lines)
        lines.insert(close_idx, new_line + nl)
        return "".join(lines)

    # ── work-level ──
    def create_work(self, author: str, genre: str, title: str,
                    *, logline: str = "") -> dict:
        """Materialise a fresh work tree on disk.

        Returns ``{path, work_md, slug}``. Idempotent: rerunning on an
        existing work re-writes the templates so a template change is
        recoverable, but PRESERVES non-template content (premise body,
        chapter bodies) — only the frontmatter `status` round-trips."""
        root = self._work_root(author, genre, title)
        root.mkdir(parents=True, exist_ok=True)
        (root / "chapters").mkdir(exist_ok=True)
        (root / "scenes").mkdir(exist_ok=True)

        fields = {
            "author_slug": slugify(author),
            "work_slug": slugify(title),
            "genre_slug": slugify(genre),
            "work_title": title,
            "premise_logline": logline,
            "created": datetime.utcnow().date().isoformat(),
        }
        work_md = root / "work.md"
        if not work_md.is_file():
            work_md.write_text(
                self._render_template("work", fields), encoding="utf-8")
        premise = root / "premise.md"
        if not premise.is_file():
            premise.write_text(
                self._render_template("premise", fields), encoding="utf-8")
        return {
            "path": str(root),
            "work_md": str(work_md),
            "slug": fields["work_slug"],
        }

    def update_work_field(self, author: str, genre: str, title: str,
                          field: str, value: str) -> bool:
        """Edit a single frontmatter field in work.md (F4 round-trip)."""
        work_md = self._work_root(author, genre, title) / "work.md"
        if not work_md.is_file():
            return False
        text = work_md.read_text(encoding="utf-8")
        work_md.write_text(
            self._set_frontmatter_field(text, field, value),
            encoding="utf-8")
        return True

    # ── chapter-level ──
    def create_chapter(self, author: str, genre: str, work_title: str,
                       number: int, title: str, *, body: str = "") -> dict:
        """Write `chapters/NN-slug.md`. Returns ``{path, slug}``."""
        root = self._work_root(author, genre, work_title)
        (root / "chapters").mkdir(parents=True, exist_ok=True)
        slug = slugify(title)
        chap = root / "chapters" / f"{number:02d}-{slug}.md"
        if chap.is_file():
            return {"path": str(chap), "slug": slug, "created": False}
        fields = {
            "author_slug": slugify(author),
            "work_slug": slugify(work_title),
            "genre_slug": slugify(genre),
            "work_title": work_title,
            "created": datetime.utcnow().date().isoformat(),
        }
        rendered = self._render_template("chapter", fields)
        rendered = self._set_frontmatter_field(rendered, "title", title)
        rendered = self._set_frontmatter_field(
            rendered, "chapter_number", str(number))
        if body:
            rendered = rendered.rstrip("\n") + "\n\n" + body + "\n"
        chap.write_text(rendered, encoding="utf-8")
        return {"path": str(chap), "slug": slug, "created": True}

    def list_chapters(self, author: str, genre: str,
                      work_title: str) -> list[dict]:
        root = self._work_root(author, genre, work_title) / "chapters"
        if not root.is_dir():
            return []
        out: list[dict] = []
        for p in sorted(root.glob("*.md")):
            stem = p.stem
            num_str, _, slug = stem.partition("-")
            try:
                num = int(num_str)
            except ValueError:
                continue
            fm = self._parse_frontmatter(p.read_text(encoding="utf-8"))
            out.append({
                "number": num,
                "slug": slug,
                "title": fm.get("title", slug),
                "status": fm.get("status", "draft"),
                "path": str(p),
            })
        return out

    def update_chapter_field(self, author: str, genre: str, work_title: str,
                             number: int, slug: str,
                             field: str, value: str) -> bool:
        chap = (self._work_root(author, genre, work_title)
                / "chapters" / f"{number:02d}-{slug}.md")
        if not chap.is_file():
            return False
        text = chap.read_text(encoding="utf-8")
        chap.write_text(
            self._set_frontmatter_field(text, field, value), encoding="utf-8")
        return True

    # ── NCP body (storyform payload on disk) ──
    def read_ncp(self, author: str, genre: str, work_title: str) -> dict | None:
        ncp = self._work_root(author, genre, work_title) / "ncp.json"
        if not ncp.is_file():
            return None
        return json.loads(ncp.read_text(encoding="utf-8"))

    def write_ncp(self, author: str, genre: str, work_title: str,
                  body: dict) -> str:
        root = self._work_root(author, genre, work_title)
        root.mkdir(parents=True, exist_ok=True)
        ncp = root / "ncp.json"
        ncp.write_text(json.dumps(body, indent=2), encoding="utf-8")
        return str(ncp)


def production_drivers(config: NovelConfig | None = None) -> dict[str, Any]:
    """Bundle factory symmetric to music.production_drivers.

    Returns a dict keyed by canonical driver name. Ships `novel_state`
    (Spec 121) + `novel_format` (Spec 124 — FakeFormatDriver in CI,
    PandocFormatDriver in production once `[novel-format]` extra is wired).
    """
    cfg = config or NovelConfig.load()
    return {
        "novel_state": FileNovelStateDriver(cfg),
        "novel_format": _select_format_driver(cfg),
    }


def _select_format_driver(_cfg):
    """Pick the production format driver based on what's importable.

    Spec 124 Slice 1: returns `FakeFormatDriver` always. Slice 2 will try
    `PandocFormatDriver` first and fall back to the fake when shell-outs
    aren't available (typed `DEPENDENCY_MISSING` on call).
    """
    return FakeFormatDriver()


class FakeFormatDriver:
    """Deterministic in-memory FormatDriver — Spec 124.

    Returns predictable paths from input hashes; records the call log so
    tests can assert "what was exported" without writing binaries. Mirrors
    `FakeAudioDriver`'s pattern: zero pandoc / wkhtmltopdf / weasyprint
    required in CI.

    The "fake" returns a path; tests can assert the path is shaped right
    and that the call landed, without the file actually existing on disk.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def available_formats(self) -> list[str]:
        return ["epub", "pdf", "docx"]

    def _record(self, fmt: str, manuscript: str, meta: dict) -> str:
        import hashlib
        h = hashlib.sha256(manuscript.encode("utf-8")).hexdigest()[:12]
        slug = (meta.get("slug") or meta.get("title") or "manuscript"
                ).lower().replace(" ", "-")
        path = f"/tmp/agency-novel-format/{slug}-{h}.{fmt}"
        self.calls.append({
            "format": fmt, "path": path, "meta": dict(meta),
            "manuscript_bytes": len(manuscript),
            "manuscript_sha256": h,
        })
        return path

    def to_epub(self, manuscript_md: str, meta: dict) -> str:
        return self._record("epub", manuscript_md, meta)

    def to_pdf(self, manuscript_md: str, meta: dict) -> str:
        return self._record("pdf", manuscript_md, meta)

    def to_docx(self, manuscript_md: str, meta: dict) -> str:
        return self._record("docx", manuscript_md, meta)
