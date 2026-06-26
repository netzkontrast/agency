"""Spec 171 Slice 2 — live node-id-guard coverage sweep over the registry.

Slice 1 shipped the typed ``GuardFinding`` shape; this is the derived sweep that
makes it load-bearing. Over every verb in the LIVE registry it flags each
``<label>_id`` parameter read via a bare ``recall(param)`` / ``get_node(param)``
WITHOUT a label check (``recall_typed`` / an explicit ``"Label"`` / ``:Label)``) —
the silent-anchor bug class (Spec 056). A verb whose signature the AST walk cannot
resolve is recorded in ``unresolved`` with ``Codes.GUARD_LINT_UNRESOLVED`` — flagged
for manual review, NEVER silently passed (the failure mode the soft rule skipped).

``ready`` is True iff zero violations AND zero unresolved — the
``agency_doctor.node_id_guard_coverage`` signal (Spec 170) and the WARN→error
promotion gate (``NodeIdGuardRule`` is ``block`` precisely while this stays clean).

The label map (``_NODE_ID_LABELS``) is the SINGLE source shared with the lint rule —
this module derives the typed finding shape; the rule keeps its lint-orchestrator
dict shape + remediation. Both read the same map (rule 2: no second label list).
"""
from __future__ import annotations

import inspect
import re
from dataclasses import asdict
from typing import Any

from ._typed_shapes_wave1 import GuardFinding
from .toolresult import Codes

_ID_RE = re.compile(r"^(.+)_id$")


def _label_map() -> dict:
    # AGENCY-DRIFT: node-id-labels — the *_id prefix→Label map lives in the lint rule
    # (single source); this sweep reads it, never re-declares it.
    from agency.capabilities.plugin.clusters.lint import _NODE_ID_LABELS
    return _NODE_ID_LABELS


def scan_cap(cap: Any, *, severity: str = "error") -> "tuple[list[GuardFinding], list[str]]":
    """Scan one capability. Returns ``(violations, unresolved_verb_ids)``."""
    labels = _label_map()
    violations: list[GuardFinding] = []
    unresolved: list[str] = []
    for vname, spec in cap.verbs.items():
        verb_id = f"{cap.name}.{vname}"
        # Class-form verbs wrap the real method on __capability_method__ (its source
        # + signature are the user-facing ones).
        fn = getattr(spec.get("fn"), "__capability_method__", spec.get("fn"))
        try:
            src = inspect.getsource(fn)
            params = inspect.signature(fn).parameters
        except (OSError, TypeError, ValueError):
            unresolved.append(verb_id)        # GUARD_LINT_UNRESOLVED — not silent
            continue
        try:
            line = inspect.getsourcelines(fn)[1]
            file = inspect.getsourcefile(fn) or ""
        except (OSError, TypeError):
            line, file = 0, ""
        for pname in params:
            m = _ID_RE.match(pname)
            if not m:
                continue
            label = labels.get(m.group(1))
            if not label:                     # unknown prefix → no guess (Spec 056)
                continue
            reads_bare = f"recall({pname})" in src or f"get_node({pname})" in src
            if not reads_bare:
                continue
            guarded = (f"recall_typed({pname}" in src or f'"{label}"' in src
                       or f"'{label}'" in src or f":{label})" in src)
            if not guarded:
                violations.append(GuardFinding(
                    verb_id=verb_id, param_name=pname, expected_label=label,
                    severity=severity, file=file, line=line))
    return violations, unresolved


def sweep(registry, *, severity: str = "error") -> dict:
    """Sweep the whole registry. Returns ``{ready, violation_count, violations,
    unresolved, unresolved_code}`` — ``ready`` iff zero violations AND zero
    unresolved (the Spec 170 doctor signal + the lint-promotion gate)."""
    all_v: list[GuardFinding] = []
    all_u: list[str] = []
    for name in registry.names():
        v, u = scan_cap(registry.get(name), severity=severity)
        all_v += v
        all_u += u
    ready = not all_v and not all_u
    return {
        "ready": ready,
        "violation_count": len(all_v),
        "violations": [asdict(f) for f in all_v],
        "unresolved": all_u,
        "unresolved_code": Codes.GUARD_LINT_UNRESOLVED if all_u else "",
    }
