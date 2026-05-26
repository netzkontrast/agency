---
slug: vision-readme
type: vision-index
status: ready
summary: Entry point and reading order for the design canon (v4). The authoritative model is CORE.md — four concepts (Intent, Capability, Lifecycle, Memory) + the Engine substrate. Supersedes the v2.1 three-domain model. The canon is authoritative; code serves it. A running seed lives in seed/.
---

# Vision — design canon (v4)

The single source of truth for the agency plugin. Code serves this canon; where
code and canon disagree, the canon wins. The repo holds the **Concept, the
Vision canon, the Plan — and the first running code** (the `agency/` package).

This canon describes the **v4 four-concept model**: the human owns the **Intent**;
the engine serves it through **Capability**, **Lifecycle**, and **Memory**, over
one FastMCP **Engine** and one bi-temporal GraphQLite graph. **5W1H is a lens,
not the architecture.**

> **Supersedes v2.1.** The earlier three-domain model (agentic / workflow /
> context) and the capability/aspect/lazy-domaining framing are superseded. An
> adversarial panel cut the six-domain 5W1H model to its irreducible core.

## Read in order

1. **[CORE.md](CORE.md)** — the authoritative v4 model, radically cut: four
   concepts + one substrate, skills as atomic gated step-graphs, what was dropped
   and why. **Read this first.**
2. **[OVERVIEW.md](OVERVIEW.md)** — the narrative model: Intent + Capability +
   Lifecycle + Memory; the isomorphic verb frame; 5W1H as a lens; the
   structure-first naming scheme.
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** — the runtime: one Engine (FastMCP)
   with code-mode as the contract (`search`/`get_schema`/`execute`); one graph
   (GraphQLite, bi-temporal, append-only); engine guards as middleware; the
   context-engineering commitments the engine honors.
4. **[VOCABULARY.md](VOCABULARY.md)** — canonical terms.
5. **[EXAMPLE.md](EXAMPLE.md)** — a worked walkthrough ("fix the failing auth
   test, via jules"), **now executable** in the `agency/` package.
6. **[specs/](specs/README.md)** — the per-part contracts (engine, intent,
   capability, lifecycle, memory, skills-and-gates).
7. **[PORTING-ROADMAP.md](PORTING-ROADMAP.md)** — every skill & function from the
   prototype plugins mapped to v4.
8. **[LESSONS.md](LESSONS.md)** — durable engineering knowledge.

Forward work is tracked in [`../ROADMAP.md`](../ROADMAP.md).

## Scope

The canon DOCUMENTS the full four-concept model. **v0.1** (the `agency/` package,
19/19 green) ships the engine, three capabilities (`plugin` / `jules` / `reflect`),
reflection-based self-registration, the extensible ontology, and the self-hosted
install — proving the moat (cross-concern provenance in one traversal), code-mode
tool-chaining, and gate/elicitation. Capabilities beyond those are specced — see
[CAPABILITY-CLUSTERS.md](CAPABILITY-CLUSTERS.md).
