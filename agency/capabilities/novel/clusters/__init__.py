"""novel.clusters — cluster mixins composed into the single NovelCapability.

Spec 286 P3 — the ~95-verb ``novel`` god-class split into one mixin per
SDLC/domain cluster. Each mixin holds the ``@verb`` methods of its cluster
verbatim; ``NovelBase`` carries the shared driver-wiring + NOT_FOUND guards.
``novel/_main.py`` composes them (mixins first, ``CapabilityBase`` last) into
ONE registered ``novel`` capability — the wire contract is unchanged.
"""
from ._base import NovelBase
from .lifecycle import LifecycleMixin
from .storyform import StoryformMixin
from .prose import ProseMixin
from .research import ResearchMixin
from .manuscript import ManuscriptMixin
from .world import WorldMixin
from .storytime import StoryTimeMixin
from .codex import CodexMixin
from .character_knowledge import CharacterKnowledgeMixin

__all__ = [
    "NovelBase",
    "LifecycleMixin",
    "StoryformMixin",
    "ProseMixin",
    "ResearchMixin",
    "ManuscriptMixin",
    "WorldMixin",
    "StoryTimeMixin",
    "CodexMixin",
    "CharacterKnowledgeMixin",
]
