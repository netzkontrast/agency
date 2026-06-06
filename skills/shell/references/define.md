<!-- agency-generated: v1 -->
# shell.define

Define a named shell template (command + output filter + doc) in the graph.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name, command (first token allowlisted), filter (output slice — full|tail` |  | N|head:N|grep:PAT|lines:A-B|count|last), doc, tags (space/comma-separated, for discovery). |

## Returns

``{name, template_id, command, filter}``; or ``{error, …}`` on a disallowed tool / unparseable command.

## Chain-next

``shell.run(template=<name>)`` or ``shell.templates(query=)``.

## Details

Records an ``Artefact{kind:"command-template", name, command, filter, doc, tags}`` so the registry is definable (CLAUDE.md #8), not a frozen dict. Re-defining a name SUPERSEDES the prior version (bi-temporal trail kept). The command's first token MUST be allowlisted — a template can't smuggle an un-allowlisted tool into ``run``.

## Example

```bash
agency-shell-define --intent-id $IID …
```
