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
from ...ontology import OntologyExtension


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
    """Spec 082 — route through the ONE token-count boundary (count_tokens →
    tiktoken → proxy); was a duplicate of the document.* inline proxy."""
    from ..._tokens import count_tokens
    return count_tokens(text)


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




# ────────────────────────────────────────────────────────────────────────────
# Spec 150 Slice 1 — amendment classifier + apply helpers (module-level).
# ────────────────────────────────────────────────────────────────────────────
# Keyword classifier rules. Each tuple is (regex, op, section, confidence).
# The keyword path is the documented fallback when the Spec 147 AnthropicDriver
# is unavailable (never silent no-op); Slice 2 swaps in structured-output
# classification through the driver.
import difflib
import hashlib

_CLASSIFIER_RULES: list[tuple[re.Pattern, str, str, float]] = [
    (re.compile(r"\bshould add\b", re.IGNORECASE), "add-done-when", "Done When", 0.7),
    (re.compile(r"\bpropose\b", re.IGNORECASE),    "add-done-when", "Done When", 0.65),
    (re.compile(r"\bshould be\b", re.IGNORECASE),  "add-done-when", "Done When", 0.6),
    (re.compile(r"\bmissing from spec\b", re.IGNORECASE),
                                                    "add-done-when", "Done When", 0.75),
    (re.compile(r"\bopen question\b", re.IGNORECASE),
                                                    "add-open-q", "Open questions", 0.65),
]


# ── Spec 150 Slice 2 — LLM classifier path ────────────────────────────────
# Documented amendment ops the LLM may emit. Kept aligned with the keyword
# path so the downstream `apply_amendment` flow is the same.
_LLM_OPS = ("add-done-when", "add-open-q", "edit-done-when", "edit-open-q")
_LLM_SECTIONS = ("Done When", "Open questions", "Followup", "row")


# JSON schema the AnthropicDriver enforces via structured outputs. Slice 2
# uses output_config.format=json_schema (Spec 147 claude-api skill).
_PROPOSAL_LIST_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["proposals"],
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["reflection_id", "spec_id", "section", "op",
                              "after", "rationale", "confidence"],
                "properties": {
                    "reflection_id": {"type": "string"},
                    "spec_id":       {"type": "string", "pattern": r"^\d{3}$"},
                    "section":       {"type": "string", "enum": list(_LLM_SECTIONS)},
                    "op":            {"type": "string", "enum": list(_LLM_OPS)},
                    "after":         {"type": "string", "minLength": 1},
                    "rationale":     {"type": "string", "minLength": 40},
                    "confidence":    {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    },
}


_CLASSIFIER_SYSTEM = (
    "You are the dogfood amendment classifier. You receive a JSON list of "
    "reflection objects (each with id + plan_slug + text + scope). For "
    "EVERY reflection whose text proposes a concrete amendment to a spec, "
    "emit one ProposalPayload — spec_id (NNN from plan_slug, 3-digit), "
    "section (one of Done When / Open questions / Followup / row), op (one "
    "of add-done-when / add-open-q / edit-done-when / edit-open-q), after "
    "(the proposed new text, 1+ chars), rationale (>= 40 chars, citing the "
    "reflection text), confidence in [0,1]. Skip neutral reflections "
    "(observations without an actionable proposal). Output strictly matches "
    "the schema; do not invent spec_ids that aren't in the input plan_slugs."
)


def _reflection_payload_for_llm(refl: dict) -> dict:
    """Trim a Reflection's properties to the fields the classifier needs.
    Keeps the LLM payload small (Spec 154 output-overflow discipline)."""
    return {
        "id":        refl.get("id") or "",
        "plan_slug": refl.get("plan_slug") or "",
        "scope":     refl.get("scope") or "",
        "text":      (refl.get("text") or "").strip()[:1200],
    }


