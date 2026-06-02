# Verification rules — Spec 044 v1

Two decidable checks ship. Each runs over the Citation nodes linked
to the Research via `CITES`. NO LLM. NO judgement-based decisions.

## evidence-supports-claim

**Goal.** Every Citation's `evidence_text` must support its
`claim_supported`.

**Algorithm.**
1. Substring path. Tokenise both strings (lowercase, ≥ 3-char
   alphanumeric tokens). Compute set-overlap. ≥ 50% of claim tokens
   appearing in evidence → pass.
2. Semantic backup. If substring fails, compute cosine via the
   engine's embedder (TF-IDF default). ≥ 0.5 → pass.
3. Otherwise fail; record the citation_id + the (low) score.

**Threshold rationale.** 0.5 cosine is the same threshold reflect.
recall_semantic uses for "this is a relevant retrieval". Below 0.5,
the embedder isn't confident the texts are about the same topic;
above 0.5, they are.

## contradiction-cluster

**Goal.** Flag pairs of citations whose claims contradict each other.

**Algorithm.**
1. Look at every (a, b) pair of citations under one Research.
2. Compute claim_a's negation words vs claim_b's. Symmetric difference
   non-empty → polarity flip exists.
3. Compute cosine of evidence_a vs evidence_b. ≥ 0.3 → same topic.
4. Polarity flip AND same topic → flag as warn (not fail — warns are
   for the human to review).

**Threshold rationale.** 0.3 cosine is low enough that "X is true"
and "X is not true" (which share most lexical tokens) get flagged,
but high enough that "X is true" + completely unrelated text doesn't.

## v2 — reachability check

Reserved. The plan: for each `source_kind="web"` Citation, HEAD the
URL with a 3-second timeout; fail on non-2xx. Cached per-session.
Defers until the web specialist driver lands.

## Override path

Verifier `status="fail"` blocks the publish phase via `gate.check`.
Override requires:
- `force=True` argument on the publish call (walker-level), AND
- A reason in the OVERRIDDEN_BY audit edge.

The override is recorded but not silent — the override edge is
visible in `memory_graph_provenance` for any auditor.
