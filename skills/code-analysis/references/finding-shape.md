# Finding shape — the contract

Every analyze axis emits findings in this exact shape:

```python
{
    "rule": str,           # rule id, e.g. "Q001", "S014"
    "severity": str,       # "info" | "warn" | "fail"
    "file": str,           # repo-relative path
    "line": int,           # 1-indexed
    "message": str,        # ≤ 120 chars (Spec 023 brief-budget)
    "evidence": str        # source line, ≤ 200 chars
}
```

## Severity assignments per axis (Spec 042)

Severity is **pinned per rule-id**, NOT user-configurable. Users
cannot reconfigure via flags in v1 (Spec 023 doctrine: severities
are contract-level, not preference-level).

### quality (`Q*`)

| Rule | Means | Severity |
|---|---|---|
| Q001 | unused import | warn |
| Q002 | line length > 100 | warn |
| Q003 | function body > 80 LOC | warn |
| Q004 | file > 500 LOC | warn |

(`fail` reserved for build-blockers when cyclomatic > 20 ships.)

### security (`S*`)

| Rule | Means | Severity |
|---|---|---|
| S001 | eval/exec call | **fail** (exploitable today) |
| S002 | hardcoded credential | **fail** (exploitable today) |
| S003 | pickle.load | warn (exploit-conditional on file provenance) |
| S004 | subprocess shell=True | warn (exploit-conditional on input) |

The KEY VALUE never appears in S002's message — only the pattern
name + line. Evidence shows the source line with the matched span
replaced by `<REDACTED>`.

### performance (`P*`)

| Rule | Means | Severity |
|---|---|---|
| P001 | nested loop on same iterable | warn (O(n²) hint) |
| P002 | `+=` in a `for` body | info (use `''.join()` / list.append) |
| P003 | unbounded `while True` (no break/return/sleep) | warn |

### architecture (`A*`)

| Rule | Means | Severity |
|---|---|---|
| A001 | import cycle (SCC > 1) | **fail** |
| A002 | file > 600 LOC | warn (split by purpose — CLAUDE.md Rule #2) |
| A003 | file > 400 LOC | info (approaching split threshold) |

## What's NOT shipped (and why)

| Family | Why not |
|---|---|
| "name is unclear" / "doc is poor" | Taste; needs LLM grounded in context |
| "may be vulnerable to deserialization" | Confidence interval; needs runtime model |
| "this loop is slow" without O(n²) proof | Profiling answer, not lint |
| "architecture smell" beyond cycle/LOC | Needs project-context knowledge |

If users want LLM-grounded judgement, they walk the `code-analysis`
skill and use `delegate.dispatch` to a subagent at the `review`
phase — but that's an EXPLICIT dispatch, not a hidden "smart" lint.
