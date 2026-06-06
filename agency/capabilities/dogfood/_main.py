"""dogfood — graph-native observation ledgers (Spec 017).

Dogfood keeps observation ledgers graph-native: notes recorded as nodes, exported and imported as JSON preserving ids and validity windows, and rendered to markdown on demand.

Use when: recording or rendering observation ledgers in the graph — capturing a development note, exporting the graph for merge-recovery, or importing it back.
Triggers:
- An insight from a dev session worth keeping
- A graph that must survive a container or merge boundary
- A ledger that should render to markdown on demand
Red flags:
- Writing a markdown ledger by hand → record it via capability_dogfood_note
- Losing graph state across a container → capability_dogfood_export the graph
"""
from __future__ import annotations

import json
import os
import re
import time

from ...capability import CapabilityBase, RenderTemplates, verb
from ...memory import OPEN


_EXPORT_VERSION = 1   # bump on shape changes


# Match the bolded observation/lesson headers we use in DOGFOOD-NOTES.md.
# Three shapes seen in the wild:
#   **Observation 1 — title text.** body...
#   **Observation 5 (architectural):** body...
#   **Dogfood lesson 5 — title text.**
# Group 3 captures everything between the index and the closing `**` so we
# can handle any separator (em-dash, hyphen, colon, parenthetical, …) at
# the orchestrator boundary by trimming leading punctuation.
_HEADER_RE = re.compile(
    r"\*\*(Observation|Dogfood lesson)\s+(\d+)([^*]*)\*\*",
    re.IGNORECASE,
)


