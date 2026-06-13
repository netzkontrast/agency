"""Strict, EXTENSIBLE ontology for the agency graph.

The **core** defines the irreducible base: every node type's required-field
schema, the enumerated edge set, and the closed enums. But the core is not
closed — **each capability extends it** with its own node types, edges, enums,
skill schemas, and template-schemas (`Capability.ontology`, an
`OntologyExtension`). The engine merges every discovered extension onto the core
into one effective `Ontology` (strictly: an extension may not redefine a core
node with different fields), and injects it into `Memory`, which enforces it on
`record`/`link`/`update` — so the graph cannot drift and capability schemata are
owned by the capability, not hard-wired centrally.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# --- the CORE: base node types (label -> strict required fields) ------------
NODE_SCHEMAS: dict[str, list[str]] = {
    # Spec 048: `owner` (closed enum below) tracks who minted the Intent
    # (REQUIRED — every intent has an owner). `parent_intent_id` is
    # OPTIONAL — '' (and missing) both signal a root intent that
    # originated from a user prompt.
    "Intent":     ["purpose", "deliverable", "acceptance", "status", "owner"],
    "Invocation": ["capability", "verb", "role"],
    "Lifecycle":  ["state", "phase"],
    "Agent":      ["runtime"],
    "Gate":       ["name", "passed"],
    "Artefact":   ["kind"],
    "Schema":     ["name", "required"],
    "Template":   ["name", "body"],
    # micro-step skills & tools (generic):
    "Skill":      ["name", "kind"],                 # a skill = an ordered Lifecycle of Phases
    "Phase":      ["skill", "index", "name", "produces"],   # one atomic step
    "Tool":       ["name", "input", "output"],      # a typed tool (input/output schema refs)
    # Spec 076 — a captured Claude Code hook event (substrate provenance). The
    # unified dispatcher records one per routed event; linked OBSERVED_DURING to
    # the active intent (AGENCY_INTENT) when set.
    "Event":      ["name", "session"],
}

# --- core closed enums ------------------------------------------------------
# Spec 286 #8 — each closed set has ONE StrEnum as its single source of truth;
# the legacy plain-string sets below DERIVE from it (`{m.value for m in …}`).
# `str, Enum` (== StrEnum on 3.11) means every member IS its string value, so
# graph storage / wire payloads stay byte-identical (a member compares equal to
# and json-serialises as its value). `FIELD_ENUMS`, `Ontology.violations`, and
# `EntityModels` consume the derived sets and are unaffected.


class Role(str, Enum):
    """How-verb roles (the `Invocation.role` closed enum)."""
    ACT = "act"
    TRANSFORM = "transform"
    EFFECT = "effect"


class LifecycleState(str, Enum):
    """A2A-aligned task states (the `Lifecycle.state` closed enum)."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    AUTH_REQUIRED = "auth-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class IntentOwner(str, Enum):
    """Spec 048 — who minted an Intent (the `Intent.owner` closed enum).

    user     — originated from a user prompt (the default for top-level)
    agent    — the running agent minted this sub-intent to scope its work
    subagent — a dispatched local subagent minted this
    jules    — a remote Jules session minted this and reported back
    system   — engine-internal (install/doctor/scaffold substrate)
    """
    USER = "user"
    AGENT = "agent"
    SUBAGENT = "subagent"
    JULES = "jules"
    SYSTEM = "system"


# Plain-string sets DERIVED from the enums above (single source of truth). The
# `.value` extraction keeps these byte-identical to the historical literals, so
# every downstream consumer (FIELD_ENUMS, Ontology.violations, EntityModels'
# `Literal[...]`) sees the same plain strings it always did.
ROLES = {m.value for m in Role}                     # how-verb roles
LIFECYCLE_STATES = {m.value for m in LifecycleState}  # A2A-aligned task states
INTENT_OWNERS = {m.value for m in IntentOwner}       # Spec 048 — Intent owners

# --- core edge types (enumerated; link() rejects anything else) -------------
EDGE_TYPES = {
    "SERVES", "PERFORMED_BY", "PRODUCES", "PASSED", "BLOCKED_ON",
    "DERIVED_FROM", "VALIDATES_AGAINST", "SUPERSEDED_BY",
    "DISPATCHED_TO", "DRIVES", "PRECEDES", "NEXT", "HAS_PHASE",
    # Spec 048 — sub-intent chains back to its originating parent.
    "PARENT_INTENT",
}

