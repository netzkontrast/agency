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
# ADR hinge (open → extract → approve → inprogress + hints) → build → lint → done.
# Each phase carries `verbs` cues that BIND existing capability verbs (no
# re-implementation, panel B1); the walker (`develop.skill_walk`) delivers ONE
# phase at a time (Goal 1) and records each as provenance under the intent
# (Goal 2). Three HARD gates: the design improve-gate (B2.3), the ADR-approval
# hinge (the spec cannot reach `inprogress` until decisions are approved —
# 355/356), and the done gate (COMPLETED ≠ done).
#
# The COMPLETE brooks linting workflow is integrated into the implement loop
# (owner directive): phase 8 `brooks-lint` reasons over the SPEC (intent.brooks_lint,
# the 9th critical-thinking method), and the new phase 14 `lint` runs the brooks
# code-quality review (develop.review — decidable scanners + the mode-aware review
# chain + the judgment pass) over the IMPLEMENTATION before the done gate; the done
# gate itself folds in the headless analyze.review quality gate. So the ADR-centred
# loop lints both the decision (spec) and the code it produces.
_DEVELOP_SPEC_SKILL = {
    "name": "develop-spec",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"new spec|develop.spec|repo.development|write a spec|"
                                r"spec.workflow|build the repo",
                     "confidence": 0.7},
    "phases": [
        # Spec 378 — inline phase content (A1/A6) for the 14-phase ADR-centred
        # repo-development lifecycle (CLAUDE.md §"The repo-development workflow").
        {"index": 1, "name": "intent", "produces": ["intent_id"],
         "verbs": ["intent.capture"],
         "goal": "Capture the intent the spec serves.",
         "instructions": "intent.capture the purpose / deliverable / acceptance — every "
                         "spec serves a confirmed intent.",
         "freedom": "medium"},
        {"index": 2, "name": "triage", "produces": ["scope"],
         "verbs": ["discover.interview", "discover.clarify"],
         "goal": "Triage the rough scope.",
         "instructions": "Interview + clarify to bound what's in and out before any "
                         "design — a vague scope produces a vague spec.",
         "freedom": "medium"},
        {"index": 3, "name": "brainstorm", "produces": ["design"],
         "verbs": ["develop.brainstorm"],
         "goal": "Brainstorm the design.",
         "instructions": "Walk develop.brainstorm — explore options, present tradeoffs, "
                         "land a direction. Design before code.",
         "freedom": "high"},
        {"index": 4, "name": "research", "produces": ["prior_art"],
         "verbs": ["research.fetch", "codegraph_explore"],
         "goal": "Research prior art + what already exists.",
         "instructions": "codegraph_explore over the existing code AND research external "
                         "prior art. Most of the design is already half-built somewhere.",
         "freedom": "medium"},
        {"index": 5, "name": "acceptance", "produces": ["acceptance"],
         "verbs": ["discover.acceptance"],
         "goal": "Write the acceptance criteria.",
         "instructions": "State the decidable acceptance checks — how you'll KNOW it's "
                         "done. Acceptance is the contract the build phase satisfies.",
         "freedom": "medium"},
        {"index": 6, "name": "spec", "produces": ["spec_md"],
         "verbs": ["develop.write_spec"],
         "goal": "Write the spec into Plan/draft/.",
         "instructions": "develop.write_spec the design + acceptance into a Plan/draft/ "
                         "spec — the why, the slices, the acceptance.",
         "freedom": "medium"},
        {"index": 7, "name": "spec-panel", "produces": ["panel_findings"],
         "verbs": ["develop.spec_panel", "panel.convene"],
         "goal": "Run the expert spec panel.",
         "instructions": "Convene the panel over the draft — steelman, assumptions, "
                         "premortem — and capture the findings to fold back in.",
         "freedom": "medium"},
        {"index": 8, "name": "brooks-lint", "produces": ["brooks_findings"],
         "verbs": ["intent.brooks_lint"],
         "goal": "Brooks-lint for conceptual integrity.",
         "instructions": "intent.brooks_lint — the 9th critical-thinking method: "
                         "essential-vs-accidental complexity, conceptual integrity, "
                         "second-system effect.",
         "freedom": "medium"},
        {"index": 9, "name": "improve", "produces": ["design_good"], "gate": "hard",
         "goal": "The design gate — loop until no blocker.",
         "instructions": "Loop the improve pass until no `block` finding remains AND the "
                         "owner confirms. Confirm this gate only when the design is "
                         "genuinely sound, not merely written.",
         "freedom": "low"},
        {"index": 10, "name": "open", "produces": ["decision_drafts"],
         "verbs": ["workflow.move_spec", "adr.extract_decisions"],
         "goal": "Move to /open and extract the ADR decisions.",
         "instructions": "workflow.move_spec to /open, then adr.extract_decisions pulls "
                         "the key decisions into proposed WH(Y) Decision drafts.",
         "freedom": "low"},
        {"index": 11, "name": "adr-approve", "produces": ["decisions_approved"],
         "gate": "hard", "verbs": ["adr.approve"],
         "goal": "The ADR hinge — owner approves the decisions.",
         "instructions": "The spec cannot advance until EVERY decision is approved "
                         "(owner-only — an agent never self-approves). Confirm this gate "
                         "only on the owner's approval.",
         "freedom": "low"},
        {"index": 12, "name": "inprogress", "produces": ["hints"],
         "verbs": ["workflow.move_spec", "adr.hints"],
         "goal": "Move to /inprogress and load the ADR hints.",
         "instructions": "workflow.move_spec to /inprogress, then adr.hints re-loads the "
                         "code + architecture hints into context as the build begins.",
         "freedom": "low"},
        {"index": 13, "name": "build", "produces": ["implementation"],
         "verbs": ["develop.tdd", "develop.plan_execute"],
         "goal": "Build it TDD, one slice at a time.",
         "instructions": "Walk develop.tdd / plan-execute — RED → GREEN → green suite → "
                         "commit → push, slice by slice. The tests are the contract.",
         "freedom": "medium"},
        # The complete brooks linting workflow over the implementation (owner
        # directive): the mode-aware review chain + judgment pass, with the final
        # approval elicit. Advisory phase (not a gate) — findings feed the done
        # verification; the headless analyze.review is the CI quality gate folded
        # into `done` below.
        {"index": 14, "name": "lint", "produces": ["lint_findings"],
         "verbs": ["develop.review", "analyze.review"],
         "goal": "Lint the implementation (brooks Iron Law).",
         "instructions": "Run the review chain over the implementation — correctness "
                         "first, then the Iron Law (over-engineering, duplication). "
                         "Advisory: findings feed the done verification.",
         "freedom": "medium"},
        {"index": 15, "name": "done", "produces": ["verified"], "gate": "hard",
         "verbs": ["develop.verify", "analyze.review", "workflow.move_spec"],
         "goal": "Verify and move to /done — COMPLETED != done.",
         "instructions": "develop.verify the acceptance, run the headless analyze.review "
                         "CI gate, then workflow.move_spec to /done. Confirm this gate "
                         "ONLY on green evidence — COMPLETED is not done.",
         "freedom": "low"},
    ],
}

workflow_ontology = OntologyExtension(
    # SpecLifecycle --TRACKS--> the spec Document (the queryable binding).
    edges={"TRACKS"},
    skills={"develop-spec": _DEVELOP_SPEC_SKILL},
)
