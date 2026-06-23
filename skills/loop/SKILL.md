---
name: loop
description: "Use when designing, opening, advancing, or emitting a self-verifying agent loop —"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# loop capability

The **wired surface** of the looper port: thin verbs delegating to the lifecycle-spine logic in ``agency/_loop.py`` so the loop is discoverable (``search``), schema'd (``get_schema``), runnable (``execute``/CLI), and — the point of Spec 387 W1 — records an ``Invocation`` on every call (the provenance moat the bare spine functions bypassed). The loop's goal IS an Intent (363); verification IS typed gate criteria (364); the council IS persona+panel (365); the runtime IS a registered Lifecycle machine (366); emission IS Document render (368); the runner is the out-of-session twin (369). See `docs/vision/reference/loop.md`.

## When to use

- "design / build / set up an agent loop" or a /goal-style iterate-until-verified task
- a loop needs typed verification criteria or a reviewer/judge gate
- emitting a portable loop workspace (loop.yaml / run-loop.py) or running it in-session

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `add_criterion` | effect | Add a typed verification criterion (programmatic|judge|human) to a loop (364). | [details](references/add_criterion.md) |
| `add_member` | effect | Add a council member (reviewer|judge) bound to a model family to a loop (365). | [details](references/add_member.md) |
| `advance` | effect | Advance the loop ONE transition — the in-session walk step (366). | [details](references/advance.md) |
| `compile` | transform | Resolve a loop into looper's loop.resolved.json shape, validated (368). | [details](references/compile.md) |
| `critique_goal` | transform | Coach a loop goal against goal-rubric.md — advisory, never blocks (363). | [details](references/critique_goal.md) |
| `detect_models` | act | Probe the model allowlist by PATH — metadata only, never secrets (369). | [details](references/detect_models.md) |
| `egress_consent` | transform | Decide the cross-vendor egress gate (consent + redaction) — pure (369). | [details](references/egress_consent.md) |
| `emit` | effect | Project the loop to its portable workspace (loop.yaml/resolved/LOOP.md…) (368). | [details](references/emit.md) |
| `emit_runner` | effect | Write the stdlib run-loop.py (reads only loop.resolved.json) (369). | [details](references/emit_runner.md) |
| `frame_goal` | effect | Frame a loop goal as a root Intent (the goal IS an Intent, 363). | [details](references/frame_goal.md) |
| `open` | effect | Open a loop Lifecycle SERVING the goal Intent; refuses a guard-free loop (366). | [details](references/open.md) |
| `preview` | act | Render the graph-derived ASCII flow preview of a loop (367 phase 6). | [details](references/preview.md) |
| `recommend_council` | transform | Report verdict-source coverage + a cross-family recommendation (365). | [details](references/recommend_council.md) |
| `register_model` | effect | Register a model invocation — argv-only, rejects secret-shaped material (369). | [details](references/register_model.md) |
| `verify_report` | transform | Audit a loop's verification SET against verification-rubric.md (364). | [details](references/verify_report.md) |

## Example

```bash
await call_tool('capability_loop_add_criterion', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- a loop with NO termination guard → `open` refuses it (never a guard-free loop)
- a `revise_until_clean` gate with no judge member / human criterion → `recommend_council` flags it
- a model invoke / check that is a shell string → rejected (argv-only, Spec 192)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`loop-usage`** (usage): use-transform → use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'loop-usage', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_loop_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_loop_add_criterion", {"intent_id": iid})
await call_tool("capability_loop_add_member", {"intent_id": iid})
await call_tool("capability_loop_advance", {"intent_id": iid})
await call_tool("capability_loop_compile", {"intent_id": iid})
await call_tool("capability_loop_critique_goal", {"intent_id": iid})
await call_tool("capability_loop_detect_models", {"intent_id": iid})
```

More verbs: `capability_loop_egress_consent`, `capability_loop_emit`, `capability_loop_emit_runner`, `capability_loop_frame_goal`, `capability_loop_open`, `capability_loop_preview`, `capability_loop_recommend_council`, `capability_loop_register_model` …
