"""Spec 181 Slice 1 — typed EmbedderHandle tests."""
from __future__ import annotations

import pytest

from agency._embedder_handle import EmbedderBackend, EmbedderHandle


def test_typed_shape_ready():
    h = EmbedderHandle(name="tfidf", dim=128, backend="tfidf", ready=True)
    assert h.dim == 128
    assert h.backend == "tfidf"


def test_typed_shape_not_ready_requires_hint():
    h = EmbedderHandle(name="bge", dim=0, backend="bge-small",
                        ready=False, hint="pip install agency[recall]")
    assert h.ready is False
    assert "install" in h.hint


def test_rejects_empty_hint_when_not_ready():
    with pytest.raises(ValueError):
        EmbedderHandle(name="x", dim=0, backend="tfidf",
                        ready=False, hint=None)
    with pytest.raises(ValueError):
        EmbedderHandle(name="x", dim=0, backend="tfidf",
                        ready=False, hint="")


def test_rejects_invalid_backend():
    with pytest.raises(ValueError):
        EmbedderHandle(name="x", dim=10, backend="bogus", ready=True)


def test_rejects_zero_dim_when_ready():
    with pytest.raises(ValueError):
        EmbedderHandle(name="x", dim=0, backend="tfidf", ready=True)


def test_rejects_negative_dim():
    with pytest.raises(ValueError):
        EmbedderHandle(name="x", dim=-1, backend="tfidf", ready=True)


def test_rejects_empty_name():
    with pytest.raises(ValueError):
        EmbedderHandle(name="", dim=10, backend="tfidf", ready=True)


def test_backend_set_equals_documented():
    """Valid backends: {tfidf, bge-small, bge-large, openai}."""
    assert set(EmbedderBackend.__args__) == {
        "tfidf", "bge-small", "bge-large", "openai"}
