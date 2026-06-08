---
spec_id: "105"
slug: novel-research-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "101", "044"]
affects:
  - agency/capabilities/novel/clusters/research.py
  - agency/capabilities/novel/ontology.py       # ResearchClaim, VerificationRecord reused from 099
  - agency/capabilities/novel/data/reference/research-domains.yaml
  - tests/test_novel_research.py
domain: novel / research / delegation
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/references/parity-table.md (10 researchers-* verbatim carry-over)"
  - "Plan/099 music-research-cluster (the proven pattern)"
---

# Spec 105 — Novel Research Cluster

## Why

Per the imported Novel-Craft Parity Table: **researcher subroles carry
over verbatim from music** — domain research is medium-agnostic. 105 ports
099's design pattern with the 10-domain registry retuned for novels:

- **historical** · **biographical** · **forensic** · **scientific** ·
  **geographic** · **cultural** · **occupational** · **mythological** ·
  **journalism** · **primary-source**
- + `document-hunter` + `verify-sources` (verbatim carry-over)
- + `researchers-verifier` (verbatim carry-over)

Like 099, 105 delegates the heavy lifting to `agency.research` (Spec 044:
`lead` / `specialist` / `verify`) and adds music-domain-style mapping.

## Done When

- [ ] **8 user-facing verbs ship** (research-scope, dispatch-research,
      capture-claim, verify-sources, list-claims, pending-verifications,
      human-signoff, document-hunt — mirror 099's verb set).
- [ ] **1 composite gate verb** ships: `verify_gate` (called by 108's
      `pre-draft` skill phase).
- [ ] **Domain registry** at `data/reference/research-domains.yaml`
      carries the 10 novel-domain configurations.
- [ ] **ResearchClaim + VerificationRecord nodes** reused from 099's
      ontology (declared in 102's consolidated extension).
- [ ] **Walkable skill `research-workflow` ships** (5 phases — verbatim
      adapted from 099).
- [ ] **`scripts/test-cap novel`** Green for novel-research tests.
- [ ] **`TODO.md` updated** with 105 row.

## Verb manifest

Mirrors 099 verbatim (every verb name preserved):

| # | Verb | Role | Delegate / Driver |
|---|---|---|---|
| 1 | `research_scope` | act | (delegate to scope-research lead) |
| 2 | `dispatch_research` | effect | agency.research.lead + agency.research.specialist × N |
| 3 | `capture_claim` | effect | (graph) — records `ResearchClaim` node SERVES intent |
| 4 | `verify_sources` | effect | agency.research.verify + TextDriver |
| 5 | `list_claims` | transform | (graph) — filter by novel/status |
| 6 | `pending_verifications` | transform | (graph) — aggregates `pending` claims |
| 7 | `human_signoff` | effect | (graph) + `elicit` |
| 8 | `document_hunt` | effect | agency.research.specialist (role="web", domain-prompted) |

**Internal gate**:

| # | Verb | Composes |
|---|---|---|
| G1 | `verify_gate` | list_claims(verified="pending") count + gate.check (BLOCKED_ON if > 0) |

**Total: 8 user + 1 gate = 9 registered verbs.**

## Design

### Domain registry (`data/reference/research-domains.yaml`)

```yaml
domains:
  historical:
    description: archives, contemporary accounts, timeline reconstruction
    preferred_sources: [archive.org, jstor, loc.gov, gutenberg.org]
    verifier_strictness: medium
    typical_novels: [historical fiction, alt-history, period thrillers]
  biographical:
    description: personal backgrounds, interviews, motivations
    preferred_sources: [linkedin, wikipedia, biography.com, oralhistory.org]
    verifier_strictness: low
    typical_novels: [biographical fiction, literary]
  forensic:
    description: crime-scene procedures, autopsy reports, investigative methodology
    preferred_sources: [doj.gov, fbi.gov, gianthoptodd.com, pubmed]
    verifier_strictness: high
    typical_novels: [thriller, crime, police procedural]
  scientific:
    description: physics, biology, chemistry; lab procedures
    preferred_sources: [pubmed, arxiv, nature, science]
    verifier_strictness: high
    typical_novels: [hard SF, technothriller, medical fiction]
  geographic:
    description: regional setting, climate, flora/fauna, languages
    preferred_sources: [nationalgeographic, openstreetmap, ethnologue]
    verifier_strictness: medium
    typical_novels: [literary, travel, regional]
  cultural:
    description: religious / ethnic / folk practices; festivals; food
    preferred_sources: [encyclopedia, jstor, owned-by-community-orgs]
    verifier_strictness: high
    typical_novels: [diaspora, multicultural, magical realism]
  occupational:
    description: trade-specific procedures (military, medical, legal, blue-collar)
    preferred_sources: [trade-magazines, professional-bodies]
    verifier_strictness: medium
    typical_novels: [procedural, workplace, war]
  mythological:
    description: world religions, folklore, mythology
    preferred_sources: [sacred-texts.com, encyclopedia-mythica, jstor]
    verifier_strictness: low
    typical_novels: [fantasy, magical realism, retelling]
  journalism:
    description: news coverage of real events the novel fictionalizes
    preferred_sources: [nytimes, propublica, reuters, ap]
    verifier_strictness: medium
    typical_novels: [literary, ripped-from-headlines thriller]
  primary_source:
    description: subject's own words — letters, diaries, blogs (for living people)
    preferred_sources: [twitter, github, archive.org, blog-archives]
    verifier_strictness: high
    typical_novels: [biographical, historical-figure-as-protagonist]
```

### Delegation pattern

Verbatim from 099's iteration-6 corrected pattern:

```python
@verb(role="effect")
def dispatch_research(self, question: str, domains: str = "all",
                      novel: str = "") -> ToolResult:
    """Drive agency.research.lead → N agency.research.specialist calls →
    agency.research.verify. Maps novel's 10 domains onto the shipped
    {codebase|prior-reflections|doc-corpus|web} role enum via
    domain-prompted queries.
    """
    state = self.ctx.get_driver("music_state")
    domain_registry = state.read_data("research-domain", "all")
    selected = (list(domain_registry["domains"].keys()) if domains == "all"
                else [d.strip() for d in domains.split(",")])

    lead = self.ctx.call("research", "lead",
                         question=question, depth="standard")
    research_id = lead["research_id"]

    for novel_domain in selected:
        cfg = domain_registry["domains"][novel_domain]
        role = "web" if cfg.get("preferred_sources") else "doc-corpus"
        domain_query = (f"[domain={novel_domain}] {question}\n"
                        f"Preferred sources: {cfg.get('preferred_sources', [])}\n"
                        f"Style: {cfg.get('description', '')}")
        result = self.ctx.call("research", "specialist",
                               research_id=research_id, role=role,
                               query=domain_query, k=cfg.get("k", 5))
        for cite in result.get("citations", []):
            claim_id = self.ctx.record("ResearchClaim", {
                "text": cite.get("snippet", ""),
                "source_uri": cite.get("uri", ""),
                "domain": novel_domain,
                "confidence": cite.get("confidence", 0.5),
                "verified": "pending",
                "captured_at": int(time.time())})
            self.ctx.link(claim_id, self.ctx.intent_id, "SERVES")
            if novel:
                hits = state.find_novel(novel)
                if hits:
                    self.ctx.link(claim_id, hits[0]["id"], "RELATES_TO")

    self.ctx.call("research", "verify", research_id=research_id)
    return ToolResult.success(data={"research_id": research_id,
                                    "novel": novel,
                                    "domain_count": len(selected)})
```

### Walkable skill: `research-workflow`

5 phases, verbatim from 099:
- scope → dispatch-specialists → collect → verify → human-signoff (hard).

## Test plan

```python
# tests/test_novel_research.py — ~8 tests
def test_research_cluster_discovers_all_verbs(): ...
def test_dispatch_research_delegates_to_agency_research(): ...
def test_dispatch_research_handles_all_10_novel_domains(): ...
def test_capture_claim_records_ResearchClaim_node_with_captured_at(): ...
def test_verify_sources_flips_claim_status(): ...
def test_pending_verifications_filters_by_novel_and_status(): ...
def test_document_hunt_specializes_to_primary_source_domain(): ...
def test_research_workflow_skill_pauses_on_human_signoff_hard_gate(): ...
def test_verify_gate_blocks_when_pending_claims_remain(): ...
```

## Open questions

1. **Research domain registry — closed enum or open set?** Closed for v1
   (same as music). Adding a domain is a small YAML + ontology change.
2. **Pre-draft gate**: 108's `pre-draft` skill calls `verify_gate` to
   enforce "no drafting until research is human-confirmed". Tested via
   the E2E in 108.
3. **Web specialist gap**: Spec 044 reserved the slot but doesn't bind a
   default. 105 inherits — production binds via `[research-web]`; CI
   stubs `{citations: [], summary: ""}`.

## Followup

(Populated when the PR ships.)
