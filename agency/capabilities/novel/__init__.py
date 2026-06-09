# agency-scaffold: v1
"""novel — long-form prose authoring capability (Spec 101 master).

Spec 101's First-Principles Minimum: a simple-novel writer uses 5 verbs
(conceptualize → create_novel → create_chapter → chapter_report →
render_manuscript) + the `novel-concept` walkable skill. Complex features
(Dramatica storyform per Spec 103, multi-POV, worldbuilding, audiobook
prep, prompt engineering, research entities) are opt-in via subsequent
slice PRs.

This Slice 1 ships the MVN: scaffold + minimum verb surface + skill.
Slices 2+ port the music cluster patterns (lifecycle/storyform/prose/
research/catalogue/manuscript/gates) per Specs 102-108.

Use when: authoring a novel — turning a premise into a structured
manuscript through gated concept → chapters → report → render.
Triggers:
- A novel premise needs structured planning before drafting
- A chapter needs a per-chapter report (word count, beat progress)
- A finished draft needs rendering to manuscript format
Red flags:
- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`
"""
from ._main import NovelCapability

__all__ = ["NovelCapability"]
