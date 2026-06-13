"""Reference cluster — capability/verb reference lookup (the `help` map).

`help_map` is the pure renderer (no `self`, no `ctx`); `ReferenceMixin` carries
the thin `@verb`. Behaviour verbatim from the pre-split `plugin._main`.
"""
from __future__ import annotations

from ....capability import CapabilityBase, verb


def help_map(caps: dict) -> dict:
    """Map macroskills (capabilities) -> micro-skills (verbs). `caps` is the live
    registry view `{capability: [verb, ...]}`; the engine INJECTS it (the `inject`
    convention) so this verb stays pure. Returns a tiny doc + the structured map
    (token-efficient delta) under one `result` payload."""
    ordered = {k: sorted(caps[k]) for k in sorted(caps)}
    lines = ["# agency — capabilities (macroskills) and their verbs (micro-skills)", ""]
    for name, verbs in ordered.items():
        lines.append(f"- **{name}** — {', '.join(verbs)}")
    lines += [
        "",
        "## Discovery",
        "",
        "There is no separate 'remember to use the skill' layer — discovery IS the contract:",
        "",
        "- `search` finds a capability/verb or a discipline by symptom;",
        "- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);",
        "- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).",
        "",
        "Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until",
        "confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's",
        "heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS",
        "the recorded walk, so there is nothing extra to remember.",
    ]
    return {"result": {"doc": "\n".join(lines) + "\n", "map": ordered}}


class ReferenceMixin(CapabilityBase):
    """Verb that maps capabilities (macroskills) to their verbs (micro-skills)."""

    @verb(role="transform")
    def help(self) -> dict:
        """Map the engine's capabilities (macroskills) to their verbs — via ctx.registry.

        Inputs: none.
        Returns: ``{result: {<cap>: [<verb>, …]}}``.
        chain_next: ``search('<keyword>')`` or ``get_schema(name=)`` for details.
        """
        caps = {n: list(self.ctx.registry.get(n).verbs) for n in self.ctx.registry.names()}
        return help_map(caps)
