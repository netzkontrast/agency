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
    # 097 Slice 2 (review-driven): production drivers expose a key-iteration
    # primitive so verbs don't reach into a `_store` private attribute.
    def list_keys(self, prefix: str = "") -> list[str]: ...


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
    """Loudness/mastering — stands in for pyloudnorm + ffmpeg.

    Spec 096 extends the surface with 13 new methods covering the bitwize
    audio handler shape (master/polish/qc/coherence/promo render). The fake
    produces deterministic outputs from path hashes so CI runs zero real
    ffmpeg / pyloudnorm / AnthemScore / LilyPond binaries. Production binds
    via the ``[music-audio]`` extra.
    """
    # ── 007 baseline ──
    def read_loudness(self, path: str) -> float: ...
    def run_ffmpeg(self, args: list[str]) -> dict: ...

    # ── 096 — audio cluster method delta ──
    def measure_signature(self, path: str) -> dict: ...
    def coherence_report(self, paths: list[str]) -> dict: ...
    def apply_coherence(self, paths: list[str], target: dict) -> dict: ...
    def qc_checklist(self, path: str) -> dict: ...
    def mono_fold(self, path: str) -> dict: ...
    def polish_stems(self, stems: dict[str, str]) -> dict: ...
    def polish_full(self, path: str) -> str: ...
    def master(self, path: str, target_lufs: float,
               preset: str = "") -> dict: ...
    def master_to_reference(self, path: str, reference: str) -> dict: ...
    def dynamic_fix(self, path: str, target_dr: float = 8.0) -> dict: ...
    def codec_preview(self, path: str, codec: str = "aac") -> dict: ...
    def render_promo_video(self, audio: str, art: str,
                            template: str = "") -> str: ...
    def render_songbook(self, tracks: list[str]) -> str: ...


@runtime_checkable
class DBDriver(Driver, Protocol):
    """A psycopg2-shaped cursor source (catalogue DB), no Postgres host required.

    Spec 097 extends with 7 typed-named methods so the catalogue cluster
    doesn't repeat SQL strings in each verb — production binds via the
    `[music-db]` extra; the fake's in-memory store keys by auto-incremented
    ID so the SQL router can be a thin shim.
    """
    # ── 007 baseline ──
    def cursor(self): ...

    # ── 097 — catalogue cluster method delta ──
    def create_tweet(self, album: str, body: str, scheduled_at: str,
                     platform: str = "x") -> int: ...
    def update_tweet(self, tweet_id: int, fields: dict) -> None: ...
    def delete_tweet(self, tweet_id: int) -> None: ...
    def list_tweets(self, album: str = "", status: str = "",
                    limit: int = 100) -> list[dict]: ...
    def search_tweets(self, query: str, limit: int = 50) -> list[dict]: ...
    def tweet_stats(self, album: str = "") -> dict: ...
    def sync_album_tweets(self, album: str,
                          tweets: list[dict]) -> dict: ...