def _build_classifier_messages(reflections: list[dict]) -> list[dict]:
    """Build the messages list for `complete_or_delegate`. The user
    message carries the reflections as JSON so the model parses
    deterministically."""
    payload = [_reflection_payload_for_llm(r) for r in reflections]
    user = (
        "Classify these reflections into ProposalPayload objects per the "
        "schema. Emit ONLY actionable proposals; skip neutral observations.\n\n"
        f"reflections = {json.dumps(payload, sort_keys=True)}"
    )
    return [{"role": "user", "content": user}]


def _parse_llm_proposals(parsed: dict | None,
                          reflections_by_id: dict[str, dict],
                          limit: int) -> list[dict]:
    """Convert the LLM's structured output into the canonical
    ProposalPayload shape (matching the keyword path's `proposals` list).
    Drops any proposal whose reflection_id isn't in the input set —
    defense against the LLM hallucinating reflections."""
    if not isinstance(parsed, dict):
        return []
    raw = parsed.get("proposals") or []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        rid = p.get("reflection_id") or ""
        refl = reflections_by_id.get(rid)
        if refl is None:
            continue                                              # hallucination — drop
        # Codex review on PR #136: host_completion bypasses the
        # driver-side JSON-schema enforcement, so validate the same
        # invariants HERE — enum-bound section + op, [0,1] confidence,
        # 40-char rationale floor. Drop the proposal on any miss.
        section = str(p.get("section") or "")
        op = str(p.get("op") or "")
        if section not in _LLM_SECTIONS or op not in _LLM_OPS:
            continue
        try:
            confidence = float(p.get("confidence") or 0.0)
        except (TypeError, ValueError):
            continue
        if not (0.0 <= confidence <= 1.0):
            continue
        rationale = str(p.get("rationale") or "")
        if len(rationale) < 40:
            continue
        after = str(p.get("after") or "").strip()
        if not after:
            continue
        # Codex review on PR #136: derive spec_id from the cited
        # reflection's plan_slug rather than trusting the model. A
        # classifier mistake could route apply_amendment to the wrong
        # spec while provenance points at a different plan — silently
        # mis-attributing the amendment. The plan_slug is the
        # ground-truth source.
        derived_spec_id = _spec_id_from_slug(refl.get("plan_slug") or "")
        if not derived_spec_id:
            continue
        model_spec_id = str(p.get("spec_id") or "")
        if model_spec_id and model_spec_id != derived_spec_id:
            continue                                              # mismatch — drop
        out.append({
            "spec_id":            derived_spec_id,
            "section":            section,
            "op":                 op,
            "before":             "",
            "after":              after,
            "rationale":          rationale,
            "source_reflections": [rid],
            "confidence":         confidence,
        })
        if len(out) >= limit:
            break
    return out


def _classify_reflection(text: str) -> dict:
    """Classify ONE reflection text into an amendment op + section + confidence.

    Returns ``{"op": None}`` for neutral observations (no amendment). The
    keyword path is deliberately CONSERVATIVE: false positives erode trust.
    """
    for rule, op, section, conf in _CLASSIFIER_RULES:
        m = rule.search(text or "")
        if m:
            return {"op": op, "section": section, "confidence": conf,
                    "matched": m.group(0)}
    return {"op": None}


def _spec_id_from_slug(plan_slug: str) -> str:
    """Extract the NNN spec-id from a `NNN-slug` plan_slug."""
    head = (plan_slug or "").split("-", 1)[0]
    return head if head.isdigit() else ""


def _resolve_spec_path(spec_id: str) -> str | None:
    """Find ``Plan/<spec_id>-*/spec.md`` on disk; return None when missing."""
    import glob
    if not spec_id or not spec_id.isdigit():
        return None
    matches = sorted(glob.glob(f"Plan/{spec_id}-*/spec.md"))
    return matches[0] if matches else None