# closed-enum constraints on specific (label, field) pairs — ENFORCED
FIELD_ENUMS: dict[tuple[str, str], set] = {
    ("Invocation", "role"): ROLES,
    ("Lifecycle", "state"): LIFECYCLE_STATES,
    # Spec 048 — Intent owner closed enum.
    ("Intent", "owner"): INTENT_OWNERS,
}

# The core ships NO domain skills — skills are owned by the capabilities that
# contribute them (via `OntologyExtension`). The core defines only the strict
# node/edge/enum backbone every capability's skills are built on.
CORE_SKILLS: dict[str, dict] = {}


def _schema_props(name: str, schema_value) -> dict:
    """Convert a schemas dict entry to the Schema node props.

    Two shapes supported (panel F-3 resolution — both coexist):
    - Simple: ``list[str]`` → ``{name, required: csv}`` (powers ``validate_schema``)
    - Draft-07: ``dict`` with ``$schema`` → ``{name, required: csv, schema_json: json}``
      (powers ``validate_schema_draft07``)
    """
    import json as _json
    if isinstance(schema_value, list):
        return {"name": name, "required": ",".join(schema_value)}
    if isinstance(schema_value, dict):
        required = ",".join(schema_value.get("required", []))
        return {
            "name": name,
            "required": required,
            "schema_json": _json.dumps(schema_value),
        }
    raise TypeError(
        f"schema {name!r} must be list[str] (simple) or dict (draft-07); "
        f"got {type(schema_value).__name__}")


@dataclass
class OntologyExtension:
    """The contract by which a capability EXTENDS the ontology. All six fields are
    optional — a capability that uses only core types contributes nothing. The
    engine merges every discovered capability's extension onto the core (see
    `Ontology.extend`), so schemata live with the capability that owns them.

    The six ways to extend (with their merge rule):

    - **nodes**   `{label: [required_fields]}` — new node types. STRICT: may not
                  redefine a core/owned label with different required fields.
    - **edges**   `{EDGE_TYPE, ...}` — new edge types (unioned in).
    - **enums**   `{(label, field): {allowed, ...}}` — closed-enum constraints.
                  WIDEN: a capability may add its OWN node's enum, or widen an
                  existing one; it never shrinks/clobbers.
    - **skills**  `{name: skill_schema}` — Lifecycle templates (phase-graphs).
                  Unique name required (collision raises).
    - **schemas** `{name: [required_fields]}` — artefact/template field schemas
                  powering `validate`. Unique name required.
    - **templates** `{name: body}` — named generator bodies. Unique name required.

    Every field added here is enforced live in Memory (`record`/`link`/`update`)."""
    nodes: dict[str, list[str]] = field(default_factory=dict)        # label -> required fields
    edges: set = field(default_factory=set)                         # additional edge types
    enums: dict = field(default_factory=dict)                       # (label, field) -> allowed set
    skills: dict = field(default_factory=dict)                      # skill-name -> skill schema
    schemas: dict = field(default_factory=dict)                     # artefact/template name -> required fields
    templates: dict = field(default_factory=dict)                   # template name -> body


