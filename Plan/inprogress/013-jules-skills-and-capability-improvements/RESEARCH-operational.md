# RESEARCH-operational — Jules operational substrate (subagent A2)

## 1. State machine + three canonical silent-fail variants

State machine (`_jules_reference.md:152`):
`QUEUED → PLANNING → AWAITING_PLAN_APPROVAL → AWAITING_USER_FEEDBACK ↔ IN_PROGRESS → COMPLETED | FAILED | PAUSED | CANCELLED`.

`COMPLETED` is **idle-awaiting-input**, never "done" (JULES_PROTOCOL.md:98, CLAUDE.md "Jules session state semantics"). The three canonical silent-fail variants, each confirmed live in DOGFOOD-NOTES:

- **`COMPLETED` + non-empty patch + no branch on origin** — Phase 4 sid `17080122233254972311` + Phase 6 sid `1696509658639614343` (DOGFOOD-NOTES.md:77-85). Leading hypothesis (per Observation §10 below): the dispatch prompt never named `submit`. Recovery: probe via `jules_message`; if 3 probes fail, apply patch via GitHub MCP (JULES_PROTOCOL.md §8-Appendix).
- **`COMPLETED` + empty patch (0 files)** — genuine no-op; only legitimate `dispatch_fresh` trigger (spec.md:155, CLAUDE.md silent-fail table).
- **`COMPLETED` + scope-creep beyond `affects:`** — patch contains paths outside the allow-list (CLAUDE.md table; spec-022 60-vs-5-file precedent in lesson-15 §9). Probe to drop OOS diffs, do not re-dispatch.

## 2. Environment knowledge that rides on every dispatch

- **`automationMode: AUTO_CREATE_PR`** (_jules_reference.md:147, §7 bullet 3) — true zero-touch by bypassing human PR confirmation. Trade-off: removes the only built-in pause point between Jules's `submit` and a live PR; the agency-driving-Jules pattern needs it, but interactive workflows lose the confirmation gate.
- **Repo-level env vars** are cryptographically locked at session start (_jules_reference.md:52). Ship `agency-protocol` env vars (timeouts, branch convention) once per repo, not in every prompt.
- **Environment snapshots** (_jules_reference.md:49-51): first-run is cold; subsequent sessions hydrate from a persistent memory + filesystem snapshot. Multi-phase agency dispatches against the same repo+branch are warm and fast.
- **`AGENTS.md` lexical scoping** (_jules_reference.md:55-56, JULES_PROTOCOL.md:72): root-level for agency-wide invariants ("verify via `git ls-remote`, never local HEAD; use `submit`"); nested files override the parent for subtree-specific rules.

## 3. MCP integration direction (one-way)

§6 of the reference (_jules_reference.md:158-165, §7 bullet 9) is explicit: Jules → external MCP via a **closed allow-list** (Linear, Stitch, Neon, Tinybird, Context7, Supabase). **We cannot host an agency MCP that Jules calls** — Google audit gates the allow-list. The integration is one-way: the agency drives Jules via the REST API (`https://jules.googleapis.com/v1alpha`), not the reverse. Watcher/recovery must live on our side.

## 4. Dogfood lessons (in-flight 012 work)

- **~700-token dispatch prompts** (DOGFOOD-NOTES.md:32-38) → motivates `protocol_preset` (lesson-15 §7).
- **SSL/clock-skew flakiness** on our reads (`CERTIFICATE_VERIFY_FAILED`, DOGFOOD-NOTES.md:69-75, 96-102, OQ9) → watcher must treat `network_error` as a distinct class, not a session failure.
- **Late publish tolerance** (DOGFOOD-NOTES.md:148-149; lesson-12 PR pattern) → recovery must be idempotent (branch-on-origin check first; never double-apply).
- **Phase 4/6 silent-fail** (DOGFOOD-NOTES.md:77-85): `COMPLETED + has_outputs=True + no branch`. Leading hypothesis — dispatch prompt never named `submit` (_jules_reference.md:94, §7 bullet 1).

## 5. Operational invariants every Jules dispatch must satisfy

1. **Name `submit`** explicitly in the prompt (silent-fail #1 root cause).
2. **Include `pre_commit_instructions`** as a mandatory pre-flight (JULES_PROTOCOL.md:74, §8 step 2).
3. **Demand `git ls-remote` verification** — never trust local HEAD (CLAUDE.md root AGENTS.md target; lesson-15 §2).
4. **Forbid scope creep beyond `affects:`** (JULES_PROTOCOL.md §5 anti-pattern 6).
5. **On ambiguity, use `request_user_input`, not `message_user`** (_jules_reference.md:114, JULES_PROTOCOL.md:79; lesson-02 `agentMessaged`-and-wait kills sessions).
