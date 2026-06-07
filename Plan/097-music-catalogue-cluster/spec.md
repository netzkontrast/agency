---
spec_id: "097"
slug: music-catalogue-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "093"]
affects:
  - agency/capabilities/music/clusters/catalogue.py
  - agency/capabilities/music/drivers.py        # DBDriver + CloudDriver(stdlib) extensions
  - agency/capabilities/music/ontology.py       # Tweet enums, streaming refs
  - agency/capabilities/music/migrations/db_init.py  # one-shot install script
  - tests/test_music_catalogue.py
domain: music / catalogue / db
wave: 7
parent_spec: "093"
---

# Spec 097 — Music Catalogue Cluster

## Why

The catalogue cluster is the **DBDriver + CloudDriver-stdlib showcase**: tweet
DB CRUD (PostgreSQL via psycopg2) + streaming-URL verification (stdlib urllib,
no boto3). It's the cluster that proves Spec 002's typed-named-method discipline
on a *real* database — psycopg2-shaped cursor against fake rows in tests, real
psycopg2 in production.

bitwize ships 14 catalogue tools (8 db_* + 4 streaming + 2 promo state). 097
ports them into a coherent CRUD-shaped cluster.

This cluster is also where the **PostgreSQL extra** lands: `[music-db]` carries
psycopg2-binary; CI runs zero Postgres via the fake DBDriver. The pattern is
the same one already proven by 007's `db_create_tweet` test — the fake's
psycopg2-shaped cursor (`cursor.execute(sql, params)`, `cursor.fetchall()`,
`cursor.close()`) matches the real API surface, so the verb code is identical
across fake and real.

## Done When

- [ ] **Verbs ship:** 14 catalogue verbs (see "Verb manifest"), covering all
  bitwize DB + streaming tools.
- [ ] **DBDriver extended** with 7 new methods; psycopg2-shaped cursor fake
  covers all of them.
- [ ] **CloudDriver(stdlib) extended** with 1 new method (`url_head` exists;
  add `update_streaming_url` that writes URL into markdown state via StateDriver).
- [ ] **Artefact schemas added:** `tweet-record`, `streaming-verify`,
  `catalogue-snapshot`.
- [ ] **Walkable skill: `tweet-curation`** — 4-phase workflow (draft → schedule
  → publish → archive) with computed gate on schedule (validates content).
- [ ] **Walkable skill: `streaming-verify`** — 3-phase workflow (collect →
  HEAD-check → record-results), driver-only, no human gate.
- [ ] **`db_init.py` migration** under `migrations/` — one-shot schema
  installer for fresh Postgres binding (carries the bitwize schema.sql verbatim
  + the tweet table indexes).
- [ ] **`scripts/test-cap music_catalogue`** Green; runs in < 6 seconds with
  ZERO Postgres host required.
- [ ] **No regression on `db_create_tweet`, `verify_streaming`** (preserved
  from 007).
- [ ] **`TODO.md` updated;** parent (093) row notes child shipped.

## Verb manifest

| # | Verb | Role | Driver | bitwize tool absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `db_create_tweet` | effect | DBDriver | `db_create_tweet` | kept from 007 |
| 2 | `db_update_tweet` | effect | DBDriver | `db_update_tweet` | |
| 3 | `db_delete_tweet` | effect | DBDriver | `db_delete_tweet` | |
| 4 | `db_list_tweets` | transform | DBDriver | `db_list_tweets` | filters/limit |
| 5 | `db_search_tweets` | transform | DBDriver | `db_search_tweets` | text search |
| 6 | `db_get_tweet_stats` | transform | DBDriver | `db_get_tweet_stats` | aggregate counts |
| 7 | `db_sync_album` | effect | DBDriver+StateDriver | `db_sync_album` | syncs tweet rows ↔ markdown promo dir |
| 8 | `verify_streaming` | transform | CloudDriver | `verify_streaming_urls` | kept from 007 |
| 9 | `update_streaming_url` | effect | CloudDriver+StateDriver | `update_streaming_url` | records URL after release |
| 10 | `get_streaming_urls` | transform | StateDriver | `get_streaming_urls` | reads recorded URLs |
| 11 | `get_promo_status` | transform | StateDriver | `get_promo_status` | per-album promo state |
| 12 | `get_promo_content` | transform | StateDriver | `get_promo_content` | reads promo dir |
| 13 | `extract_links` | transform | TextDriver | `extract_links` | finds URLs in track files |
| 14 | `catalogue_status` | transform | DBDriver | (composite of stats) | kept from 007 |

**Total: 14 verbs covering 14 bitwize tools.**

> Note: bitwize `extract_links` lives in the database/text helpers — placed
> here because it feeds streaming URL discovery. Could equally land in 095
> (lyrics) if cleaner; 097 owns it via association with the catalogue.

## Design

### DBDriver method delta

```python
class DBDriver(Boundary):
    # existing 007 methods preserved
    def cursor(self) -> Cursor: ...        # psycopg2-shaped

    # new methods (097)
    def create_tweet(self, album: str, body: str, scheduled_at: str,
                     platform: str = "x") -> int: ...
    def update_tweet(self, tweet_id: int, fields: dict) -> None: ...
    def delete_tweet(self, tweet_id: int) -> None: ...
    def list_tweets(self, album: str = "", status: str = "",
                    limit: int = 100) -> list[dict]: ...
    def search_tweets(self, query: str, limit: int = 50) -> list[dict]: ...
    def tweet_stats(self, album: str = "") -> dict: ...
    def sync_album_tweets(self, album: str, tweets: list[dict]) -> dict: ...
```

