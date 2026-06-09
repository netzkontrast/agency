# agency-scaffold: v1
"""music drivers — the five external I/O boundaries the music capability reaches
through, as Spec-002 ``Driver`` protocols (Option B: typed, named methods; the
uniform contract is the RETURN TYPE via the wrapping verb, not a ``dispatch(op)``).

Each driver is a marker ``Boundary`` exposing its own typed methods (the ``jules.py``
``create/get/list`` shape). The capability resolves them via ``ctx.get_driver(name)``
(Spec 002's ``DriverRegistry``) — so the music capability edits NO file under
``agency/engine.py`` and a host binds real drivers while tests bind deterministic fakes.

This module ships BOTH the Protocols (the contract) and small deterministic FAKES (so
``tests/test_music_*`` runs with no ffmpeg / Postgres / R2 / network). A real
deployment registers production drivers via
``Engine(..., drivers={"music_state": RealStateDriver(), ...})``.

Migrated from ``examples/music_drivers.py`` under Spec 094 (music graduates
from ``examples/`` into a first-class cluster). The legacy module remains as a
deprecation re-export shim for one spec cycle.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from agency.capability import Driver


# ─────────────────────────── the five Driver protocols ───────────────────────────
@runtime_checkable
class StateDriver(Driver, Protocol):
    """Album/track state persistence (bitwize's unified state cache).

    Spec 094 Slice 2 extends the surface with 14 new methods that mirror the
    bitwize-music handler shape (graph-canonical in agency; on-disk reads/writes
    behind the driver). A real production driver writes the bitwize-shaped
    ``artists/{artist}/albums/{genre}/{slug}/`` tree; the fake holds an in-memory
    dict so tests run hermetically.
    """
    # ── 007 baseline (unchanged) ──
    def get(self, key: str) -> dict | None: ...
    def put(self, key: str, value: dict) -> None: ...

    # ── 094 Slice 2 — lifecycle method delta ──
    def list_ideas(self, status: str = "") -> list[dict]: ...
    def update_idea(self, idea_id: str, fields: dict) -> None: ...
    def create_album_root(self, artist: str, genre: str, slug: str,
                          title: str = "", type: str = "thematic") -> str: ...
    def find_album(self, query: str) -> list[dict]: ...
    def list_albums(self) -> list[dict]: ...
    def create_track(self, album: str, slug: str, title: str,
                     body: str = "") -> str: ...
    def list_tracks(self, album: str) -> list[dict]: ...
    def update_track_field(self, album: str, track: str, field: str,
                           value: str) -> None: ...
    def rename_album(self, old_slug: str, new_slug: str) -> dict: ...
    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> dict: ...
    def album_progress(self, album: str) -> dict: ...
    def get_session(self) -> dict: ...
    def update_session(self, fields: dict) -> None: ...
    def resolve_path(self, kind: str, **vars) -> str: ...
    def read_data(self, kind: str, slug: str) -> dict: ...


@runtime_checkable
class TextDriver(Driver, Protocol):
    """Pure text analysis — no external process.

    Spec 095 extends the surface with 11 new methods that mirror the bitwize
    ``text_analysis``/``lyrics_analysis`` handler shape (pattern-table-driven,
    no `pronouncing`/`textstat` deps). Real deployments can later bind
    `pronouncing` etc. via the ``[lyrics]`` extra; the fake covers all of
    them with stdlib + bundled pattern tables.
    """
    # ── 007 baseline ──
    def syllables(self, word: str) -> int: ...

    # ── 095 — lyrics cluster method delta ──
    def stats(self, text: str) -> dict: ...
    def rhyme_scheme(self, lines: list[str]) -> dict: ...
    def readability(self, text: str) -> dict: ...
    def pronunciation(self, text: str, guide: dict | None = None) -> list[dict]: ...
    def homographs(self, text: str) -> list[dict]: ...
    def streaming_safe(self, text: str, platform: str = "spotify") -> dict: ...
    def cross_track(self, tracks: list[str]) -> dict: ...
    def explicit(self, text: str) -> dict: ...
    def distinctive_phrases(self, text: str, corpus: list[str]) -> list[str]: ...
    def extract_section(self, text: str, label: str) -> str: ...
    def validate_sections(self, text: str) -> dict: ...
    def scan_artist_names(self, text: str,
                          allow: list[str] | None = None) -> list[dict]: ...
    def voice_tells(self, text: str) -> list[dict]: ...


@runtime_checkable
class AudioDriver(Driver, Protocol):
    """Loudness/mastering — stands in for pyloudnorm + ffmpeg."""
    def read_loudness(self, path: str) -> float: ...
    def run_ffmpeg(self, args: list[str]) -> dict: ...


@runtime_checkable
class DBDriver(Driver, Protocol):
    """A psycopg2-shaped cursor source (catalogue DB), no Postgres host required."""
    def cursor(self): ...


@runtime_checkable
class CloudDriver(Driver, Protocol):
    """Object storage / CDN (R2) + URL checks."""
    def url_head(self, url: str) -> int: ...
    def r2_put(self, key: str, data: bytes) -> dict: ...


# ─────────────────────────────── deterministic fakes ───────────────────────────────
class FakeStateDriver:
    """In-memory StateDriver fake.

    Spec 094 Slice 2: ports the bitwize ``state_cache.json`` shape — albums
    keyed by slug, tracks per album, ideas list, session dict — into a
    deterministic in-memory store. Production binds a real disk-backed driver
    that mirrors the bitwize ``artists/{artist}/albums/{genre}/{slug}/`` tree;
    the fake skips disk and keeps the same surface for tests.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._albums: dict[str, dict] = {}
        self._tracks: dict[str, list[dict]] = {}      # album_slug → [track,…]
        self._ideas: list[dict] = []                  # ordered for stable list
        self._session: dict = {}
        self._counter = 0

    # ── 007 baseline ──
    def get(self, key: str) -> dict | None:
        return self._store.get(key)

    def put(self, key: str, value: dict) -> None:
        self._store[key] = dict(value)
        # Mirror idea writes into the structured ideas list so list_ideas /
        # update_idea see them. Production driver writes both surfaces too
        # (state_cache.json plus IDEAS.md). The mirror is keyed by `idea_id`
        # to keep updates idempotent.
        if key.startswith("idea:") and "idea_id" in value:
            self._ideas[:] = [
                i for i in self._ideas
                if i.get("idea_id") != value["idea_id"]
            ]
            self._ideas.append(dict(value))

    # ── 094 Slice 2: ideas ──
    def list_ideas(self, status: str = "") -> list[dict]:
        if not status:
            return [dict(i) for i in self._ideas]
        return [dict(i) for i in self._ideas if i.get("status") == status]

    def update_idea(self, idea_id: str, fields: dict) -> None:
        for i in self._ideas:
            if i.get("idea_id") == idea_id:
                i.update(fields)
                return

    # ── 094 Slice 2: album CRUD ──
    def create_album_root(self, artist: str, genre: str, slug: str,
                          title: str = "", type: str = "thematic") -> str:
        root = f"artists/{artist}/albums/{genre}/{slug}"
        self._albums[slug] = {
            "slug": slug, "artist": artist, "genre": genre,
            "title": title or slug, "type": type, "status": "draft",
            "root": root,
        }
        self._tracks.setdefault(slug, [])
        return root

    def find_album(self, query: str) -> list[dict]:
        if not query:
            return [dict(a) for a in self._albums.values()]
        # exact-slug match first, then directional substring (query is the
        # search term, slug/title is the haystack). The reverse direction
        # (`slug in query`) was too lax — `find_album("origin-classic")`
        # matched an existing "origin" — see PR #65 review.
        if query in self._albums:
            return [dict(self._albums[query])]
        q = query.lower()
        return [dict(a) for a in self._albums.values()
                if q in a["slug"].lower() or q in a["title"].lower()]

    def list_albums(self) -> list[dict]:
        return [dict(a) for a in self._albums.values()]

    def rename_album(self, old_slug: str, new_slug: str) -> dict:
        if old_slug not in self._albums:
            return {"success": False, "error": "NOT_FOUND",
                    "old_slug": old_slug}
        album = self._albums.pop(old_slug)
        album["slug"] = new_slug
        album["root"] = album["root"].rsplit("/", 1)[0] + "/" + new_slug
        self._albums[new_slug] = album
        self._tracks[new_slug] = self._tracks.pop(old_slug, [])
        return {"success": True, "old_slug": old_slug, "new_slug": new_slug,
                "title": album["title"], "tracks_updated": len(self._tracks[new_slug])}

    # ── 094 Slice 2: tracks ──
    def create_track(self, album: str, slug: str, title: str,
                     body: str = "") -> str:
        self._counter += 1
        track_id = f"track:{self._counter}"
        self._tracks.setdefault(album, []).append({
            "track_id": track_id, "album": album, "slug": slug,
            "title": title, "status": "draft", "body": body,
        })
        return track_id

    def list_tracks(self, album: str) -> list[dict]:
        return [dict(t) for t in self._tracks.get(album, [])]

    def update_track_field(self, album: str, track: str, field: str,
                           value: str) -> None:
        for t in self._tracks.get(album, []):
            if t["slug"] == track:
                t[field] = value
                return

    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> dict:
        for t in self._tracks.get(album, []):
            if t["slug"] == old_slug:
                t["slug"] = new_slug
                return {"success": True, "album_slug": album,
                        "old_slug": old_slug, "new_slug": new_slug,
                        "title": t["title"]}
        return {"success": False, "error": "NOT_FOUND",
                "album_slug": album, "old_slug": old_slug}

    # ── 094 Slice 2: aggregates + session ──
    def album_progress(self, album: str) -> dict:
        tracks = self._tracks.get(album, [])
        by_status: dict[str, int] = {}
        for t in tracks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        completed = by_status.get("mastered", 0)
        pct = (100 * completed // len(tracks)) if tracks else 0
        return {"album_slug": album, "track_count": len(tracks),
                "tracks_completed": completed,
                "completion_percentage": pct,
                "tracks_by_status": by_status}

    def get_session(self) -> dict:
        return dict(self._session)

    def update_session(self, fields: dict) -> None:
        self._session.update(fields)

    def resolve_path(self, kind: str, **vars) -> str:
        templates = {
            "album": "artists/{artist}/albums/{genre}/{slug}",
            "track": "artists/{artist}/albums/{genre}/{album}/tracks/{slug}.md",
            "artist": "artists/{artist}",
            "genre": "artists/{artist}/albums/{genre}",
            "ideas": "IDEAS.md",
        }
        tpl = templates.get(kind, "")
        try:
            return tpl.format(**vars)
        except KeyError:
            return tpl

    def read_data(self, kind: str, slug: str) -> dict:
        # Stub — production reads `data/{kind}/{slug}.{md,yaml}`. Slice 1's
        # vendored genres + reference docs back this in the real driver.
        return {"kind": kind, "slug": slug, "body": ""}


class FakeTextDriver:
    """In-memory TextDriver fake — Spec 095 lyrics-cluster surface.

    Deterministic, stdlib-only implementations: covers the 14 user verbs +
    4 gate verbs without any `pronouncing`/`textstat` dep. Pattern tables
    (homograph list, explicit lexicon, voice-tell heuristics) are bundled
    inline + can be widened via the OntologyExtension's data folder later.
    """
    _VOWELS = "aeiouy"
    # Minimal pattern tables — deepened by Slice 2+ via YAML in
    # data/reference/. Each entry's behaviour is decidable + cheap.
    _HOMOGRAPHS: dict[str, list[str]] = {
        "lead":   ["led (verb, past)", "leed (metal)"],
        "tear":   ["teer (rip)", "teir (eye-water)"],
        "read":   ["reed (present)", "red (past)"],
        "wind":   ["wynd (turn)", "wihnd (air)"],
    }
    _PRONUNCIATION_GUIDE: dict[str, str] = {
        "phreaker": "freak-er",
        "synth":    "sinth",
        "modem":    "mo-dem",
    }
    # Exact-word-match only — derived forms ("fucking", "fucked", "shitter")
    # slip through. Documented limitation; widen via the bundled
    # `data/reference/` YAML when Slice 2 of 095 lands the override-path.
    # CLAUDE.md rule 8: this is a tunable budget, not a snapshot — the v1
    # lexicon stays minimal until real corpus data justifies expansion.
    _EXPLICIT_LEXICON: set[str] = {"fuck", "shit", "damn", "bitch", "ass"}
    _SUGGESTIVE_LEXICON: set[str] = {"hell", "crap", "piss"}
    _VOICE_TELLS: list[tuple[str, str]] = [
        # (heuristic_key, severity)
        ("abstract_noun_stack", "warning"),  # ≥3 abstract nouns in 2 lines
        ("cliche_escalation",   "info"),     # "deeper than", "more than ever"
        ("over_explained_metaphor", "info"), # like a + simile + because clause
        ("missing_idiosyncrasy", "info"),    # zero proper nouns + zero numbers
    ]
    _ABSTRACT_NOUNS = {"love", "hope", "fear", "truth", "soul", "heart",
                       "dream", "freedom", "destiny", "passion"}
    _ARTIST_BLOCKLIST = {"drake", "beyonce", "taylor swift", "kendrick",
                         "sza", "the weeknd"}

    # ── 007 baseline ──
    def syllables(self, word: str) -> int:
        """A deterministic syllable heuristic (vowel-group count, ≥ 1) — driver-free
        text math, no external pronunciation dictionary."""
        w = word.lower().strip()
        count, prev_vowel = 0, False
        for ch in w:
            is_vowel = ch in self._VOWELS
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if w.endswith("e") and count > 1:        # silent trailing 'e'
            count -= 1
        return max(1, count)

    # ── 095 — lyrics cluster delta ──
    def stats(self, text: str) -> dict:
        lines = [ln for ln in text.splitlines() if ln.strip()]
        words = text.split()
        return {"lines": len(lines), "words": len(words),
                "syllables": sum(self.syllables(w) for w in words),
                "chars": len(text)}

    def rhyme_scheme(self, lines: list[str]) -> dict:
        """Build a rhyme scheme by clustering trailing syllables.

        Two lines rhyme iff their last word's 2-character tail matches.
        Returns ``{scheme, groups, self_rhymes}``.
        """
        labels: dict[str, str] = {}
        next_label = 0
        scheme_chars = []
        self_rhymes = 0
        for ln in lines:
            words = ln.strip().split()
            if not words:
                scheme_chars.append("-")
                continue
            tail = words[-1].lower().rstrip(",.!?\"'")[-2:]
            if tail in labels:
                scheme_chars.append(labels[tail])
            else:
                lbl = chr(ord("A") + next_label) if next_label < 26 else "Z"
                labels[tail] = lbl
                next_label += 1
                scheme_chars.append(lbl)
            if len(words) >= 2 and words[-1].lower() == words[-2].lower():
                self_rhymes += 1
        return {"scheme": "".join(scheme_chars), "groups": len(labels),
                "self_rhymes": self_rhymes}

    def readability(self, text: str) -> dict:
        """Flesch-Kincaid-shaped readability (no `textstat` dep)."""
        words = text.split()
        sentences = max(1, sum(1 for ch in text if ch in ".!?"))
        syll = sum(self.syllables(w) for w in words) or 1
        fk_grade = 0.39 * (len(words) / sentences) + 11.8 * (syll / max(len(words), 1)) - 15.59
        return {"grade_level": round(fk_grade, 2),
                "avg_words_per_sentence": len(words) / sentences,
                "avg_syllables_per_word": syll / max(len(words), 1)}

    def pronunciation(self, text: str, guide: dict | None = None) -> list[dict]:
        guide = guide or self._PRONUNCIATION_GUIDE
        findings = []
        for word in text.lower().split():
            stripped = word.strip(",.!?\"'()[]")
            if stripped in guide:
                findings.append({"word": stripped,
                                 "suggested": guide[stripped],
                                 "severity": "warning"})
        return findings

    def homographs(self, text: str) -> list[dict]:
        findings = []
        for word in text.lower().split():
            stripped = word.strip(",.!?\"'()[]")
            if stripped in self._HOMOGRAPHS:
                findings.append({"word": stripped,
                                 "ambiguous_readings": self._HOMOGRAPHS[stripped],
                                 "severity": "info"})
        return findings

    def streaming_safe(self, text: str, platform: str = "spotify") -> dict:
        # Streaming platforms strip bracketed section tags; we flag them.
        bracketed = sum(1 for ln in text.splitlines()
                        if ln.strip().startswith("[") and ln.strip().endswith("]"))
        return {"platform": platform, "bracket_tags": bracketed,
                "safe": bracketed == 0,
                "fix": "strip [Verse]/[Chorus] tags before upload"
                       if bracketed else None}

    def cross_track(self, tracks: list[str]) -> dict:
        seen_lines: dict[str, list[int]] = {}
        for i, t in enumerate(tracks):
            for ln in t.splitlines():
                norm = ln.strip().lower()
                if len(norm.split()) < 3:
                    continue
                seen_lines.setdefault(norm, []).append(i)
        repeats = {ln: ids for ln, ids in seen_lines.items()
                   if len({i for i in ids}) > 1}
        return {"repeated_lines": len(repeats),
                "track_count": len(tracks),
                "examples": list(repeats.items())[:5]}

    def explicit(self, text: str) -> dict:
        words = {w.lower().strip(",.!?\"'()[]") for w in text.split()}
        explicit_hits = words & self._EXPLICIT_LEXICON
        suggestive_hits = words & self._SUGGESTIVE_LEXICON
        if explicit_hits:
            rating = "explicit"
        elif suggestive_hits:
            rating = "suggestive"
        else:
            rating = "clean"
        return {"rating": rating, "explicit_words": sorted(explicit_hits),
                "suggestive_words": sorted(suggestive_hits)}

    def distinctive_phrases(self, text: str, corpus: list[str]) -> list[str]:
        """Return tri-grams in `text` that don't appear in any line of `corpus`."""
        words = [w.lower().strip(",.!?\"'") for w in text.split() if w.strip()]
        trigrams = [" ".join(words[i:i+3]) for i in range(len(words) - 2)]
        corpus_blob = " ".join(corpus).lower()
        return [tg for tg in trigrams if tg and tg not in corpus_blob][:10]

    def extract_section(self, text: str, label: str) -> str:
        """Extract the body under a ``[<label>]`` section tag (e.g. ``Verse 1``)."""
        target = f"[{label}]".lower()
        lines = text.splitlines()
        out = []
        capture = False
        for ln in lines:
            stripped = ln.strip()
            if stripped.lower() == target:
                capture = True
                continue
            if capture and stripped.startswith("[") and stripped.endswith("]"):
                break
            if capture:
                out.append(ln)
        return "\n".join(out).strip()

    def validate_sections(self, text: str) -> dict:
        """Section tags must be ``[<Title Case>]``; raises findings on malformed."""
        findings = []
        for i, ln in enumerate(text.splitlines(), 1):
            s = ln.strip()
            if s.startswith("[") and s.endswith("]"):
                inner = s[1:-1]
                if not inner or inner.lower() == inner:
                    findings.append({"line": i, "tag": s,
                                     "issue": "title-case required",
                                     "severity": "warning"})
        return {"findings": findings, "ok": not findings}

    def scan_artist_names(self, text: str,
                          allow: list[str] | None = None) -> list[dict]:
        allow_set = {a.lower() for a in (allow or [])}
        blob = text.lower()
        hits = []
        for name in self._ARTIST_BLOCKLIST:
            if name in blob and name not in allow_set:
                hits.append({"name": name, "severity": "warning",
                             "fix": f"replace or add to allow-list"})
        return hits

    def voice_tells(self, text: str) -> list[dict]:
        """Heuristic AI-tell detection — advisory only (no gate impact)."""
        findings = []
        lines = [ln.lower() for ln in text.splitlines() if ln.strip()]
        # Heuristic 1: abstract-noun stacking (≥3 in any 2-line window)
        for i in range(len(lines) - 1):
            window = lines[i] + " " + lines[i + 1]
            stack = sum(1 for n in self._ABSTRACT_NOUNS if n in window.split())
            if stack >= 3:
                findings.append({"heuristic": "abstract_noun_stack",
                                 "line": i + 1, "severity": "warning",
                                 "fix": "swap abstract nouns for concrete imagery"})
                break
        # Heuristic 2: cliché escalation
        cliches = ["deeper than", "more than ever", "stronger than", "harder than"]
        for c in cliches:
            if c in text.lower():
                findings.append({"heuristic": "cliche_escalation",
                                 "phrase": c, "severity": "info",
                                 "fix": "replace with a specific image"})
                break
        # Heuristic 3: missing idiosyncrasy (no proper nouns + no digits).
        # Strip ``[Section Tag]`` lines first so `[Verse 1]` doesn't satisfy
        # the digit check (review finding: section tags don't count as
        # lyric content for this heuristic).
        body_lines = [ln for ln in text.splitlines()
                      if not (ln.strip().startswith("[")
                              and ln.strip().endswith("]"))]
        body_text = "\n".join(body_lines)
        has_proper = any(w[0].isupper() and len(w) > 1
                         for ln in body_lines for w in ln.split()
                         if w and w[0].isupper())
        has_digit = any(ch.isdigit() for ch in body_text)
        if not has_proper and not has_digit:
            findings.append({"heuristic": "missing_idiosyncrasy",
                             "severity": "info",
                             "fix": "add a proper noun, number, or specific detail"})
        return findings


class FakeAudioDriver:
    """Returns a fixed loudness so a mastering verb is deterministic in tests."""
    def __init__(self, loudness: float = -14.0) -> None:
        self._loudness = loudness
        self.ffmpeg_calls: list[list[str]] = []

    def read_loudness(self, path: str) -> float:
        return self._loudness

    def run_ffmpeg(self, args: list[str]) -> dict:
        self.ffmpeg_calls.append(list(args))
        return {"ok": True, "args": list(args)}


class _FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._sql = sql

    def fetchall(self) -> list[tuple]:
        return list(self._rows)

    def close(self) -> None:
        pass


class FakeDBDriver:
    def __init__(self, rows: list[tuple] | None = None) -> None:
        self._rows = rows or [("track-1", "mastered"), ("track-2", "draft")]

    def cursor(self):
        return _FakeCursor(self._rows)


class FakeCloudDriver:
    """`url_head` is real (stdlib-shaped); `r2_put` reports DEPENDENCY_MISSING when
    unconfigured, so the verb returns a typed failure instead of importing boto3."""
    def __init__(self, configured: bool = False, head_status: int = 200) -> None:
        self._configured = configured
        self._head_status = head_status

    def url_head(self, url: str) -> int:
        return self._head_status

    def r2_put(self, key: str, data: bytes) -> dict:
        if not self._configured:
            return {"ok": False, "error": "DEPENDENCY_MISSING"}
        return {"ok": True, "key": key, "bytes": len(data)}


def fake_drivers() -> dict[str, object]:
    """The driver bundle a test passes to ``Engine(..., drivers=fake_drivers())``."""
    return {
        "music_state": FakeStateDriver(),
        "music_text": FakeTextDriver(),
        "music_audio": FakeAudioDriver(),
        "music_db": FakeDBDriver(),
        "music_cloud": FakeCloudDriver(),
    }
