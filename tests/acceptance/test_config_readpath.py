"""Acceptance — unified config read-path unification (Spec 334 Slice 6).

Behaviour: a capability's own `*.load()` consults the unified `config_get`
as a live-but-lowest-priority source. Cap-local nested file wins; then the
unified `.agency/config.yaml`; then the built-in dataclass default. Editing the
unified file invalidates the cap's mtime-keyed load cache. Drives the real
`NovelConfig.load` / `MusicConfig.load`, the same way test_config.py drives
agency._config directly.
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _config
from agency.capabilities.music import config as music_config
from agency.capabilities.novel import config as novel_config

scenarios("features/config_readpath.feature")

_CONFIG_CLS = {"novel": novel_config.NovelConfig, "music": music_config.MusicConfig}
_DEFAULT_ROOT = {"novel": novel_config._DEFAULT_CONTENT_ROOT,
                 "music": music_config._DEFAULT_CONTENT_ROOT}


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    # Isolate the caches that persist across tests, point the unified config at a
    # tmp path, and clear the cap env-dir overrides so only the explicit search
    # path + the unified file are in play.
    novel_config._LOAD_CACHE.clear()
    music_config._LOAD_CACHE.clear()
    _config._READ_CACHE.clear()
    unified = str(tmp_path / ".agency" / "config.yaml")
    monkeypatch.setenv("AGENCY_CONFIG", unified)
    monkeypatch.delenv("AGENCY_NOVEL_HOME", raising=False)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    return {"tmp": tmp_path, "unified": unified,
            "search": {"novel": [str(tmp_path / "absent-novel.yaml")],
                       "music": [str(tmp_path / "absent-music.yaml")]},
            "loaded": {}}


@given(parsers.parse('no cap-local config for "{cap}"'))
def _no_cap_local(ctx, cap):
    ctx["search"][cap] = [str(ctx["tmp"] / f"absent-{cap}.yaml")]


@given(parsers.parse('a cap-local "{cap}" config with content_root "{value}"'))
def _cap_local(ctx, cap, value):
    p = ctx["tmp"] / f"{cap}-local.yaml"
    p.write_text(f"paths:\n  content_root: {value}\n")
    ctx["search"][cap] = [str(p)]


@given(parsers.parse('the unified config sets "{dotted}" to "{value}"'))
@when(parsers.parse('the unified config sets "{dotted}" to "{value}"'))
def _unified_set(ctx, dotted, value):
    _config.config_set(dotted, value, path=ctx["unified"])


@given("the unified config is empty")
def _unified_empty(ctx):
    return ctx


@given(parsers.parse('I load the "{cap}" config'))
@when(parsers.parse('I load the "{cap}" config'))
def _load(ctx, cap):
    ctx["loaded"][cap] = _CONFIG_CLS[cap].load(search_paths=ctx["search"][cap])


@then(parsers.parse('the loaded content_root is "{value}"'))
def _check_root(ctx, value):
    cap = next(iter(ctx["loaded"]))
    assert ctx["loaded"][cap].content_root == value, ctx["loaded"][cap].content_root


@then(parsers.parse('the loaded content_root is the "{cap}" default'))
def _check_default(ctx, cap):
    expected = os.path.expanduser(_DEFAULT_ROOT[cap])
    assert ctx["loaded"][cap].content_root == expected, ctx["loaded"][cap].content_root
