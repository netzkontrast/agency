---
target: "$target"
depth: "$depth"
kind: "$kind"
intent_id: "$intent_id"
---

# Explanation: $target

<!-- AGENT: This is the rendered output of document.explain — a
composed explanation, NOT a generated one. The agent reads the code,
the ontology, and prior reflections, then composes the answer at the
requested depth. -->

$content

<!-- AGENT: After rendering, the explanation is stored as a Reflection
(scope=technical, kind=explanation) linked SERVES + OBSERVED_DURING.
Spec 058's lint rule enforces both edges; do not skip
OBSERVED_DURING or the explanation disappears from intent-scoped
views. -->
