"""novel.codex — Codex cluster — Novelcrafter-parity codex entries (Spec 132).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes
from .._main import (
    CODEX_ENTRY_KIND,
)


class CodexMixin:
    """Codex cluster — Novelcrafter-parity codex entries (Spec 132)."""

    @verb(role="effect", param_enums={"kind": CODEX_ENTRY_KIND})
    def create_codex_entry(self, novel_id: str, slug: str, name: str,
                            kind: str, body: str,
                            triggers: str = "") -> ToolResult:
        """Mint a CodexEntry + CODEX_OF edge to the Novel (effect).

        Inputs: novel_id, slug, name, kind (one of CODEX_ENTRY_KIND),
                body (agent-facing description), triggers (comma-separated
                trigger phrases; defaults to ``name, slug`` if empty).
        Returns: ``{entry_id, slug, name, kind}``.
        chain_next: ``novel.match_codex_entries`` to verify auto-injection.
        """
        if kind not in CODEX_ENTRY_KIND:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"kind={kind!r} not in {sorted(CODEX_ENTRY_KIND)}")
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"novel_id={novel_id!r} not found")
        if not triggers:
            triggers = f"{name}, {slug}"
        cid = self.ctx.record("CodexEntry", {
            "novel": novel_id, "slug": slug, "name": name,
            "kind": kind, "body": body, "triggers": triggers,
        })
        self.ctx.link(cid, novel_id, "CODEX_OF")
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "entry_id": cid, "slug": slug, "name": name, "kind": kind,
        })

    @verb(role="transform")
    def list_codex_entries(self, novel_id: str,
                            kind: str = "") -> ToolResult:
        """List CodexEntries for a novel, optionally filtered by kind (transform).

        Inputs: novel_id, kind (optional — one of CODEX_ENTRY_KIND).
        Returns: ``{entries: [{entry_id, slug, name, kind, body}], count}``.
        chain_next: ``novel.match_codex_entries`` to scan a body.
        """
        if kind and kind not in CODEX_ENTRY_KIND:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"kind={kind!r} not in {sorted(CODEX_ENTRY_KIND)}")
        entries = [
            {"entry_id": e.get("id"), "slug": e.get("slug"),
             "name": e.get("name"), "kind": e.get("kind"),
             "body": e.get("body")}
            for e in self.ctx.find("CodexEntry")
            if e.get("novel") == novel_id
            and (not kind or e.get("kind") == kind)
            and e.get("archived") != "yes"
        ]
        return ToolResult.success(data={
            "entries": entries, "count": len(entries),
        })

    @verb(role="transform")
    def match_codex_entries(self, novel_id: str,
                              text: str) -> ToolResult:
        """Scan ``text`` for any registered codex trigger and return matches (transform).

        Case-insensitive whole-substring match (the simpler half of the
        Novelcrafter behaviour; word-boundary matching is a Slice 2
        refinement). Archived entries are skipped.

        Inputs: novel_id, text (the body to scan — chapter outline, scene
                draft, etc.).
        Returns: ``{matches: [{entry_id, slug, name, kind, body,
                  trigger_hit}]}``.
        chain_next: feed matches to ``prompt.assemble_scene_brief``'s
                    world_rules section.
        """
        text_l = text.lower()
        matches: list[dict] = []
        for e in self.ctx.find("CodexEntry"):
            if e.get("novel") != novel_id:
                continue
            if e.get("archived") == "yes":
                continue
            triggers = [t.strip() for t in (e.get("triggers") or "").split(",")
                        if t.strip()]
            for trigger in triggers:
                if trigger.lower() in text_l:
                    matches.append({
                        "entry_id": e.get("id"),
                        "slug": e.get("slug"),
                        "name": e.get("name"),
                        "kind": e.get("kind"),
                        "body": e.get("body"),
                        "trigger_hit": trigger,
                    })
                    break   # one match per entry — don't duplicate
        return ToolResult.success(data={"matches": matches})

    @verb(role="effect")
    def update_codex_entry(self, entry_id: str,
                            body: str = "", triggers: str = "",
                            name: str = "") -> ToolResult:
        """Edit a CodexEntry's body / triggers / name (effect).

        Inputs: entry_id; any of body / triggers / name (empty = unchanged).
        Returns: ``{entry_id, fields_updated: [str]}``.
        chain_next: ``novel.list_codex_entries`` to verify.
        """
        node = self.ctx.recall(entry_id)
        if node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"entry_id={entry_id!r} not found")
        updates: dict = {}
        if body:
            updates["body"] = body
        if triggers:
            updates["triggers"] = triggers
        if name:
            updates["name"] = name
        if updates:
            self.ctx.memory.update(entry_id, updates)
        return ToolResult.success(data={
            "entry_id": entry_id,
            "fields_updated": sorted(updates.keys()),
        })

    @verb(role="effect")
    def archive_codex_entry(self, entry_id: str,
                              reason: str = "") -> ToolResult:
        """Flag a CodexEntry as archived (effect, soft-delete).

        Archived entries are skipped by ``match_codex_entries`` and
        ``list_codex_entries``. They remain in the graph for provenance.

        Inputs: entry_id, reason (optional — recorded in `archived_reason`).
        Returns: ``{entry_id, archived: True}``.
        chain_next: ``novel.list_codex_entries`` to verify the prune.
        """
        node = self.ctx.recall(entry_id)
        if node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"entry_id={entry_id!r} not found")
        self.ctx.memory.update(entry_id, {
            "archived": "yes",
            "archived_reason": reason or "",
        })
        return ToolResult.success(data={
            "entry_id": entry_id, "archived": True,
        })
