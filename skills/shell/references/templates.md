<!-- agency-generated: v1 -->
# shell.templates

Discover named query templates — built-in seeds ∪ graph-defined (Spec 075).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (optional — matches name/doc/tags, case-insensitive; ""=all).` |  |  |

## Returns

``{result: [{name, command, filter, doc, tags, source}, …]}`` (``source`` ∈ seed|graph), name-sorted; ranked by match locus when a query is given.

## Chain-next

``shell.run(template=<name>)`` or ``shell.define(…)`` to add one.

## Details

(no further detail)

## Example

```bash
agency-shell-templates --intent-id $IID …
```
