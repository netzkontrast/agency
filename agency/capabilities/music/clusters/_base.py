# agency-scaffold: v1
"""music clusters — shared base + module constants/helpers (Spec 286 Phase 3).

The per-cluster file split (Spec 094 design §"Module layout") relocates the
``MusicCapability`` god-class into cluster mixin classes, one per domain
cluster. This module hosts the cross-cluster shared surface so no cluster
duplicates it (CLAUDE.md §"Derivability audit" — one source, no drift):

- The tunable budgets (``STREAMING_TARGET_LUFS`` etc.) the verbs reference as
  default args (Spec 095/096/099; CLAUDE.md rule 8 — documented config, not a
  snapshot of current state).
- The single-source helpers (``_validate_album_type``, ``_fill_*_body``,
  ``_syllables``, ``conceptualize``) the verbs delegate to.
- ``_MusicBase`` — the shared mixin holding the Spec-117 lazy production-driver
  auto-wiring (``_production_enabled`` / ``_autowire_music_drivers`` /
  ``_require_drv`` override) + the deterministic ``_name_exposure_hits`` scan
  (Spec 119) used by both ``check_name_exposure`` (transform) and
  ``name_exposure_gate`` (effect).

Behaviour is byte-identical to the prior single-module form — pure relocation.
"""
from __future__ import annotations

from typing import Optional

from agency.capability import CapabilityBase
from agency.toolresult import ToolResult, Codes

from agency._prosody import syllables as _syllables_shared

from ..ontology import ALBUM_TYPES
from .._slug import slugify as _slugify  # noqa: F401  (re-export for cluster use)

_VOWELS = "aeiouy"   # kept for module-level constant compatibility

# Spec 095 — prosody-gate tunables (CLAUDE.md rule 8: documented budgets, not
# snapshots). The MIN_RHYME_GROUPS bound = "actual rhyming needs at least 2
# distinct rhyme groups; all-A monorhyme is an opinionated reject — set the
# bound to 1 via a verb-param override if your genre (hip-hop, blues) wants
# monorhyme to pass". The SYLLABLE_TOLERANCE = ±2 syllables around the
# per-line target — a default; per-genre tuning lands when the YAML preset
# layer ships (deferred to Slice 2+).
_MIN_RHYME_GROUPS: int = 2
_SYLLABLE_TOLERANCE: int = 2

# Spec 096 — mastering / streaming loudness target. Industry baseline for
# streaming-platform delivery is -14 LUFS integrated (Spotify / Apple Music /
# YouTube reference). Per CLAUDE.md rule 8: a documented tunable budget, not a
# frozen snapshot — verb args can override per-platform (LANDR / Tidal / etc.).
# Referenced by the 4 master/QC verbs + the audio Driver default.
STREAMING_TARGET_LUFS: float = -14.0

# Spec 099 — default confidence for `capture_claim`. 0.8 = "moderate
# confidence by default" for an unverified primary-source claim (raised by
# `verify_sources` when a second source corroborates, lowered when one
# contradicts). Per CLAUDE.md rule 8: documented tunable, not a snapshot.
DEFAULT_CLAIM_CONFIDENCE: float = 0.8


def _validate_album_type(value: str) -> Optional["ToolResult"]:
    """Single-source ALBUM_TYPES enum check (post-Round-1 dedup).

    Returns a ToolResult.failure when ``value`` is not in the enum, else None.
    Used by `promote_idea` and `create_album` — the two verbs that take a
    user-supplied `type` arg and return ToolResult. The standalone
    `conceptualize()` (and its verb-form wrapper) raises ValueError instead
    because it pre-dates the ToolResult convention and stays delegated; that
    contract is the standalone-fn doctrine carve-out.
    """
    if value not in ALBUM_TYPES:
        return ToolResult.failure(
            Codes.INVALID_ARGUMENT,
            f"type={value!r} not in {sorted(ALBUM_TYPES)}")
    return None


def _fill_album_body(body: str, artist: str, title: str, genre: str) -> str:
    """Substitute the album template's placeholders with the real values
    (Spec 117 Slice 2 / F3). Only replaces placeholder strings that exist in
    ``templates/album.md`` — `[Album Title]` (frontmatter `title:` + H1 + the
    Album row), `[Album Name]`, `[Artist Name]`, `[Genre Name]`."""
    if not body:
        return body
    body = body.replace('title: "[Album Title]"', f'title: "{title}"')
    body = body.replace("[Album Title]", title)
    body = body.replace("[Album Name]", title)
    body = body.replace("[Artist Name]", artist)
    # Genre appears in the Album Details table as
    # `| **Genre** | [Genre](/genres/[genre]/README.md) / [Subgenre] |` —
    # fill the link label + the path slug (both placeholders present in
    # templates/album.md).
    body = body.replace("[Genre](/genres/[genre]/README.md)",
                        f"[{genre}](/genres/{genre}/README.md)")
    body = body.replace("[Genre Name]", genre)
    return body


