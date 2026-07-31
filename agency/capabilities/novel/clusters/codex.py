"""novel.codex — Codex cluster — Novelcrafter-parity codex entries (Spec 132).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.

Spec 242 — ``match_codex_entries`` upgraded from plain substring to the
decidable/judged MatchResult partition: word-boundary regex matches are
``decidable`` (span-aligned, confidence None — the gate input); an optional
driver-backed fuzzy pass yields ``judged`` advisory matches (never gate
input). The legacy ``matches`` key survives, derived from decidable.
"""
from __future__ import annotations

import re

from agency.capability import verb
from agency.toolresult import ToolResult, Codes
from .._main import (
    CODEX_ENTRY_KIND,
)

# Spec 242 — a trigger prefixed "re:" is a RAW regex pattern (power users);
# anything else is escaped verbatim. A raw pattern that fails to compile is
# the reachable CODEX_ENTRY_INVALID path — the entry is named, others match.
_RAW_TRIGGER_PREFIX = "re:"

# Spec 242 — the driver name the fuzzy pass resolves on ``ctx.drivers``.
# Absent driver = graceful degrade (judged=[], fuzzy_status names the code).
CODEX_MATCH_DRIVER = "codex_match"


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
    def match_codex_entries(self, novel_id: str, text: str,
                              fuzzy: bool = False) -> ToolResult:
        """Scan ``text`` for codex triggers — word-boundary decidable + optional fuzzy judged (transform).

        Spec 242 MatchResult: ``decidable`` matches are case-insensitive
        WHOLE-WORD regex hits (``\\b…\\b`` — "raven" never matches inside
        "ravenous"), each with a span aligned to word boundaries in ``text``
        and ``confidence: None``. Only decidable matches feed continuity
        gates. With ``fuzzy=True`` a wired ``codex_match`` driver adds
        ``judged`` advisory matches (typos, partial mentions) with a float
        confidence + the driver's model id; no driver → graceful degrade
        (``judged=[]``, ``fuzzy_status`` names the code). A trigger prefixed
        ``re:`` is a raw regex; a malformed one lands the entry in
        ``invalid`` (CODEX_ENTRY_INVALID) while other entries still match.
        Archived entries are skipped. The legacy ``matches`` key remains —
        first decidable hit per entry in the Spec-132 shape.

        Inputs: novel_id, text (the body to scan), fuzzy (opt-in advisory
                pass; default False).
        Returns: ``{matches, decidable: [{entry_id, surface_form,
                  span: [start, end], kind: "whole_word", confidence: None,
                  slug, name}], judged: [... kind: "fuzzy", confidence,
                  model_id], total, invalid, fuzzy_status}`` with
                  ``total == len(decidable) + len(judged)``.
        chain_next: feed matches to ``prompt.assemble_scene_brief``'s
                    world_rules section; judged suggestions go to the
                    author, never to a gate.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                Codes.CODEX_NOT_FOUND, f"novel_id={novel_id!r} not found")
        entries = [e for e in self.ctx.find("CodexEntry")
                   if e.get("novel") == novel_id
                   and e.get("archived") != "yes"]
        decidable: list[dict] = []
        invalid: list[dict] = []
        legacy: list[dict] = []
        for e in entries:
            triggers = [t.strip() for t in
                        (e.get("triggers") or "").split(",") if t.strip()]
            first_hit: str | None = None
            for trigger in triggers:
                if trigger.startswith(_RAW_TRIGGER_PREFIX):
                    pattern = trigger[len(_RAW_TRIGGER_PREFIX):]
                else:
                    pattern = re.escape(trigger)
                try:
                    rx = re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)
                except re.error as exc:
                    invalid.append({
                        "entry_id": e.get("id"), "slug": e.get("slug"),
                        "code": Codes.CODEX_ENTRY_INVALID,
                        "trigger": trigger, "error": str(exc)})
                    continue
                for m in rx.finditer(text):
                    decidable.append({
                        "entry_id": e.get("id"),
                        "surface_form": m.group(0),
                        "span": [m.start(), m.end()],
                        "kind": "whole_word",
                        "confidence": None,
                        "slug": e.get("slug"),
                        "name": e.get("name"),
                    })
                    if first_hit is None:
                        first_hit = trigger
                        legacy.append({
                            "entry_id": e.get("id"),
                            "slug": e.get("slug"),
                            "name": e.get("name"),
                            "kind": e.get("kind"),
                            "body": e.get("body"),
                            "trigger_hit": trigger,
                        })
        judged: list[dict] = []
        fuzzy_status = "off"
        if fuzzy:
            reg = self.ctx.drivers
            driver = (reg.get(CODEX_MATCH_DRIVER)
                      if (reg is not None and reg.has(CODEX_MATCH_DRIVER))
                      else None)
            if driver is None:
                fuzzy_status = Codes.DRIVER_UNAVAILABLE
            else:
                fuzzy_status = "ok"
                suggestions = driver.fuzzy_match(text, [
                    {"entry_id": e.get("id"), "name": e.get("name"),
                     "triggers": e.get("triggers", "")} for e in entries])
                covered = {(d["entry_id"], tuple(d["span"]))
                           for d in decidable}
                for s in suggestions or []:
                    span = list(s.get("span") or (-1, -1))
                    if not (0 <= span[0] < span[1] <= len(text)):
                        invalid.append({
                            "entry_id": s.get("entry_id", ""),
                            "code": Codes.MATCH_INVALID,
                            "error": f"span {span} out of bounds for "
                                     f"len(text)={len(text)}"})
                        continue
                    if (s.get("entry_id"), tuple(span)) in covered:
                        continue          # decidable already owns this span
                    judged.append({
                        "entry_id": s.get("entry_id", ""),
                        "surface_form": text[span[0]:span[1]],
                        "span": span,
                        "kind": "fuzzy",
                        "confidence": float(s.get("confidence", 0.0)),
                        "model_id": s.get("model_id",
                                          getattr(driver, "model_id", "")),
                    })
        return ToolResult.success(data={
            "matches": legacy,
            "decidable": decidable,
            "judged": judged,
            "total": len(decidable) + len(judged),
            "invalid": invalid,
            "fuzzy_status": fuzzy_status,
        })

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
