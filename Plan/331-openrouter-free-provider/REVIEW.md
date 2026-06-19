# Review of Spec 331 (OpenRouter free-provider implementation)

## Overview
The implementation correctly enforces the use of OpenRouter's free tier, adds auto-discovery, integrates `.env` loading, and introduces the S12 optional LLM tie-breaker for dispatch decisions.

## Checklist Evaluation

1. **`:free` suffix enforcement**
   - **Finding:** Correctly checked both at `LLMClient` initialization and per-call in `decide()`. An invalid suffix gracefully raises a `ValueError` early before any network call.
   - **Severity:** None (Looks good)

2. **`system` param in `decide()`**
   - **Finding:** Correctly overrides `_SYSTEM` when provided and successfully passes through `_chat()` to the HTTP request payload.
   - **Severity:** None (Looks good)

3. **`_generate_dispatch_system_prompt()`**
   - **Finding:** The prompt explicitly outlines driver options, heuristic drivers, signals fired, and decision criteria. The context is robust and constrained enough to prevent hallucination.
   - **Severity:** None (Looks good)

4. **S12 signal (`_llm_dispatch_signal()`)**
   - **Finding:** Safely skips and falls back to the heuristic on `DriverMissing`, network exceptions (429, etc.), low confidence (`< confidence_threshold`), and wrong choices not in the predefined options list.
   - **Severity:** None (Looks good)

5. **`resolve_model()` fallback**
   - **Finding:** Handled correctly. Encapsulated in a `try...except Exception` block, which safely falls back to `_DEFAULT_MODEL` if the OpenRouter models endpoint is unreachable.
   - **Severity:** None (Looks good)

6. **Acceptance scenarios in spec**
   - **Finding:** The 13 scenarios are testable, complete, and do not overlap. They sufficiently cover enforcement, auto-discovery, and the S12 tie-breaker.
   - **Severity:** None (Looks good)

## Additional Findings & Suggested Improvements

- **Unused variable `is_free` in `LLMClient.list_free_models`**
  - **Severity:** Info
  - **Finding:** In `agency/_llm.py`, the boolean variable `is_free` is calculated but never used. The subsequent `if` condition only checks `if mid.endswith(_FREE_SUFFIX):`.
  - **Improvement:** Remove the redundant `is_free` variable computation or use it in the `if` statement to clean up the code.

## Test Results
Tests run command: `PYTHONPATH=$PWD python3 -m pytest -q -k "delegate or llm" tests/`

**Output:**
```
.......................................                                  [100%]
=============================== warnings summary ===============================
tests/acceptance/test_delegate.py: 63 warnings
tests/acceptance/test_dispatch_decision_extended.py: 9 warnings
tests/acceptance/test_dogfood.py: 5 warnings
tests/acceptance/test_install.py: 2 warnings
tests/acceptance/test_jules.py: 1 warning
tests/acceptance/test_music.py: 2 warnings
tests/acceptance/test_skills_registry.py: 1 warning
...
39 passed, 1059 deselected, 166 warnings in 27.67s
```
**Conclusion:** All applicable unit tests pass.
