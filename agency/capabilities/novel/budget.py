import json
import uuid
from typing import Any, Dict, List, Optional
from agency.toolresult import ToolResult, TypedError

MAX_BODY_BYTES = 4000

_OVERFLOW_STORE: Dict[str, List[Dict[str, Any]]] = {}

class Codes:
    FIELDS_UNKNOWN = "FIELDS_UNKNOWN"
    OVERFLOW_HANDLE_MISSING = "OVERFLOW_HANDLE_MISSING"
    PREFIX_BUDGET_EXCEEDED = "PREFIX_BUDGET_EXCEEDED"

def project_fields(items: List[Dict[str, Any]], fields: Optional[List[str]]) -> List[Dict[str, Any]]:
    if not fields:
        return items
    projected = []
    for item in items:
        for f in fields:
            if f not in item:
                raise ValueError(f"Unknown field: {f}")
        projected.append({k: v for k, v in item.items() if k in fields})
    return projected

def apply_output_budget(
    work_id: str,
    schema_version: str,
    capability_set_hash: str,
    items: List[Dict[str, Any]],
    fields: Optional[List[str]] = None,
    max_bytes: int = MAX_BODY_BYTES
) -> ToolResult:
    try:
        projected_items = project_fields(items, fields)
    except ValueError as e:
        unknown_field = str(e).split(": ")[1]
        return ToolResult(
            data=None,
            ok=False,
            error=TypedError(code=Codes.FIELDS_UNKNOWN, message=f"Unknown field requested: {unknown_field}")
        )

    rendered_body_bytes = len(json.dumps(projected_items))

    shown_items = projected_items
    overflow_handle = None

    if rendered_body_bytes > max_bytes:
        shown_items = []
        current_bytes = len(json.dumps([]))

        for item in projected_items:
            item_bytes = len(json.dumps([item])) - len(json.dumps([]))
            if current_bytes + item_bytes > max_bytes and len(shown_items) > 0:
                break
            shown_items.append(item)
            current_bytes += item_bytes

        overflow_handle = f"overflow:{uuid.uuid4().hex}"
        _OVERFLOW_STORE[overflow_handle] = projected_items

    result = {
        "prefix": {
            "work_id": work_id,
            "schema_version": schema_version,
            "capability_set_hash": capability_set_hash
        },
        "body": {
            "items": shown_items,
            "total": len(items),
            "shown": len(shown_items),
            "overflow_handle": overflow_handle,
            "next_cursor": None
        }
    }

    return ToolResult(data=result)

def recall_overflow(handle: str, grep: str = "") -> ToolResult:
    if handle not in _OVERFLOW_STORE:
        return ToolResult(
            data=None,
            ok=False,
            error=TypedError(code=Codes.OVERFLOW_HANDLE_MISSING, message="Overflow handle missing or expired")
        )

    items = _OVERFLOW_STORE[handle]
    if grep:
        items = [item for item in items if grep in json.dumps(item)]

    return ToolResult(data={"items": items})
