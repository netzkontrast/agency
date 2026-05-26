---
slug: vision-readme
type: vision-index
status: ready
summary: Entry point and reading order for the design canon. This canon is authoritative; code serves it. This repo is the initial Concept, Vision (v2.1, four-domain 5W1H model), and Plan.
---

# Vision — design canon (v2.1)

The single source of truth for the agency plugin. Code serves this canon; where
code and canon disagree, the canon wins. At this stage the repo is the
**Concept, the Vision canon, and the Plan** — all documentation; implementation
follows.

This canon describes the **v2.1 four-domain 5W1H model**: the human owns
**Why / What = INTENT**; the engine executes **who / how / when / where** as
four isomorphic domains, over one FastMCP engine and one GraphQLite graph.

## Read in order

1. **[OVERVIEW.md](OVERVIEW.md)** — the model: intent + four domains
   (who / how / when / where); the two-axis canonical verb frame; capabilities
   authored in one home domain and expressed across the four as aspects
   (lazy-domaining); the self-describing naming scheme.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — the runtime: one engine (FastMCP)
   with its four-verb meta-contract and code-mode call surface; one graph
   (GraphQLite, bi-temporal, append-only); engine guards; and the
   context-engineering commitments the engine honors.
3. **[VOCABULARY.md](VOCABULARY.md)** — canonical terms (intent, who, how, when,
   where, capability, home domain, aspect, lazy-domaining, the two verb axes,
   DRIVES, dispatcher-vs-dispatchee, engine guards, `where.project`, naming).
4. **[EXAMPLE.md](EXAMPLE.md)** — a worked walkthrough ("fix the failing auth
   test, via jules") tracing intent through who / how / when / where. A spec
   walkthrough, NOT a shipped path.
5. **[specs/](specs/README.md)** — the per-system-part contracts.
6. **[LESSONS.md](LESSONS.md)** — durable engineering knowledge.

Forward work is tracked in [`../ROADMAP.md`](../ROADMAP.md).

## Scope

The Vision DOCUMENTS the entire four-domain model. The buildable/committed
slice is MINIMAL: `jules` anchored in `who`, one authored aspect, the rest lazy,
plus the worked example. Everything else is **"specced — not built."**
