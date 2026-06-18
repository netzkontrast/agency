"""novel.clusters._base — shared NovelCapability infrastructure (Spec 286 P3).

The production-driver auto-wiring (Spec 121) + NOT_FOUND guards extracted
verbatim from ``novel/_main.py`` into a base mixin every cluster mixin and
the composed ``NovelCapability`` inherit. Behaviour-frozen relocation.
"""
from __future__ import annotations

from agency.toolresult import ToolResult, Codes


class NovelBase:
    """Shared infrastructure for the novel cluster mixins.

    Holds the lazy production-driver auto-wiring (Spec 121) + the
    ``_require_novel`` / ``_require_chapter`` NOT_FOUND guards used across
    multiple clusters. Cluster mixins inherit these via the composed
    ``NovelCapability`` MRO; ``CapabilityBase`` provides ``ctx`` + the base
    ``_require_drv`` resolver this overrides.
    """

    # ───────── Spec 121: lazy production-driver auto-wiring ─────────
    # AGENCY-DRIFT: novel driver set — mirror production_drivers() keys
    # and the diagnose-wanted list when adding novel drivers (text/format/etc).
    _NOVEL_DRIVER_NAMES = ("novel_state", "novel_format")

    def _production_enabled(self) -> bool:
        """Auto-wiring only fires under the production MCP runtime
        (`agency/__main__.py` flips ``engine._novel_production = True``).
        Unit tests build a bare Engine without the flag and keep the typed
        ``DEPENDENCY_MISSING`` contract — bounded blast radius."""
        return self.ctx.production_enabled("novel")

    def _autowire_novel_drivers(self) -> None:
        """Build ``production_drivers(NovelConfig.bootstrap())`` ONCE and
        register the bundle on first miss. ``NovelConfig.bootstrap()``
        writes the default `.agency/novel-config.yaml` + creates the
        content root when a fresh repo has none.
        """
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return
        if all(reg.has(n) for n in self._NOVEL_DRIVER_NAMES):
            return
        from ..config import NovelConfig
        from ..drivers_production import production_drivers
        bundle = production_drivers(NovelConfig.bootstrap())
        for n, drv in bundle.items():
            if not reg.has(n):
                reg.register(n, drv)

    def _require_drv(self, name: str):  # type: ignore[override]
        """Auto-wire production drivers on first miss before falling
        back to the base typed-failure resolver (Spec 121 mirrors Spec 117)."""
        if name in self._NOVEL_DRIVER_NAMES:
            reg = self.ctx.drivers
            if reg is not None and not reg.has(name):
                self._autowire_novel_drivers()
        return super()._require_drv(name)

    def _maybe_state_driver(self):
        """Return the wired novel_state driver or None when production
        isn't on. Used by verbs that have a graph-only default with an
        opportunistic disk side-effect (CLAUDE.md rule 2)."""
        return self._maybe_driver("novel_state")

    def _maybe_format_driver(self):
        """Spec 124 — opportunistic FormatDriver. When production is on
        (FakeFormatDriver lands by default; PandocFormatDriver in Slice 2),
        export verbs hand the manuscript markdown to the driver. Otherwise
        export verbs return DEPENDENCY_MISSING typed failure."""
        return self._maybe_driver("novel_format")

    def _maybe_driver(self, name: str):
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return None
        if not reg.has(name):
            self._autowire_novel_drivers()
        if reg.has(name):
            return reg.get(name)
        return None

    def _require_novel(self, novel_id: str) -> tuple[dict | None, ToolResult | None]:
        """NOT_FOUND guard shared by every verb taking a novel_id.

        Returns ``(node, fail)``: when the novel exists, ``node`` is the
        graph payload and ``fail`` is ``None``; when missing, ``node`` is
        ``None`` and ``fail`` is a typed ToolResult.failure the caller
        forwards.

        One source of truth for the NOT_FOUND message — keeps the error
        string drift-free across create_chapter, chapter_report, and
        render_manuscript (which previously held a hand-rolled copy).
        """
        node = self.ctx.recall(novel_id)
        if node is None:
            return None, ToolResult.failure(
                Codes.NOT_FOUND, f"novel_id={novel_id!r} not found")
        return node, None

    def _require_chapter(self, chapter_id: str) -> tuple[dict | None, ToolResult | None]:
        """NOT_FOUND guard for verbs taking a chapter_id — mirrors `_require_novel`."""
        node = self.ctx.recall(chapter_id)
        if node is None:
            return None, ToolResult.failure(
                Codes.NOT_FOUND, f"chapter_id={chapter_id!r} not found")
        return node, None
