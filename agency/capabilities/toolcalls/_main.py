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

from ... import _config
from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# Spec 336 S4 — export config (Spec 334 registry).
_config.register_config_section("toolcalls", [
    _config.ConfigKey("export_top_n", "AGENCY_TOOLCALLS_TOP_N", 20,
                      "how many top tool-call shapes the Stop-hook export lists"),
    _config.ConfigKey("suggest_via_llm", "AGENCY_TOOLCALLS_LLM", False,
                      "also propose new specs via the LLM driver (heuristic always runs)"),
])


class ToolcallsCapability(CapabilityBase):
    name = "toolcalls"
    home = "memory"   # high-volume capture, distilled into durable Memory artefacts
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"ToolcallExport": ["session", "top_n", "suggestions"]},
    )

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
    def export(self, top_n: int = 0, apply: bool = False, prune: bool = False) -> dict:
        """Distil the session's tool calls into a durable export — the top calls +
        responses + new-spec SUGGESTIONS (the dogfooding fold-back, Goal 6).

        Heuristic suggestions always run (a repeated command → a `shell.define`
        template; a repeated read → an index; a high-volume call → a filter); an
        LLM pass adds richer ideas when `toolcalls.suggest_via_llm` is set. With
        `apply` the FULL markdown report is written to
        `.agency/sessions/<session>-toolcalls.md` (never truncated) and a
        `ToolcallExport` artefact is recorded, so the signal survives a `prune`.

        Inputs: top_n (int — 0 uses the `toolcalls.export_top_n` config default),
                apply (bool — write the report + record the artefact),
                prune (bool — clear the store after a successful export).
        Returns: ``{top, suggestions, report, written, export_id}``.
        chain_next: open a spec for a strong suggestion; `toolcalls.prune` when done.
        """
        from . import _export
        n = int(top_n) if int(top_n) > 0 else int(_config.config_get("toolcalls.export_top_n"))
        return _export.run(self.ctx, top_n=n, apply=apply, prune=prune)

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