def _fill_track_body(body: str, title: str, track_number: int) -> str:
    """Substitute the track template's placeholders with the real values
    (Spec 117 Slice 2 / F3). Targets the frontmatter `title:`, the H1, and the
    Track Details table rows (`Track #`, `Title`); keeps the existing
    `track_number: 0` → real-number substitution."""
    if not body:
        return body
    body = body.replace("track_number: 0", f"track_number: {track_number}")
    body = body.replace('title: "[Track Title]"', f'title: "{title}"')
    body = body.replace("# [Track Title]", f"# {title}")
    body = body.replace("| **Track #** | XX |",
                        f"| **Track #** | {track_number} |")
    body = body.replace("| **Title** | [Track Title] |",
                        f"| **Title** | {title} |")
    body = body.replace("[Track Title]", title)
    return body


def _syllables(word: str) -> int:
    """Deterministic syllable heuristic — delegates to agency._prosody.syllables.

    Kept as a local alias so existing call sites (used in 094-Slice-2's
    `lyric_report` family) don't churn. Post Round-1 sc-analyze F2
    (CLAUDE.md §"Derivability audit") — the heuristic lives in
    `agency/_prosody.py` so music + novel share one implementation.
    """
    return _syllables_shared(word)


def conceptualize(artist: str, title: str, type: str,
                  theme: str = "", tracklist: str = "") -> dict:
    "Render an album-concept document (act). `type` must be a known album type."
    if type not in ALBUM_TYPES:
        # Standalone (no ctx) — raise. Verb-form callers use _validate_album_type.
        raise ValueError(f"type={type!r} not in {sorted(ALBUM_TYPES)}")
    body = (f"# {title}\n\n**Artist:** {artist}  \n**Type:** {type}\n\n"
            f"## Theme\n{theme}\n\n## Tracklist\n{tracklist}\n")
    return {"result": body, "artefact": {
        "kind": "album-concept", "artist": artist, "title": title,
        "type": type, "body": body}}


class _MusicBase(CapabilityBase):
    """Shared base for every music cluster mixin (Spec 286 Phase 3).

    Holds the Spec-117 lazy production-driver auto-wiring + the Spec-119
    name-exposure scan — the cross-cluster surface the cluster mixins call via
    ``self``. Composed into the single registered ``MusicCapability`` via
    multiple inheritance; behaviour is identical to the prior single class.
    """

    # AGENCY-DRIFT: music driver set — mirror `diagnose` wanted + production_drivers() keys.
    _MUSIC_DRIVER_NAMES = ("music_state", "music_text", "music_audio",
                           "music_db", "music_cloud")

    # ───────── Spec 117: lazy production-driver auto-wiring ─────────
    def _production_enabled(self) -> bool:
        """Lazy auto-wiring is enabled only in the production runtime — the MCP
        server (`agency/__main__.py`) flips ``engine._music_production = True``.

        A bare ``Engine(..., drivers={})`` built by a unit test has no flag, so
        the driver-backed verbs keep their typed ``DEPENDENCY_MISSING`` contract
        (the enforcement blast-radius stays bounded; CLAUDE.md heuristic).
        """
        return self.ctx.production_enabled("music")

    def _autowire_music_drivers(self) -> None:
        """Build ``production_drivers(MusicConfig.bootstrap())`` ONCE and register
        the bundle on the engine's DriverRegistry the first time a verb needs a
        driver — so every later verb + ``diagnose`` sees them wired without the
        caller passing ``Engine(..., drivers=…)``. ``MusicConfig.bootstrap()``
        writes a default config + creates a fresh content root when none exists.

        No-op when there's no DriverRegistry (bare unit tests), the production
        flag is off, or all five drivers are already registered (fake-driver
        tests + idempotent re-entry).
        """
        reg = self.ctx.drivers
        if reg is None or not self._production_enabled():
            return
        if all(reg.has(n) for n in self._MUSIC_DRIVER_NAMES):
            return
        from ..config import MusicConfig
        from ..drivers_production import production_drivers
        bundle = production_drivers(MusicConfig.bootstrap())
        for n, drv in bundle.items():
            if not reg.has(n):
                reg.register(n, drv)

    def _require_drv(self, name: str):  # type: ignore[override]
        """Override (Spec 117): auto-wire production drivers on first miss before
        falling back to the base typed-failure resolver."""
        if name in self._MUSIC_DRIVER_NAMES:
            reg = self.ctx.drivers
            if reg is not None and not reg.has(name):
                self._autowire_music_drivers()
        return super()._require_drv(name)

    @staticmethod
    def _name_exposure_hits(text: str, roster: list[str]) -> list[dict]:
        """Deterministic whole-word, case-insensitive scan of `text` vs `roster`.

        Spec 119 — shared by `check_name_exposure` (transform) and
        `name_exposure_gate` (effect). Pure text math, no driver/network/disk.
        A name fires only on a whole-word match (so "Lex" never matches inside
        "lexicon"). Returns ``[{name, count}]`` for any name with ≥ 1 hit.
        """
        import re
        hits: list[dict] = []
        for name in roster:
            name = (name or "").strip()
            if not name:
                continue
            count = len(re.findall(r"\b" + re.escape(name) + r"\b", text, re.I))
            if count:
                hits.append({"name": name, "count": count})
        return hits
