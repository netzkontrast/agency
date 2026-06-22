---
spec_id: "057"
slug: analyzer-rule-axis-registry
status: done   # Shipped 2026-06-06 (branch claude/spec-056-057-058-lint-batch)
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["050"]
affects:
  - agency/capabilities/analyze/_main.py     # remove the hardcoded prefix map
  - agency/capabilities/analyze/_quality.py  # declare AXIS_PREFIXES
  - agency/capabilities/analyze/_security.py # declare AXIS_PREFIXES
  - agency/capabilities/analyze/_performance.py
  - agency/capabilities/analyze/_architecture.py
  - agency/capabilities/analyze/_paths.py
  - agency/capabilities/analyze/_ruff.py     # declare its prefix set
  - agency/capabilities/analyze/_bandit.py   # declare its prefix set
  - agency/capabilities/analyze/_radon.py
  - tests/test_analyze_axis_registry.py      # NEW
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 057 — Analyzer rule-axis registry

## Why

`analyze.improve(analysis_id, axes=[...])` filters findings by mapping
each finding's `rule` prefix to one of the four axes. Today the map
lives as a hardcoded if-elif in `agency/capabilities/analyze/_main.py`:

```python
two_letter_to_axis = {"IP": "paths"}
ruff_prefixes = {"E", "F", "W", "I", "C", "N", "UP", "D",
                 "PL", "PT", "RUF", "SIM", "RET", "TRY"}
one_letter_to_axis = {"Q": "quality", "S": "security",
                      "P": "performance", "A": "architecture",
                      "B": "security"}
```

Two problems:

1. **It will keep growing.** PR #17's review pass caught the bug that
   the round-1 axis map only handled internal Q/S/P/A — Spec 050's
   external-tool wrappers (ruff, bandit) needed their prefixes added.
   Future tools — mypy (`error:`), pylint (`C/W/E/R/I` — collision
   with ruff), semgrep (rule ids), pyright — all extend the map.

2. **The knowledge lives in the wrong place.** Each `_<tool>.py`
   wrapper KNOWS which prefixes its findings emit. Forcing `_main.py`
   to re-declare that knowledge is duplication: when the ruff wrapper
   adds a new code category, two files must change in lock-step. The
   round-1→round-2 bug fix was exactly this missed-coupling.

The right shape: **each `_<tool>.py` module declares its own
`AXIS_PREFIXES: dict[str, set[str]]` mapping axis → set of prefixes
it owns**. `_main.py`'s filter does a registry lookup at startup;
adding a new tool means dropping in a wrapper that declares its
prefixes — no `_main.py` edit.

## Done When

- [ ] **Each existing analyzer module declares `AXIS_PREFIXES`** as a
  module-level constant:
  ```python
  # _quality.py
  AXIS_PREFIXES: dict[str, frozenset[str]] = {
      "quality": frozenset({"Q"}),
  }

  # _ruff.py
  AXIS_PREFIXES: dict[str, frozenset[str]] = {
      "quality": frozenset({"E", "F", "W", "I", "C", "N", "UP",
                            "D", "PL", "PT", "RUF", "SIM", "RET", "TRY"}),
  }

  # _bandit.py
  AXIS_PREFIXES: dict[str, frozenset[str]] = {
      "security": frozenset({"B"}),
  }

  # _paths.py
  AXIS_PREFIXES: dict[str, frozenset[str]] = {
      "paths": frozenset({"IP"}),
  }
  ```
- [ ] **`_main.py` builds the runtime registry by union** over every
  analyzer module's `AXIS_PREFIXES`. New tools drop in by declaring
  their constant — no central edit.
- [ ] **Longest-prefix-first ordering** is preserved (3 > 2 > 1) so
  e.g. `RUF` matches before `R` would (no internal one-letter R
  exists today; the rule guards future collisions).
- [ ] **Collision detection at registry build** — if two modules
  declare overlapping prefixes for DIFFERENT axes, the registry build
  raises with a clear message naming both modules. Same-axis overlaps
  are silently unioned (idempotent).
- [ ] **`tests/test_analyze_axis_registry.py`**:
  - Asserts the built registry contains the prefixes from every
    shipped analyzer module.
  - Asserts longest-prefix-first ordering on the lookup function.
  - Asserts collision detection raises.
  - Asserts `improve(..., axes=['quality'])` includes ruff E/F/W
    findings AND internal Q findings.
  - Asserts `improve(..., axes=['security'])` includes bandit B
    findings AND internal S findings.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### The registry function

