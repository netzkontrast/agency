# Mode A preamble — dogfood (self-dispatch)

<!-- AGENT: This preamble prepends to a Jules dispatch when the source
matches DISPATCH_SELF_SOURCE (the agency repo dispatching against
itself). Mode A relies on Jules's lexical scoping to inherit
AGENTS.md + AGENCY_PROTOCOL.md from the cloned agency repo —
do NOT prepend an explicit READ-ONLY clone block here. -->

You are operating against the **agency** repo itself.

Read the operational docs Jules already cloned next to your working
copy:

- `AGENTS.md` — the operational doctrine (this session's contract).
- `AGENCY_PROTOCOL.md` — the remote-agent doctrine (your agreement
  with the orchestrator).
- `CLAUDE.md` — the in-repo rules (Rules 1-7).

<!-- AGENT: After Jules reads the docs, the dispatched task body
below applies in the dogfood context — the engine + capability code
+ test suite are in scope. -->

$task_body

<!-- AGENT: Before submit, run `python -m pytest -q -m "not e2e"` and
include the result in your reply. Per AGENCY_PROTOCOL §9, end every
reply with `reply_to_pr_comments(...)` so the orchestrator's poll loop
sees your push. -->
