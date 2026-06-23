"""Keep the INSTALLED ``agency`` package in step with the source checkout the MCP
server runs in — the durable half of "update the installed version every time"
(Spec 302 Slice 3).

The pipx-only install doctrine (Spec 055/065) INTENDS an editable install
(``pipx install --editable …``) so the running server always imports the live
source. When an environment instead holds a NON-editable COPY (a frozen
site-packages snapshot) while the server's cwd is a newer checkout, the installed
files drift: ``agency_reload`` re-imports stale disk and never sees new
capabilities — the exact stale-MCP blocker the fresh-agent-onboarding-proof loop
hit (live ``agency_welcome`` stuck at 30 caps while the source tree had 36).

:func:`sync_installed_from_source` mirrors the source ``agency/`` tree onto the
installed location so a reload — and every future server start — reads current
code. It is a no-op for an editable install (``source == installed``) or when the
server is not running inside a source checkout. :meth:`agency.engine.Engine.reload`
calls it FIRST: capability-only changes then hot-reload in process as before,
while CORE-module changes (which an in-process reload cannot safely swap — they
would skew against already-imported objects, e.g. ``skill.phase`` gaining a new
kwarg) set ``core_changed`` so ``reload`` asks for a restart instead of
corrupting the live process.
"""
from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

_SKIP_DIRS = {"__pycache__"}
_SKIP_SUFFIXES = {".pyc", ".pyo"}


def installed_package_dir() -> Path:
    """Where the RUNNING ``agency`` package is imported from (the install)."""
    import agency
    return Path(agency.__file__).resolve().parent


def source_package_dir() -> Path | None:
    """The ``agency/`` package under the server's cwd when it is a SOURCE
    checkout distinct from the install; ``None`` when editable / absent."""
    src = (Path.cwd() / "agency").resolve()
    return src if (src / "__init__.py").is_file() else None


def _tracked_files(root: Path) -> dict[str, Path]:
    """Relative-path → file map of the package tree, skipping byte-caches."""
    out: dict[str, Path] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix in _SKIP_SUFFIXES:
            continue
        out[str(rel)] = p
    return out


def sync_installed_from_source(installed: Path | None = None,
                               source: Path | None = None) -> dict:
    """Mirror ``source`` → ``installed`` (copy new/changed, drop vanished files).

    Returns ``{synced, reason, installed, source, changed, core_changed}``:
    ``synced`` is True iff any file was copied or removed; ``core_changed`` is
    True when any mirrored path is OUTSIDE ``capabilities/`` — the signal that an
    in-process reload is insufficient and a server restart is needed. No-op
    (``synced=False``) for an editable install (same path), when the server is
    not in a source checkout, or when the install dir is not writable.
    """
    installed = installed or installed_package_dir()
    source = source if source is not None else source_package_dir()
    base = {"installed": str(installed) if installed else None,
            "source": str(source) if source else None,
            "changed": [], "core_changed": False, "synced": False}
    if source is None:
        return {**base, "reason": "no-source-checkout"}
    if source == installed:
        return {**base, "reason": "editable-install"}
    try:
        src_files = _tracked_files(source)
        dst_files = _tracked_files(installed)
        changed: list[str] = []
        for rel, sp in src_files.items():
            dp = installed / rel
            if not dp.exists() or not filecmp.cmp(sp, dp, shallow=False):
                dp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, dp)
                changed.append(rel)
        for rel in dst_files:
            if rel not in src_files:
                (installed / rel).unlink()
                changed.append(rel)
    except OSError as exc:                                       # noqa: BLE001
        return {**base, "reason": f"not-writable: {exc}"}
    core_changed = any(Path(c).parts[0] != "capabilities" for c in changed)
    return {"installed": str(installed), "source": str(source),
            "changed": sorted(changed), "synced": bool(changed),
            "reason": "mirrored" if changed else "already-current",
            "core_changed": core_changed}
