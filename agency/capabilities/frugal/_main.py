# agency-scaffold: v1
"""frugal — the lazy-senior-dev discipline as a capability (Spec 348, the ponytail port).

Frugal forces the laziest solution that actually works: the ladder
YAGNI -> stdlib -> native -> installed-dep -> one line -> minimum, with a
non-negotiable safety floor (validate / secure / accessibility never cut). The
verbs EXPOSE the core discipline (``agency/_frugal.py``, Spec 332 — the single
source for the ladder + floor); they never re-define it.

Use when: you want to read or switch the active frugal level, pull the ruleset
for a host that injects via a tool/prompt call (the ponytail-MCP port), or show
the frugal reference card.
Triggers:
- "be lazy" / "lazy mode" / "simplest solution" / "yagni" / "do less"
- A host with no always-on hook that must pull the discipline as a tool/prompt
- Asking what the frugal levels are or how to switch them
Red flags:
- Over-engineering / boilerplate / a new dependency for a few lines → frugal.instructions
- Hand-writing the ladder text → it lives in core _frugal (single source)
"""
from __future__ import annotations

from ... import _frugal
from ...capability import CapabilityBase, verb


class FrugalCapability(CapabilityBase):
    name = "frugal"
    home = "lifecycle"   # a discipline parameterizing HOW work proceeds (cf. mode/select; Spec 347)

    @verb(role="transform")
    def level(self) -> dict:
        """Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full).

        Returns: ``{level}`` — one of off|lite|full|ultra.
        chain_next: ``frugal.set_level(level)`` to change it; ``frugal.instructions`` for the ruleset.
        """
        return {"level": _frugal.frugal_level()}

    @verb(role="effect")
    def set_level(self, level: str) -> dict:
        """Persist the frugal level (durable across processes via the Spec 334 config).

        Inputs: level (str — off|lite|full|ultra; an invalid value falls back to full).
        Returns: ``{level}`` — the normalized, persisted level.
        chain_next: the new level governs the SessionStart inject + the per-verb stamp.
        """
        return {"level": _frugal.set_frugal_level(level)}

    @verb(role="transform")
    def instructions(self, level: str = "") -> dict:
        """Return the frugal ruleset text at a level — the ponytail-MCP port
        (``ponytail_instructions``). For an external / no-hook host whose only
        injection point is a tool or prompt pull; agency-internal agents already
        receive the discipline via the SessionStart inject (Spec 348 §4).

        Inputs: level (str — off|lite|full|ultra; empty = the active level).
        Returns: ``{level, instructions}`` (instructions is empty at level off).
        chain_next: inject the returned text as the session's discipline.
        """
        lvl = _frugal._norm(level) if level else _frugal.frugal_level()
        return {"level": lvl, "instructions": _frugal.render(lvl)}

    @verb(role="transform")
    def help(self) -> dict:
        """The frugal reference card (the ponytail-help info): the discipline +
        the levels table + how to switch + what is configurable.

        Returns: ``{help}`` — the complete help text (empty at level off).
        chain_next: ``frugal.set_level`` to switch; ``frugal.instructions`` for just the ruleset.
        """
        return {"help": _frugal.help_text()}
