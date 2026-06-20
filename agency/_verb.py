"""Spec 286 Phase-1 / A4 — the typed ``Verb`` value object.

A capability verb was historically an untyped ``dict`` —
``{"role", "fn", "inject", "tags", "param_enums", "name"?}`` — built by the
``@verb`` decorator (``fn._verb``), normalised by ``_wrap_method`` /
``Registry.register``, and **mutated in place** (``_wire_skill_tags`` does
``spec.setdefault("tags", set()).add(...)``). Many readers reach into it by
subscript (``spec["fn"]``) or ``.get`` (``spec.get("role", ...)``) across the
engine wire path, the CLI mirror, ``skill_emit``, ``disclosure``, the plugin
lint cluster and ``document`` rendering.

A4 makes "drop-in folder = capability" **type-safe, not convention-safe**: a
verb is now a frozen-ish dataclass with named fields, while remaining a
drop-in replacement for the dict via a ``Mapping``-style bridge
(``__getitem__`` / ``get`` / ``setdefault`` / ``__contains__``). The spine
sites (``capability.py``, ``_invoke.py``) read attributes (``verb.fn``,
``verb.role``); the broad/external readers keep their subscript access through
the bridge. Either way the wire contract + provenance are byte-identical.

The ONE mutation that survives is ``tags`` — ``_wire_skill_tags`` appends
``skill:<name>`` tags after registration. ``tags`` stays a mutable ``set`` so
``setdefault("tags", set()).add(...)`` keeps working; everything else is set
once at build time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Verb:
    """A typed capability-verb spec (Spec 286-A4).

    Fields mirror the keys the verb dict carried:

    - ``name``    — the PUBLIC verb name (the wire / registry key; may differ
                    from the Python method, e.g. ``import_`` → ``import``).
    - ``role``    — the verb role string (``act`` / ``transform`` / ``effect`` /
                    ``gate``). Stored as the plain ``str`` value even when an
                    ``ontology.Role`` enum is passed (``str(Role.X) == "x"`` via
                    ``StrEnum``) so wire strings never leak an enum repr and all
                    comparisons stay string-equal.
    - ``fn``      — the callable the registry invokes (``spec["fn"]``).
    - ``inject``  — the injected-parameter names (``["ctx", ...]``).
    - ``tags``    — discovery tags (a mutable ``set``; ``_wire_skill_tags``
                    appends ``skill:<name>`` post-registration).
    - ``param_enums`` — Spec 284 projected-enum members per parameter.

    A drop-in for the former dict: subscript / ``.get`` / ``.setdefault`` /
    ``in`` all work via the bridge methods below, so unmigrated readers need
    no change.
    """

    name: str
    role: str
    fn: Callable
    inject: list[str] = field(default_factory=list)
    tags: set = field(default_factory=set)
    param_enums: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Accept an ontology.Role (or any StrEnum) but store the plain string
        # value so wire strings + comparisons never see an enum. `str(Role.ACT)`
        # is "act" under StrEnum; a plain str passes through unchanged.
        if not isinstance(self.role, str) or type(self.role) is not str:
            self.role = str(self.role)

    # ---- Mapping-style bridge: keep the dict readers working unchanged -----

    _FIELDS = ("name", "role", "fn", "inject", "tags", "param_enums")

    def __getitem__(self, key: str) -> Any:
        if key in self._FIELDS:
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default) if key in self._FIELDS else default

    def __contains__(self, key: str) -> bool:
        return key in self._FIELDS

    def setdefault(self, key: str, default: Any) -> Any:
        """Bridge for ``spec.setdefault("tags", set())`` in ``_wire_skill_tags``.

        For an already-set field returns the current value (the ``tags`` set is
        always present, so the appended ``skill:*`` tags mutate the real set).
        """
        if key in self._FIELDS:
            return getattr(self, key)
        raise KeyError(key)

    # ---- Builders ----------------------------------------------------------

    @classmethod
    def from_spec(cls, name: str, spec: "dict | Verb") -> "Verb":
        """Build a ``Verb`` from the legacy verb-spec dict (functional-form
        ``Capability(verbs={name: {...}})``) or pass an existing ``Verb``
        through. Missing keys take their dataclass defaults; ``tags`` is
        coerced to a ``set`` (it may arrive as a list or be absent)."""
        if isinstance(spec, cls):
            return spec
        raw_tags = spec.get("tags") or set()
        tags = raw_tags if isinstance(raw_tags, set) else set(raw_tags)
        return cls(
            name=spec.get("name") or name,
            role=spec["role"],
            fn=spec["fn"],
            inject=list(spec.get("inject") or []),
            tags=tags,
            param_enums=dict(spec.get("param_enums") or {}),
        )
