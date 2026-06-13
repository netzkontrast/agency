# Mode B preamble — delegate (cross-repo dispatch)

<!-- AGENT: This preamble prepends to a Jules dispatch when the source
is ANY repo other than DISPATCH_SELF_SOURCE. Jules's lexical scoping
does NOT carry agency's operational docs into the target repo, so
this preamble MUST prepend an explicit READ-ONLY clone block that
makes those docs reachable. -->

You are operating against **$source** — an external repo. The agency
plugin's operational doctrine lives in a separate repo; read it from
the public clone before touching code:

```bash
git clone --depth=1 https://github.com/netzkontrast/agency.git \
  ~/work/vendor/agency
```

Then read (READ-ONLY — do not modify your clone of the agency repo):

- `~/work/vendor/agency/AGENTS.md` — operational doctrine.
- `~/work/vendor/agency/AGENCY_PROTOCOL.md` — remote-agent doctrine.
- `~/work/vendor/agency/CLAUDE.md` — engine rules.

<!-- AGENT: Mode B clones agency for READING. Do NOT install the
agency plugin into the target repo unless the task body explicitly
requests it. -->

$task_body

<!-- AGENT: Before submit, follow the target repo's testing
conventions (its README / CONTRIBUTING). Per AGENCY_PROTOCOL §9,
end every reply with `reply_to_pr_comments(...)` so the orchestrator's
poll loop sees your push. -->
