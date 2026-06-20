import pytest
from agency.capabilities.novel.catalogue_query import catalogue_query, CatCodes
from agency.capabilities.novel.budget import MAX_BODY_BYTES, Codes as BudgetCodes

def test_catalogue_query_budget_and_fields():
    rows = [{"title": "Scene 1", "novel_title": "Novel A", "wc": 500, "extra": "x"}]
    res = catalogue_query(
        "mock_query",
        "author_A",
        "1.0",
        "hash123",
        fields=["title", "novel_title", "wc"],
        mock_db_responses=rows
    )

    assert res.ok is True
    assert res.data["body"]["rows"] == [{"title": "Scene 1", "novel_title": "Novel A", "wc": 500}]
    assert "Scene-SERVES-Novel" in res.data["body"]["edges_traversed"]

def test_catalogue_query_author_scope_violation():
    rows = [{"title": "Scene 1", "novel_title": "Novel A_author_B", "wc": 500}]
    res = catalogue_query(
        "mock_query",
        "author_A",
        "1.0",
        "hash123",
        mock_db_responses=rows
    )

    assert res.ok is False
    assert res.error.code == CatCodes.AUTHOR_SCOPE_VIOLATION

def test_catalogue_query_invalid_graph_query():
    res = catalogue_query(
        "nonexistent_edge",
        "author_A",
        "1.0",
        "hash123"
    )

    assert res.ok is False
    assert res.error.code == CatCodes.GRAPH_QUERY_INVALID

def test_catalogue_query_unknown_field():
    rows = [{"title": "Scene 1", "novel_title": "Novel A"}]
    res = catalogue_query(
        "mock_query",
        "author_A",
        "1.0",
        "hash123",
        fields=["nonexistent_key"],
        mock_db_responses=rows
    )

    assert res.ok is False
    assert res.error.code == BudgetCodes.FIELDS_UNKNOWN