The fake holds a dict-keyed in-memory store with auto-incremented IDs;
`cursor()` returns a shim with `execute(sql, params)`, `fetchall()`,
`fetchone()`, `close()`. SQL strings are matched against a small router
(SELECT/INSERT/UPDATE/DELETE) — the same pattern proven in 007.

### CloudDriver(stdlib) method delta

```python
class CloudDriver(Boundary):
    # existing 007 methods preserved
    def url_head(self, url: str) -> int: ...     # stdlib urllib HEAD→GET

    # new methods (097, stdlib half only — boto3 half lives in 098)
    # (No new methods needed — update_streaming_url uses url_head for verify
    # + StateDriver.put for persistence.)
```

### Primary actors (panel-added, iteration 1 / Cockburn)

- `tweet-curation` — **Primary actor: agent** (drafts + schedules); human-
  curator signs off implicitly via the schedule gate (which validates body
  + timing).
- `streaming-verify` — **Primary actor: agent** (routine ops); no human
  gate.

### Failure modes (panel-added, iteration 1 / Nygard)

| Boundary call | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| Postgres unreachable | `psycopg2.OperationalError` | raises `BoundaryFailed` | `ToolResult.failure(BOUNDARY_FAILED, "DB unreachable")` |
| Postgres auth failed | `psycopg2.OperationalError` | raises | `ToolResult.failure(DEPENDENCY_MISSING, "DB auth failed — check `[music-db]` config")` |
| Postgres schema missing (tweets table) | `psycopg2.errors.UndefinedTable` | raises | `ToolResult.failure(BOUNDARY_FAILED, "schema not initialized — run db_init")` |
| Streaming URL HEAD timeout (default 5s) | `urllib.error.URLError` | returns 0 | `ToolResult.success(dead=[url])` (the verb records "dead" — not failure; the URL is provably unreachable) |
| Streaming URL invalid scheme (`file:`, `javascript:`) | rejected at SSRF guard | returns 0 | `ToolResult.success(dead=[url])` (SSRF guard preserves bitwize's safety) |
| `psycopg2` import fails | `ImportError` at driver init | driver `__init__` raises | engine bootstrap fails with `DependencyMissing("[music-db]")` |

### Walkable skill: `tweet-curation`

```python
TWEET_CURATION_SKILL = {
    "name": "tweet-curation",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft",
         "produces": ["tweet_body", "tweet_platform"]},
        {"index": 2, "name": "schedule",
         "produces": ["scheduled_at_set"],
         "gate": "computed", "gate_verb": "music.tweet_schedule_gate"},
        {"index": 3, "name": "publish",
         "produces": ["posted"]},
        {"index": 4, "name": "archive",
         "produces": ["archived"]},
    ],
}
```

The `tweet_schedule_gate` verb validates body length (platform-specific),
schedules-in-the-future, and album-status (must be `mastered` or
`released`).

### Walkable skill: `streaming-verify`

```python
STREAMING_VERIFY_SKILL = {
    "name": "streaming-verify",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "collect",
         "produces": ["urls_to_check"]},
        {"index": 2, "name": "head-check",
         "produces": ["live_urls", "dead_urls"]},
        {"index": 3, "name": "record",
         "produces": ["verification_recorded"]},
    ],
}
```

No human gate — this is a routine ops workflow that runs after release.

### Artefact schemas added

```python
CATALOGUE_ARTEFACTS = [
    "tweet-record",         # one tweet's insert row (provenance)
    "streaming-verify",     # the live/dead report
    "catalogue-snapshot",   # composite of stats for audit
]
```

### Postgres schema (carried verbatim from bitwize)

`agency/capabilities/music/migrations/db_init.py` runs the bitwize `schema.sql`
adapted to the agency music tweet table:

```sql
CREATE TABLE IF NOT EXISTS tweets (
    id SERIAL PRIMARY KEY,
    album TEXT NOT NULL,
    body TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'draft',
    platform TEXT NOT NULL DEFAULT 'x',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS tweets_album_idx ON tweets(album);
CREATE INDEX IF NOT EXISTS tweets_status_idx ON tweets(status);
CREATE INDEX IF NOT EXISTS tweets_scheduled_at_idx ON tweets(scheduled_at);
```

The migration is **not a verb** — it's an install-time script invoked
manually OR by a future `agency music init-db` shell template (Spec 075).

## Test plan

```python
# tests/test_music_catalogue.py — ~12 tests
def test_catalogue_cluster_discovers_all_verbs(): ...
def test_db_create_tweet_returns_id_and_records_artefact(): ...
def test_db_update_tweet_modifies_row(): ...
def test_db_delete_tweet_removes_row(): ...
def test_db_list_tweets_filters_by_album_and_status(): ...
def test_db_search_tweets_returns_text_match(): ...
def test_db_get_tweet_stats_aggregates_counts(): ...
def test_db_sync_album_reconciles_db_with_markdown_state(): ...
def test_verify_streaming_returns_live_and_dead_urls(): ...
def test_update_streaming_url_persists_via_state_driver(): ...
def test_get_promo_status_aggregates_per_album(): ...
def test_catalogue_verb_fails_typed_when_db_driver_missing(): ...
```

## Open questions

1. **`db_init` as a verb?** No — it's a one-shot install op. Becomes a
   migration script + (optionally) a shell template (Spec 075).
2. **Schema migrations beyond initial?** Reuse Spec 040's dogfood ledger — each
   migration records a graph node `MigrationRun`. Deferred to followup.
3. **Tweet platform enum — closed or open?** Closed (`x`, `threads`,
   `instagram`, `tiktok`, `bluesky`) — adding a platform is a small change;
   open invites typo bugs.
4. **Extract_links — should be in 095?** Could be — but bitwize associates it
   with database/streaming workflows. 097 owns it; cross-cluster reuse is fine
   per Spec 047 patterns.

## Followup

(Populated when the PR ships.)
