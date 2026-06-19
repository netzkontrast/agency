# agency-scaffold: v1
"""discover — guided intent-discovery capability (Spec 307 program · 308 scaffold).

The Intent pillar's prompt-shaped peer: it turns a one-sentence seed into a
grounded, clarity-gated, confirmed Intent by interleaving research-grounding
with AskUser elicitation. Spec 308 lands the drop-in scaffold (ontology + the
docstring-derived SkillDoc + the derived ``discover-usage`` walkable); the 17
children (309-325) fill in the verb behaviour.
"""
from ._main import DiscoverCapability

__all__ = ["DiscoverCapability"]