@runtime_checkable
class CloudDriver(Driver, Protocol):
    """Object storage / CDN (R2) + URL checks.

    Spec 098 extends with 4 typed-named methods for delete, list, and signed-URL
    flows; production binds boto3 via the ``[music-cloud]`` extra. The in-memory
    fake records every upload for audit + holds a dict-shaped object store.
    """
    # ── 007 baseline ──
    def url_head(self, url: str) -> int: ...
    def r2_put(self, key: str, data: bytes) -> dict: ...

    # ── 098 — promo cluster method delta ──
    def r2_delete(self, key: str) -> dict: ...
    def r2_list(self, prefix: str = "") -> list[dict]: ...
    def r2_signed_url(self, key: str, ttl_s: int = 3600) -> str: ...
    def r2_head(self, key: str) -> dict | None: ...


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

    def list_keys(self, prefix: str = "") -> list[str]:
        """Spec 097 Slice 2 (review-driven): return keys matching prefix.

        Lets `get_streaming_urls` / `get_promo_status` iterate without
        reaching into `_store` (a private attribute production drivers
        don't expose). Production redis/etcd-backed implementations use
        their native prefix-scan; the fake just iterates the dict.
        """
        if not prefix:
            return sorted(self._store.keys())
        return sorted(k for k in self._store if k.startswith(prefix))


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
    """In-memory AudioDriver fake — Spec 096 audio cluster surface.

    Deterministic outputs from path hashes: zero ffmpeg / pyloudnorm /
    AnthemScore / LilyPond required in CI. The fake covers the 13 new
    methods Spec 096 adds; production binds via the ``[music-audio]`` extra.
    """
    _QC_ROWS = ("loudness", "clipping", "silence", "phase",
                "stereo_width", "frequency_balance", "dynamic_range")

    def __init__(self, loudness: float = -14.0) -> None:
        self._loudness = loudness
        self.ffmpeg_calls: list[list[str]] = []

    # ── 007 baseline ──
    def read_loudness(self, path: str) -> float:
        # Constructor-provided fixed loudness — 007 contract preserved.
        # Per-path variation is exposed through `measure_signature.rms_db`
        # (Spec 096) so tests that depend on `-14.0` as a baseline still
        # match while spectral signatures stay hash-derived.
        return self._loudness

    def run_ffmpeg(self, args: list[str]) -> dict:
        self.ffmpeg_calls.append(list(args))
        return {"ok": True, "args": list(args)}

    # ── 096 — audio cluster delta ──
    def measure_signature(self, path: str) -> dict:
        """Deterministic spectral signature from path hash — a fingerprint
        for cross-track coherence comparison."""
        h = sum(ord(c) for c in path)
        return {"path": path,
                "centroid_hz": 1000 + (h % 4000),       # 1000..5000 Hz
                "rolloff_hz":  4000 + (h % 8000),
                "flatness":    round((h % 100) / 100.0, 3),  # 0..1
                "rms_db":     -12.0 - ((h % 600) / 100.0)}   # -12..-18

    def coherence_report(self, paths: list[str]) -> dict:
        sigs = [self.measure_signature(p) for p in paths]
        if len(sigs) < 2:
            return {"coherent": True, "avg_distance": 0.0,
                    "outliers": [], "track_count": len(sigs)}
        # Avg pairwise centroid distance — proxy for tonal coherence.
        from itertools import combinations
        dists = [abs(a["centroid_hz"] - b["centroid_hz"])
                 for a, b in combinations(sigs, 2)]
        avg = sum(dists) / max(len(dists), 1)
        outliers = []
        if avg > 0:
            mean_c = sum(s["centroid_hz"] for s in sigs) / len(sigs)
            for s in sigs:
                if abs(s["centroid_hz"] - mean_c) > avg * 1.5:
                    outliers.append(s["path"])
        return {"coherent": avg <= 1500,    # threshold tunable
                "avg_distance": avg,
                "outliers": outliers,
                "track_count": len(sigs)}

    def apply_coherence(self, paths: list[str], target: dict) -> dict:
        # Deterministic: report what would change; fake doesn't write files.
        return {"applied_to": list(paths), "target": dict(target),
                "ok": True}

    def qc_checklist(self, path: str) -> dict:
        """7-point QC checklist with deterministic pass/warn/fail per row."""
        h = sum(ord(c) for c in path)
        rows = {}
        for i, row in enumerate(self._QC_ROWS):
            v = (h + i * 7) % 10
            status = "pass" if v < 7 else ("warn" if v < 9 else "fail")
            rows[row] = status
        worst = "fail" if "fail" in rows.values() else (
                "warn" if "warn" in rows.values() else "pass")
        return {"path": path, "rows": rows, "summary": worst}

    def mono_fold(self, path: str) -> dict:
        h = sum(ord(c) for c in path) % 20
        cancellation_db = -h * 0.5            # -0..-10 dB
        return {"path": path, "cancellation_db": cancellation_db,
                "phase_safe": cancellation_db > -6.0}

    def polish_stems(self, stems: dict[str, str]) -> dict:
        return {"polished_stems": {n: f"{p}.polished"
                                   for n, p in stems.items()},
                "stem_count": len(stems)}

    def polish_full(self, path: str) -> str:
        return f"{path}.polished"

    def master(self, path: str, target_lufs: float,
               preset: str = "") -> dict:
        measured = self.read_loudness(path)
        gain = target_lufs - measured
        out = f"{path}.mastered"
        return {"input": path, "output": out, "preset": preset,
                "measured_lufs": measured,
                "target_lufs": target_lufs,
                "gain_db": gain}

    def master_to_reference(self, path: str, reference: str) -> dict:
        target = self.read_loudness(reference)
        return self.master(path, target_lufs=target,
                           preset=f"ref:{reference}")

    def dynamic_fix(self, path: str, target_dr: float = 8.0) -> dict:
        h = sum(ord(c) for c in path) % 10
        measured_dr = 4.0 + h * 0.5            # 4.0..8.5
        return {"path": path, "measured_dr": measured_dr,
                "target_dr": target_dr,
                "applied": measured_dr < target_dr,
                "output": f"{path}.dyn"}

    def codec_preview(self, path: str, codec: str = "aac") -> dict:
        return {"path": path, "codec": codec,
                "output": f"{path}.{codec}.preview",
                "bitrate_kbps": 256 if codec == "aac" else 320}

    def render_promo_video(self, audio: str, art: str,
                            template: str = "") -> str:
        return f"{audio}.{template or 'default'}.mp4-stub"

    def render_songbook(self, tracks: list[str]) -> str:
        return f"songbook-{len(tracks)}-tracks.pdf-stub"


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
    """In-memory DBDriver fake — Spec 097 catalogue cluster surface.

    The 007 cursor-shim path is preserved (rows-based fake for catalogue_status
    + release_check); Spec 097 adds an indexed tweet store keyed by auto-id.
    Production binds psycopg2-binary via the `[music-db]` extra.
    """

    def __init__(self, rows: list[tuple] | None = None) -> None:
        self._rows = rows or [("track-1", "mastered"), ("track-2", "draft")]
        # 097: tweet table (album → list[{id, body, status, platform, scheduled_at}])
        self._tweets: dict[int, dict] = {}
        self._tweet_seq = 0

    # ── 007 baseline ──
    def cursor(self):
        return _FakeCursor(self._rows)

    # ── 097 — catalogue cluster delta ──
    def create_tweet(self, album: str, body: str, scheduled_at: str,
                     platform: str = "x") -> int:
        self._tweet_seq += 1
        tid = self._tweet_seq
        self._tweets[tid] = {
            "id": tid, "album": album, "body": body,
            "scheduled_at": scheduled_at, "platform": platform,
            "status": "draft",
        }
        return tid

    def update_tweet(self, tweet_id: int, fields: dict) -> None:
        if tweet_id in self._tweets:
            self._tweets[tweet_id].update(fields)

    def delete_tweet(self, tweet_id: int) -> None:
        self._tweets.pop(tweet_id, None)

    def list_tweets(self, album: str = "", status: str = "",
                    limit: int = 100) -> list[dict]:
        out = list(self._tweets.values())
        if album:
            out = [t for t in out if t.get("album") == album]
        if status:
            out = [t for t in out if t.get("status") == status]
        return [dict(t) for t in out[:limit]]

    def search_tweets(self, query: str, limit: int = 50) -> list[dict]:
        q = query.lower()
        return [dict(t) for t in self._tweets.values()
                if q in t.get("body", "").lower()][:limit]

    def tweet_stats(self, album: str = "") -> dict:
        tweets = (list(self._tweets.values()) if not album else
                  [t for t in self._tweets.values()
                   if t.get("album") == album])
        by_status: dict[str, int] = {}
        for t in tweets:
            s = t.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {"album": album or "*", "total": len(tweets),
                "by_status": by_status}

    def sync_album_tweets(self, album: str,
                          tweets: list[dict]) -> dict:
        """Idempotent sync — replaces all tweets for an album with the input list."""
        existing = [tid for tid, t in self._tweets.items()
                    if t.get("album") == album]
        for tid in existing:
            del self._tweets[tid]
        created = 0
        for t in tweets:
            self.create_tweet(album=album, body=t.get("body", ""),
                              scheduled_at=t.get("scheduled_at", ""),
                              platform=t.get("platform", "x"))
            created += 1
        return {"album": album, "removed": len(existing),
                "created": created}


