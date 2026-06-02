"""Scope renderers for ``document.render`` — graph → markdown.

Each function takes a Memory and returns the rendered markdown for
its scope. Schemas are fixed per Spec 043 §"Done When" — changing
them is a spec amendment, not a runtime decision.
"""
from __future__ import annotations

from ._templates import fenced, h1, h2, italic_footer, table, truncate


_REFLECTION_TEXT_TRUNCATE = 500


def render_install_artefacts(memory) -> tuple[str, int]:
    """``install-artefacts`` scope.

    Schema (Spec 043 §"Done When"):
      H1 = "Install artefacts"
      one H2 per artefact sorted by `name`
      H2 body = fenced code block with rendered `body`
      H2 footer = italic ``<vfrom> · <id>``
    """
    nodes = [r for r in memory.find("Reflection")
             if r.get("kind") == "install-artefact"]
    nodes.sort(key=lambda r: r.get("name", ""))
    parts = [h1("Install artefacts")]
    for n in nodes:
        name = n.get("name", "<unnamed>")
        body = n.get("body", "")
        parts.append(h2(name))
        parts.append(fenced(body))
        parts.append(italic_footer(f"{n.get('vfrom', '?')} · {n.get('id', '?')}"))
    return "".join(parts), len(nodes)


def render_reflections(memory, intent_id: str = "") -> tuple[str, int]:
    """``reflections`` scope.

    Schema: H1 "Reflections (intent=<id|all>)"; H2 per Reflection
    newest-first by `vfrom`; H2 body = `text` truncated to 500 chars
    + italic header ``scope: <scope>``.

    Intent-scoped filter uses the OBSERVED_DURING edge — the same
    relation reflect.note records on every write.
    """
    if intent_id:
        # OBSERVED_DURING from Reflection → Intent. The graph query is
        # the authoritative filter; Reflection properties don't carry
        # intent_id (provenance lives on edges, not nodes).
        rows = [r["r"]["properties"] for r in memory.g.query(
            "MATCH (r:Reflection)-[:OBSERVED_DURING]->(i:Intent) "
            "WHERE i.id = $id RETURN r",
            {"id": intent_id})]
    else:
        rows = list(memory.find("Reflection"))
    rows.sort(key=lambda r: r.get("vfrom", 0), reverse=True)
    label = intent_id if intent_id else "all"
    parts = [h1(f"Reflections (intent={label})")]
    for r in rows:
        parts.append(h2(r.get("id", "<reflection>")))
        parts.append(italic_footer(f"scope: {r.get('scope', '?')}"))
        parts.append(truncate(r.get("text", ""), _REFLECTION_TEXT_TRUNCATE))
        parts.append("\n")
    return "".join(parts), len(rows)


def render_provenance(memory, intent_id: str) -> tuple[str, int]:
    """``provenance`` scope — per-intent provenance brief.

    Schema: H1 "Intent <id> provenance"; H2 "Acceptance" (one line);
    H2 "Invocations" (markdown table timestamp | verb | role |
    duration_ms); H2 "Artefacts" (markdown table kind | id | size).
    """
    if not intent_id:
        return h1("Intent (none) provenance") + "\n_no intent id provided_\n", 0
    intents = [i for i in memory.find("Intent") if i.get("id") == intent_id]
    acceptance = intents[0].get("acceptance", "<unknown>") if intents else "<unknown>"
    parts = [h1(f"Intent {intent_id} provenance")]
    parts.append(h2("Acceptance"))
    parts.append(acceptance + "\n")
    # Invocations table — provenance lives on SERVES edges from
    # Invocation → Intent. Use the graph query, not a property filter.
    inv_rows = [r["i"]["properties"] for r in memory.g.query(
        "MATCH (i:Invocation)-[:SERVES]->(it:Intent) WHERE it.id = $id "
        "RETURN i",
        {"id": intent_id})]
    inv_rows.sort(key=lambda r: r.get("vfrom", 0))
    parts.append(h2("Invocations"))
    if inv_rows:
        parts.append(table(
            ["timestamp", "verb", "role", "duration_ms"],
            [[str(r.get("vfrom", "?")), r.get("verb", "?"),
              r.get("role", "?"), str(r.get("duration_ms", ""))]
             for r in inv_rows],
        ))
    else:
        parts.append("\n_no invocations recorded_\n")
    # Artefacts (Spec 020 §"reduction") — SERVES edge to the intent.
    art_rows = [r["a"]["properties"] for r in memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(it:Intent) WHERE it.id = $id "
        "RETURN a",
        {"id": intent_id})]
    # Spec 048 — sub-intents under this one (PARENT_INTENT downward
    # walk; capped at 2 levels for the default provenance render).
    sub_rows = [r["c"]["properties"] for r in memory.g.query(
        "MATCH (c:Intent)-[:PARENT_INTENT]->(p:Intent) "
        "WHERE p.id = $id RETURN c",
        {"id": intent_id})]
    parts.append(h2("Artefacts"))
    if art_rows:
        parts.append(table(
            ["kind", "id", "size"],
            [[r.get("kind", "?"), r.get("id", "?"),
              str(r.get("size", ""))] for r in art_rows],
        ))
    else:
        parts.append("\n_no artefacts recorded_\n")
    # Spec 048 — Sub-intents H2 section (PARENT_INTENT downward).
    parts.append(h2("Sub-intents"))
    if sub_rows:
        parts.append(table(
            ["intent_id", "owner", "purpose"],
            [[r.get("id", "?"), r.get("owner", "?"),
              r.get("purpose", "")[:60]] for r in sub_rows],
        ))
    else:
        parts.append("\n_no sub-intents recorded_\n")
    return ("".join(parts),
             len(inv_rows) + len(art_rows) + len(sub_rows))


def render_capability_catalogue(registry) -> tuple[str, int]:
    """``capability-catalogue`` scope — the engine's live capability map.

    Schema: H1 "Capability catalogue"; H2 per capability sorted by
    `name`; H2 body = bullets ``<verb>`` (brief slice + role tag);
    footer counts (capabilities, verbs).
    """
    parts = [h1("Capability catalogue")]
    cap_names = sorted(registry.names())
    total_verbs = 0
    for cap_name in cap_names:
        cap = registry.get(cap_name)
        parts.append(h2(cap_name))
        verbs = sorted(cap.verbs)
        for v in verbs:
            spec = cap.verbs[v]
            role = spec.get("role", "?")
            fn = spec.get("fn")
            doc_lines = (fn.__doc__ or "").strip().splitlines() if fn else []
            doc = doc_lines[0] if doc_lines else ""
            parts.append(f"- **{v}** _({role})_ — {doc}\n")
            total_verbs += 1
    parts.append(italic_footer(
        f"{len(cap_names)} capabilities · {total_verbs} verbs"))
    return "".join(parts), len(cap_names)