def _count_tokens(text: str) -> int:
    """cl100k tokens via tiktoken; char//4 proxy when tiktoken absent.

    Same shape as Spec 043's _index_repo._count_tokens — token-budget
    discipline matches the document.* family.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except (ImportError, KeyError):
        return max(1, len(text) // 4)


def _clean_title(raw: str) -> str:
    """Strip leading separator punctuation + trailing period from the
    header tail so a heading like ` — dispatch hardcodes …. ` becomes
    `dispatch hardcodes …`."""
    t = raw.strip()
    while t and t[0] in " -–—:":
        t = t[1:].lstrip()
    return t.rstrip(".")


def _parse_observations(text: str) -> list[dict]:
    """Extract observations from one DOGFOOD-NOTES.md body.

    Each entry runs from its header to the next header OR a blank-line
    paragraph break before the next ``**`` boundary. Returns a list of
    ``{kind, index, title, text}`` dicts; ``text`` includes the body
    paragraph the header introduces (best-effort first paragraph after
    the header line).
    """
    out: list[dict] = []
    matches = list(_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        # Stop at the first blank line so we capture only the immediate
        # paragraph; downstream sub-paragraphs frequently introduce other
        # subjects.
        first_para = body.split("\n\n", 1)[0].strip()
        out.append({
            "kind": m.group(1).lower(),                       # "observation" | "dogfood lesson"
            "index": int(m.group(2)),
            "title": _clean_title(m.group(3) or ""),
            "text": first_para,
        })
    return out




class DogfoodCapability(CapabilityBase):
    name = "dogfood"
    home = "memory"
    render_templates = RenderTemplates.from_module(__file__)

    # -----------------------------------------------------------------
    # Spec 017 — graph-native authoring path.
    # -----------------------------------------------------------------

    @verb(role="act")
    def note(self, observation: str, plan_slug: str) -> dict:
        """Record an observation Reflection tagged with plan_slug.

        Inputs: observation (str — the body text), plan_slug (str — the
        Plan/NNN-slug directory name; used to scope render() queries).
        Returns: ``{reflection_id, plan_slug}``.
        chain_next: ``dogfood.render(plan_slug)`` when humans need the
                    DOGFOOD-NOTES.md projection.
        """
        rid = self.ctx.record("Reflection", {
            "scope": "observation",
            "text": observation,
            "plan_slug": plan_slug,
        })
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return {"reflection_id": rid, "plan_slug": plan_slug}

    @verb(role="transform")
    def render(self, plan_slug: str, max_tokens: int = 5000) -> dict:
        """Project plan_slug observations into DOGFOOD-NOTES.md.

        Inputs: plan_slug (str — same shape as note's tag),
                max_tokens (int — wire-payload cap; default 5000 cl100k;
                            additional observations get omitted with a
                            "_… (N more omitted)_" marker).
        Returns: ``{content, count, omitted, plan_slug, tokens}``. Empty
        plan returns clean markdown with "(none yet)" — never raises.
        Only Reflections with BOTH ``plan_slug == <slug>`` AND
        ``scope == 'observation'`` are surfaced (matches dogfood.note's
        write shape). Other-scope reflections + reflections without
        plan_slug are deliberately excluded.
        chain_next: caller writes ``Plan/<slug>/DOGFOOD-NOTES.md`` IF
                    a file projection is wanted (graph stays canonical).
        """
        # Query observation-scoped reflections matching plan_slug.
        # Both literals parametrized for parametrize-once-injection-
        # always-safe discipline (sc:sc-analyze F1 review finding).
        rows = self.ctx.memory.g.query(
            "MATCH (r:Reflection) WHERE r.plan_slug = $slug "
            "AND r.scope = $scope RETURN r",
            {"slug": plan_slug, "scope": "observation"})
        notes = [r["r"]["properties"] for r in rows]
        notes.sort(key=lambda r: r.get("vfrom", 0))
        # Spec 060 — render via `ctx.template('dogfood-notes')` so the
        # markdown shape lives as a file and iterating it is a markdown
        # commit, not a Python edit. Strip the `<!-- AGENT: -->` blocks
        # from the human-facing output (Spec 060 §Renderers strip blocks
        # for human-facing output).
        import re as _re
        tpl = self.ctx.template("dogfood-notes")
        if not notes:
            content = tpl.substitute(plan_slug=plan_slug, body="\n(none yet)\n")
            content = _re.sub(r"<!--.*?-->", "", content, flags=_re.DOTALL).strip()
            return {"content": content + "\n", "count": 0,
                    "omitted": 0, "tokens": _count_tokens(content),
                    "plan_slug": plan_slug}
        # Build the body string with mid-loop budget check.
        body_parts: list[str] = []
        rendered_count = 0
        for i, n in enumerate(notes, 1):
            chunk = (
                f"\n**Observation {i} — graph-native**\n\n"
                f"{n.get('text', '')}\n"
            )
            # PR review (round 7): probe BEFORE committing the chunk so
            # an oversize single observation can't push the rendered
            # payload past the cap. Trim the chunk if the probe overshoots
            # and stop iteration (the budget marker is appended later).
            probe = tpl.substitute(
                plan_slug=plan_slug,
                body="".join(body_parts) + chunk,
            )
            if _count_tokens(probe) > max_tokens * 0.92:
                # Compute remaining headroom and truncate this chunk to fit.
                current = tpl.substitute(
                    plan_slug=plan_slug, body="".join(body_parts))
                headroom_tokens = max(0, int(max_tokens * 0.92) - _count_tokens(current))
                # Token-budget proxy: ~4 chars per token (mirrors _count_tokens
                # fallback). Trim chunk to that char budget.
                char_cap = max(0, headroom_tokens * 4)
                if char_cap > 0 and rendered_count == 0:
                    # Always render at least a truncated form of the FIRST
                    # observation (so callers get SOMETHING back).
                    truncated = chunk[:char_cap] + "\n_…(truncated)_\n"
                    body_parts.append(truncated)
                    rendered_count = i
                break
            body_parts.append(chunk)
            rendered_count = i
        omitted = max(0, len(notes) - rendered_count)
        if omitted:
            body_parts.append(
                f"\n_… ({omitted} more observations omitted to fit "
                f"max_tokens={max_tokens})_\n")
        content = tpl.substitute(plan_slug=plan_slug, body="".join(body_parts))
        # Strip AGENT instruction blocks for the human-view output.
        content = _re.sub(r"<!--.*?-->", "", content, flags=_re.DOTALL).strip() + "\n"
        return {"content": content, "count": rendered_count,
                "omitted": omitted, "tokens": _count_tokens(content),
                "plan_slug": plan_slug}

    # -----------------------------------------------------------------
    # Spec 020 — JSON export (merge-conflict recovery fallback).
    # -----------------------------------------------------------------

    @verb(role="effect")
    def export(self, path: str = "") -> dict:
        """Dump the provenance store to a portable JSON file.

        Inputs: path (str — destination; empty → ``.agency/export-<ns>.json``
                  with a nanosecond-precision timestamp to avoid path
                  collisions between exports in the same second).
        Returns: ``{path, nodes, edges, bytes}``.

        Snapshot semantics: this export captures the FULL bi-temporal
        history (all nodes regardless of vto), not just the
        current-as-of-now snapshot. Replay against a fresh DB
        therefore reconstructs the entire append-only timeline —
        which is the right behaviour for merge-conflict recovery.

        Use case: merge-conflict recovery (Spec 020 line 69-73). When
        two branches both write to ``.agency/session.db`` and merge,
        the binary conflict can't be resolved. Recovery: export each
        branch's graph to JSON, then replay both JSONs against a fresh
        DB on the merged branch. The export is portable + diff-able
        (JSON is indent=2 + sort_keys=True).

        v1 scope: this verb ONLY emits the export. A matching
        ``dogfood.import`` verb that replays the JSON (preserving
        original node ids + vfrom/vto windows) is a v2 follow-up.

        chain_next: caller can rsync, commit, or replay the JSON.
        """
        graph_path = path or self._default_export_path()
        os.makedirs(os.path.dirname(graph_path) or ".", exist_ok=True)
        nodes = self._collect_all_nodes()
        edges = self._collect_all_edges()
        payload = {
            "version": _EXPORT_VERSION,
            "generated_at": int(time.time()),
            "nodes": nodes,
            "edges": edges,
        }
        with open(graph_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        return {
            "path": graph_path,
            "nodes": len(nodes),
            "edges": len(edges),
            "bytes": os.path.getsize(graph_path),
        }

    def _default_export_path(self) -> str:
        """``.agency/export-<unix-ns>.json`` in the CWD; mirrors the
        Spec 020 ``.agency/`` convention.

        Uses nanosecond precision (review F6) so two exports in the
        same second don't clobber each other. Returned absolute so
        the caller doesn't need to track CWD."""
        ns = time.time_ns()
        return os.path.abspath(
            os.path.join(".agency", f"export-{ns}.json"))

    def _collect_all_nodes(self) -> list[dict]:
        """Every node in the graph — FULL bi-temporal history (per F1
        review finding + the merge-recovery use case). The MATCH (n)
        pattern returns superseded nodes alongside current ones, which
        is exactly what replay needs to reconstruct the timeline."""
        rows = self.ctx.memory.g.query("MATCH (n) RETURN n")
        out: list[dict] = []
        for r in rows:
            n = r["n"]
            props = n.get("properties", {})
            label = n.get("label") or n.get("labels", [""])[0] \
                if isinstance(n.get("labels"), list) else n.get("label", "")
            out.append({
                "id": props.get("id", ""),
                "label": label,
                "properties": {k: v for k, v in props.items() if k != "id"},
            })
        return out

    # -----------------------------------------------------------------
    # Spec 020 v2 — JSON replay (the matching reverse of export).
    # -----------------------------------------------------------------

    @verb(role="effect", name="import")
    def import_(self, path: str) -> dict:
        """Replay a JSON export into this graph, preserving ids + windows.

        Inputs: path (str — JSON file written by ``dogfood.export``).
        Returns: ``{imported_nodes, imported_edges, version}``.
        Raises: FileNotFoundError on missing path; ValueError on
        unsupported export version.

        Closes Spec 020's merge-conflict recovery loop: each branch's
        DB is exported, the binary conflict is discarded, and both
        JSONs replay into a fresh DB on the merged branch.

        Preservation discipline: nodes land at their original ids with
        the original ``vfrom``/``vto`` window — bypassing ``record()``'s
        clock tick so bi-temporal history is exact. After replay, the
        memory's logical clock advances past every imported tick so new
        writes cannot collide with imported windows.

        chain_next: terminal — caller can verify with
                    ``MATCH (n) RETURN count(n)`` or ``reflect.search``.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        version = payload.get("version")
        if version != _EXPORT_VERSION:
            raise ValueError(
                f"unsupported export version {version!r}; "
                f"this build reads version {_EXPORT_VERSION}")

        nodes = payload.get("nodes", [])
        edges = payload.get("edges", [])

        max_tick = 0
        existing = {
            r["n"].get("properties", {}).get("id")
            for r in self.ctx.memory.g.query("MATCH (n) RETURN n")
        }
        for n in nodes:
            nid = n.get("id")
            if not nid or nid in existing:
                continue
            label = n.get("label") or "Entity"
            props = dict(n.get("properties", {}))
            # Direct upsert — bypass record()'s clock tick + ontology
            # gate so the original vfrom/vto window survives intact.
            self.ctx.memory.g.upsert_node(nid, props, label=label)
            for k in ("vfrom", "vto"):
                v = props.get(k)
                if isinstance(v, int) and v != OPEN and v > max_tick:
                    max_tick = v

        imported_edges = 0
        for e in edges:
            src, dst = e.get("from"), e.get("to")
            rel = e.get("type") or "RELATED"
            if not src or not dst:
                continue
            self.ctx.memory.g.upsert_edge(
                src, dst, dict(e.get("properties") or {}), rel_type=rel)
            v = e.get("properties", {}).get("vfrom")
            if isinstance(v, int) and v != OPEN and v > max_tick:
                max_tick = v
            imported_edges += 1

        # Advance the logical clock past every imported tick so a
        # subsequent record()/link() can't reuse a stale vfrom.
        with self.ctx.memory._lock:
            if max_tick >= self.ctx.memory._tick:
                self.ctx.memory._tick = max_tick

        return {
            "imported_nodes": sum(
                1 for n in nodes
                if n.get("id") and n["id"] not in existing),
            "imported_edges": imported_edges,
            "version": version,
        }

    def _collect_all_edges(self) -> list[dict]:
        """Every edge in the graph with type + endpoints + properties."""
        rows = self.ctx.memory.g.query("MATCH (a)-[e]->(b) RETURN a, e, b")
        out: list[dict] = []
        for r in rows:
            edge = r["e"]
            props = edge.get("properties", {}) if isinstance(edge, dict) else {}
            edge_type = (
                edge.get("type") or edge.get("rel_type")
                or (edge.get("relationship") if isinstance(edge, dict) else "")
                or ""
            )
            out.append({
                "from": r["a"].get("properties", {}).get("id", ""),
                "to": r["b"].get("properties", {}).get("id", ""),
                "type": edge_type,
                "properties": props,
            })
        return out

    # -----------------------------------------------------------------
    # Spec 017 — collect kept for backward-compat (Spec 014 pipeline).
    # -----------------------------------------------------------------

    @verb(role="transform")
    def collect(self, plan_dir: str = "Plan") -> dict:
        """Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

        Inputs: plan_dir (str — root dir of plans; default ``Plan``).
        Returns: ``{observations: [{plan, kind, index, title, text}],
                 texts: [str], count, plans: [str], warnings: [str]}``.
        chain_next: ``reflect.batch_note(scope='observation', texts=)`` to
                    seed the graph from one-shot migration of legacy files.

        Deprecated for ongoing use — prefer ``dogfood.note`` (graph-
        native authoring) + ``dogfood.render`` (markdown projection on
        demand). Errors (missing dir, unreadable file) degrade into
        the ``warnings`` list rather than raising.
        """
        observations: list[dict] = []
        plans: list[str] = []
        warnings: list[str] = []

        if not os.path.isdir(plan_dir):
            return {"observations": [], "texts": [], "count": 0,
                    "plans": [], "warnings": [f"plan_dir not found: {plan_dir}"]}

        for entry in sorted(os.listdir(plan_dir)):
            plan_path = os.path.join(plan_dir, entry)
            notes_path = os.path.join(plan_path, "DOGFOOD-NOTES.md")
            if not os.path.isfile(notes_path):
                continue
            plans.append(entry)
            try:
                with open(notes_path, encoding="utf-8") as fh:
                    body = fh.read()
            except OSError as e:
                warnings.append(f"{notes_path}: {e}")
                continue
            for obs in _parse_observations(body):
                obs["plan"] = entry
                observations.append(obs)

        texts = [o["text"] for o in observations if o["text"]]
        return {
            "observations": observations,
            "texts": texts,
            "count": len(observations),
            "plans": plans,
            "warnings": warnings,
        }
