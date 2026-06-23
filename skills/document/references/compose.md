<!-- agency-generated: v1 -->
# document.compose

Compose a doc from a DETERMINISTIC scaffold + CUSTOM SAMPLED sections (Spec 394).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (render scope) XOR target (explain target) for the scaffold, sections (list of {heading, prompt}), apply_path (target .md), system (optional system prompt for every sampled section).` |  |  |

## Returns

``{document_id, revision_id, written, action, scaffold_tokens, sampled, degraded}``.

## Chain-next

``document.ingest``/``sync`` to prompt-audit the body, then commit.

## Details

The template+sample MIX in ONE verb — the owner's "templates plus custom sampled parts via MCP". The scaffold is a reproducible projection: ``scope`` → ``render`` (a graph scope) XOR ``target`` → ``explain`` (code→markdown). Each ``sections`` entry is a ``{heading, prompt}`` whose body is authored by an MCP ``ctx.host.sample`` call GROUNDED in that scaffold (so the prose is about real state, not thin air). Degrades honestly (Spec 391): with no sampling-capable host the section becomes a placeholder that PRESERVES its prompt (``<!-- AGENT: sample — … -->``, rule 9) and ``degraded=True`` — the document still assembles + round-trips. Emitted via the keep-both ``_emit_graph_document`` (anchor + DocRevision + SERVES); the clarity gate stays a SEPARATE ``ingest``/``sync`` pass so the sampler never optimizes its own audit score.

## Example

```bash
agency-document-compose --intent-id $IID …
```
