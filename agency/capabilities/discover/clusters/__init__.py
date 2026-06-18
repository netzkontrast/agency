"""discover.clusters — cluster mixins composed into the single DiscoverCapability.

Mirrors ``prompt/clusters/``: ``DiscoverCluster`` (in ``_base``) is the shared
MRO anchor carrying helpers every child cluster reuses; each child spec
(309-325) adds ONE mixin module here (interview / ask / clarify / ground /
frame / examine / scope / refine / session) and ``discover/_main.py`` composes
them — a pure addition, never a structural change (Spec 308 acceptance).
"""
from ._base import DiscoverCluster
from .ask import AskCluster
from .interview import InterviewCluster

__all__ = ["DiscoverCluster", "AskCluster", "InterviewCluster"]
