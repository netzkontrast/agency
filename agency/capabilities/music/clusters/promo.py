# agency-scaffold: v1
"""music promo cluster — promo copy · object-store publish · release package.

Spec 098 — 7 promo verbs + 1 composite gate verb (promo-review), plus the 007
promo verb (promo_copy). Object-store ops route through the CloudDriver.
Relocated VERBATIM from ``_main.py`` per Spec 094 design §"Module layout"
(Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult, Codes

from ._base import _MusicBase


class PromoCluster(_MusicBase):
    # ───────── content/promo cluster (act, produces promo-copy) ─────────
    @verb(role="act")
    def promo_copy(self, album: str, angle: str = "") -> ToolResult:
        """Draft promotional copy for an album (act, produces a ``promo-copy`` artefact).

        Inputs: album, angle.
        Returns: ``{result, artefact}`` where artefact.kind = ``promo-copy``.
        chain_next: ``music.publish_asset`` the copy.
        """
        body = f"🎵 {album} — {angle or 'out now'}. Stream it everywhere.\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-copy", "album": album, "angle": angle, "body": body}})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 098 — promo cluster: 7 NEW verbs + 1 composite gate verb
    # (3 already shipped: promo_copy from 007, publish_asset from 007,
    # generate_promo_videos from 096)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def promo_review(self, body: str,
                      platform: str = "x") -> ToolResult:
        """Rule-based scoring of promo copy quality (transform).

        Scores body 0-100 on: length-in-window per platform, has-CTA
        (call to action), no-explicit-words.

        Inputs: body, platform.
        Returns: ``{score, findings, max_length, platform}``.
        chain_next: ``music.promo_review_gate`` for an admissible threshold.
        """
        _LIMITS = {"x": 280, "twitter": 280, "threads": 500,
                   "bluesky": 300, "instagram": 2200, "tiktok": 2200,
                   "facebook": 63206, "youtube": 5000}
        max_length = _LIMITS.get(platform.lower(), 280)
        findings = []
        score = 100
        if not body.strip():
            findings.append({"kind": "empty", "severity": "fail"})
            score = 0
        if len(body) > max_length:
            findings.append({"kind": "over_length",
                             "actual": len(body), "max": max_length,
                             "severity": "fail"})
            score -= 40
        cta_words = ("stream", "listen", "watch", "buy", "out now",
                     "available", "preorder")
        if not any(w in body.lower() for w in cta_words):
            findings.append({"kind": "no_cta", "severity": "warn"})
            score -= 15
        if any(w in body.lower() for w in ("fuck", "shit", "damn",
                                            "bitch", "ass")):
            findings.append({"kind": "explicit", "severity": "warn"})
            score -= 20
        # Spec 119 (promo layer): a project-DNA forbidden name must not reach
        # public copy either. Reuse the lyrics name-exposure scan against the
        # configured roster; a hit is a hard miss (severity fail + heavy
        # penalty) so `promo_review_gate`'s score threshold blocks it. Empty
        # roster → no hits → no-op for rosterless projects.
        from ..config import MusicConfig
        name_hits = self._name_exposure_hits(
            body, MusicConfig.load().name_exposure_blocklist)
        if name_hits:
            findings.append({"kind": "name_exposure",
                             "names": [h["name"] for h in name_hits],
                             "severity": "fail"})
            score -= 50
        return ToolResult.success(data={
            "score": max(0, score), "findings": findings,
            "max_length": max_length, "platform": platform})

    @verb(role="effect")
    @requires_driver("music_cloud", as_="cloud")
    def publish_sheet_music(self, album: str, key: str,
                              body: bytes = b"", *, cloud) -> ToolResult:
        """Publish a sheet-music PDF to object storage (effect).

        Sheet-music-specific wrapper around ``publish_asset`` that records a
        ``published-asset`` artefact tagged ``sheet-music``.

        Inputs: album, key (the R2 object key), body (PDF bytes).
        Returns: ``{result, artefact}`` published-asset artefact.
        chain_next: ``music.r2_signed_url`` to share.
        """
        res = cloud.r2_put(key, body or b"\x00")
        if not res.get("ok"):
            return ToolResult.failure(res.get("error", "INTERNAL"),
                                      f"cloud put failed for {key!r}")
        return ToolResult.success(data={"result": f"published:{key}",
                                        "artefact": {
                                            "kind": "published-asset",
                                            "album": album, "key": key,
                                            "bytes": res.get("bytes", 0),
                                            "asset_kind": "sheet-music"}})

    @verb(role="effect")
    @requires_driver("music_cloud", as_="cloud")
    def upload_promo_video(self, album: str, key: str,
                            body: bytes = b"", *, cloud) -> ToolResult:
        """Upload a promo video to object storage (effect).

        Promo-video-specific wrapper that records a ``published-asset``
        artefact tagged ``promo-video``.

        Inputs: album, key (R2 object key), body (video bytes).
        Returns: ``{result, artefact}`` published-asset artefact.
        chain_next: ``music.r2_signed_url`` to share.
        """
        res = cloud.r2_put(key, body or b"\x00")
        if not res.get("ok"):
            return ToolResult.failure(res.get("error", "INTERNAL"),
                                      f"cloud put failed for {key!r}")
        return ToolResult.success(data={"result": f"uploaded:{key}",
                                        "artefact": {
                                            "kind": "published-asset",
                                            "album": album, "key": key,
                                            "bytes": res.get("bytes", 0),
                                            "asset_kind": "promo-video"}})

    @verb(role="effect")
    @requires_driver("music_cloud", as_="cloud")
    def r2_delete(self, key: str, *, cloud) -> ToolResult:
        """Retract a published asset from object storage (effect).

        Inputs: key.
        Returns: ``{key, deleted}``.
        chain_next: ``music.r2_list`` to verify.
        """
        res = cloud.r2_delete(key)
        if not res.get("ok"):
            return ToolResult.failure(res.get("error", "INTERNAL"),
                                      f"cloud delete failed for {key!r}")
        return ToolResult.success(data={"key": key,
                                        "deleted": res.get("deleted", False)})

    @verb(role="transform")
    @requires_driver("music_cloud", as_="cloud")
    def r2_list(self, prefix: str = "", *, cloud) -> ToolResult:
        """List published assets by key prefix (transform).

        Inputs: prefix.
        Returns: ``{prefix, objects: [{key, bytes}], count}``.
        chain_next: ``music.r2_delete`` for cleanup.
        """
        objects = cloud.r2_list(prefix=prefix)
        return ToolResult.success(data={"prefix": prefix,
                                        "objects": objects,
                                        "count": len(objects)})

    @verb(role="act")
    def release_package(self, album: str,
                         assets: list[str]) -> ToolResult:
        """Record a release package — gathers all release artefact paths (act).

        Inputs: album, assets (list of artefact keys / paths to bundle).
        Returns: ``{result, artefact}`` promo-album-package artefact.
        chain_next: ``music.release-publish`` skill walk to upload + announce.
        """
        body = (f"# Release package: {album}\n"
                f"asset count: {len(assets)}\n"
                f"assets:\n" + "\n".join(f"- {a}" for a in assets))
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-album-package", "album": album,
            "assets": list(assets), "body": body}})

    # ── 1 composite gate verb — called by the promo-pass skill ──

    @verb(role="effect")
    def promo_review_gate(self, lifecycle_id: str, body: str,
                            platform: str = "x",
                            min_score: int = 70) -> ToolResult:
        """Computed promo-review gate (effect) — composes ``promo_review`` scoring.

        Passes iff ``promo_review.score >= min_score``. Records the score on
        gate evidence so audit knows the threshold + actual.

        Inputs: lifecycle_id, body, platform, min_score (default 70).
        Returns: ``{gate, passed, score, findings}`` or typed GATE_FAILED.
        chain_next: on failure, revise the copy + re-call ``promo_review_gate``.
        """
        review = self.promo_review(body=body, platform=platform).data
        passed = review["score"] >= min_score
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="promo-review", passed=passed,
                      evidence=(f"score={review['score']} >= {min_score}"
                                if passed else
                                f"score={review['score']} < {min_score}"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"promo-review: score={review['score']} < {min_score}")
        return ToolResult.success(data={"gate": "promo-review",
                                        "passed": True,
                                        "score": review["score"],
                                        "findings": review["findings"]})
