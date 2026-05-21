---
slug: vision-readme
type: vision-index
status: ready
summary: Entry point and reading order for the design canon. This canon is authoritative; code serves it.
---

# Vision — design canon

The single source of truth for the agency plugin. Code serves this canon; where
code and canon disagree, the canon wins.

## Read in order

1. **[OVERVIEW.md](OVERVIEW.md)** — the model: three exported domains, capability
   rows nested in their owning domain, name derivation.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — the runtime: one engine (FastMCP), one
   graph (GraphQLite), workflows as graph paths, drivers, CodeMode.
3. **[VOCABULARY.md](VOCABULARY.md)** — canonical terms.
4. **[specs/](specs/README.md)** — the contracts implementation must satisfy.
5. **[LESSONS.md](LESSONS.md)** — durable engineering knowledge.

Forward work is tracked in [`../ROADMAP.md`](../ROADMAP.md).
