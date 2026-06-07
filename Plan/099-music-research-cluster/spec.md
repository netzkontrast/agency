---
spec_id: "099"
slug: music-research-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["044", "094", "093"]
affects:
  - agency/capabilities/music/clusters/research.py
  - agency/capabilities/music/ontology.py       # ResearchClaim, VerificationRecord
  - agency/capabilities/music/data/reference/research-domains.yaml
  - tests/test_music_research.py
domain: music / research / delegation
wave: 7
parent_spec: "093"
---

# Spec 099 — Music Research Cluster

## Why

bitwize's research system is a **10-domain parallel-research orchestrator**:
one `researcher` lead skill that dispatches to specialists (legal, financial,
security, government, journalism, biographical, historical, primary-source,
technical, document-hunter) and a `verifier` that cross-checks claims before
human review. For documentary/true-story albums, every lyric line traces to a
captured, verified primary source.

agency already ships this contract — **Spec 044's `research` capability** is
exactly this pattern (lead + specialists + verifier). The music research
cluster does NOT re-implement it; instead it **specializes** Spec 044 with:

1. **Music-domain specialist registry** (the 10 bitwize domains as a named set)
2. **`ResearchClaim` + `VerificationRecord` nodes** in the music ontology, so
   research output is provenance-recorded against the Album
3. **Pre-generation gate integration** (Spec 100): no lyric generation until
   `verify-sources` has confirmed claims for the album

This is the cluster that proves agency's research capability **composes** —
the music domain doesn't need its own research engine, it parameterizes the
existing one.

## Done When

