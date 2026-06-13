# agency-scaffold: v1
"""music cloud cluster — object-store publish via the CloudDriver.

``publish_asset`` (the CloudDriver banner verb from 007) — the generic
object-store publish entry point. Promo-specific wrappers
(publish_sheet_music · upload_promo_video · r2_delete · r2_list) live in the
PromoCluster alongside the promo surface. Relocated VERBATIM from ``_main.py``
per Spec 094 design §"Module layout" (Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult

from ._base import _MusicBase


class CloudCluster(_MusicBase):
    # ───────── cloud cluster (effect via CloudDriver) ─────────
    @verb(role="effect")
    @requires_driver("music_cloud", as_="cloud")
    def publish_asset(self, album: str, key: str, body: str = "",
                      *, cloud) -> ToolResult:
        """Publish an album asset to object storage via the CloudDriver (effect).

        Returns ``DEPENDENCY_MISSING`` (typed) when the cloud backend is
        unconfigured — never a stringly-typed raise.
        Inputs: album, key, body.
        Returns: ``{key, bytes}`` on success.
        chain_next: ``music.verify_streaming`` once distributor links propagate.
        """
        res = cloud.r2_put(key, body.encode())
        if not res.get("ok"):
            return ToolResult.failure(res.get("error", "INTERNAL"),
                                      f"cloud put failed for {key!r}")
        return ToolResult.success(data={"key": key, "bytes": res.get("bytes", 0)})
