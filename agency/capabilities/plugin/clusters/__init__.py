"""Cluster mixins for the `plugin` capability (Spec 286 P3).

`PluginCapability` is composed from four single-responsibility mixins —
authoring, lint, publish, reference — each carrying the verbs of its cluster.
The mixins are pure verb-carriers (`@verb` methods reaching services via
`self.ctx`); the heavy logic lives in module functions / the `LintRule`
registry, so the mixins stay thin and the wire contract is unchanged.
"""
from .authoring import AuthoringMixin
from .lint import LintMixin
from .publish import PublishMixin
from .reference import ReferenceMixin

__all__ = ["AuthoringMixin", "LintMixin", "PublishMixin", "ReferenceMixin"]