```python
# _main.py

def _build_axis_registry() -> tuple[dict[int, dict[str, str]], int]:
    """Walk every analyzer module's AXIS_PREFIXES and build a flat
    lookup: prefix → axis. Returns ({prefix_len: {prefix: axis}},
    max_prefix_len) so the lookup can iterate longest-first.

    Raises ValueError on cross-axis collision.
    """
    from . import (_quality, _security, _performance, _architecture,
                   _paths, _ruff, _bandit, _radon)
    by_len: dict[int, dict[str, str]] = {}
    seen: dict[str, tuple[str, str]] = {}   # prefix -> (axis, module)
    for mod in (_quality, _security, _performance, _architecture,
                _paths, _ruff, _bandit, _radon):
        mapping = getattr(mod, "AXIS_PREFIXES", {})
        for axis, prefixes in mapping.items():
            for p in prefixes:
                if p in seen:
                    prev_axis, prev_mod = seen[p]
                    if prev_axis != axis:
                        raise ValueError(
                            f"prefix {p!r} owned by both "
                            f"{prev_mod} (axis={prev_axis}) and "
                            f"{mod.__name__} (axis={axis})")
                seen[p] = (axis, mod.__name__)
                by_len.setdefault(len(p), {})[p] = axis
    return by_len, max(by_len, default=1)


_AXIS_LOOKUP, _MAX_PREFIX_LEN = _build_axis_registry()


def _rule_axis(rule: str) -> str:
    for n in range(min(len(rule), _MAX_PREFIX_LEN), 0, -1):
        axis = _AXIS_LOOKUP.get(n, {}).get(rule[:n])
        if axis:
            return axis
    return ""
```

The lookup is O(max_prefix_len) per finding — same complexity as the
current if-elif, with the registry-walk cost paid once at module load.

### Drop-in pattern

When a future spec adds a new external tool, the diff is one new
`_<tool>.py` file with its `AXIS_PREFIXES` constant. `_main.py`
imports it (one-line addition to the import tuple) and the registry
picks up the new prefixes. No filter-logic edits.

## Files

- **Create:**
  - `tests/test_analyze_axis_registry.py`.
- **Modify:**
  - `agency/capabilities/analyze/_main.py` — replace the hardcoded
    if-elif with the `_build_axis_registry()` function + lookup.
  - `agency/capabilities/analyze/_quality.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_security.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_performance.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_architecture.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_paths.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_ruff.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_bandit.py` — add `AXIS_PREFIXES`.
  - `agency/capabilities/analyze/_radon.py` — add `AXIS_PREFIXES` (none —
    radon emits findings via `_quality` so this stays empty; the
    constant exists for symmetry).

## Open Questions

1. **`AXIS_PREFIXES` empty dict vs no attribute.** Modules that don't
   contribute prefixes (e.g. `_radon.py` if its findings ride on
   `_quality`'s prefixes) can either declare an empty dict OR omit the
   attribute. Recommend explicit empty dict for symmetry — `getattr(...,
   {})` handles both but explicit beats implicit.

2. **Pylint W-prefix collision with ruff W-prefix.** Pylint also uses
   `C/W/E/R/I` for its categories. If a future spec adds a pylint
   wrapper, the collision detection will fire (both want `W`). Solutions:
   (a) prefix pylint codes at injection time (`PL` already in ruff's
   set — but pylint's `W0611` would become `PLW0611`); (b) introduce
   a "source" qualifier on rules so the lookup is by `(rule, source)`
   not just `rule`. Recommend (a) — pylint wrapper transforms its codes
   to `PL`-prefixed at finding-creation time.

3. **What about analyzer modules that emit MULTIPLE axes?** A
   hypothetical future linter might emit both security findings and
   quality findings. The `AXIS_PREFIXES` dict naturally supports this —
   one module declares prefixes for multiple axes. Already the spec's
   shape; no extra work.

## Evidence (cites)

- `agency/capabilities/analyze/_main.py:275-296` — the current
  hardcoded prefix map.
- PR #17 review r3345071847 — the original bug ("paths findings
  dropped because IP wasn't in the map") + the follow-up that asked
  for ruff/bandit prefixes (r3345114545 round-2 equivalent).
- `agency/capabilities/analyze/_ruff.py` + `_bandit.py` — the external
  wrappers shipped under Spec 050.
- Spec 050 — the external-analyzer composition pattern this spec
  refines from "central if-elif" to "wrapper-local declaration."


## Followup — Implementation Status (2026-06-06)

> Shipped on branch `claude/spec-056-057-058-lint-batch`.

**Verdict:** Shipped

### Done
- Each analyzer module (`_quality/_security/_performance/_architecture/_paths/
  _ruff/_bandit`) declares `AXIS_PREFIXES`; `_radon` declares `{}` (rides on
  quality's `Q`).
- `analyze/_main._build_axis_registry(modules=None)` unions them at import time
  with longest-prefix-first lookup (`_rule_axis`) + cross-axis collision
  detection. The hardcoded if-elif prefix map in `improve`/`_findings_of` is gone.
- Drop-in pattern: a future linter (mypy/pylint/semgrep) = one wrapper file + one
  import line; no central filter edit.

### Tests
- `tests/test_analyze_axis_registry.py` — 9 (registry contents, longest-first,
  collision raises, same-axis idempotent union, live registry clean). analyze
  slice 51 passed / 2 skipped.
