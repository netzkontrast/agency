"""workflow ontology — the spec-state Lifecycle binding (Spec 357).

No new node label: a spec's state IS a ``Lifecycle`` on the Spec 345 ``spec``
machine (states draft → open → inprogress → done, + superseded). The only new
surface is the ``TRACKS`` edge binding that ``Lifecycle`` to the spec's
``Document`` (declared AND traversed — `ctx.neighbors(doc, "TRACKS")`).
"""
from __future__ import annotations

from agency.ontology import OntologyExtension
from agency._lifecycle_machines import resolve_machine

# Single source — the `spec` machine's states (read from machines.json, never a
# second literal; rule 2/8). AGENCY-DRIFT: spec-states — the `spec` machine lives
# in agency/_lifecycle_data/machines.json; this derives from it.
SPEC_STATES = set(resolve_machine("spec")["states"])

workflow_ontology = OntologyExtension(
    # SpecLifecycle --TRACKS--> the spec Document (the queryable binding).
    edges={"TRACKS"},
)
