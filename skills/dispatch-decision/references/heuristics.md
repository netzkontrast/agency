# Heuristics — the eleven signals + algorithm

The dispatch-vs-inline decision is a deterministic function of 11
signals. The function lives in `agency/capabilities/delegate.py::
DelegateCapability.dispatch_decision`; this doc explains it.

## The 11 signals (full reference)

| # | Signal | Type | Range | Dispatch when | Inline when |
|---|---|---|---|---|---|
| **S1** | `expected_return_tokens` | int | ≥ 0 | ≥ 5000 | < 5000 |
| **S2** | `file_count` | int | ≥ 0 | ≥ 4 unfamiliar | ≤ 3 known |
| **S3** | `exploration_needed` | bool | T/F | True (grep/find pattern) | False |
| **S4** | `parallelism` | int | ≥ 1 | ≥ 3 sibling tasks | 1–2 |
| **S5** | `est_duration_min` | int | ≥ 0 | ≥ 15 wall-clock | < 15 |
| **S6** | `mutates` | bool | T/F | False (read-only safe) | True (no provenance) |
| **S7** | `read_only` | bool | T/F | True (amplifies) | False |
| **S8** | `driver_hint` | str | inline\|local\|jules\|mcp\|"" | matches signals | conflicts |
| **S9** | `context_overlap` | float | 0..1 | ≤ 0.3 | ≥ 0.7 (re-load tax) |
| **S10** | `cache_warmth` | float | 0..1 | ≤ 0.3 | ≥ 0.6 (10% cost) |
| **S11** | `local_budget_relevant` | bool | T/F | False (Jules-path) | True (no relaxation) |

S1 / S6 / S7 / S8 / S9 / S10 / S11 are the seven added by Spec 040.
S2-S5 are the original four (shipped with the delegate capability).

## Two disqualifiers ALWAYS run BEFORE positive scoring

### Disqualifier 1 — mutating-without-provenance

```python
if mutates and not _is_effect_with_provenance(driver_hint):
    return inline(reason="mutating task without effect-with-provenance "
                         "discipline; inline keeps the provenance edge intact.",
                  signals=["S6:mutates"])
```

**Rationale.** Mutations without provenance are how systems silently
lose work. The `effect` verb role tag exists precisely to mark verbs
that record `PRODUCES`d artefacts; dispatching such a verb is safe
because its child Lifecycle carries the provenance edge back. Any
OTHER mutating verb stays inline.

v1 note: `_is_effect_with_provenance(driver_hint)` is a conservative
stub that always returns False. A future enhancement may pass the
verb's role tag through to enable safe dispatch of true `effect` verbs.

### Disqualifier 2 — local-budget penalties

Only fires when `local_budget_relevant=True`. For Jules-path
(S11=False), these go silent.

```python
if local_budget_relevant:
    if context_overlap >= 0.7 and expected_return_tokens < 5000:
        return inline(reason="parent context already holds the working set; "
                             "subagent would re-load cold.",
                      signals=["S9:overlap-high"])
    if cache_warmth >= 0.6 and est_duration_min < 30:
        return inline(reason="parent prompt-cache is hot (cached input ≈ 10% cost) "
                             "and inline duration is short.",
                      signals=["S10:cache-hot"])
```

## Positive signals (additive)

```python
signals = []
if expected_return_tokens >= 5000 and local_budget_relevant: signals += ["S1:tokens"]
if file_count >= 4 and context_overlap < 0.5:                signals += ["S2:files"]
if exploration_needed:                                        signals += ["S3:explore"]
if parallelism >= 3:                                          signals += ["S4:parallel"]
if est_duration_min >= 15:                                    signals += ["S5:duration"]
if read_only and signals:                                     signals += ["S7:read_only_amplifies"]
# Jules-specific:
if not local_budget_relevant and (expected_return_tokens >= 2000
                                  or est_duration_min >= 30):
    signals += ["S11:jules-budget-free"]
```

Note S2 — file_count fires only when overlap < 0.5. The overlap weight
is doubly applied: it stops Disqualifier 2 from misfiring on small
returns, AND it prevents S2 from firing when the parent already has
the files.

Note S7 — `read_only` doesn't fire alone. It's an AMPLIFIER — when at
least one other signal already favours dispatch, S7 confirms safety
(read-only dispatches are unambiguously safe). Without other signals,
read-only doesn't justify dispatch overhead on its own.

## If no positive signal fires → inline

```python
if not signals:
    return inline(reason="no positive signals; dispatch overhead exceeds "
                         "inline cost.",
                  signals=[])
```

## Driver selection (cost-model aware)

```python
if not local_budget_relevant:                                       driver = "jules"
elif parallelism >= 3:                                              driver = "local"
elif est_duration_min >= 45 and not _interactive_required():        driver = "jules"
elif driver_hint and not _conflicts_with(driver_hint, signals):     driver = driver_hint
else:                                                               driver = "local"
```

When `driver_hint` is honoured, an `S8:driver_hint=<X>` signal is
appended to `signals_fired` so the rationale records the input.

## The two budgets

The payload reports cost estimates twice:

- **`token_cost_estimate`** — total tokens spent across all parties.
- **`local_budget_token_estimate`** — what comes out of the LOCAL
  parent context's budget (0 for Jules driver).

The split lets the caller reason about local-vs-remote budgets
independently. See [`cache-and-budget-model.md`](cache-and-budget-model.md)
for the per-driver cost formulas.