class Ontology:
    """The effective ontology: the core, plus every capability's extension."""

    def __init__(self) -> None:
        self.nodes = {k: list(v) for k, v in NODE_SCHEMAS.items()}
        self.edges = set(EDGE_TYPES)
        self.enums = {k: set(v) for k, v in FIELD_ENUMS.items()}
        self.skills = dict(CORE_SKILLS)
        self.schemas: dict[str, list[str]] = {}
        self.templates: dict[str, str] = {}

    @classmethod
    def core(cls) -> "Ontology":
        return cls()

    def extend(self, ext: OntologyExtension, owner: str = "?") -> "Ontology":
        for label, req in ext.nodes.items():
            if label in self.nodes and list(self.nodes[label]) != list(req):
                raise ValueError(
                    f"ontology extension by {owner!r}: node {label!r} redefines an "
                    f"existing schema {self.nodes[label]} with {list(req)}")
            self.nodes[label] = list(req)
        self.edges |= set(ext.edges)
        for key, allowed in ext.enums.items():
            self.enums.setdefault(key, set()).update(allowed)     # enums widen, never clobber
        for name, sk in ext.skills.items():
            if name in self.skills:
                raise ValueError(f"{owner!r}: skill {name!r} already defined")
            self.skills[name] = sk
        for name, req in ext.schemas.items():
            if name in self.schemas:
                raise ValueError(f"{owner!r}: schema {name!r} already defined")
            # Preserve dict-shaped (draft-07) schemas verbatim; the
            # ``_schema_props`` materializer dispatches on shape. Only
            # cast list-shaped (simple) schemas to a fresh list. A bare
            # cast `list(dict)` here would silently collapse the draft-07
            # schema to its top-level keys (`['name', 'required']`),
            # corrupting validation downstream.
            if isinstance(req, dict):
                self.schemas[name] = dict(req)
            else:
                self.schemas[name] = list(req)
        for name, body in ext.templates.items():
            if name in self.templates:
                raise ValueError(f"{owner!r}: template {name!r} already defined")
            self.templates[name] = body
        return self

    # --- enforcement (used by Memory) --------------------------------------
    def missing_required(self, label: str, props: dict) -> list[str]:
        return [f for f in self.nodes.get(label, []) if props.get(f) in (None, "")]

    def violations(self, label: str, props: dict) -> list[str]:
        if label not in self.nodes:                      # strict: no typo/unknown labels slip in
            return [f"unknown node label {label!r} (not in the ontology)"]
        out = [f"missing required {f!r}" for f in self.missing_required(label, props)]
        for (lbl, fld), allowed in self.enums.items():
            if lbl == label and fld in props and props[fld] not in allowed:
                out.append(f"{fld}={props[fld]!r} not in {sorted(allowed)}")
        return out

    def is_known_edge(self, rel: str) -> bool:
        return rel in self.edges

    def skill(self, name: str) -> dict:
        return self.skills[name]

    # --- materialisation (Spec 032 §D / panel F-4) -------------------------
    def materialise_schemas(self, memory) -> dict[str, str]:
        """Record one Schema node per ontology.schemas entry (Spec 032 §D).

        Idempotent on re-run; bi-temporal supersede when a schema's shape
        changes (the ``required`` list grows/shrinks, OR simple↔draft-07 flip,
        OR draft-07 nested form changes). Old versions preserved via
        SUPERSEDED_BY edge — ``memory.recall(node_id)`` returns the latest.

        Returns ``{name: node_id}`` for every materialised schema.
        """
        mapping: dict[str, str] = {}
        for name, schema_value in self.schemas.items():
            node_id = f"schema:{name}"
            desired_props = _schema_props(name, schema_value)
            existing = memory.recall(node_id)
            if existing is None:
                # Fresh record
                memory.record("Schema", desired_props, node_id=node_id)
                mapping[name] = node_id
            else:
                # Compare only the meaningful props (ignore graphqlite internals
                # like id/vfrom/vto). A missing key on either side means a flip
                # (simple↔draft-07) — that's exactly what we want to detect.
                existing_meaningful = {k: existing.get(k)
                                       for k in desired_props}
                if existing_meaningful == desired_props:
                    # No change — no-op (preserve idempotency)
                    mapping[name] = node_id
                else:
                    # Shape change → bi-temporal supersede (panel F-4)
                    new_id = memory.supersede(node_id, desired_props)
                    mapping[name] = new_id
        return mapping

    def materialise_templates(self, memory) -> dict[str, str]:
        """Record one Template node per ontology.templates entry (Spec 032 §D).

        Same semantics as ``materialise_schemas``: idempotent on re-run, with
        bi-temporal supersede on body change. Preserves old versions via
        SUPERSEDED_BY edge.

        Returns ``{name: node_id}`` for every materialised template.
        """
        mapping: dict[str, str] = {}
        for name, body in self.templates.items():
            node_id = f"template:{name}"
            # Spec 060: bodies arriving from the file loader are
            # `string.Template` objects; pre-existing dict declarations
            # are bare strings. Coerce to str for the graph property
            # (sqlite can't serialise a Template; it expects scalar).
            body_str = body.template if hasattr(body, "template") else str(body)
            desired_props = {"name": name, "body": body_str}
            existing = memory.recall(node_id)
            if existing is None:
                memory.record("Template", desired_props, node_id=node_id)
                mapping[name] = node_id
            else:
                existing_meaningful = {k: existing.get(k)
                                       for k in desired_props}
                if existing_meaningful == desired_props:
                    mapping[name] = node_id
                else:
                    new_id = memory.supersede(node_id, desired_props)
                    mapping[name] = new_id
        return mapping
