---
spec_id: "168"
slug: research-web-driver-depth
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "052"
depends_on: ["052", "044", "147", "146"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/research/_web.py
  - tests/test_research_web_depth.py
---

# Spec 168 — research web-driver depth (server-side tools)

## Why

Spec 052 shipped a DuckDuckGo zero-config web backend + reachability
check, closing Spec 044's v1 web scope-cut. But the Claude API ships
SERVER-SIDE `web_search` + `web_fetch` tools with dynamic filtering
(`claude-api` skill, tool-use-concepts) that filter results before they
hit context — strictly better token economy than scraping into the
orchestrator. When the Spec 147 Driver is present, the research web
specialist should prefer the server-side tools.

## Done When

- [ ] **Web specialist routes through Spec 147 server-side `web_search`
      / `web_fetch`** (`web_search_20260209` dynamic filtering) when
      `[anthropic]` present; degrades to the DuckDuckGo backend
      otherwise.
- [ ] **Results return as Citations** (Spec 044) regardless of backend
      — the verify checks (evidence-supports-claim) run identically.
- [ ] **Fetched bodies honor the output budget** (Spec 146/154) — large
      pages capture-and-recall, never dumped.
- [ ] Test: server-side path returns Citations (mocked Driver);
      DuckDuckGo fallback deterministic.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146/154).
- Spec 044 (research cap) is the parent; Spec 052 the web v1.

## Open questions

1. Cost of server-side fetch vs scrape? **Recommend**: server-side when
   available (dynamic filtering saves tokens); the user's web policy
   governs egress either way.
