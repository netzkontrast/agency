# Testing doctrine — behaviour, not implementation

> Vision canon (owner directive, 2026-06-13). The agency test suite verifies
> what the system **does**, never how it is **built**. This is part of the
> Vision: tests are a behavioural contract, not a mirror of the code.

## The rule

**We only test behaviour.** No unit tests coupled to internal workings — no
asserting on private methods, call shapes, or structure. A test that breaks when
you *refactor without changing behaviour* is testing the wrong thing.

## The form — Gherkin acceptance scenarios

Behaviour is specified as **Given / When / Then** `.feature` scenarios
(`tests/acceptance/`, run via `pytest-bdd`). A scenario reads as a fact about the
system an outside observer could confirm:

- *Given a fresh engine in code-mode, When a client lists tools, Then it sees
  exactly search / get_schema / execute* (the wire contract).
- *Given a confirmed intent, When I invoke a verb, Then an Invocation SERVES the
  intent* (provenance — the moat).

The scenarios double as the **acceptance criteria** shared with implementing
agents: the behavioural contract is explicit, in plain language.

## Co-evolution

Behaviour legitimately evolves. When a valid, good change moves a behaviour a
scenario pinned, the **scenario is updated** to the new contract. When a change
breaks observable behaviour or a Vision goal, the scenario **stays red** and the
change is flagged. Assert **relationships/invariants**, never frozen snapshots
(CLAUDE.md rule 8) — e.g. "the verb surface is substantial", not "exactly 73".

## What is NOT a test

Structural cleanliness — OOP separation, module boundaries, "no raw graph
access in capabilities", capability-per-folder — is verified by **code review**,
not automated tests. It is craft, judged by a reviewer reading the code, not a
behavioural fact.

## The gate

During a large refactor the GitHub CI workflow may be disabled; the acceptance
suite is then run continuously (in the background, against the working branch)
by the reviewer, who is the gate. The refactor is "done" when every acceptance
scenario passes (behaviour preserved + features working) and the code reads
cleanly on review. CI is re-enabled when the refactor lands.
