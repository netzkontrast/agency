"""Spec 032 §B — capability folder loader.

Discovers and loads per-capability templates + schemas from on-disk
folders declared via the RenderTemplates / ArtefactSchemas dataclasses
on CapabilityBase.

Path-safe (os.path.realpath check; rejects '..' AND symlinks escaping
the capability folder), kebab-case filename rule, empty-folder rule.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from string import Template

# Kebab-case rule: filename stem MUST match this pattern.
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Recognized template file extensions.
_TEMPLATE_EXTS = (".md", ".tpl", ".sh")


def _safe_resolve(file_path: Path, folder: Path) -> Path:
    """Resolve file_path's realpath and verify it stays inside folder's realpath.

    Defends against '..' traversal AND symlinks escaping the folder.
    Returns the resolved path; raises ValueError on escape.
    """
    real_file = Path(os.path.realpath(file_path))
    real_folder = Path(os.path.realpath(folder))
    try:
        real_file.relative_to(real_folder)
    except ValueError:
        raise ValueError(
            f"path safety: {file_path!r} resolves outside the capability "
            f"folder {folder!r} (rejects '..' AND escaping symlinks)"
        )
    return real_file


def _check_kebab(stem: str, full_path: Path) -> None:
    if not _KEBAB_RE.match(stem):
        raise ValueError(
            f"filename stem {stem!r} in {full_path!r} must be kebab-case "
            f"(^[a-z0-9]+(-[a-z0-9]+)*$); rename or fix"
        )


def _load_templates_from(folder: Path) -> dict[str, Template]:
    if not folder.exists():
        raise ValueError(
            f"templates folder {folder!r} does not exist — declared but "
            f"the directory is missing"
        )
    out: dict[str, Template] = {}
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        if path.suffix not in _TEMPLATE_EXTS:
            continue
        real = _safe_resolve(path, folder)
        # Path safety check uses realpath; dict key uses VISIBLE filename
        # (path.stem, not real.stem) so two visible names symlinked to the
        # same real file load as two distinct entries — the user-facing
        # name is the canonical key.
        _check_kebab(path.stem, path)
        out[path.stem] = Template(real.read_text())
    if not out:
        raise ValueError(
            f"templates folder {folder!r} is empty (no *.md / *.tpl / *.sh "
            f"files) — declared the contract but didn't fulfill it; "
            f"either ship at least one file OR set render_templates = None"
        )
    return out


def _load_schemas_from(folder: Path) -> dict[str, dict]:
    if not folder.exists():
        raise ValueError(
            f"schemas folder {folder!r} does not exist — declared but "
            f"the directory is missing"
        )
    out: dict[str, dict] = {}
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        if path.suffix != ".json":
            continue
        real = _safe_resolve(path, folder)
        # Visible filename for the dict key (see _load_templates_from rationale).
        _check_kebab(path.stem, path)
        try:
            content = json.loads(real.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(
                f"schema {path.stem!r} in {path!r} is invalid JSON: {e}"
            ) from e
        out[path.stem] = content
    if not out:
        raise ValueError(
            f"schemas folder {folder!r} is empty (no *.json files) — "
            f"declared the contract but didn't fulfill it; either ship at "
            f"least one file OR set artefact_schemas = None"
        )
    return out


def load_capability_folders(cap) -> tuple[dict, dict]:
    """Load (templates, schemas) for a capability.

    Inputs: cap (Capability or CapabilityBase subclass; functional-form
                 Capability has no render_templates/artefact_schemas attrs
                 — handled via getattr defaults).
    Returns: (templates_dict, schemas_dict).
    Raises ValueError on path-safety violation, kebab-case violation,
    missing folder, empty folder, or malformed JSON.
    """
    templates: dict = {}
    schemas: dict = {}

    rt = getattr(cap, "render_templates", None)
    if rt is not None:
        templates = _load_templates_from(Path(rt.folder))

    asch = getattr(cap, "artefact_schemas", None)
    if asch is not None:
        schemas = _load_schemas_from(Path(asch.folder))

    return templates, schemas
