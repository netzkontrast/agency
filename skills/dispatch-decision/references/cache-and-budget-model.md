# Cache + budget model — S9, S10, S11 deep dive

The three new cost-model signals (Spec 040 §"eleven signals" lines
181–217) encode the parts of dispatch economics the original 4-signal
heuristic missed. This doc explains the math and the pinning.

## S9 — `context_overlap` (parent already loaded the working set)

If the parent context already holds the files / symbols the task
needs (e.g. you just `Read` three files and the task processes those
same three files), **dispatching means the subagent re-reads them
cold**. You pay twice — once for the parent's original load, once
for the subagent's fresh load, plus the dispatch envelope and the
return-summary tokens.

**The S9 disqualifier (≥ 0.7 + small return).** When the parent
already paid the load cost AND the return is small (< 5000 tokens),
finishing inline is cheaper than dispatching.

**The S2 mute.** When overlap ≥ 0.5, S2 (`file_count >= 4`) stops
firing. Files in context aren't "unfamiliar" — the orchestrator
already loaded them.

**Measurement (v1).** Caller-provided. The orchestrator estimates
"I just Read these 3 files; the task needs 2 of those 3 → overlap=0.67".
v2 may add engine-inferred measurement by parsing recent tool calls.

## S10 — `cache_warmth` (parent's prompt-cache hit ratio)

Anthropic's prompt-cache makes **cached input tokens cost ~10% of
fresh tokens** within the 5-minute TTL. Continuing inline after a
long session means most of the prefix is hot — system prompt, tool
definitions, prior turns, prior file reads — all amortised at 10%.

A subagent's prompt starts cold: no cache hit on its first turn (or
hits only the system-prompt portion). When the parent cache is hot
(≥ 0.6) AND the inline work is not heavy (< 30 min), **inline wins
even against signals that would otherwise favour dispatch**.

When cache is cold anyway (fresh session, just-compacted history),
this signal goes silent — dispatch overhead is no longer worse than
inline overhead.

**Measurement (v1).** Caller-provided estimate. The Anthropic API
exposes cache statistics in `usage.cache_read_input_tokens` /
`usage.cache_creation_input_tokens` per response; track the last-turn
ratio: `warmth = cache_read / (cache_read + fresh_input)`. v2 may
have the engine read from the API usage block automatically.

**TTL decay.** 5 minutes. For sessions paused > 5 min, treat as cold.
For tier-2 cache (1-hour TTL at 25% premium), the math changes (cached
input ≈ 25% rather than 10%); v1 doesn't expose a `cache_tier` param —
defaults to the 5-min/10% model.

## S11 — `local_budget_relevant` (Jules side-step)

Jules sessions run on a **separate budget axis** — they don't consume
the local interactive agent's per-turn token budget. The "cost" of
dispatching to Jules is:

- **wall-clock latency** — minutes to hours, async.
- **Jules's own billing** — independent of the local API key.
- **a small token cost in the parent** for the dispatch envelope +
  the returned PR/diff summary (~500 + ~500 tokens).

So when `local_budget_relevant=False` (the caller signals "I'm okay
with async + Jules's bill"), the S1 / S9 / S10 disqualifiers go silent.
They all penalise *local* budget consumption; Jules doesn't touch it.

A task that would be too cheap to dispatch locally (S1 fails, S9
fires) can still be a great Jules candidate — heavy compute that the
local agent shouldn't block on.

**Inverted rule for Jules.** Dispatch wins when wall-clock budget
allows async (≥ 30 min slack) AND the task is read-mostly + auditable
in a PR. The Jules-specific positive signal:

```python
if not local_budget_relevant and (expected_return_tokens >= 2000
                                  or est_duration_min >= 30):
    signals += ["S11:jules-budget-free"]
```

## What "local budget" means precisely

There are three local-budget axes; `local_budget_relevant=False`
means **none** of them are touched (Jules has its own API key + own
context):

1. **The user's per-turn token budget** (visible in the Claude Code UI).
2. **The API spend in $** (Claude API per-token pricing).
3. **The conversation's context-window utilisation** (the 200k limit
   — once you fill it, you compact and lose detail).

When `local_budget_relevant=True`, the heuristic optimises all three
together. When False, none of them matter — Jules's own billing and
context window apply instead.

## The cost estimators (deterministic; v1 constants pinned)

```python
_LOCAL_SUBAGENT_ENVELOPE = 700   # tokens — preamble + handoff
_JULES_ENVELOPE = 500            # tokens — leaner framing
_JULES_RETURN_SUMMARY = 500      # tokens — PR/diff summary back to parent
_CACHED_INPUT_RATIO = 0.10       # Anthropic 5-min cache: 10% of fresh
_SUBAGENT_RETURN_CAP = 2000      # subagent summary cap before parent sees raw
```

### Local cost (out of parent's budget)

```python
def _estimate_local_tokens(s1_tokens, s9_overlap, s10_warmth, driver):
    if driver == "inline":
        effective = s1_tokens * (1 - s9_overlap)         # overlap-discount
        fresh = effective * (1 - s10_warmth)             # uncached portion
        cached = effective * s10_warmth * 0.10           # cached at 10%
        return int(fresh + cached)
    if driver == "local":
        return 700 + min(s1_tokens, 2000)                # envelope + bounded summary
    if driver == "jules":
        return 0                                          # Jules pays its own way
    return 1000                                           # mcp placeholder
```

### Total work cost (all parties)

```python
def _estimate_total_work_tokens(s1_tokens, s5_dur_min, driver):
    if driver == "inline":  return s1_tokens
    if driver == "local":   return 700 + s1_tokens + 200
    if driver == "jules":   return 500 + max(s1_tokens, s5_dur_min*1000) + 500
    return 2000                                           # mcp placeholder
```

The Jules formula uses `max(s1_tokens, s5_dur_min*1000)` because Jules's
total cost is dominated by duration (~1k tokens/min as a coarse v1
estimate; Open Q1 — measure and pin).

## Open Questions (Spec 040 §"Open Questions")

1. **Pin the envelopes.** `~700` (local) and `~500` (Jules) are
   v1 estimates. A one-hour timing experiment can replace them with
   measured values.
2. **Per-driver S1 cutoff.** v1 uses one cutoff (5000) for local;
   Jules's wake-up cost may justify a different cutoff. Refine v2.
3. **Cache tier param.** 5-min (10%) vs. 1-hour (25%) cache TTL
   changes the math. v1 hard-codes 5-min; v2 may accept a `cache_tier`.
4. **Engine-read cache stats.** v1 is caller-provided; v2 may read
   the Anthropic API's `usage.cache_*` fields automatically.
