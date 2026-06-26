"""Spec 173 Slice 2 — live reflection-link coverage sweep over the graph.

Slice 1 shipped the typed ``LinkFinding`` shape (``agency/_link_finding.py``) but it
was dormant. This is the derived sweep that makes it load-bearing: over every live
``Reflection`` node it requires BOTH edges — ``SERVES`` (provenance; surfaces in
``Memory.provenance``) AND ``OBSERVED_DURING`` (the intent-scoped reflection view +
the Spec 150 classifier's attribution source). A node missing either is a
``LinkFinding``; a node missing exactly one is a PARTIAL write
(``Codes.REFLECTION_PARTIAL_LINKS``).

``ready`` is True iff ``unlinked_reflections == ∅`` — the
``agency_doctor.reflection_link_coverage`` signal and the WARN→error promotion gate
(``ReflectionLinkRule`` is ``block`` precisely while this stays clean). The
companion write-path invariant (``Codes.REFLECTION_NO_INTENT``) is enforced upstream
by the substrate IntentGuard: an ``act`` verb cannot run without a confirmed Intent,
so a Reflection write can never lack a SERVES target — the error already points at
``intent_bootstrap``.
"""
from __future__ import annotations

from dataclasses import asdict

from ._link_finding import LinkFinding
from .toolresult import Codes

_REQUIRED_EDGES = ("SERVES", "OBSERVED_DURING")


def sweep(memory, *, severity: str = "error") -> dict:
    """Sweep every live ``Reflection`` for the SERVES + OBSERVED_DURING edges.

    Returns ``{ready, unlinked, findings, partial_code}`` — ``ready`` iff zero
    findings; ``unlinked`` is the count of distinct reflections missing ≥1 edge;
    ``findings`` are ``LinkFinding`` dicts; ``partial_code`` names
    ``REFLECTION_PARTIAL_LINKS`` when any reflection is missing exactly one edge.
    """
    findings: list[LinkFinding] = []
    partial = False
    for refl in memory.find("Reflection"):
        rid = refl.get("id")
        if not rid:
            continue
        missing = [e for e in _REQUIRED_EDGES
                   if not memory.neighbors(rid, e, direction="out")]
        if len(missing) == 1:
            partial = True
        for edge in missing:
            findings.append(LinkFinding(reflection_id=rid, missing_edge=edge,
                                        severity=severity))
    unlinked = len({f.reflection_id for f in findings})
    return {
        "ready": not findings,
        "unlinked": unlinked,
        "findings": [asdict(f) for f in findings],
        "partial_code": Codes.REFLECTION_PARTIAL_LINKS if partial else "",
    }
