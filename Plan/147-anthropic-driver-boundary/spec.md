---
spec_id: "147"
slug: anthropic-driver-boundary
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "002"
depends_on: ["002", "026", "082", "110", "146", "150"]
vision_goals: [3, 8]
affects:
  - agency/_drivers/_anthropic.py  (NEW)
  - agency/capabilities/thinking/_main.py
  - tests/test_anthropic_driver.py
---

# Spec 147 — Canonical AnthropicDriver boundary

## Why

Spec 002 ships the Boundary/Driver protocol; Spec 026 mentions an
`llm_select` Matcher still pending a Driver. Spec 110 ships eight
critical-thinking methods that "do it in chat — but lossy". The
agency needs ONE canonical `AnthropicDriver` so every verb that needs
LLM inference (thinking, prompt-composition, dogfood-classifier, scene-
writer, sensitivity-reader) wires through the SAME typed surface with
adaptive thinking, `output_config.format`, `stop_reason` handling, and
optional Managed-Agents session bridging.

## Done When

- [ ] **`AnthropicDriver(Boundary)`** lives at `agency/_drivers/_anthropic.py`.
      Methods: `complete(messages, system, output_schema=None,
      effort="high")`, `stream(...)`, `count_tokens(messages)`,
      `dispatch_session(agent_id, env_id, kickoff)` (Managed Agents).
- [ ] **Defaults from the `claude-api` skill** — `model="claude-opus-4-8"`,
      `thinking={"type":"adaptive"}`, `output_config.format` for
      structured outputs, streaming when `max_tokens > 16000`.
- [ ] **`refusal` + `pause_turn` handled** — never crash the engine.
- [ ] **Managed-Agents bridge** — `dispatch_session(...)` creates a
      Session referencing a pre-created Agent (Spec 137 Lock stores
      `agent_id`; create-once doctrine), streams events back as
      `MonitorEvent`s (Spec 021), records each as a graph node.
- [ ] **`[anthropic]` extra** in `pyproject.toml`; `agency_doctor`
      reports `anthropic_driver` (api-key-present / managed-agents-
      capable / model-id-resolved).
- [ ] **Spec 110 verbs flip** to use this Driver behind a feature flag.
- [ ] Test scaffold: mocks the SDK; live test gated on env-var.
- [ ] TODO row + drift clean.

## Interconnects

- Anchors the **LLM-driver chain** the charter declares.
- Spec 150 (dogfood classifier) is the first non-thinking consumer.
- Spec 146 (output-prefix) is honored on every wrapped call.
- Spec 026 `llm_select` Matcher lands once this ships.
- Spec 137 (canon-locks) stores the persisted Agent ID + version.

## Open questions

1. Where does the Agent config YAML live? **Recommend**: vendored
   `agency/_drivers/agents/<purpose>.agent.yaml` per the `ant` CLI
   pattern; CI applies via `ant beta:agents update` (claude-api skill
   `shared/anthropic-cli.md`).
2. Vault credential storage? **Recommend**: Spec 137 Lock with
   `topic="vault-id"` — durable across sessions.
