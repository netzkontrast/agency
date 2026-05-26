# agency-seed — the running proof

A **running** proof of the v4 core (see [`../docs/vision/CORE.md`](../docs/vision/CORE.md))
on the **real substrate** — `graphqlite` (SQLite + Cypher) + `fastmcp` (incl. the
experimental code-mode transform). Built after the adversarial spec panel's
unanimous verdict: *stop spec'ing, build the smallest thing that proves the moat
and falsifies the risks.*

This is the repo's first RUNNING code: **6/6 green on graphqlite + fastmcp**
(`tests/test_seed.py`).

## What it proves (`tests/test_seed.py`, 6/6 green)

1. **The moat — cross-concern provenance is one graph traversal.**
   `Memory.provenance(intent)` returns, in one Cypher walk, every action that
   `SERVES` the intent, the agent that `PERFORMED_BY` it, the artefact it
   `PRODUCES`d, and the gate it `PASSED`. A flat SDK + memory-tool stack needs a
   join across four systems for this. *(`test_provenance_moat`)*
2. **One graph + the verb frame carry two genuinely different capabilities** — a
   stateless `transform` (`count_syllables`) and an `agent` (`jules`). This is
   the panel's falsifier; it holds. *(in `test_provenance_moat`)*
3. **Bi-temporal memory** — the *what* changes while the *why* holds; the prior
   version is reconstructable `as_of` an earlier tick (append-only `supersede`).
   *(`test_bitemporal_what_changes_why_holds`)*
4. **`COMPLETED ≠ done`** — the jules silent-fail lesson as a first-class
   `verify` step. *(`test_completed_not_done`)*
5. **Four-verb engine over real FastMCP** — MCP-conformant tool names
   (`<concept>_<capability>_<verb>`, underscores, ≤64, no dots).
   *(`test_four_verb_engine_real_fastmcp`)*
6. **Code-mode tool-chaining = an executable graph.** An `execute` block chains
   `transform → agent` in plain Python; the raw tools are hidden behind
   `search` / `get_schema` / `execute`; 4 tool calls run in-sandbox and only a
   single small delta crosses into context (**token efficiency** — the −98%
   pattern), while every call records an Invocation, so the executable dataflow
   graph is **mirrored into the durable provenance graph**.
   *(`test_codemode_chaining_is_an_executable_graph`)*
7. **Gate/elicitation human-in-the-flow** — a gate ELICITS a decision mid-flow
   (`ctx.elicit`): a one-line prompt streams to the human/agent, the answer
   resumes the chain, and the outcome is recorded as a `Gate` in the provenance
   graph. The atomic, token-tiny human-in-the-loop step.
   *(`test_gate_elicits_human_in_flow`)*

> Six test functions cover these seven proofs (the moat test carries both proof
> 1 and the two-capabilities falsifier 2).

## Run

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Layout

| File | Concept |
|---|---|
| `agency_seed/memory.py` | **Memory** — bi-temporal graph on GraphQLite; `record·link·supersede` / `recall·find·validate`; `project` (budgeted); `provenance` (the moat) |
| `agency_seed/intent.py` | **Intent** — `capture·confirm·amend` (why/what merged) |
| `agency_seed/lifecycle.py` | **Lifecycle** — `open·move·complete·status`; A2A-aligned states; agent parameterization; gates |
| `agency_seed/capability.py` + `capabilities/` | **Capability** — open verbs, role-tagged `act·transform·effect`; `syllables` (transform), `jules` (agent) |
| `agency_seed/engine.py` | **Engine** — FastMCP four-verb surface + optional code-mode transform |

> Status: a proof-of-concept seed, not the shipped engine. It exists to make the
> v4 claims *runnable and falsifiable* rather than spec-only.
