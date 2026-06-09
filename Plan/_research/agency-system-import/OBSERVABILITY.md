# Observability — Specs 109, 110, 112, 113, 114

> Iter-15 panel fix (consensus issue D16). Production observability
> story for the substrate-adjacent capabilities. Without this, you
> can't tell if `prompt.engineer` is slow, if `dossier.extract_entities`
> is silently failing, or if `thinking.bayesian_update` is being abused.

## Metrics per cap

Every cap emits OTel-style metric counters/histograms via the existing
Spec 020 graph-DB substrate (graph writes ARE the metrics; no separate
metrics backend required).

### 109 `prompt`

| Metric | Type | What it tracks |
|---|---|---|
| `prompt.builder.calls{builder=<name>}` | counter | per-builder invocation rate |
| `prompt.builder.duration_ms{builder=<name>}` | histogram | per-builder latency (p50/p95/p99) |
| `prompt.engineer.calls{builder=<name>}` | counter | composition calls per builder |
| `prompt.engineer.token_budget_overflow` | counter | requests where token budget was exceeded |
| `prompt.engineer.snippet_count{kind=<k>}` | histogram | how many snippets per call |
| `prompt.framework_walk.calls{framework=<f>}` | counter | per-framework start rate |
| `prompt.framework_walk.phase_advances{framework=<f>, phase=<p>}` | counter | how often each phase is reached |
| `prompt.framework_walk.loop_iterations{framework=<f>}` | histogram | for loop-based frameworks (ReAct, Reflexion) |
| `prompt.score_output.calls{accepted=<bool>}` | counter | how often outputs are accepted as canonical |
| `prompt.audit.calls{clarity_score_band=<b>}` | counter | audit results binned (<60, 60-80, 80+) |

### 110 `thinking`

| Metric | Type | What it tracks |
|---|---|---|
| `thinking.method.calls{method=<name>}` | counter | per-method invocation rate |
| `thinking.method.duration_ms{method=<name>}` | histogram | per-method latency |
| `thinking.composite.calls{verb=<name>}` | counter | apply_full_review / apply_decision_discipline / apply_design_review |
| `thinking.composite.method_coverage{verb=<name>}` | histogram | how many of 14 methods actually ran |
| `thinking.bayesian.posterior_band{band=<low\|mid\|high>}` | counter | distribution of posterior beliefs |
| `thinking.pre_commitment.binding_strength{strength=<s>}` | counter | soft/firm/hard distribution |
| `thinking.red_team.severity_distribution{severity=<s>}` | counter | low/medium/high/critical distribution |

### 112 `dossier`

| Metric | Type | What it tracks |
|---|---|---|
| `dossier.intent_capture.calls{path=<a\|b>}` | counter | rule-based vs LLM-assisted |
| `dossier.ingest.calls{kind=<paper\|book\|...>}` | counter | source-kind distribution |
| `dossier.ingest.duration_ms{kind=<k>}` | histogram | per-kind ingest latency |
| `dossier.chunk.chunks_per_source` | histogram | source size signal |
| `dossier.extract.entities_per_chunk` | histogram | extraction yield |
| `dossier.extract.path{a\|b}` | counter | rule-based vs LLM-assisted distribution |
| `dossier.context.declared{purpose=<p>}` | counter | backbone/flavor/factcheck/counterpoint/metaphor-source |
| `dossier.render_snippet.token_budget_usage` | histogram | how close to the token cap |
| `dossier.render_snippet.calls{kind=<k>}` | counter | per-snippet-kind rate |
| `dossier.dispatch_research.cascade_size` | histogram | how many specialist calls per dispatch |
| `dossier.audit.clarity_score` | histogram | brief clarity distribution |
| `dossier.workflow.phase_progress{phase=<p>}` | counter | DossierWorkflow Lifecycle phase advancement |

### 113 `research-ingestion-port`

| Metric | Type | What it tracks |
|---|---|---|
| `port.ingest.sources_completed` | counter | sources fully ingested |
| `port.ingest.sources_failed{phase=<p>}` | counter | failures per phase |
| `port.design_review.findings_per_method` | histogram | thinking-method yield |
| `port.snippet_render.calls{pattern=<p>}` | counter | per-pattern snippet rate |
| `port.audit.passes` | counter | brief audits that passed clarity threshold |

### 114 `plugin-as-session-driver`

| Metric | Type | What it tracks |
|---|---|---|
| `session.init.calls{mode=<m>}` | counter | mode-detection distribution at session start |
| `session.init.resumed_from_prior` | counter | how often prior lifecycle is found |
| `session.mode_shift.calls{from_mode=<f>, to_mode=<t>}` | counter | mode-transition matrix |
| `session.boundary_use.records{tool=<t>}` | counter | raw-tool usage rate per tool |
| `session.boundary_use.suggested_verb_present` | counter | how often substrate could have covered the action |
| `session.boundary_use.adoption_ratio` | gauge | (verb_calls / total_actions) — Phase D measurement |
| `session.synthesize.calls{outcome=<o>}` | counter | session-end outcome distribution |
| `session.lifecycle.duration_minutes` | histogram | session length |
| `session.lifecycle.actions_per_session` | histogram | activity per session |

## Alerts

| Alert | Condition | Severity |
|---|---|---|
| `prompt.engineer.token_overflow_burst` | `>10` overflows in 60s | warning — token-budget tuning needed |
| `dossier.extract.zero_entities_run` | a full source yielded 0 entities | warning — chunking or extraction broken |
| `dossier.dispatch_research.cascade_failure_rate > 30%` | over a 5-minute window | error — research-cap degraded |
| `thinking.composite.partial_run_rate > 20%` | composite verbs not completing | warning — long-running compositions failing |
| `session.boundary_use.adoption_ratio < 0.5` | session uses more raw tools than verbs | info — Phase-C adoption stalled |
| `session.synthesize.outcome=abandoned_rate > 30%` | over 24h | warning — sessions not closing cleanly |
| `prompt.framework_walk.loop_iterations p99 > 20` | loops running away | warning — ReAct/Reflexion not converging |

## Dashboards

Two dashboards land with the iter-15 PR (lightweight markdown
descriptions; integrations are downstream-team's concern):

### 1. "Capability adoption health"
- Per-capability invocation rate (which caps are actually being used)
- Verb-first vs raw-tool ratio (`session.boundary_use.adoption_ratio`)
- Cross-cap handshake throughput (109 → 110 → 112 chain timings)

### 2. "Provenance moat coverage"
- Sessions with ≥ 1 SessionReflection artefact (closed-the-loop rate)
- Sessions with ≥ 1 DecisionRecord (decision-discipline rate)
- Average artefacts per intent (the moat depth)

## How metrics emit

Every effect verb wraps its body in:

```python
with self.ctx.span("cap.verb_name", attributes={...}):
    result = ... do work ...
self.ctx.metric_counter("cap.verb_name.calls", attributes={...}, value=1)
self.ctx.metric_histogram("cap.verb_name.duration_ms", value=elapsed_ms)
return result
```

`ctx.span` / `ctx.metric_*` are NEW CapabilityContext methods landing
alongside iter-15 (Spec 020 graph nodes — no external OTel needed for
v1; metrics ARE graph nodes per the substrate's "graph is the store"
discipline).

## v1 vs v2

**v1** (iter-15): metric definitions documented; verbs emit to graph
as `Metric{name, value, attributes}` nodes. Queryable via
`memory.provenance(intent_id)` per-session OR via `analyze.graph`
cap for aggregate.

**v2**: optional OTel exporter (`[observability]` extra) for production
deployments wanting external dashboards.
