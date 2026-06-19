"""Acceptance — no-truncate-or-paginate data fidelity (Spec 336 S1).

Behaviour: `paginate` returns one page + a read-continuation cursor + instruction,
and walking the cursor reconstructs the COMPLETE set — the tail is reachable, never
truncated. The complement of `keep_full` (full stored data) for bounded returns.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from agency._capture import paginate

scenarios("features/fidelity.feature")


@given(parsers.parse("a sequence of {n:d} items"), target_fixture="items")
def _items(n):
    return list(range(n))


@when(parsers.parse("I paginate it with page size {size:d}"), target_fixture="result")
def _paginate(items, size):
    return paginate(items, cursor=0, page_size=size)


@when(parsers.parse("I walk every page at page size {size:d}"), target_fixture="walked")
def _walk(items, size):
    out, cursor = [], 0
    # Bounded loop: every iteration consumes ≥1 item or the set is exhausted.
    for _ in range(len(items) + 1):
        r = paginate(items, cursor=cursor, page_size=size)
        out.extend(r["page"])
        if not r["read_more"]:
            break
        cursor = r["next_cursor"]
    return out


@then(parsers.parse("the page holds all {n:d} items"))
def _page_all(result, n):
    assert len(result["page"]) == n


@then(parsers.parse("the page holds {n:d} items"))
def _page_n(result, n):
    assert len(result["page"]) == n


@then("the read-more instruction is empty")
def _no_more(result):
    assert result["read_more"] == ""


@then(parsers.parse("the read-more instruction names cursor {c:d}"))
def _names_cursor(result, c):
    assert result["read_more"], "expected a non-empty read-more instruction"
    assert f"cursor={c}" in result["read_more"], result["read_more"]


@then(parsers.parse("the reported remaining count is {n:d}"))
def _remaining(result, n):
    assert result["remaining"] == n


@then(parsers.parse("the walked set equals the original {n:d} items"))
def _walked_complete(walked, n):
    assert walked == list(range(n)), f"dropped/duplicated data: {walked}"
