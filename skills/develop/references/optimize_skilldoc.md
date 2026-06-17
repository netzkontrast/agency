<!-- agency-generated: v1 -->
# develop.optimize_skilldoc

Author an optimized functional doc — flags + candidate, NO rewrite (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `target_ref (a capability name, a file path, or literal text), kind (``skilldoc`` | ``tool-desc`` | ``template``).` |  |  |

## Returns

``{flags, candidate, rationale, artefact_id, scores, status, source, kind}`` OR ``{error}``.

## Chain-next

``develop.validate_skill`` (the 080 gate) on the applied doc.

## Details

The metaprompt loop (Spec 306): agency uses its own framework substrate to enrich its own documentation. A capability docstring / SkillDoc / tool-description / template is a FUNCTIONAL prompt — its job is correct routing + invocation, not persuasion — so it is scored against the functional framework family (304), not CO-STAR. Resolves ``target_ref`` → text, evaluates it (305 functional profile → goal-keyed flags incl. the load-bearing ``role_padding`` — a function needs no Role), renders the functional framework into an optimized CANDIDATE, and records a ``doc-optimization`` Artefact. **Advisory: returns the candidate, writes no source** (a human or a later ``branch.commit_smart`` applies it).

## Example

```bash
agency-develop-optimize_skilldoc --intent-id $IID …
```
