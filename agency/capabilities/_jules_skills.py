"""Jules-specific Lifecycle skill templates (Spec 013 Phase 5+).

A skill IS a capability (CORE.md:47-62) — Lifecycle templates of atomic
gated step-graphs. These skills are registered on
``JulesCapability.ontology.skills`` and walked via ``agency.skill.SkillRun``.

This module is consumed by ``jules.py`` at module load (the
``OntologyExtension(skills=…)`` argument) and is otherwise pure data.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Phase 5 — jules-protocol-preamble
# ---------------------------------------------------------------------------
# Walked ONCE per dispatch. The doctrine docs at the repo root
# (AGENTS.md + AGENCY_PROTOCOL.md) carry the invariants once per snapshot;
# this skill compresses the per-dispatch boilerplate from ~700 tokens to
# ~120 tokens by binding 3 of its 5 phases to real verbs.
#
# Phase 1 (`detect-mode`) is invoke-bound to `jules.detect_mode`: produces
# `{mode, self_source, reason}` where `mode ∈ {"dogfood", "delegate"}`.
# Phase 2 (`verify-remote-state`) is invoke-bound to `jules.verify`: the
# silent-fail guard before dispatch.
# Phase 3 (`name-canonical-tools`) is invoke-bound to `jules.lint_prompt`:
# refuses to advance unless the assembled prompt names every canonical
# tool symbol (see _jules_preambles._MUST_NAME_TOOLS).
# Phase 4 (`set-scope`) is a document phase: caller declares the scope
# allow-list + the Mode-B read-only assertion (`agency_clone_ro_in_delegate`).
# Phase 5 (`dispatched`) is a HARD GATE elicit (CORE.md:56-60): walker
# pauses at `input-required` until a `session_id` is supplied + confirmed.
JULES_PROTOCOL_PREAMBLE_SKILL: dict = {
    "name": "jules-protocol-preamble",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "detect-mode",
         "produces": ["mode_decision"],
         "invoke": {"capability": "jules", "verb": "detect_mode"},
         "inputs": ["source"]},
        {"index": 2, "name": "verify-remote-state",
         "produces": ["verify_result"],
         "invoke": {"capability": "jules", "verb": "verify"},
         "inputs": ["state", "branch", "remote"]},
        {"index": 3, "name": "name-canonical-tools",
         "produces": ["lint_result"],
         "invoke": {"capability": "jules", "verb": "lint_prompt"},
         "inputs": ["text", "must_name"]},
        {"index": 4, "name": "set-scope",
         "produces": ["affects_paths", "no_create_outside",
                      "agency_clone_ro_in_delegate"]},
        {"index": 5, "name": "dispatched",
         "produces": ["session_id"], "gate": "hard"},
    ],
}


JULES_SKILLS: dict[str, dict] = {
    "jules-protocol-preamble": JULES_PROTOCOL_PREAMBLE_SKILL,
}
