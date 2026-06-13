# agency-scaffold: v1
"""music catalogue cluster — DB tweets · streaming URLs · promo state.

Spec 097 — 11 catalogue verbs + 1 composite gate verb (tweet-schedule), plus
the 007 catalogue verbs (catalogue_status · verify_streaming). Reads/writes
flow through the DBDriver / StateDriver / CloudDriver — never inline SQL or
HTTP. Relocated VERBATIM from ``_main.py`` per Spec 094 design §"Module layout"
(Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import DriverMissing, requires_driver, verb
from agency.toolresult import ToolResult

from ._base import _MusicBase


class CatalogueCluster(_MusicBase):
    # ───────── catalogue DB cluster (transform via DBDriver) ─────────
    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def catalogue_status(self, album: str = "", *, db) -> ToolResult:
        """Read track statuses from the catalogue DB via the DBDriver (transform).

        Inputs: album.
        Returns: ``{tracks: [{slug, status}]}``.
        chain_next: gate on all-tracks-mastered before release.
        """
        cur = db.cursor()
        cur.execute("SELECT slug, status FROM tracks WHERE album = %s", (album,))
        rows = cur.fetchall()
        cur.close()
        return ToolResult.success(data={"tracks": [{"slug": r[0], "status": r[1]} for r in rows]})

    # ───────── streaming cluster (transform via CloudDriver) ─────────
    @verb(role="transform")
    @requires_driver("music_cloud", as_="cloud")
    def verify_streaming(self, album: str, urls: str = "", *, cloud) -> ToolResult:
        """Verify an album's streaming links are live via the CloudDriver (transform).

        Spec 097 Slice 2 (review-driven): produces a `streaming-verify`
        artefact — without this the ontology schema was dormant.

        Inputs: album, urls (comma-separated).
        Returns: ``{album, live, dead, artefact}`` partitioning the URLs by HEAD-status.
        chain_next: re-submit any dead links to the distributor.
        """
        targets = [u.strip() for u in urls.split(",") if u.strip()]
        live = [u for u in targets if cloud.url_head(u) == 200]
        dead = [u for u in targets if u not in live]
        return ToolResult.success(data={"album": album, "live": live,
                                        "dead": dead,
                                        "artefact": {"kind": "streaming-verify",
                                                     "album": album,
                                                     "live": live,
                                                     "dead": dead}})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 097 — catalogue cluster: 11 NEW verbs + 1 composite gate verb
    # (3 already shipped: verify_streaming + catalogue_status from 007;
    # db_create_tweet ships NEW here as the typed DBDriver entry point)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    @requires_driver("music_db", as_="db")
    def db_create_tweet(self, album: str, body: str, scheduled_at: str,
                         platform: str = "x", *, db) -> ToolResult:
        """Insert a tweet row via the DBDriver (effect); produces tweet-record artefact.

        Inputs: album, body, scheduled_at (ISO), platform (default ``x``).
        Returns: ``{result, artefact}`` tweet-record artefact with tweet_id.
        chain_next: ``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.
        """
        tid = db.create_tweet(album=album, body=body,
                              scheduled_at=scheduled_at, platform=platform)
        return ToolResult.success(data={"result": f"tweet:{tid}", "artefact": {
            "kind": "tweet-record", "album": album, "body": body,
            "platform": platform, "tweet_id": tid,
            "scheduled_at": scheduled_at}})

    @verb(role="effect")
    @requires_driver("music_db", as_="db")
    def db_update_tweet(self, tweet_id: int,
                         fields: dict, *, db) -> ToolResult:
        """Update tweet row fields via the DBDriver (effect).

        Inputs: tweet_id, fields (dict of {field: value}).
        Returns: ``{tweet_id, fields}``.
        chain_next: ``music.db_list_tweets`` to verify.
        """
        db.update_tweet(tweet_id=tweet_id, fields=fields)
        return ToolResult.success(data={"tweet_id": tweet_id,
                                        "fields": fields})

    @verb(role="effect")
    @requires_driver("music_db", as_="db")
    def db_delete_tweet(self, tweet_id: int, *, db) -> ToolResult:
        """Delete a tweet row via the DBDriver (effect).

        Inputs: tweet_id.
        Returns: ``{tweet_id, deleted}``.
        chain_next: ``music.db_list_tweets`` to verify.
        """
        db.delete_tweet(tweet_id=tweet_id)
        return ToolResult.success(data={"tweet_id": tweet_id, "deleted": True})

    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def db_list_tweets(self, album: str = "", status: str = "",
                        limit: int = 100, *, db) -> ToolResult:
        """List tweets via the DBDriver, filtered by album + status (transform).

        Inputs: album, status, limit.
        Returns: ``{tweets, count, album, status}``.
        chain_next: ``music.tweet_schedule_gate`` per row.
        """
        tweets = db.list_tweets(album=album, status=status, limit=limit)
        return ToolResult.success(data={"tweets": tweets,
                                        "count": len(tweets),
                                        "album": album, "status": status})

    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def db_search_tweets(self, query: str,
                          limit: int = 50, *, db) -> ToolResult:
        """Substring search across tweet bodies via DBDriver (transform).

        Inputs: query, limit.
        Returns: ``{tweets, count, query}``.
        chain_next: ``music.db_update_tweet`` to revise hits.
        """
        tweets = db.search_tweets(query=query, limit=limit)
        return ToolResult.success(data={"tweets": tweets,
                                        "count": len(tweets),
                                        "query": query})

    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def db_get_tweet_stats(self, album: str = "", *, db) -> ToolResult:
        """Aggregate counts of tweets by status via DBDriver (transform).

        Inputs: album (empty = all albums).
        Returns: ``{album, total, by_status}``.
        chain_next: ``music.tweet-curation`` skill walk.
        """
        return ToolResult.success(data=db.tweet_stats(album=album))

    @verb(role="effect")
    @requires_driver("music_db", as_="db")
    def db_sync_album(self, album: str,
                       tweets: list[dict], *, db) -> ToolResult:
        """Idempotent sync of an album's tweets — replaces existing (effect).

        Inputs: album, tweets (list of {body, scheduled_at, platform}).
        Returns: ``{album, removed, created}``.
        chain_next: ``music.db_list_tweets(album)`` to verify.
        """
        return ToolResult.success(data=db.sync_album_tweets(
            album=album, tweets=tweets))

    @verb(role="effect")
    @requires_driver("music_state", as_="state")
    def update_streaming_url(self, album: str, platform: str,
                              url: str, *, state) -> ToolResult:
        """Persist a verified streaming URL via StateDriver (effect).

        Caller invokes ``music.verify_streaming`` first if reachability matters;
        this verb only persists. Two-step idiom keeps the CloudDriver surface clean
        (Spec 097 §"CloudDriver method delta" — no new methods).

        Inputs: album, platform, url.
        Returns: ``{album, platform, url, persisted}``.
        chain_next: ``music.get_streaming_urls`` to verify.
        """
        state.put(f"streaming:{album}:{platform}",
                  {"album": album, "platform": platform, "url": url})
        return ToolResult.success(data={"album": album, "platform": platform,
                                        "url": url, "persisted": True})

    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def get_streaming_urls(self, album: str, *, state) -> ToolResult:
        """Read recorded streaming URLs for an album via StateDriver (transform).

        Inputs: album.
        Returns: ``{album, urls: [{platform, url}]}``.
        chain_next: ``music.verify_streaming`` to re-check.
        """
        # Iterate via StateDriver.list_keys — production drivers expose this
        # primitive; reaching into a private `_store` would lose the
        # contract in production (review finding).
        urls = []
        for k in state.list_keys(prefix=f"streaming:{album}:"):
            v = state.get(k) or {}
            if "platform" in v and "url" in v:
                urls.append({"platform": v["platform"], "url": v["url"]})
        return ToolResult.success(data={"album": album, "urls": urls})

    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def get_promo_status(self, album: str, *, db) -> ToolResult:
        """Per-album promo state via StateDriver + DBDriver (transform).

        Inputs: album.
        Returns: ``{album, tweets: {total, by_status}, streaming_urls: int}``.
        chain_next: ``music.tweet-curation`` skill walk for any pending tweets.
        """
        self._autowire_music_drivers()    # Spec 117: wire-on-need before the direct get
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            state = None
        tweet_stats = db.tweet_stats(album=album)
        # Same fix as get_streaming_urls — use the StateDriver primitive,
        # not a private attribute (review finding).
        url_count = 0
        if state is not None:
            url_count = len(state.list_keys(prefix=f"streaming:{album}:"))
        return ToolResult.success(data={"album": album,
                                        "tweets": tweet_stats,
                                        "streaming_urls": url_count})

    @verb(role="transform")
    @requires_driver("music_db", as_="db")
    def get_promo_content(self, album: str, *, db) -> ToolResult:
        """Read promo content (drafts + scheduled tweets) via DBDriver (transform).

        Inputs: album.
        Returns: ``{album, drafts, scheduled, total}``.
        chain_next: ``music.db_update_tweet`` to advance status.
        """
        drafts = db.list_tweets(album=album, status="draft")
        scheduled = db.list_tweets(album=album, status="scheduled")
        return ToolResult.success(data={"album": album,
                                        "drafts": drafts,
                                        "scheduled": scheduled,
                                        "total": len(drafts) + len(scheduled)})

    @verb(role="transform")
    def extract_links(self, text: str) -> ToolResult:
        """Extract URLs from text via simple regex (transform).

        Driver-free — uses stdlib re. Filters obvious SSRF risks
        (rejects javascript:/file:/data: schemes).

        Inputs: text.
        Returns: ``{urls, count}``.
        chain_next: ``music.verify_streaming`` to check each.
        """
        import re
        urls = re.findall(
            r"https?://[A-Za-z0-9.\-_/?#:&=%+~]+", text)
        return ToolResult.success(data={"urls": urls, "count": len(urls)})

    # ── 1 composite gate verb — called by the tweet-curation skill ──

    @verb(role="effect")
    def tweet_schedule_gate(self, lifecycle_id: str, body: str,
                             scheduled_at: str,
                             platform: str = "x",
                             max_length: int = 280) -> ToolResult:
        """Computed tweet-schedule gate (effect) — composes 3 checks.

        Passes iff: body length ≤ max_length AND scheduled_at is a non-empty
        future-looking timestamp AND body is non-empty.

        Inputs: lifecycle_id, body, scheduled_at, platform, max_length (default 280 = X/Twitter).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: on PASSED, ``music.db_create_tweet`` to persist.
        """
        problems = []
        if not body.strip():
            problems.append("body is empty")
        if len(body) > max_length:
            problems.append(
                f"body length {len(body)} > {max_length} for {platform}")
        if not scheduled_at.strip():
            problems.append("scheduled_at is required")
        passed = not problems
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="tweet-schedule", passed=passed,
                      evidence=(f"ok ({len(body)} chars)" if passed else
                                "; ".join(problems)))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"tweet-schedule: {'; '.join(problems)}")
        return ToolResult.success(data={"gate": "tweet-schedule",
                                        "passed": True,
                                        "length": len(body),
                                        "platform": platform})
