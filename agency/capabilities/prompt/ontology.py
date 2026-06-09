# agency-scaffold: v1
"""prompt ontology — Spec 109 consolidated OntologyExtension.

Nodes, enums, edges, schemas, skills, templates for the prompt capability.
"""
from __future__ import annotations

from agency.ontology import OntologyExtension


# ─────────────────────────── enums ───────────────────────────
DELIVERABLE_KIND = {"dossier", "report", "outline", "memo"}
CATALOG_CATEGORY = {"A", "B", "C"}
PROMPT_PURPOSE = {
    "writing-assist", "dialogue-prompt", "description-prompt",
    "exposition-prompt", "metaphor-prompt", "system-prompt",
    "few-shot-bundle",
}
VARIANT_KIND = {
    "tone-shift", "length-target", "constraint-relax",
    "constraint-tighten", "structure-shift", "voice-shift",
}
ANTI_PATTERN_KIND = {
    "on-the-nose", "filter-words", "adjective-heavy",
    "telling-not-showing", "leading-question", "yes-bias",
    "hallucination-prone", "ambiguous-instruction",
}
OPTIMIZATION_KIND = {
    "clarity", "brevity", "specificity",
    "instruction-tightening", "few-shot-injection",
    "negative-example-injection", "structural-reformat",
}
AUDIT_STATUS = {"pending", "passed", "failed"}


# ─────────────────────────── skills ───────────────────────────
DOSSIER_AUTHOR_SKILL = {
    "name": "dossier-author", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "intent-capture",
         "produces": ["intent_recorded"]},
        {"index": 2, "name": "module-select",
         "produces": ["catalog_modules_chosen"]},
        {"index": 3, "name": "dossier-render",
         "produces": ["brief_body_rendered"]},
        {"index": 4, "name": "audit",
         "produces": ["audit_findings"],
         "gate": "computed", "gate_verb": "prompt.audit_gate"},
        {"index": 5, "name": "finalize",
         "produces": ["brief_finalized"], "gate": "hard"},
    ],
}

PROMPT_ENGINEERING_PASS_SKILL = {
    "name": "prompt-engineering-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "select-builder",
         "produces": ["builder_kind_selected"]},
        {"index": 2, "name": "inject-context",
         "produces": ["context_refs_chosen"]},
        {"index": 3, "name": "specify-constraints",
         "produces": ["constraints_declared", "anti_patterns_loaded"]},
        {"index": 4, "name": "render-prompt",
         "produces": ["prompt_instance_built"],
         "gate": "computed", "gate_verb": "prompt.token_budget_gate"},
        {"index": 5, "name": "iterate-variants",
         "produces": ["variants_evaluated"]},
        {"index": 6, "name": "score-output",
         "produces": ["output_scored"], "gate": "hard"},
    ],
}


# ─────────────────────────── consolidated extension ───────────────────────────
prompt_ontology = OntologyExtension(
    nodes={
        # Research-dossier lineage (verbs 1-5)
        "ResearchIntent": ["seed_query", "topic", "deliverable"],
        "ResearchBrief":  ["intent", "body"],
        "BriefAudit":     ["brief", "clarity_score"],
        "CatalogModule":  ["category", "identifier", "name"],
        # Engineering lineage (verbs 6+)
        "PromptInstance":   ["builder_kind", "rendered_body"],
        "PromptVariant":    ["parent_instance", "variant_kind"],
        "PromptOutput":     ["instance", "response_body"],
        "AntiPattern":      ["kind", "body"],
        "OptimizationPass": ["slug", "kind"],
    },
    enums={
        ("ResearchIntent", "deliverable"):   DELIVERABLE_KIND,
        ("CatalogModule",  "category"):      CATALOG_CATEGORY,
        ("PromptInstance", "purpose"):       PROMPT_PURPOSE,
        ("PromptVariant",  "variant_kind"):  VARIANT_KIND,
        ("AntiPattern",    "kind"):          ANTI_PATTERN_KIND,
        ("OptimizationPass", "kind"):        OPTIMIZATION_KIND,
        ("BriefAudit",     "status"):        AUDIT_STATUS,
    },
    edges={
        "RENDERS_FROM",      # ResearchBrief → ResearchIntent
        "AUDITS",            # BriefAudit    → ResearchBrief
        "VARIANT_OF",        # PromptVariant → PromptInstance
        "PRODUCED_BY",       # PromptOutput  → PromptInstance
        "FLAGS_ANTI",        # PromptOutput  → AntiPattern
        "APPLIES_PASS",      # PromptInstance → OptimizationPass
    },
    skills={
        "dossier-author":            DOSSIER_AUTHOR_SKILL,
        "prompt-engineering-pass":  PROMPT_ENGINEERING_PASS_SKILL,
    },
    schemas={
        "intent-yaml":      ["topic", "deliverable", "success_criteria"],
        "research-dossier": ["intent_ref", "body"],
        "prompt-instance":  ["builder_kind", "rendered_body"],
        "audit-report":     ["brief_ref", "clarity_score", "missing_sections"],
    },
)
