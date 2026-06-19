# agency-scaffold: v1
"""toolcalls — the ephemeral tool-call capture surface (Spec 336).

Every pre/post tool call (Bash/Read/Edit/…) is captured in FULL into a local,
gitignored `.agency/toolcalls.db` — OFF the durable provenance graph, so the graph
stays the moat (Intents/Invocations/Gates) while **no capture data is lost**
(Spec 336 S2). This capability is the clear, discoverable surface over that store:
inspect the top calls by frequency × cost, read recent calls in full, and export
the session's top calls + responses with new-spec suggestions — the dogfooding
fold-back loop for Goal 6, where lessons become specs, made automatic.

Use when: reviewing what a session actually did — which tool calls ran, how often,
how expensively — or distilling that capture into durable spec ideas before it is
pruned.
Triggers:
- "what did this session DO / which commands ran the most / what was expensive"
- end-of-session review of the top tool calls and responses
- pruning the ephemeral capture once it has been distilled
Red flags:
- Reaching into session.db or analyze.graph for tool-call stats → they live in the ephemeral toolcalls.db now, not the graph
- Truncating the captured payload → it is stored in FULL by policy via keep_full
"""
from __future__ import annotations

from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


class ToolcallsCapability(CapabilityBase):
    name = "toolcalls"
    home = "memory"   # high-volume capture, distilled into durable Memory artefacts
    ontology = OntologyExtension()

    @verb(role="act")
    def top(self, n: int = 20) -> dict:
        """The top captured tool-call shapes by frequency × payload cost (read-only).

        Identical (tool, input) calls are grouped — a command run 30× ranks above a
        one-off — so this surfaces the repeated/expensive work worth a capability
        or a filter.

        Inputs: n (int — how many shapes; default 20).
        Returns: ``{top: [{tool, shape, calls, bytes, sample}], total}``.
        chain_next: ``toolcalls.export`` to distil these into a durable report.
        """
        store = self.ctx.toolcalls
        if store is None:
            return {"top": [], "total": 0}
        return {"top": store.top_calls(n), "total": store.count()}

    @verb(role="act")
    def recent(self, limit: int = 20) -> dict:
        """The most recent captured tool calls, in FULL (read-only).

        Inputs: limit (int — max rows from the tail; default 20).
        Returns: ``{calls: [{id, ts, phase, tool, input_json, output_json,
                 filtered}], total}``.
        chain_next: ``toolcalls.top`` for the aggregate ranking.
        """
        store = self.ctx.toolcalls
        if store is None:
            return {"calls": [], "total": 0}
        rows = store.rows()
        return {"calls": rows[-max(1, int(limit)):], "total": len(rows)}

    @verb(role="act")
    def stats(self) -> dict:
        """Capture counts broken down by phase and tool (read-only).

        Inputs: (none).
        Returns: ``{total, by_phase: {pre, post}, by_tool: {Bash, Read, …}}``.
        chain_next: ``toolcalls.top`` for the ranked shapes.
        """
        store = self.ctx.toolcalls
        if store is None:
            return {"total": 0, "by_phase": {}, "by_tool": {}}
        by_phase: dict[str, int] = {}
        by_tool: dict[str, int] = {}
        rows = store.rows()
        for r in rows:
            by_phase[r["phase"]] = by_phase.get(r["phase"], 0) + 1
            if r["tool"]:
                by_tool[r["tool"]] = by_tool.get(r["tool"], 0) + 1
        return {"total": len(rows), "by_phase": by_phase, "by_tool": by_tool}

    @verb(role="effect")
    def prune(self) -> dict:
        """Clear the ephemeral capture store (after it has been distilled/exported).

        Inputs: (none).
        Returns: ``{pruned: <rows removed>}``.
        chain_next: terminal — the durable signal lives in the export artefact.
        """
        store = self.ctx.toolcalls
        if store is None:
            return {"pruned": 0}
        return {"pruned": store.prune()}
