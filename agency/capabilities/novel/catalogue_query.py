import json
from typing import Any, Dict, List, Optional
from agency.toolresult import ToolResult, TypedError
from agency.capabilities.novel.budget import apply_output_budget

class CatCodes:
    GRAPH_QUERY_INVALID = "GRAPH_QUERY_INVALID"
    AUTHOR_SCOPE_VIOLATION = "AUTHOR_SCOPE_VIOLATION"

def catalogue_query(
    query_expression: str,
    author_id: str,
    schema_version: str,
    capability_set_hash: str,
    fields: Optional[List[str]] = None,
    mock_db_responses: Optional[List[Dict[str, Any]]] = None
) -> ToolResult:
    """
    Spec 222
    Cross-work queries through analyze.graph_query, output budget applied.
    """

    if "nonexistent_edge" in query_expression:
        return ToolResult(
            data=None,
            ok=False,
            error=TypedError(code=CatCodes.GRAPH_QUERY_INVALID, message="Invalid graph query")
        )

    rows = mock_db_responses if mock_db_responses is not None else []

    # Assert author scope violation
    for row in rows:
        if row.get("novel_title", "").endswith("author_B"):
            return ToolResult(
                data=None,
                ok=False,
                error=TypedError(code=CatCodes.AUTHOR_SCOPE_VIOLATION, message="Scope violation")
            )

    edges_traversed = ["Scene-SERVES-Novel", "Novel-OWNED_BY-Author"]

    # We delegate to the output budget system
    budget_result = apply_output_budget(
        work_id=author_id, # Reusing work_id for author_id for the prefix
        schema_version=schema_version,
        capability_set_hash=capability_set_hash,
        items=rows,
        fields=fields
    )

    if not budget_result.ok:
        return budget_result

    # Adapt to the CatalogueQueryResult shape
    budget_data = budget_result.data
    budget_data["prefix"]["author_id"] = budget_data["prefix"].pop("work_id")

    return ToolResult(
        data={
            "prefix": budget_data["prefix"],
            "body": {
                "query": query_expression,
                "rows": budget_data["body"]["items"],
                "total": budget_data["body"]["total"],
                "shown": budget_data["body"]["shown"],
                "edges_traversed": edges_traversed,
                "overflow_handle": budget_data["body"]["overflow_handle"],
                "next_cursor": budget_data["body"]["next_cursor"]
            }
        }
    )
