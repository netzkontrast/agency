"""workflow ontology — the spec-state Lifecycle binding (Spec 357).

No new node label: a spec's state IS a ``Lifecycle`` on the Spec 345 ``spec``
machine (states draft → open → inprogress → done, + superseded). The only new
surface is the ``TRACKS`` edge binding that ``Lifecycle`` to the spec's
``Document`` (declared AND traversed — `ctx.neighbors(doc, "TRACKS")`).
"""
from __future__ import annotations

from agency.ontology import OntologyExtension
from agency._lifecycle_machines import resolve_machine

# Single source — the `spec` machine's states (read from machines.json, never a
# second literal; rule 2/8). AGENCY-DRIFT: spec-states — the `spec` machine lives
# in agency/_lifecycle_data/machines.json; this derives from it.
SPEC_STATES = set(resolve_machine("spec")["states"])

# Spec 358 — the walkable repo-development discipline. A Lifecycle template
# (Spec 018) that orders the owner's process — intent → triage → brainstorm →
# research → acceptance → spec → spec-panel → Brooks-lint → improve-loop → the
# ADR hinge (open → extract → approve → inprogress + hints) → build → done.
# Each phase carries `verbs` cues that BIND existing capability verbs (no
# re-implementation, panel B1); the walker (`develop.skill_walk`) delivers ONE
# phase at a time (Goal 1) and records each as provenance under the intent
# (Goal 2). Three HARD gates: the design improve-gate (B2.3), the ADR-approval
# hinge (the spec cannot reach `inprogress` until decisions are approved —
# 355/356), and the done gate (COMPLETED ≠ done).
_DEVELOP_SPEC_SKILL = {
    "name": "develop-spec",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"new spec|develop.spec|repo.development|write a spec|"
                                r"spec.workflow|build the repo",
                     "confidence": 0.7},
    "phases": [
        {"index": 1, "name": "intent", "produces": ["intent_id"],
         "verbs": ["intent.capture"]},
        {"index": 2, "name": "triage", "produces": ["scope"],
         "verbs": ["discover.interview", "discover.clarify"]},
        {"index": 3, "name": "brainstorm", "produces": ["design"],
         "verbs": ["develop.brainstorm"]},
        {"index": 4, "name": "research", "produces": ["prior_art"],
         "verbs": ["research.fetch", "codegraph_explore"]},
        {"index": 5, "name": "acceptance", "produces": ["acceptance"],
         "verbs": ["discover.acceptance"]},
        {"index": 6, "name": "spec", "produces": ["spec_md"],
         "verbs": ["develop.write_spec"]},
        {"index": 7, "name": "spec-panel", "produces": ["panel_findings"],
         "verbs": ["develop.spec_panel", "panel.convene"]},
        {"index": 8, "name": "brooks-lint", "produces": ["brooks_findings"],
         "verbs": ["intent.brooks_lint"]},
        {"index": 9, "name": "improve", "produces": ["design_good"], "gate": "hard"},
        {"index": 10, "name": "open", "produces": ["decision_drafts"],
         "verbs": ["workflow.move_spec", "adr.extract_decisions"]},
        {"index": 11, "name": "adr-approve", "produces": ["decisions_approved"],
         "gate": "hard", "verbs": ["adr.approve"]},
        {"index": 12, "name": "inprogress", "produces": ["hints"],
         "verbs": ["workflow.move_spec", "adr.hints"]},
        {"index": 13, "name": "build", "produces": ["implementation"],
         "verbs": ["develop.tdd", "develop.plan_execute"]},
        {"index": 14, "name": "done", "produces": ["verified"], "gate": "hard",
         "verbs": ["develop.verify", "workflow.move_spec"]},
    ],
}

workflow_ontology = OntologyExtension(
    # SpecLifecycle --TRACKS--> the spec Document (the queryable binding).
    edges={"TRACKS"},
    skills={"develop-spec": _DEVELOP_SPEC_SKILL},
)
