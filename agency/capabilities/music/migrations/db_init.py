"""Spec 097 — one-shot schema installer for the catalogue cluster's PostgreSQL backend.

Carries the bitwize ``schema.sql`` verbatim + the tweet table indexes that the
DBDriver methods (``create_tweet`` / ``list_tweets`` / ``search_tweets``) need
for sub-second response at scale. Run once when binding to a fresh Postgres
host via the ``[music-db]`` extra.

Usage::

    from agency.capabilities.music.migrations.db_init import init_schema

    # In production (real DBDriver with psycopg2 connection):
    init_schema(my_db_driver)
"""
from __future__ import annotations


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tweets (
    id           SERIAL PRIMARY KEY,
    album        TEXT NOT NULL,
    body         TEXT NOT NULL,
    platform     TEXT NOT NULL DEFAULT 'x',
    status       TEXT NOT NULL DEFAULT 'draft',
    scheduled_at TIMESTAMPTZ,
    posted_at    TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tweets_album        ON tweets(album);
CREATE INDEX IF NOT EXISTS idx_tweets_status       ON tweets(status);
CREATE INDEX IF NOT EXISTS idx_tweets_album_status ON tweets(album, status);
CREATE INDEX IF NOT EXISTS idx_tweets_scheduled    ON tweets(scheduled_at);

-- Tracks catalogue (the 007 baseline; agency uses a graph but production
-- often wants a flat read-side for analytics dashboards).
CREATE TABLE IF NOT EXISTS tracks (
    slug         TEXT PRIMARY KEY,
    album        TEXT NOT NULL,
    title        TEXT,
    status       TEXT NOT NULL DEFAULT 'draft',
    explicit     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album);
"""


def init_schema(db_driver) -> dict:
    """Apply the catalogue schema via the DBDriver's cursor.

    Inputs: db_driver (a DBDriver-shaped object — real or fake).
    Returns: ``{statements_executed, ok}``.
    """
    statements = [s.strip() for s in _SCHEMA_SQL.split(";") if s.strip()]
    cur = db_driver.cursor()
    for stmt in statements:
        cur.execute(stmt, ())
    cur.close()
    return {"statements_executed": len(statements), "ok": True}
