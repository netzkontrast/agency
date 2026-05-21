---
slug: vision-readme
type: vision-index
status: ready
summary: Entry point and reading order for the design canon. This canon is authoritative; code serves it. This repo is the initial Concept, Vision, and Plan.
---

# Vision — design canon

The single source of truth for the agency plugin. Code serves this canon; where
code and canon disagree, the canon wins. At this stage the repo is the
**Concept, the Vision canon, and the Plan**; implementation follows.

## Read in order

1. **[OVERVIEW.md](OVERVIEW.md)** — the model: one engine, three domains
   (`agentic`, `workflow`, `context`); capabilities authored in one home domain
   and expressed across the domains as aspects; lazy-domaining; name derivation.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — the runtime: one engine (FastMCP),
   one graph (GraphQLite), workflows as graph paths, drivers, CodeMode, and the
   context-engineering commitments the engine honors.
3. **[VOCABULARY.md](VOCABULARY.md)** — canonical terms (domain, capability,
   home domain, aspect, lazy-domaining, naming, cross-capability dispatch).
4. **[specs/](specs/README.md)** — the contracts implementation must satisfy.
5. **[LESSONS.md](LESSONS.md)** — durable engineering knowledge.

Forward work is tracked in [`../ROADMAP.md`](../ROADMAP.md).
