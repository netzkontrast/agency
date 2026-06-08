# Upstream Pin

This `upstream/` directory is a verbatim snapshot of the open-source
Narrative Context Protocol repository at the SHA referenced in the SPEC:

- Repo: https://github.com/narrative-first/narrative-context-protocol
- Pinned SHA: `0b9ab1223d3822a49eddc139bcdf2669aa067734`
- Snapshot date: 2026-05-03

`examples/legacy/` is excluded from this snapshot (it is intentionally
non-validating migration material in the upstream repo).

## Re-pin policy (T-14)

Re-pin **on demand**, not on a schedule. The trigger is a real conflict —
e.g., a user's Subtxt export, an upstream-NCP-canonical example, or a
target downstream tool requires fields that the pinned schema rejects.
Routine drift (cosmetic schema cleanup, doc rewordings) is not a re-pin
trigger; the pinned version stays stable so authoring sessions stay
reproducible across weeks.

When re-pinning:

1. Update `Pinned SHA` and `Snapshot date` above.
2. Refresh `schema/`, `docs/`, `examples/` (minus `legacy/`), `tests/`,
   and the top-level `*.md` files.
3. Re-run the validator against `assets/template-empty.json` and
   `assets/template-storyform.json`. If either fails, fix the templates
   in the same commit — the templates ship as the canonical
   "definitely-valid" examples and must always validate clean against
   the pinned schema.
4. Note the trigger (what broke at the old pin) in a one-line entry
   below this paragraph.

## To refresh, run:

```bash
git clone https://github.com/narrative-first/narrative-context-protocol.git /tmp/ncp
cd /tmp/ncp && git checkout <new-sha>
# then rsync schema/, docs/, examples/ (minus legacy/), tests/, top-level *.md
```
