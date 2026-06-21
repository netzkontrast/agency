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
        rows = memory.sources_via_edge(
            "OBSERVED_DURING", intent_id, "Intent", label="Reflection")
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


def render_lifecycle_board(memory) -> tuple[str, int]:
    """``lifecycle-board`` scope (Spec 343 phase 6) — the in-flight board.

    Schema: H1 "Lifecycle board"; H2 "By state" (markdown table state | count
    over ALL lifecycles); H2 "In flight" (markdown table id | state | machine |
    parameterization | intent over the NON-terminal lifecycles — the ones still
    needing attention). Terminal = ``completed`` / ``canceled`` (the universal
    A2A endings; ``failed`` stays on the board as retry-able). Read-only graph→
    markdown — the discipline's report phase mirrors this to ``lifecycle-board.md``
    as a Spec 292 file peer (``document.mirror``).
    """
    terminal = {"completed", "canceled"}
    lcs = list(memory.find("Lifecycle"))
    by_state: dict[str, int] = {}
    for lc in lcs:
        s = lc.get("state", "?")
        by_state[s] = by_state.get(s, 0) + 1
    parts = [h1("Lifecycle board")]
    parts.append(h2("By state"))
    if by_state:
        parts.append(table(["state", "count"],
                           [[s, str(by_state[s])] for s in sorted(by_state)]))
    else:
        parts.append("\n_no lifecycles_\n")
    in_flight = [lc for lc in lcs if lc.get("state") not in terminal]
    in_flight.sort(key=lambda lc: (lc.get("state", ""), lc.get("vfrom", 0)))
    parts.append(h2("In flight"))
    if in_flight:
        rows = []
        for lc in in_flight:
            lid = lc.get("id", "?")
            serving = memory.neighbors(lid, "SERVES", direction="out")
            intent = serving[0].get("id", "") if serving else ""
            rows.append([lid, lc.get("state", "?"), lc.get("machine", "a2a"),
                         lc.get("parameterization", "") or "—", intent or "—"])
        parts.append(table(["id", "state", "machine", "parameterization", "intent"], rows))
    else:
        parts.append("\n_nothing in flight_\n")
    return "".join(parts), len(in_flight)


def render_provenance(memory, intent_id: str) -> tuple[str, int]:
    """``provenance`` scope — per-intent provenance brief.

    Schema: H1 "Intent <id> provenance"; H2 "Acceptance" (one line);
    H2 "Invocations" (markdown table timestamp | verb | role |
    duration_ms); H2 "Artefacts" (markdown table kind | id | size).
    """
    if not intent_id:
        return h1("Intent (none) provenance") + "\n_no intent id provided_\n", 0
    # PR review (round 7): walk the SUPERSEDED_BY chain so an amended
    # intent's provenance fragments don't disappear. Mirrors
    # Memory.provenance() which already does the right thing for the
    # programmatic surface; the markdown render had drifted.
    chain = list(memory._intent_chain(intent_id))
    intents = [i for i in memory.find("Intent") if i.get("id") in chain]
    acceptance = intents[0].get("acceptance", "<unknown>") if intents else "<unknown>"
    parts = [h1(f"Intent {intent_id} provenance")]
    parts.append(h2("Acceptance"))
    parts.append(acceptance + "\n")
    # Invocations table — provenance lives on SERVES edges from
    # Invocation → Intent. Use the graph query, not a property filter.
    inv_rows = memory.nodes_serving(chain, label="Invocation")
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
    art_direct = memory.nodes_serving(chain, label="Artefact")
    art_via_inv = memory.artefacts_produced_under(chain)
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
    # Walk the chain (PR review round 7) so amended intents' sub-tree
    # is fully visible.
    sub_rows = memory.sources_via_edge("PARENT_INTENT", chain, "Intent",
                                       label="Intent")
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
    r = memory.recall_typed(research_id, "Research")
    if not r:
        return (h1("Research report") +
                f"\n_no Research record found for `{research_id}`._\n"), 0
    parts = [h1(f"Research: {r.get('question', '(no question)')}")]
    meta = (f"_status: {r.get('status', '?')}_ · "
            f"_verdict: {r.get('verdict', '?')}_ · "
            f"_ok: {r.get('ok', '?')}_\n\n")
    parts.append(meta)
    # Citations
    citations = memory.neighbors(research_id, "CITES", direction="out")
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
    ver_rows = memory.sources_via_edge(
        "VERIFIES", research_id, "Research", label="Verification")
    if ver_rows:
        parts.append(h2("Verification"))
        for v in ver_rows:
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
