"""discover.clusters._base — the shared mixin every child cluster composes.

Spec 308 establishes the foundation; child specs (309-325) add their helpers
here as they implement (``_record_turn`` for interview/clarify, ``_session`` /
``_session_of`` for the session lifecycle, ``_clarity_inputs`` for the Spec 322
score). The scaffold ships only the one helper that is genuinely shared from day
one — ``_recall_intent`` (the Spec 091 ambient-intent pattern) — so we don't
land speculative, untraversed surface (CLAUDE.md dormant-surface audit).
"""
from __future__ import annotations


class DiscoverCluster:
    """Shared base for the ``discover`` cluster mixins.

    Carries cross-cluster helpers; composed (mixins first, ``CapabilityBase``
    last) into the single ``DiscoverCapability``. ``self.ctx`` is the
    ``CapabilityContext`` injected by the engine on every verb call.
    """

    def _recall_intent(self, intent_id: str = "") -> dict | None:
        """The serving intent's node (Spec 091 ambient pattern).

        Defaults to ``self.ctx.intent_id`` so a child verb can read the intent
        it serves without threading the id through every signature.
        """
        return self.ctx.recall(intent_id or self.ctx.intent_id)
