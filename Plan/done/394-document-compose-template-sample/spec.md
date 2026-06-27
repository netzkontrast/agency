<!-- agency-node: document:8056d949 -->
---
spec_id: "394"
slug: document-compose-template-sample
status: done
state: done
last_updated: 2026-06-23
title: document.compose — deterministic template scaffold + MCP-sampled custom sections
owner: "@agency"
vision_goals: [7, 9]
---

# Spec 394 — `document.compose`: the template + custom-sampled mix

## Why

Documentation generation in agency has two halves that never met in ONE verb:

- **Deterministic templates** — `document.render` (fixed graph scopes),
  `document.explain` (code → markdown), `document.index_repo`. Pure, reproducible
  projections. No prose a projection can't derive.
- **Custom sampled prose** — `ctx.host.sample` (Spec 285 HostBridge) can author the
  narrative a projection can't derive (rationale, "why it matters", caveats), but
  nothing assembles it WITH a deterministic scaffold.

The owner's ask: *"improve documentation generation — with MCP tool and sample
calls via MCP, a mix of templates and custom sampled parts."* That is exactly a
compose step: a deterministic base + named sampled sections, written as ONE
round-trippable Document.

## What

A new `document.compose` verb (role `effect`):

```
compose(scope="", target="", sections=[{heading, prompt}],
        apply_path="", system="") -> {document_id, revision_id, written,
                                       action, scaffold_tokens, sampled, degraded}
```

- **Scaffold (deterministic):** `scope` → `self.render(scope)`; else `target` →
  `self.explain(target)`; else empty. This is the template half — verbatim,
  reproducible.
- **Sampled sections (custom):** each `sections` entry is `{heading, prompt}`. The
  body is produced by `ctx.host.sample(messages, system=…)` GROUNDED in the
  scaffold (the scaffold is passed as context so the model writes ABOUT the real
  state, not from thin air). `param_shapes={"sections": "[{heading, prompt}]"}`
  (dogfoods Spec 390 so `get_schema` shows the shape).
- **Graceful degradation (honest signal — Spec 391):** when no sampling-capable
  host is bound (CLI / bare tests / a client that declines sampling), the section
  is emitted as a template PLACEHOLDER that PRESERVES its prompt
  (`<!-- AGENT: sample — {prompt} -->`), and `degraded=True`. The document still
  assembles + round-trips; the sampled prose is simply deferred to an agent that
  has a host. Never a hard failure.
- **Convergence:** the assembled markdown is emitted via the existing
  `_emit_graph_document` (keep-both `DocRevision`, stable anchor, SERVES the
  intent). The clarity gate stays SEPARATE — a later `document.ingest`/`sync`
  prompt-audits the body — so the sampler never optimizes against its own score
  (anti-overfitting, the loop-library rule).

## Acceptance (behaviour, not implementation)

1. **Mix:** with a sampling-capable host bound, `compose(scope=…, sections=[…])`
   returns a Document whose body contains BOTH the deterministic scaffold AND a
   `## {heading}` block carrying the sampled body; `degraded=False`.
2. **Grounding:** the sampled call receives the scaffold as context (the prompt
   the host sees mentions the scaffold), so sampled prose is about real state.
3. **Degradation:** with NO host bound, `compose` still emits a Document,
   `degraded=True`, and each placeholder PRESERVES its section prompt (rule 9 —
   captured intent is not dropped).
4. **Round-trip:** the emitted Document is a keep-both peer — `document.revisions`
   shows the appended revision; re-composing identical content appends none.

## Followup — Implementation Status (2026-06-23)

- **Done:** `compose` verb shipped on `DocumentCapability`; `param_shapes` on
  `sections`; sampled + degraded paths; emit via `_emit_graph_document`.
  `tests/test_document_compose.py` (sampled-mix · degraded-preserves-prompt ·
  round-trip). README refreshed to current state (36 caps / 474 verbs / state
  folders / workflow+adr). `agency_reload` repo-root no-op caveat noted.
- **Still:** owner ADR-approve + done-cascade on merge; wire a `develop-spec`
  doc-generation discipline skill that drives compose over stale docs.
