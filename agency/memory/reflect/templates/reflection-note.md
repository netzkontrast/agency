---
scope: "$scope"
intent_id: "$intent_id"
vfrom: "$vfrom"
---

# Reflection

$text

<!-- AGENT: Reflections are durable cross-session memory. Use scope
to tag the lens: `observation` (raw signal), `reflection` (post-task
synthesis), `project` / `technical` / `user` / `world` (domain-tagged
context). Choose the scope BEFORE writing — it gates which downstream
queries surface this note. -->

<!-- AGENT: Reflections SERVE the calling intent AND link
OBSERVED_DURING. Skipping OBSERVED_DURING hides the reflection from
`document.render(scope='reflections', for_intent_id=...)` and the
repo-briefing recent-activity surface (Spec 058 lint rule catches
this on the writer side). -->
