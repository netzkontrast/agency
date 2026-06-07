"""music drivers — the five external I/O boundaries the music capability reaches
through, as Spec-002 ``Driver`` protocols (Option B: typed, named methods; the
uniform contract is the RETURN TYPE via the wrapping verb, not a ``dispatch(op)``).

Each driver is a marker ``Boundary`` exposing its own typed methods (the ``jules.py``
``create/get/list`` shape). The capability resolves them via ``ctx.get_driver(name)``
(Spec 002's ``DriverRegistry``) — so the music capability edits NO file under
``agency/`` and a host binds real drivers while tests bind deterministic fakes.

This file ships BOTH the Protocols (the contract) and small deterministic FAKES (so
``examples/test_music_capability.py`` runs with no ffmpeg / Postgres / R2 / network).
A real deployment would register production drivers via
``Engine(..., drivers={"audio": RealAudioDriver(), ...})``.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from agency.capability import Driver


# ─────────────────────────── the five Driver protocols ───────────────────────────
@runtime_checkable
class StateDriver(Driver, Protocol):
    """Album/track state persistence (bitwize's unified state cache)."""
    def get(self, key: str) -> dict | None: ...
    def put(self, key: str, value: dict) -> None: ...


@runtime_checkable
class TextDriver(Driver, Protocol):
    """Pure text analysis (syllables, pronunciation) — no external process."""
    def syllables(self, word: str) -> int: ...


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
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        return self._store.get(key)

    def put(self, key: str, value: dict) -> None:
        self._store[key] = dict(value)


class FakeTextDriver:
    _VOWELS = "aeiouy"

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
