<!-- doc-source: brooks-lint@ec44ec8 skills/_shared/remedy-guide.md -->
# Quality remedy — the --fix enrichment

<!-- AGENT: Rendered in the remedy phase (Spec 380 §4, develop.remediate / --fix)
     AFTER diagnosis is complete. What NOT to do: never write files during the
     DIAGNOSIS phase — the Iron Law is "no fixes before findings". Remedy runs only
     once the report exists. -->

<!-- AGENT: Enrich each finding's Remedy as Target → Action → Rationale:
     Target = the exact file:symbol; Action = the concrete edit; Rationale = the
     principle it restores (cite the same book as the finding's Source). -->

<!-- AGENT: Fixability tier per finding — [quick-fix] mechanical + local (safe to
     auto-apply); [guided] needs a judgement call (propose, await confirm);
     [manual] structural (describe, never auto-apply). This tier IS the
     $fix_tier_label slot in the iron-law-finding template. Safe = auto-apply under
     develop.remediate(apply_safe=True); risky = reported in gated[] for confirm. -->

<!-- AGENT: Close with a Fix Summary table — | Finding | Tier | Status | — so the
     human sees what was applied vs gated at a glance. -->
