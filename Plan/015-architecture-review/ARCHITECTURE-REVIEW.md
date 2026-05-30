# Architecture Review

This document contains a multi-perspective review of the agency Claude Code plugin architecture, summarizing the strengths, weaknesses, and structural feedback found during the dogfooding and testing of the system.

## Strengths

1. **Strict Ontology:** The strict ontology prevents drift. In my dogfooding via code-mode, my first run of `capability_reflect_note` failed exactly because I provided a `scope` (`cli`) that wasn't in the explicit list of ENUMS. The error message `Reflection record violates ontology: ["scope='cli' not in ['observation', 'project', 'reflection', 'technical', 'user', 'world']"]` accurately diagnosed it (`agency/memory.py:73`).
2. **Harness-in-Harness code-mode:** Harness-in-harness acts as a powerful composition tool for executing complex scripts. By using `agency.cli`, we are able to compose commands into python scripts seamlessly such as `echo 'r = await call_tool(...); return r' | python -m agency.cli --db /tmp/dog.db execute` (`agency/cli.py:46`).
3. **Pydantic Validation:** In code-mode, running tools incorrectly leads to explicit error messages about the validation missing such as missing keyword arguments. For example: `Missing required keyword only argument... tags: Unexpected keyword argument` (`fastmcp/server/server.py:1274`).

## Weaknesses

1. **`graph-vs-file-misuse`**: The `dogfood.collect` flow relies heavily on creating `DOGFOOD-NOTES.md` markdown ledgers rather than storing the knowledge natively in the bi-temporal graph. `agency/capabilities/dogfood.py:108` manually parses and walks file paths reading the file contents directly using `with open()`. The graph must be the primary store instead of disk files.
2. **`graph-vs-file-misuse`**: The core mechanism for the plugin capabilities generates artifacts and writes to files explicitly on disk, violating the graph paradigm where files should be rendered views. For example, `agency/install.py:145` writes to files via `with open(path, "w") as f:` directly.
3. **`token-leak`**: The `agency.cli` code-mode engine returns executed output via `sys.stdout` but when querying without returning specific keys, the CLI will format and stringify the entire Python dictionary containing full tracebacks or nested schemas directly (`agency/cli.py:27`). This leaks tokens on subsequent chained operations or debugging if an error trace is large.
4. **`vision-drift`**: The engine explicitly unwraps output dictionaries in `agency/engine.py:85`: `out = result["result"] if isinstance(result, dict) and "result" in result else result`. This causes functions like `capability_reflect_note` to return a raw string `ID` instead of a dictionary with a `reflection_id` key, removing consistency and making trial and error necessary for writing code-mode execution scripts.
5. **`test-gap`**: There are extensive tests for `jules` skills in `tests/test_jules_skills_*.py`, but no tests were found specifically for the `plugin-dev` capability inside `agency/capabilities/plugin.py:80` `PLUGIN_DEV_SKILL`.
6. **`missing-capability`**: Given the `graph-vs-file-misuse`, there lacks a `dogfood.render` capability to extract observations stored as `Reflection` nodes natively and emit markdown on demand.