class FakeCloudDriver:
    """In-memory CloudDriver fake.

    `url_head` is real (stdlib-shaped); object-store ops (`r2_put`/`r2_delete`/
    `r2_list`/`r2_head`/`r2_signed_url`) use an in-memory dict so Spec 098
    promo cluster verbs run hermetically. Production binds boto3 via the
    `[music-cloud]` extra. When unconfigured (the default), `r2_put` /
    `r2_delete` return `{"ok": False, "error": "DEPENDENCY_MISSING"}` and the
    wrapping verb converts to a typed `ToolResult.failure`.
    """

    def __init__(self, configured: bool = False, head_status: int = 200) -> None:
        self._configured = configured
        self._head_status = head_status
        # In-memory object store — populated only when configured=True.
        self._objects: dict[str, dict] = {}

    # ── 007 baseline ──
    def url_head(self, url: str) -> int:
        return self._head_status

    def r2_put(self, key: str, data: bytes) -> dict:
        if not self._configured:
            return {"ok": False, "error": "DEPENDENCY_MISSING"}
        self._objects[key] = {"key": key, "bytes": len(data),
                               "data": bytes(data)}
        return {"ok": True, "key": key, "bytes": len(data)}

    # ── 098 — promo cluster delta ──
    def r2_delete(self, key: str) -> dict:
        if not self._configured:
            return {"ok": False, "error": "DEPENDENCY_MISSING"}
        existed = self._objects.pop(key, None) is not None
        return {"ok": True, "key": key, "deleted": existed}

    def r2_list(self, prefix: str = "") -> list[dict]:
        if not self._configured:
            return []
        return [{"key": k, "bytes": v["bytes"]}
                for k, v in self._objects.items() if k.startswith(prefix)]

    def r2_signed_url(self, key: str, ttl_s: int = 3600) -> str:
        # Deterministic stub — production drivers return real pre-signed URLs.
        return f"https://r2.example.com/{key}?ttl={ttl_s}&sig=fake"

    def r2_head(self, key: str) -> dict | None:
        obj = self._objects.get(key) if self._configured else None
        if obj is None:
            return None
        return {"key": key, "bytes": obj["bytes"]}


def fake_drivers() -> dict[str, object]:
    """The driver bundle a test passes to ``Engine(..., drivers=fake_drivers())``."""
    return {
        "music_state": FakeStateDriver(),
        "music_text": FakeTextDriver(),
        "music_audio": FakeAudioDriver(),
        "music_db": FakeDBDriver(),
        "music_cloud": FakeCloudDriver(),
    }
