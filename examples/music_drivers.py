"""DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music drivers graduated from ``examples/music_drivers.py`` into
``agency/capabilities/music/drivers.py`` as part of the Spec 094
migration. This shim preserves third-party imports during the migration
cycle and is removed in Spec 110 (or when no external import survives
a grep — whichever first).

Migrate imports::

    # before
    from examples.music_drivers import fake_drivers, FakeStateDriver

    # after
    from agency.capabilities.music.drivers import fake_drivers, FakeStateDriver
"""
from __future__ import annotations

import warnings

from agency.capabilities.music.drivers import (  # noqa: F401
    AudioDriver,
    CloudDriver,
    DBDriver,
    FakeAudioDriver,
    FakeCloudDriver,
    FakeDBDriver,
    FakeStateDriver,
    FakeTextDriver,
    StateDriver,
    TextDriver,
    fake_drivers,
)

warnings.warn(
    "examples.music_drivers is deprecated since Spec 094 — import from "
    "agency.capabilities.music.drivers instead. This shim is removed in Spec 110.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AudioDriver",
    "CloudDriver",
    "DBDriver",
    "FakeAudioDriver",
    "FakeCloudDriver",
    "FakeDBDriver",
    "FakeStateDriver",
    "FakeTextDriver",
    "StateDriver",
    "TextDriver",
    "fake_drivers",
]
