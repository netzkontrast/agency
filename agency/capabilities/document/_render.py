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
    # Artefacts: union of (a) Artefact -SERVES-> Intent (the explicit
    # delegation/reduction path used by Spec 020) and (b) Artefact
    # PRODUCED by an Invocation that SERVES the intent (the standard
    # registry path used by every effect verb). Memory.provenance()
    # already merges these two — mirror it here so the markdown shows
    # both kinds of artefact.
    art_direct = [r["a"]["properties"] for r in memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(it:Intent) WHERE it.id = $id "
        "RETURN a",
        {"id": intent_id})]
    art_via_inv = [r["a"]["properties"] for r in memory.g.query(
        "MATCH (it:Intent)<-[:SERVES]-(inv:Invocation)-[:PRODUCES]->(a:Artefact) "
        "WHERE it.id = $id RETURN a",
        {"id": intent_id})]
    seen_ids: set[str] = set()
    art_rows: list[dict] = []
    for r in art_direct + art_via_inv:
        rid = r.get("id") or id(r)
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        art_rows.append(r)
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


def render_research_report(memory, research_id: str) -> tuple[str, int]:
    """``research-report`` scope — render a Research record + its
    citations as the deep-research publication artefact.

    Schema: H1 "Research: <question>" with the Research node's metadata
    (status, verdict, ok), H2 "Citations" with one bullet per Citation
    (source kind, source URL/path, evidence snippet, confidence), and
    H2 "Verification" reporting check statuses if a Verification node
    is linked.

    Spec 044 §"Render" — this is the documented publish path for the
    deep-research flow. Empty ``research_id`` returns a friendly error
    block (never raises).
    """
    if not research_id:
        return (h1("Research report") +
                "\n_no research_id supplied — call "
                "`research.lead` then pass its id here._\n"), 0
    rows = memory.g.query(
        "MATCH (r:Research) WHERE r.id = $rid RETURN r",
        {"rid": research_id})
    if not rows:
        return (h1("Research report") +
                f"\n_no Research record found for `{research_id}`._\n"), 0
    r = rows[0]["r"]["properties"]
    parts = [h1(f"Research: {r.get('question', '(no question)')}")]
    meta = (f"_status: {r.get('status', '?')}_ · "
            f"_verdict: {r.get('verdict', '?')}_ · "
            f"_ok: {r.get('ok', '?')}_\n\n")
    parts.append(meta)
    # Citations
    cit_rows = memory.g.query(
        "MATCH (r:Research)-[:CITES]->(c:Citation) "
        "WHERE r.id = $rid RETURN c",
        {"rid": research_id})
    citations = [row["c"]["properties"] for row in cit_rows]
    parts.append(h2("Citations"))
    if citations:
        for c in citations:
            kind = c.get("source_kind", "?")
            src = c.get("source_url_or_path", "")
            ev = truncate(c.get("evidence_text", ""), 160)
            conf = c.get("confidence", "?")
            parts.append(
                f"- **{kind}** `{src}` (conf={conf})\n"
                f"  > {ev}\n"
            )
    else:
        parts.append("\n_no citations recorded yet._\n")
    # Verification (if present) — edge points Verification -> Research
    # (`research.verify` records `link(vid, research_id, "VERIFIES")`),
    # so the query must MATCH the actual direction or the renderer
    # silently treats verified research as unverified.
    ver_rows = memory.g.query(
        "MATCH (v:Verification)-[:VERIFIES]->(r:Research) "
        "WHERE r.id = $rid RETURN v",
        {"rid": research_id})
    if ver_rows:
        parts.append(h2("Verification"))
        for row in ver_rows:
            v = row["v"]["properties"]
            # The Verification node carries rolled-up `status` + a
            # comma-joined per-check summary (e.g. "evidence-supports-
            # claim:pass,contradiction-cluster:warn"). Render the
            # roll-up plus each individual check row.
            parts.append(f"- **status**: `{v.get('status', '?')}`\n")
            checks_str = v.get("checks", "") or ""
            for item in (s for s in checks_str.split(",") if s):
                name, _, st = item.partition(":")
                parts.append(f"  - {name}: `{st or '?'}`\n")
            parts.append(
                f"  - started_at: {v.get('started_at', '?')}\n")
    parts.append(italic_footer(f"research_id: {research_id}"))
    return "".join(parts), 1 + len(citations) + len(ver_rows)