- [ ] **Verbs ship:** **8 user-facing + 1 composite gate verb = 9 registered**
  (Codex P2 iteration 6 — `verify_gate` is required by both 099's
  `research-workflow` AND 100's `pre-generation` skill walks), all delegating
  to `agency.research` with music-domain configuration.
- [ ] **No DRIVER additions** — research routes through the existing
  `agency.research` capability and its `Researcher` boundary; music adds zero
  driver methods.
- [ ] **Ontology adds `ResearchClaim` + `VerificationRecord` nodes** with the
  `(ResearchClaim, verified)` closed enum (`pending / human-confirmed /
  rejected`).
- [ ] **Walkable skill: `research-workflow`** — 5-phase workflow (scope →
  dispatch-specialists → collect → verify → human-sign-off) with terminal hard
  gate.
- [ ] **Domain registry** at `data/reference/research-domains.yaml` carries the
  10 bitwize specialist domains as named configurations (each declares
  preferred-sources, prompt-style, verifier-strictness).
- [ ] **`scripts/test-cap music_research`** Green; the test bind a fake
  `Researcher` boundary that returns canned multi-specialist results.
- [ ] **`TODO.md` updated;** parent (093) row notes child shipped.

## Verb manifest

| # | Verb | Role | Driver / Delegate | bitwize tool / skill absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `research_scope` | act | (delegate) | `researcher` lead skill | defines the research question + domain set |
| 2 | `dispatch_research` | effect | agency.research | `researcher` lead + N specialists | calls `research.fan_out` on selected domains |
| 3 | `capture_claim` | effect | (graph) | (new — was implicit in bitwize) | records a `ResearchClaim` node SERVES the intent |
| 4 | `verify_sources` | effect | agency.research+TextDriver | `researchers-verifier`, `verify-sources` skill | cross-checks claims; flips status |
| 5 | `list_claims` | transform | (graph) | (new — was implicit) | filters claims by album/status |
| 6 | `pending_verifications` | transform | (graph) | `get_pending_verifications` | aggregates `pending` claims |
| 7 | `human_signoff` | effect | (graph) + `elicit` | (the human-review skill) | terminal human-approval step |
| 8 | `document_hunt` | effect | agency.research | `document-hunter` skill | specific specialist: court filings / govt docs |

**Total: 8 user-facing verbs.** Lighter verb count than the others because
the heavy lifting lives in `agency.research`.

**Internal composite gate verb** (Codex P2 iteration 6 — registered, but
called only by walkable skill phase; counted in 093's gate-verb column for
099):

| # | Verb | Role | Composes | Called by skill |
|---|---|---|---|---|
| G1 | `verify_gate` | effect | `list_claims(verified="pending")` count + gate.check (BLOCKED_ON if pending count > 0) | `research-workflow` phase 4 + Spec 100's `pre-generation` phase 2 |

**Done-When implication:** the cluster ships **8 user + 1 gate = 9
registered verbs**. Without `verify_gate`, both the `research-workflow`
verify phase AND Spec 100's `pre-generation` research-verified phase crash
at "unknown verb".

## Design

### Research-domain registry

```yaml
# agency/capabilities/music/data/reference/research-domains.yaml
domains:
  legal:
    description: court documents, indictments, plea agreements, sentencing
    preferred_sources: [courtlistener, pacer, justice.gov]
    verifier_strictness: high
  financial:
    description: SEC filings, earnings calls, analyst reports
    preferred_sources: [sec.gov, edgar, finra]
    verifier_strictness: high
  security:
    description: malware analysis, CVEs, attribution reports
    preferred_sources: [mitre, nist-nvd, virustotal, krebs]
    verifier_strictness: medium
  government:
    description: DOJ/FBI/SEC press releases, agency statements
    preferred_sources: [justice.gov, fbi.gov, sec.gov, treasury.gov]
    verifier_strictness: high
  journalism:
    description: investigative articles, interviews, news coverage
    preferred_sources: [nytimes, wapo, propublica, reuters, ap]
    verifier_strictness: medium
  biographical:
    description: personal backgrounds, interviews, motivations
    preferred_sources: [linkedin, wikipedia, biography.com]
    verifier_strictness: low
  historical:
    description: archives, contemporary accounts, timeline reconstruction
    preferred_sources: [archive.org, jstor, loc.gov]
    verifier_strictness: medium
  primary_source:
    description: subject's own words — tweets, blogs, forums, chat logs
    preferred_sources: [twitter, github, telegram, pastebin]
    verifier_strictness: high
  technical:
    description: project histories, changelogs, developer interviews
    preferred_sources: [github, gitlab, hackernews]
    verifier_strictness: medium
  document_hunter:
    description: automated browser navigation for primary sources
    preferred_sources: [courtlistener, sec-edgar, govinfo, archive-today]
    verifier_strictness: high
```

### Ontology additions

```python
# In ontology.py (the consolidated extension):
RESEARCH_NODES = {
    "ResearchClaim": {"text", "source_uri", "domain", "confidence",
                      "verified", "captured_at"},
    "VerificationRecord": {"claim", "verified_by", "verified_at",
                           "verdict", "notes"},
}
RESEARCH_ENUMS = {
    ("ResearchClaim", "verified"): {"pending", "human-confirmed", "rejected"},
    ("VerificationRecord", "verdict"): {"confirmed", "rejected",
                                        "needs-more-evidence"},
    ("ResearchClaim", "domain"): {"legal", "financial", "security",
                                  "government", "journalism", "biographical",
                                  "historical", "primary_source", "technical",
                                  "document_hunter"},
}
```

### Walkable skill: `research-workflow`

```python
RESEARCH_WORKFLOW_SKILL = {
    "name": "research-workflow",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "scope",
         "produces": ["question", "domains_selected"]},
        {"index": 2, "name": "dispatch",
         "produces": ["specialist_dispatches"]},
        {"index": 3, "name": "collect",
         "produces": ["claims_captured"]},
        {"index": 4, "name": "verify",
         "produces": ["verified_count", "pending_count"],
         "gate": "computed", "gate_verb": "music.verify_gate"},
        {"index": 5, "name": "human-signoff",
         "produces": ["all_human_confirmed"],
         "gate": "hard"},   # elicit — human is the final filter
    ],
}
```

### Primary actors (panel-added, iteration 1 / Cockburn)

- `research-workflow` — **Primary actor: agent** (orchestrates specialist
  fan-out + verifier); human-curator is the final filter at phase 5
  (human-signoff hard gate). Without human signoff, no lyric generation
  proceeds (the pre-generation skill in 100 reads `pending_count == 0`).

### Delegation pattern

### The actual `agency.research` API (panel-corrected — Codex P2)

The shipped `agency.research` capability (Spec 044, `agency/capabilities/
research/_main.py`) exposes **three verbs**:

- `research.lead(question, depth)` → `{research_id, specialists, plan}` —
  mints a `Research` graph node SERVES the intent
- `research.specialist(research_id, role, query, …)` → `{citations, summary}`
  — runs ONE bounded sub-search; records `Citation` nodes under the research_id
- `research.verify(research_id)` → `{verified, contradictions}` — cross-
  checks claims; the verifier pass

The shipped specialist `role` enum is `{codebase, prior-reflections,
doc-corpus, web}` — generic, NOT music-domain. Music's 10-domain registry
(legal, financial, …) maps onto this surface as **(role, query, search_root)
tuples** — each music domain becomes a `web` or `doc-corpus` specialist
call with a domain-prompted query.

```python
# In clusters/research.py (CORRECTED — matches the shipped API):
@verb(role="effect")
def dispatch_research(self, question: str, domains: str = "all",
                      album: str = "") -> ToolResult:
    """Drive agency.research.lead → N agency.research.specialist calls →
    agency.research.verify. Maps music's 10 domain specialists onto the
    shipped {codebase|prior-reflections|doc-corpus|web} role enum by
    domain-prompting the query. Records ResearchClaim nodes per finding,
    all SERVES the parent intent.
    """
    state = self.ctx.get_driver("music_state")
    domain_registry = state.read_data("research-domain", "all")
    selected = (list(domain_registry["domains"].keys()) if domains == "all"
                else [d.strip() for d in domains.split(",")])

    # 1. Lead — mints the Research node.
    # NOTE: CapabilityContext.call returns the spawned verb's unwrapped result
    # dict (NOT a ToolResult) — `self.spawn(...)[0]` per capability.py:138.
    # Codex P2: never .data on a ctx.call result.
    lead = self.ctx.call("research", "lead",
                         question=question, depth="standard")
    research_id = lead["research_id"]

    # 2. Specialists — one call per music-domain, mapped to a research role:
    for music_domain in selected:
        cfg = domain_registry["domains"][music_domain]
        # Music domains primarily hit web sources (court records, SEC
        # filings, news); document_hunter + legal map to web with stricter
        # source filtering inside the query prompt:
        role = "web" if cfg.get("preferred_sources") else "doc-corpus"
        domain_query = (f"[domain={music_domain}] {question}\n"
                        f"Preferred sources: {cfg.get('preferred_sources', [])}\n"
                        f"Style: {cfg.get('description', '')}")
        result = self.ctx.call("research", "specialist",
                               research_id=research_id, role=role,
                               query=domain_query, k=cfg.get("k", 5))
        # Record each citation as a music ResearchClaim:
        # Codex P2 iteration 5: `captured_at` is a required ontology field;
        # omitting it causes Memory.record() to raise. Stamp it from time.
        for cite in result.get("citations", []):
            claim_id = self.ctx.record("ResearchClaim", {
                "text": cite.get("snippet", ""),
                "source_uri": cite.get("uri", ""),
                "domain": music_domain,
                "confidence": cite.get("confidence", 0.5),
                "verified": "pending",
                "captured_at": int(time.time())})
            self.ctx.link(claim_id, self.ctx.intent_id, "SERVES")
            if album:
                # Codex P2 iteration 5: RELATES_TO must be declared in
                # music's OntologyExtension.edges (added in 094).
                # Codex P2 iteration 6: `album` here is a slug (e.g. "X"),
                # NOT a graph node id. Memory.link() endpoints MUST be node
                # ids — resolve the album to its node id via the music_state
                # driver's find_album, then link to that id.
                state = self.ctx.get_driver("music_state")
                hits = state.find_album(album)
                if hits:
                    album_node_id = hits[0]["id"]   # the canonical Album node id
                    self.ctx.link(claim_id, album_node_id, "RELATES_TO")

    # 3. Verify — agency.research.verify cross-checks the citations under
    # the Research node; music inherits the verification verdict:
    self.ctx.call("research", "verify", research_id=research_id)
    return ToolResult.success(data={"research_id": research_id,
                                    "album": album,
                                    "domain_count": len(selected)})
```

**The web specialist** (research.specialist with role=`web`) requires a
web-search Boundary on the engine — Spec 044 reserved the slot but does
NOT bind a default driver. Music's research cluster inherits that gap: in
CI, the web specialist returns a stub `{citations: [], summary: ""}` (the
fake `Researcher` boundary). In production, binding a web-search Driver
(e.g. via `[research-web]` extra) enables real specialist calls.

## Test plan

```python
# tests/test_music_research.py — ~8 tests
def test_research_cluster_discovers_all_verbs(): ...
def test_dispatch_research_delegates_to_agency_research(): ...
def test_capture_claim_records_research_claim_node_with_serves_edge(): ...
def test_verify_sources_flips_claim_status_to_human_confirmed_or_rejected(): ...
def test_pending_verifications_filters_by_album_and_status(): ...
def test_document_hunt_specializes_to_document_hunter_domain(): ...
def test_research_workflow_skill_pauses_on_human_signoff_hard_gate(): ...
def test_verify_gate_blocks_when_pending_claims_remain(): ...
```

## Open questions

1. **Should the 10 specialists be hard-coded or extensible?** Hard-coded enum
   for now (matches bitwize). Adding a domain is a small ontology change.
2. **Verifier as a verb or a skill phase?** Verb (`verify_sources`) — it
   produces a record-of-truth `VerificationRecord` artefact. The skill
   orchestrates calls.
3. **Web search vs document-hunter — split clusters?** No — they're both
   "research dispatch" with different specialist registries. Same cluster.
4. **`agency.research`-side changes required?** **Corrected (Codex P2
   iteration 6 — matches the delegation pattern above):** the shipped
   `agency.research` capability (`agency/capabilities/research/_main.py`)
   exposes `lead(question, depth)`, `specialist(research_id, role, query, …)`,
   and `verify(research_id)` — NOT a `fan_out` verb. The specialist `role`
   enum is the generic `{codebase, prior-reflections, doc-corpus, web}`.
   099 maps music's 10 domain-specialists onto this surface via
   `(role="web", query=domain-prompted)` tuples; no agency.research-side
   change required.

## Followup

(Populated when the PR ships.)
