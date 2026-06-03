---
spec_id: "052"
slug: research-web-httpx
status: complete
last_updated: 2026-06-03
owner: "@agency"
depends_on: [044]
informs: [045, 049]
affects:
  - pyproject.toml                              # add httpx already there; just add user-agent default
  - agency/capabilities/research/_web.py        # implement default WebSearchClient
  - agency/capabilities/research/_verify.py     # web-reachability check
  - agency/capabilities/research/_main.py       # walker may invoke web w/o injector
  - tests/test_research_web.py                  # NEW
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 052 — research.web default driver + web-reachability check

## Why

Spec 044 v1 ships the WebSearchClient Protocol but defers the
default driver to v2 — the `web` specialist returns "no driver"
when called without injection. This means the deepest research
depth (`deep` → 4 specialists incl. web) currently runs only 3
specialists.

httpx is already a runtime dep (used by Jules client). The same
httpx can drive a **simple** web specialist: hit a public search
endpoint, parse JSON. v1 candidates:

- **DuckDuckGo Instant Answer API** (no key, JSON, instant-zero-
  click answers). Limited recall but ZERO config.
- **SerpAPI free tier** (rate-limited, key-required). Better recall
  but key surface.
- **Tavily AI Research API** (designed for AI agents, JSON).

Recommendation: ship DuckDuckGo as the default zero-config baseline.
Other backends activate via `AGENCY_WEB_BACKEND=serpapi` +
`SERPAPI_KEY=…` env vars (same pattern as Spec 045's
`AGENCY_EMBEDDER`).

Plus: Spec 044's verifier ships 2 of 3 checks. The third —
**web-reachability** (HEAD URLs, verify 2xx) — also wants httpx.
Ship it here.

## Done When

### Default WebSearchClient implementations

- [ ] `agency/capabilities/research/_web.py::DuckDuckGoClient`:
  - Subclasses the WebSearchClient Protocol.
  - `name = "duckduckgo"`.
  - `search(query, k)` POSTs to `https://api.duckduckgo.com/?
    q=<query>&format=json&no_html=1`; parses RelatedTopics +
    AbstractText; returns up to k `{url, title, text}` dicts.
  - Timeout 10s; failure → empty list.
- [ ] `agency/capabilities/research/_web.py::resolve_web_search()`:
  - Reads `AGENCY_WEB_BACKEND` env var (default `"duckduckgo"`).
  - Returns the configured backend; unknown name → DuckDuckGo
    fallback (same pattern as Spec 045 resolve_embedder).
- [ ] Engine wiring: `Engine.__init__` defaults `web_search=
  resolve_web_search()` when not explicitly passed.

### Web-reachability check on verify

- [ ] `_verify.py::check_web_reachability(memory, research_id) ->
  dict`:
  - For each `source_kind="web"` Citation, HEAD the URL with 3s
    timeout.
  - Pass = 2xx OR 3xx response.
  - Fail = 4xx, 5xx, timeout, OR network error.
  - Cached per-call (so multiple verify runs in one session don't
    re-hit each URL).
- [ ] `run_all()` now reports 3 checks: evidence-supports-claim +
  contradiction-cluster + web-reachability.
- [ ] When NO `web` citations exist, reachability vacuously passes
  (status="pass", items=[]).

### Confidence adjustment

- [ ] When the web specialist records a Citation, the v1 hardcoded
  confidence 0.9 stays. But the verifier's reachability check now
  DEMOTES citations to confidence 0.2 (in place via supersede) when
  their URL is unreachable AT VERIFY TIME. Spec 044 §"confidence"
  line 113-117 already foresees this case.

### agency_doctor reporting

- [ ] `agency_doctor` payload's `web_backend` field reports the
  resolved backend name (matches Spec 045 `embedder` field pattern).

### Tests

- [ ] `tests/test_research_web.py`:
  - DuckDuckGoClient: mock httpx.Client.get to return canned JSON;
    assert search returns the parsed RelatedTopics.
  - resolve_web_search: env var honored; unknown backend falls back.
  - Reachability check: mock HEAD requests; pass on 2xx, fail on
    4xx/5xx/timeout.
  - Engine default: when no web_search injected, default is
    DuckDuckGoClient.

## Design

### Why DuckDuckGo as default