def _payload_hash(payload: dict) -> str:
    """Stable id-hash for a proposal — used by the confirm_token live-write
    gate. Hashed over (spec_id, section, op, after) so a re-classification
    that proposes the same edit yields the same token."""
    key = "|".join([payload.get("spec_id", ""),
                    payload.get("section", ""),
                    payload.get("op", ""),
                    (payload.get("after") or "").strip()])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _render_unified_diff(spec_path: str, *, before: str, after: str,
                          spec_id: str) -> str:
    """Render an amendment as a unified-diff hunk. The dry-run output the
    reviewer reads. For Slice 1 we emit a SYNTHETIC unified diff that names
    the spec file + the proposed before/after — enough for a reviewer to
    decide; the file-line surgery is Slice 2 (needs a proper section
    locator).
    """
    before_lines = (before + "\n").splitlines(keepends=True) if before else []
    after_lines = (after + "\n").splitlines(keepends=True) if after else []
    diff_iter = difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"a/{spec_path}",
        tofile=f"b/{spec_path}",
        n=0,
    )
    diff = "".join(diff_iter)
    if not diff:
        diff = f"--- a/{spec_path}\n+++ b/{spec_path}\n@@ -0,0 +1 @@\n+{after}\n"
    return diff


class DogfoodCapability(CapabilityBase):
    name = "dogfood"
    home = "memory"
    render_templates = RenderTemplates.from_module(__file__)
    # Spec 114 — session-tracking ontology: DecisionRecord binds decisions to
    # a session; BoundaryUse records a raw-tool invocation so future sessions
    # can detect "should have called a capability verb" patterns.
    ontology = OntologyExtension(
        nodes={
            # `rationale` required for grounded decisions; `next_action`
            # optional. SessionLifecycle linkage via RELATES_TO when known.
            "DecisionRecord": ["subject", "decision", "rationale"],
            # Spec 195 Slice 1 — BoundaryUse carries the raw-tool
            # bypass info: `tool` (Write/Edit/Bash), `argument_summary`
            # (trimmed), `target` (full path/command), `verb_shadow`
            # (the capability verb that SHOULD have served the same
            # intent), `intent_id` (SERVES which Intent), `session`.
            "BoundaryUse":    ["tool", "argument_summary"],
            # Spec 150 — amendment-proposal provenance: every accepted
            # amendment writes an `Artefact(kind="amendment-proposal")`
            # with PRODUCES_FROM edges to every cited Reflection so a
            # reviewer can trace any amendment back to its sources.
            "Artefact":       ["kind"],
        },
        # PRODUCES_FROM: amendment → cited Reflection
        # RECORDED_BY: Spec 195 — BoundaryUse → originating Event
        edges={"RELATES_TO", "PRODUCES_FROM", "RECORDED_BY"},
    )

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

    # ════════════════════════════════════════════════════════════════════════
    # Spec 114 — session-tracking: bind decisions + audit boundary uses.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    def record_decision(self, subject: str, decision: str,
                         rationale: str = "",
                         next_action: str = "",
                         session_lifecycle_id: str = "") -> dict:
        """Bind a decision to the current session (effect).

        Creates a `DecisionRecord` node SERVING the intent. Optionally edges
        to a SessionLifecycle so the decision history is queryable.

        Inputs: subject (what was decided about), decision (the choice),
                rationale (why), next_action (what follows), session_lifecycle_id
                (optional — links the DecisionRecord to the session).
        Returns: ``{decision_id, subject, decision}``.
        chain_next: act on `next_action`, or `reflect.note` the rationale.
        """
        did = self.ctx.record("DecisionRecord", {
            "subject": subject, "decision": decision,
            "rationale": rationale, "next_action": next_action,
        })
        self.ctx.link(did, self.ctx.intent_id, "SERVES")
        if session_lifecycle_id:
            self.ctx.link(did, session_lifecycle_id, "RELATES_TO")
        return {"decision_id": did, "subject": subject,
                "decision": decision}

    @verb(role="transform")
    def boundary_use_audit(self,
                            for_intent_id: str = "",
                            session_lifecycle_id: str = "") -> dict:
        """Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform).

        Reads BoundaryUse nodes (Spec 195 Slice 1: recorded by the
        engine's default hook handler when a raw Write/Edit/Bash fires
        under an active intent) and aggregates them into a typed audit
        report.

        Spec 195 invariants:
        - `bypass_count` is the sum of `by_tool` counts (no double-count).
        - When `for_intent_id` is given, only uses SERVING that intent
          are included (cross-intent contamination caught by the SERVES
          edge filter).
        - `samples` shows up to 5 representative records per tool (a
          paged audit reader can chain `dogfood.recall_overflow_slice`
          for the full set).

        Inputs: for_intent_id (str — filter to BoundaryUses serving
                this intent; "" = global).
                session_lifecycle_id (legacy alias; ignored when
                for_intent_id is set).
        Returns: ``{intent_id, bypass_count, by_tool: {Write, Edit, Bash, …},
                 samples: [{tool, target, verb_shadow, argument_summary,
                 session}], count}``.
        chain_next: ``dogfood.parse_amendment`` reads the bypass rate
                    when the dogfood loop classifies amendments.
        """
        # Suggestion mapping (Pillar 2 of Spec 114 — capability-first
        # routing). Spec 195 carries the live `verb_shadow` from the
        # BoundaryUse node; this dict is only a fallback for legacy
        # records (Slice 0 BoundaryUse nodes that pre-date Slice 1).
        _SUGGEST = {
            "Write":    "develop.scaffold_capability OR dogfood.observe",
            "Edit":     "dogfood.observe (spec edit) OR direct verb call",
            "Bash":     "shell.run OR branch.commit_smart OR develop.test",
            "WebFetch": "research.fetch (future)",
            "Grep":     "analyze.search (future)",
        }
        uses = self.ctx.find("BoundaryUse")
        # Filter by intent_id when requested. The BoundaryUse node
        # carries `intent_id` as a property; we use it directly rather
        # than walking SERVES edges to keep the filter O(N).
        if for_intent_id:
            uses = [u for u in uses
                    if u.get("intent_id") == for_intent_id]
        by_tool: dict[str, int] = {}
        samples_per_tool: dict[str, list[dict]] = {}
        for u in uses:
            tool = str(u.get("tool", ""))
            by_tool[tool] = by_tool.get(tool, 0) + 1
            bucket = samples_per_tool.setdefault(tool, [])
            if len(bucket) < 5:
                bucket.append({
                    "tool":             tool,
                    "target":           u.get("target", ""),
                    "verb_shadow":      u.get("verb_shadow")
                                          or _SUGGEST.get(tool, "(none)"),
                    "argument_summary": u.get("argument_summary", ""),
                    "session":          u.get("session", ""),
                })
        samples: list[dict] = []
        for tool in sorted(samples_per_tool):
            samples.extend(samples_per_tool[tool])
        return {
            "intent_id":    for_intent_id,
            "bypass_count": sum(by_tool.values()),
            "by_tool":      dict(sorted(by_tool.items())),
            "samples":      samples,
            "count":        sum(by_tool.values()),                 # legacy alias
        }

    @verb(role="transform")
    def replay_events(self, for_intent_id: str = "",
                       tool: str = "", limit: int = 100) -> dict:
        """Replay every Event recorded OBSERVED_DURING the given intent
        (Spec 195 Slice 2 — typed replay + monotonic chain).

        Returns the sequence of typed event rows in record order, each
        linked to its `prior_event_id` (the previous event in the same
        intent's replay; empty for the first). Slice 1 BoundaryUse nodes
        are joined in via the RECORDED_BY edge so the replay surface
        carries the moat metadata when present.

        Inputs: for_intent_id (str — required; the SERVES anchor).
                tool (str — optional filter; "" = every tool).
                limit (int — bound the row count; default 100).
        Returns: ``{intent_id, events: [{event_id, prior_event_id, name,
                  tool, session, target, verb_shadow, summary}], count}``.
        chain_next: ``dogfood.parse_amendment`` reads the replay when the
                    classifier needs the recent-event window.
        """
        intent_id = for_intent_id
        if not intent_id:
            return {"intent_id": "", "events": [], "count": 0}
        # Walk Event nodes that OBSERVED_DURING the intent; preserve
        # record-creation order (the in-graph id is a stable monotone
        # sequence per Spec 002 substrate guarantees).
        rows = self.ctx.memory.g.query(
            "MATCH (e:Event)-[:OBSERVED_DURING]->(i:Intent) "
            "WHERE i.id = $iid RETURN e",
            {"iid": intent_id})
        events = [r["e"]["properties"] for r in rows]
        # Stable order by created_at if present, else by id (record-order
        # convention). The graph appends in insertion order; we sort the
        # list explicitly to stay deterministic across query backends.
        events.sort(key=lambda p: (
            p.get("created_at", ""), str(p.get("id", ""))))
        if tool:
            events = [p for p in events if p.get("tool") == tool]
        events = events[: max(0, int(limit))]
        # Join BoundaryUse via the RECORDED_BY edge — collect every
        # BoundaryUse for this intent in one query, then index by the
        # Event id it references.
        bu_rows = self.ctx.memory.g.query(
            "MATCH (b:BoundaryUse)-[:RECORDED_BY]->(e:Event) "
            "MATCH (b)-[:SERVES]->(i:Intent) "
            "WHERE i.id = $iid RETURN b, e",
            {"iid": intent_id})
        bu_by_event: dict[str, dict] = {}
        for r in bu_rows:
            eid = str(r["e"]["properties"].get("id", ""))
            bu_by_event[eid] = r["b"]["properties"]
        out: list[dict] = []
        prev_id = ""
        for p in events:
            eid = str(p.get("id", ""))
            bu = bu_by_event.get(eid, {})
            out.append({
                "event_id":       eid,
                "prior_event_id": prev_id,
                "name":           p.get("name", ""),
                "tool":           p.get("tool", ""),
                "session":        p.get("session", ""),
                "summary":        p.get("summary", ""),
                "target":         bu.get("target", ""),
                "verb_shadow":    bu.get("verb_shadow", ""),
            })
            prev_id = eid
        return {
            "intent_id": intent_id,
            "events":    out,
            "count":     len(out),
        }

    # ════════════════════════════════════════════════════════════════════════
    # Spec 150 Slice 1 — dogfood amendment classifier (close Goal 6).
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def parse_amendment(self, scope: str = "", since: str = "",
                         limit: int = 20, use_llm: bool = True,
                         prefer_delegate: bool = False,
                         host_completion: dict | None = None) -> dict:
        """Classify recent Reflections into amendment proposals.

        Slice 1 shipped the keyword classifier (the documented fallback
        path). Slice 2 (this) swaps in Spec 147 AnthropicDriver
        structured-output classification — same ProposalPayload shape,
        sharper recall — wrapped through Spec 279's ``complete_or_delegate``
        so the no-key host (Claude Code) can run inference itself
        instead of degrading to keywords.

        Three paths (resume wins):

        1. ``host_completion`` supplied — the host already ran inference
           after a prior delegation; parse the result into proposals.
        2. ``use_llm=True`` AND an AnthropicDriver is wired AND capable:
           structured-output ``complete()`` call.
        3. ``use_llm=True`` AND ``prefer_delegate=True`` AND driver backend
           is ``"none"`` → return a ``llm_delegate`` envelope so the host
           (Claude Code) can run inference and re-call (Spec 279). When
           ``prefer_delegate=False`` (default), backend ``"none"`` silently
           degrades to keyword — backwards-compat default so tests +
           non-host callers don't have to handle the envelope.
        4. else / ``use_llm=False`` / no driver — keyword classifier
           fallback (Slice 1 path).

        Inputs: scope (substring filter on plan_slug), since (reserved
                bi-temporal cursor), limit (caps proposals; default 20),
                use_llm (default True; set False to force keyword path),
                host_completion (Spec 279 resume envelope from Claude
                Code — ``{text, parsed?}`` where ``parsed`` is the
                ProposalPayload list).
        Returns: ``{proposals: [ProposalPayload], classifier: str,
                    kind?: "llm_delegate", request?: HostLLMRequest dict}``.
        chain_next: ``dogfood.apply_amendment(payload, dry_run=True)``.
        """
        rows = self.ctx.memory.g.query(
            "MATCH (r:Reflection) WHERE r.scope = $scope RETURN r",
            {"scope": "observation"})
        reflections = [r["r"]["properties"] for r in rows]
        if scope:
            reflections = [r for r in reflections
                           if scope in (r.get("plan_slug") or "")]

        # ── LLM path (Slice 2) ────────────────────────────────────────
        if use_llm and reflections:
            llm_result = self._llm_classify(
                reflections, limit, host_completion, prefer_delegate)
            if llm_result is not None:
                return llm_result

        # ── Keyword fallback (Slice 1 path) ───────────────────────────
        proposals: list[dict] = []
        for refl in reflections:
            tag = _classify_reflection(refl.get("text") or "")
            if tag["op"] is None:
                continue
            spec_id = _spec_id_from_slug(refl.get("plan_slug") or "")
            if not spec_id:
                continue
            proposals.append({
                "spec_id":      spec_id,
                "section":      tag["section"],
                "op":           tag["op"],
                "before":       "",
                "after":        (refl.get("text") or "").strip(),
                "rationale":    (
                    f"Classifier promoted this Reflection based on a strong-"
                    f"intent keyword (`{tag['matched']}`). Source observation "
                    f"text: {(refl.get('text') or '')[:200]}"),
                "source_reflections": [refl.get("id") or ""],
                "confidence":   tag["confidence"],
            })
            if len(proposals) >= limit:
                break
        return {"proposals": proposals, "classifier": "keyword"}

    def _llm_classify(self, reflections: list[dict], limit: int,
                       host_completion: dict | None,
                       prefer_delegate: bool) -> dict | None:
        """Slice 2 LLM classification via `complete_or_delegate`. Returns:

        - dict with `{proposals, classifier: "llm"}` on driver-capable
          path or `{proposals, classifier: "host"}` on host resume.
        - dict with `{proposals: [], classifier: "llm-delegate",
          kind: "llm_delegate", request: …}` when ``prefer_delegate`` is
          True AND the driver backend is "none" — Spec 279 envelope so
          Claude Code runs inference.
        - None when the LLM path can't run AND the keyword fallback
          should take over (no driver wired AND no host_completion;
          OR driver backend "none" AND `prefer_delegate=False`;
          OR a driver failure that we recover from gracefully).
        """
        # Resolve the anthropic driver (None when not wired).
        driver = None
        try:
            reg = getattr(self.ctx, "drivers", None)
            if reg is not None and reg.has("anthropic"):
                driver = reg.get("anthropic")
        except Exception:
            driver = None
        # No driver AND no resume → keyword fallback.
        if driver is None and host_completion is None:
            return None
        # Driver present but not capable AND not opting into delegation
        # AND no resume → silent keyword degrade (spec contract).
        if (driver is not None and host_completion is None
                and not prefer_delegate
                and driver.backend() == "none"):
            return None

        from agency._host_llm import (
            complete_or_delegate, HostLLMRequest, HostDelegateError,
        )
        # Driver may be None when we have a host_completion to resume —
        # complete_or_delegate's resume branch ignores the driver.
        if driver is None:
            class _NoDriver:
                def backend(self) -> str:
                    return "none"
            driver = _NoDriver()

        messages = _build_classifier_messages(reflections)
        reflections_by_id = {r.get("id") or "": r for r in reflections}
        try:
            result = complete_or_delegate(
                driver,
                messages=messages,
                system=_CLASSIFIER_SYSTEM,
                output_schema=_PROPOSAL_LIST_SCHEMA,
                host_completion=host_completion,
            )
        except HostDelegateError:
            raise                                                  # bubble up
        except Exception:
            return None                                            # graceful degrade

        if isinstance(result, HostLLMRequest):
            return {
                "proposals":  [],
                "classifier": "llm-delegate",
                "kind":       result.kind,
                "request":    result.to_dict(),
            }
        parsed = result.parsed
        if parsed is None and result.text:
            try:
                parsed = json.loads(result.text)
            except (ValueError, TypeError):
                parsed = None
        proposals = _parse_llm_proposals(parsed, reflections_by_id, limit)
        classifier = ("host" if result.stop_reason == "host_provided"
                      else "llm")
        return {"proposals": proposals, "classifier": classifier}

    @verb(role="effect")
    def apply_amendment(self, payload: dict, dry_run: bool = True,
                         confirm_token: str = "") -> dict:
        """Render a ProposalPayload as a unified diff; provenance Artefact.

        v1 always renders the diff and writes an
        `Artefact(kind="amendment-proposal")` with PRODUCES_FROM edges
        to every cited Reflection so a reviewer can trace any amendment
        back to its source observations (the provenance moat invariant).

        Inputs: payload (dict — ProposalPayload schema; see Plan/150),
                dry_run (bool — default True; False requires
                  ``confirm_token`` to match the payload id-hash),
                confirm_token (str — opt-in live-write gate).
        Returns: ``{diff, artefact_id, written_path?}``.
        Failure modes: ``AMENDMENT_BAD_SPEC`` (no such spec dir),
                       ``AMENDMENT_NO_SOURCE`` (citations empty),
                       ``AMENDMENT_VAGUE`` (rationale < 40 chars),
                       ``AMENDMENT_UNCONFIRMED`` (live write requested,
                       confirm_token does not match the payload id-hash).
        """
        # Hard-coded constants are tunable budgets (rule 8):
        _RATIONALE_FLOOR = 40   # documented in Plan/150 §"Done When"
        sources = payload.get("source_reflections") or []
        if not sources:
            raise RuntimeError("amendment_no_source: "
                               "payload.source_reflections is empty — every "
                               "amendment must trace to ≥ 1 Reflection")
        if len(payload.get("rationale", "")) < _RATIONALE_FLOOR:
            raise RuntimeError(
                f"amendment_vague: rationale below the "
                f"{_RATIONALE_FLOOR}-char floor "
                f"(got {len(payload.get('rationale', ''))})")
        spec_id = payload.get("spec_id", "")
        spec_path = _resolve_spec_path(spec_id)
        if spec_path is None:
            raise RuntimeError(f"amendment_bad_spec: no spec dir for "
                               f"spec_id={spec_id!r}")
        # Live-write requires confirm_token matching the payload id-hash.
        payload_hash = _payload_hash(payload)
        if not dry_run and confirm_token != payload_hash:
            raise RuntimeError(
                f"amendment_unconfirmed: confirm_token mismatch; expected "
                f"id-hash={payload_hash!r} for this proposal")
        # Render the diff (dry-run path is the same; only the final write
        # branch differs by `dry_run`).
        diff = _render_unified_diff(spec_path,
                                    before=payload.get("before") or "",
                                    after=payload.get("after") or "",
                                    spec_id=spec_id)
        # Record the provenance Artefact + PRODUCES_FROM edges.
        art_id = self.ctx.record("Artefact", {
            "kind": "amendment-proposal",
            "spec_id": spec_id,
            "op": payload.get("op", ""),
            "payload_hash": payload_hash,
        })
        self.ctx.link(art_id, self.ctx.intent_id, "SERVES")
        for rid in sources:
            self.ctx.link(art_id, rid, "PRODUCES_FROM")
        result: dict = {"diff": diff, "artefact_id": art_id,
                        "payload_hash": payload_hash}
        # Live write is Slice 2; v1 records the Artefact + returns the diff.
        return result
