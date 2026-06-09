# agency-scaffold: v1
"""prompt — prompt-engineering capability (Spec 109).

Two-lineage capability:

1. **Research-dossier lineage** (verbs 1-5): the 5-tool research-prompt-optimizer
   pattern — intent_capture → catalog_list → brief_render → brief_audit →
   brief_finalize. Produces dossier-shaped research deliverables grounded in
   intent + the bundled module catalog.
2. **Prompt-engineering lineage** (verbs 6+): the 10-builder family — register
   builders, engineer prompts inside a token budget, optimize, audit,
   iterate variants.

Use when: authoring research dossiers, engineering structured prompts that
honor a token budget, auditing prompts for clarity / anti-patterns, or
running an optimization pass on an existing prompt.
Triggers:
- A research intent needs a dossier authored before generation begins
- A prompt is being constructed and needs token-budget gating
- An LLM output flagged for anti-patterns needs an optimization pass
Red flags:
- Hand-rolling prompts outside the engineering pipeline → call `prompt.engineer`
- Skipping the audit gate → call `prompt.audit` (general-case) or
  `prompt.brief_audit` (dossier-case)
"""
from ._main import PromptCapability

__all__ = ["PromptCapability"]