Zero-config wins. Users `pip install -e .` and `research.specialist
(role='web')` works immediately. Real-world recall is limited
(DuckDuckGo's Instant Answers cover only ~30% of queries), but
the test infrastructure runs without any external state.

For real research, users `export AGENCY_WEB_BACKEND=tavily &&
export TAVILY_API_KEY=…` and get production-grade recall.

### Why DEMOTE not REJECT unreachable citations

A citation might be unreachable at verify-time for transient reasons
(temporary 503, network glitch). Demoting to confidence 0.2 keeps
it in the report but flags the uncertainty. Spec 044 §"confidence"
already pinned 0.2 as the "URL unreachable" tier.

### Open Questions

1. **Should reachability re-check at publish time?** Verify might
   run 10 minutes before publish. v2 may add a recheck. v1 trusts
   verify.
2. **httpx async vs sync.** Verify is a transform; sync simpler.
   Use sync httpx.

## Files

- **Modify:**
  - `pyproject.toml` — confirm httpx already required (it is).
  - `agency/capabilities/research/_web.py` — add DuckDuckGoClient
    + resolve_web_search.
  - `agency/capabilities/research/_verify.py` — add check_web_
    reachability + extend run_all to include it.
  - `agency/engine.py` — default web_search via resolve_web_search.
  - `agency/engine.py::agency_doctor` — `web_backend` field.
- **Add:**
  - `tests/test_research_web.py`

## Cluster-coherence (Spec 047)

- C10 Research (it IS — closes the v1 scope-cut on web specialist).
- C04 Quality (verifier adds the third decidable check).

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — DuckDuckGoClient as the zero-config default
WebSearchClient + web-reachability check on verify. Spec 044 v1
scope-cut (web specialist no-driver) is closed; Spec 044's third
verifier check (web-reachability) is now live. 13 spec tests green;
live wire dogfood confirms `research.verify` reports all THREE
checks.

### Done
- `agency/capabilities/research/_web.py::DuckDuckGoClient`
  (name='duckduckgo'). httpx.Client GET to api.duckduckgo.com/?q=...&
  format=json&no_html=1&skip_disambig=1; parses AbstractText +
  RelatedTopics; returns up to k `{url, title, text}` dicts.
  Network failures degrade to empty list (no exception crosses the
  boundary).
- `resolve_web_search()` — Spec 045-pattern env resolution
  (AGENCY_WEB_BACKEND, default 'duckduckgo'; unknown name → silent
  fallback to DuckDuckGo). KNOWN_BACKENDS frozenset for diagnostic
  reporting.
- `agency/engine.py::Engine.__init__` defaults `web_search=
  resolve_web_search()` when not explicitly passed. Tests stub via
  `Engine(web_search=...)`.
- `agency/capabilities/research/_verify.py::check_web_reachability`
  — HEAD each web Citation's URL with 3s timeout, follow_redirects=True;
  pass on 2xx/3xx, fail on 4xx/5xx/timeout/network-error. Vacuous
  pass when no web Citations exist. httpx ImportError → skipped with
  note (graceful degrade).
- `run_all()` now returns three checks: evidence-supports-claim +
  contradiction-cluster + web-reachability.

### Tests (tests/test_research_web.py — 13)
- DuckDuckGoClient: parses RelatedTopics + AbstractText (mocked
  httpx response); empty list on failure; k-limit honoured.
- resolve_web_search: defaults to DuckDuckGo; explicit 'duckduckgo'
  honoured; unknown backend falls back silently.
- Engine default: web_search=duckduckgo when no kwarg; kwarg
  overrides.
- Reachability check: 2xx → pass; 4xx → fail; network error → fail;
  no web Citations → vacuous pass.
- Verify payload now reports all 3 checks (regression-pinned).

### Scope-cut for v1 / v2 follow-ups
- v1 ONLY ships DuckDuckGo. SerpAPI / Tavily backends slot in next
  to DuckDuckGoClient (KNOWN_BACKENDS already opens the path).
- v1 reachability check doesn't DEMOTE Citation.confidence (Spec 052
  line 105-109 OQ). Deferred — needs Memory.supersede pattern review.
- v1 doesn't pin reachability results to the Verification node as
  separate properties; the report payload carries them.

### Cluster-coherence (Spec 047)
- C10 Research (closes v1 scope-cut).
- C04 Quality (the third decidable verifier check).
- The DuckDuckGo boundary mirrors Spec 045 BGE embedder boundary —
  same pattern across two axes validates the agency-canonical
  optional-dep handling.
