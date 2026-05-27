# Architecture Critique & Findings

This document summarizes the architectural findings based on the exhaustive ingestion of the `agency` codebase and relevant parts of `the-agency-system` reference repository.

## 1. Object Model Decomposition

### The Current State
The PR1 implementation has established a powerful "code-mode is the contract" foundation. Its primary components:
- **Capability/CapabilityBase/CapabilityContext**: Well-designed for extensibility (`agency/capability.py:23` and `agency/capability.py:106`). Capabilities self-register via reflection.
- **Registry & SkillRun**: Skill execution relies on dictionary schemas rather than strictly typed structures (`agency/skill.py:40`).
- **OntologyExtension**: Centralizes domain-specific semantics.

### Seams and Smells
- **Ad-hoc Return Types**: Capabilities and internal engine tools do not share a common result shape (`agency/engine.py:112` and capability verb returns). This will lead to brittle string parsing by clients.
- **Dict-Typed Phases**: `agency/skill.py:40` (`def current(self) -> Optional[dict]`) models phases as dictionaries. This lacks encapsulation and makes validation logic implicit rather than object-oriented.
- **Scattered Boundaries**: While `JulesBackend` (`agency/capabilities/jules.py:19`) and `VCSBackend` (`agency/capabilities/_vcs.py:24`) are excellent injections, they are not unified under a single driver or boundary protocol, leading to duplication in how tests mock them.
- **Stringly-Typed Errors**: Errors thrown across the module rely on generic python Exceptions which cannot be robustly evaluated by programmatic loop-recovery heuristics.

## 2. Pre-mortem Inversion

**"In six months PR1 was abandoned/rewritten — what design flaw caused it?"**
The most likely cause of a rewrite would be the rigidity and fragility of the internal data pipelines. Specifically, if the engine cannot reliably distinguish between a failed action, a requirement for more data, or a successfully completed phase without complex heuristic string matching, the orchestration layer will collapse under edge cases. The lack of typed error handling and a standardized `ToolResult` envelope are the critical vectors for this failure.

Because `Skill` phases are dictionaries (`agency/skill.py:48` `submit(self, outputs: Optional[dict])`), developers cannot confidently rely on type checkers to catch broken execution states.
