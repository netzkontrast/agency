import pytest
from agency._research_citation import compute_citation_hash

def test_compute_citation_hash_deterministic():
    """Test that the same input produces the exact same hash across multiple calls."""
    url = "https://example.com"
    snippet = "This is a test snippet for the deterministic test."
    hash1 = compute_citation_hash(url, snippet)
    hash2 = compute_citation_hash(url, snippet)
    assert hash1 == hash2

def test_compute_citation_hash_length():
    """Test that the hash is exactly 16 characters long and is a string."""
    url = "https://example.com"
    snippet = "Length test snippet."
    hash_val = compute_citation_hash(url, snippet)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 16

def test_compute_citation_hash_change_sensitivity():
    """Test that different inputs (URL or snippet) produce different hashes."""
    url1 = "https://example.com/1"
    url2 = "https://example.com/2"
    snippet1 = "Snippet A"
    snippet2 = "Snippet B"

    # Same snippet, different URL
    assert compute_citation_hash(url1, snippet1) != compute_citation_hash(url2, snippet1)

    # Same URL, different snippet
    assert compute_citation_hash(url1, snippet1) != compute_citation_hash(url1, snippet2)

    # Different URL and snippet
    assert compute_citation_hash(url1, snippet1) != compute_citation_hash(url2, snippet2)

def test_compute_citation_hash_empty_strings():
    """Test that empty strings are handled correctly and produce a 16-char hash."""
    # Both empty
    hash_val = compute_citation_hash("", "")
    assert len(hash_val) == 16

    # One empty
    assert compute_citation_hash("", "snippet") != compute_citation_hash("url", "")

def test_compute_citation_hash_unicode():
    """Test that unicode characters in URL and snippet are correctly encoded and hashed."""
    url = "https://example.com/🚀"
    snippet = "Hello world! 🌍 Unicode text: 你好，世界！"
    hash_val = compute_citation_hash(url, snippet)
    assert len(hash_val) == 16

    # Must be deterministic with unicode
    assert compute_citation_hash(url, snippet) == hash_val

def test_compute_citation_hash_delimiter_collision():
    """Test the edge case where the delimiter '|' might cause collisions.

    Since the implementation uses `payload = "|".join([url, snippet])`,
    "a|b" and "c" becomes "a|b|c"
    "a" and "b|c" becomes "a|b|c"

    The hash *will* be identical due to the implementation.
    This test asserts the current behavior to prevent regressions if
    the hashing strategy is updated.
    """
    url1 = "a|b"
    snippet1 = "c"

    url2 = "a"
    snippet2 = "b|c"

    assert compute_citation_hash(url1, snippet1) == compute_citation_hash(url2, snippet2)
