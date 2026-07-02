"""novel.plural — plural-character system, the dissociative-system model (Spec 138).

The KP protagonist is not one person but a SYSTEM of alters under a clinical
TSDP architecture: ANP/EP/special/mirror categories, trauma layers, a
phobia-driven inter-alter conflict matrix, per-alter voice binding (Spec 134),
the "recognized, never labeled" prose discipline (incl. the Akt-I veil), and
the no-fusion resolution invariant — the canonical end-state is a plural
"Wir", never a merged single self.
"""
from __future__ import annotations

import re

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

ALTER_CATEGORY = {"anp", "ep", "special", "mirror"}
TRAUMA_LAYER = {"layer-1", "layer-2", "cross-layer"}
PHOBIA_VECTOR = {"anp-ep", "anp-anp", "ep-ep", "mirror"}
PHOBIA_INTENSITY = {"max", "phobic-avoidance", "friction", "ambivalent"}

#: R-4 — max micro-cues per bridge scene before it over-signals the switch.
MICRO_CUE_CAP = 3

#: Alter-labeling patterns forbidden in prose REGARDLESS of chapter.
_HEADER_PATTERNS = (
    re.compile(r"\[\w+\]:?\s"),                 # "[Nyx]: …"
    re.compile(r"(?m)^\w+ spricht:"),           # "Lex spricht: …"
)


class PluralMixin:
    """Plural cluster — system roster, conflict matrix, recognition, no-fusion."""

    def _alters(self, system_id: str) -> list[dict]:
        return self.ctx.neighbors(system_id, "ALTER_OF", direction="in")

    @verb(role="effect")
    def create_character_system(self, novel_id: str, name: str,
                                model: str = "TSDP") -> ToolResult:
        """Mint the host ``CharacterSystem`` (effect).

        Inputs: novel_id, name (e.g. "Kael"), model (TSDP | OSDD | authored —
                documents the clinical frame).
        Returns: ``{system_id, novel_id, name, model}``.
        chain_next: ``novel.add_alter`` per system member.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        sid = self.ctx.record("CharacterSystem", {
            "novel": novel_id, "name": name, "model": model})
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "system_id": sid, "novel_id": novel_id, "name": name,
            "model": model})

    @verb(role="effect")
    def add_alter(self, system_id: str, name: str, category: str,
                  layer: str, function: str = "",
                  taboo_rules: str = "") -> ToolResult:
        """Add an alter to the system (effect). Enum-validates category +
        layer; duplicate names in one system are rejected.

        Inputs: system_id, name, category (anp|ep|special|mirror), layer
                (layer-1|layer-2|cross-layer), function (freeform — Fight /
                Freeze / Caregiver / …), taboo_rules (csv anti-cliché rules;
                read as HARD violations by Spec 134 check_pov_voice).
        Returns: ``{alter_id, system_id, name, category, layer, function}``.
        chain_next: ``novel.record_alter_conflict`` for the matrix;
                    ``novel.assign_voice_to_alter`` for the voice.
        """
        if category not in ALTER_CATEGORY:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"category={category!r} not in {sorted(ALTER_CATEGORY)}")
        if layer not in TRAUMA_LAYER:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"layer={layer!r} not in {sorted(TRAUMA_LAYER)}")
        if self.ctx.recall(system_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"system {system_id!r} not found")
        if any(a.get("name") == name for a in self._alters(system_id)):
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"alter name {name!r} already in system {system_id!r}")
        aid = self.ctx.record("Alter", {
            "system_id": system_id, "name": name, "category": category,
            "layer": layer, "function": function,
            "taboo_rules": taboo_rules})
        self.ctx.link(aid, system_id, "ALTER_OF")
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "alter_id": aid, "system_id": system_id, "name": name,
            "category": category, "layer": layer, "function": function})

    @verb(role="effect")
    def record_alter_conflict(self, alter_a: str, alter_b: str, vector: str,
                              intensity: str,
                              rationale: str = "") -> ToolResult:
        """Mint the ``PHOBIA_OF`` conflict-matrix edge a→b (effect). Symmetric
        phobia = call twice.

        Inputs: alter_a, alter_b (distinct), vector (anp-ep|anp-anp|ep-ep|
                mirror), intensity (max|phobic-avoidance|friction|ambivalent),
                rationale (freeform why).
        Returns: ``{a, b, vector, intensity}``.
        chain_next: ``novel.conflict_matrix_report(system_id)``.
        """
        if vector not in PHOBIA_VECTOR:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"vector={vector!r} not in {sorted(PHOBIA_VECTOR)}")
        if intensity not in PHOBIA_INTENSITY:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"intensity={intensity!r} not in {sorted(PHOBIA_INTENSITY)}")
        if alter_a == alter_b:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT, "an alter has no phobia of itself")
        for aid in (alter_a, alter_b):
            if self.ctx.recall(aid) is None:
                return ToolResult.failure(
                    Codes.NOT_FOUND, f"alter {aid!r} not found")
        self.ctx.link(alter_a, alter_b, "PHOBIA_OF",
                      {"vector": vector, "intensity": intensity,
                       "rationale": rationale})
        # Memory exposes no edge-prop reader, so the matrix CELL lives as its
        # own node (the edge stays for graph traversal — declared ⇒ traversed).
        cid = self.ctx.record("AlterConflict", {
            "a": alter_a, "b": alter_b, "vector": vector,
            "intensity": intensity, "rationale": rationale})
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "a": alter_a, "b": alter_b, "vector": vector,
            "intensity": intensity})

    @verb(role="transform")
    def conflict_matrix_report(self, system_id: str) -> ToolResult:
        """Render the full conflict matrix (transform): all typed phobia
        cells, counts per vector, and the max-intensity pairs that must never
        co-front a scene without a voice-collision warning.

        Inputs: system_id.
        Returns: ``{alters, cells, max_pairs, by_vector}``.
        chain_next: consult ``max_pairs`` before staging a co-front scene.
        """
        if self.ctx.recall(system_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"system {system_id!r} not found")
        alters = self._alters(system_id)
        alter_ids = {a["id"] for a in alters}
        cells: list[dict] = []
        max_pairs: list[tuple] = []
        by_vector = {v: 0 for v in sorted(PHOBIA_VECTOR)}
        for c in self.ctx.find("AlterConflict"):
            if c.get("a") not in alter_ids or c.get("b") not in alter_ids:
                continue
            vector = c.get("vector", "")
            intensity = c.get("intensity", "")
            cells.append({"from": c["a"], "to": c["b"], "vector": vector,
                          "intensity": intensity,
                          "rationale": c.get("rationale", "")})
            if vector in by_vector:
                by_vector[vector] += 1
            if intensity == "max":
                max_pairs.append((c["a"], c["b"]))
        return ToolResult.success(data={
            "alters": [{"id": a["id"], "name": a.get("name", ""),
                        "category": a.get("category", ""),
                        "layer": a.get("layer", "")} for a in alters],
            "cells": cells, "max_pairs": max_pairs, "by_vector": by_vector})

    @verb(role="effect")
    def assign_voice_to_alter(self, alter_id: str,
                              voice_profile_id: str) -> ToolResult:
        """Bind a Spec 134 ``VoiceProfile`` to an alter (effect). One voice
        per alter — rebind replaces.

        Inputs: alter_id, voice_profile_id.
        Returns: ``{alter_id, voice_profile_id, replaced_voice}``.
        chain_next: ``novel.switching_log`` infers fronting from the bound
                    voices.
        """
        if self.ctx.recall(alter_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"alter {alter_id!r} not found")
        if self.ctx.recall(voice_profile_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"profile {voice_profile_id!r} not found")
        alter = self.ctx.recall(alter_id)
        replaced = alter.get("voice_profile_id", "")
        # Keep-both: the property carries the CURRENT binding; prior
        # VOICED_BY edges stay as history (nothing is overwritten).
        self.ctx.memory.update(alter_id,
                               {"voice_profile_id": voice_profile_id})
        self.ctx.link(alter_id, voice_profile_id, "VOICED_BY")
        return ToolResult.success(data={
            "alter_id": alter_id, "voice_profile_id": voice_profile_id,
            "replaced_voice": replaced})

    @verb(role="transform")
    def check_alter_recognition(self, scene_id: str, veil_chapter: int = 13,
                                veil_terms: str = "DID,Alter,Fragment,ANP,"
                                                  "EP,TSDP") -> ToolResult:
        """The "recognized, never labeled" discipline (transform): alters are
        identified by syntax + somatik + lexicon, never by headers or labels;
        clinical veil terms are forbidden before the reveal chapter.

        Inputs: scene_id, veil_chapter (Akt-I veil boundary; default 13),
                veil_terms (csv of clinical terms under the veil).
        Returns: ``{passed, violations: [{kind, pattern, reason}],
                 checked_chapter, veil_active}``.
        chain_next: rewrite flagged spans; re-run.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        body = scene.get("body", "")
        chapter = self.ctx.recall(scene.get("chapter", "")) or {}
        number = int(chapter.get("number", 0))
        violations: list[dict] = []
        for pat in _HEADER_PATTERNS:
            for m in pat.finditer(body):
                violations.append({
                    "kind": "header", "pattern": m.group(0).strip(),
                    "reason": "alters are recognized by voice, never "
                              "labeled in prose"})
        veil_active = number < veil_chapter
        if veil_active:
            words = {w.strip() for w in veil_terms.split(",") if w.strip()}
            for term in sorted(words):
                if re.search(rf"\b{re.escape(term)}\b", body):
                    violations.append({
                        "kind": "veil", "pattern": term,
                        "reason": f"clinical term {term!r} veiled before "
                                  f"chapter {veil_chapter}"})
        return ToolResult.success(data={
            "passed": not violations, "violations": violations,
            "checked_chapter": number, "veil_active": veil_active})

    @verb(role="transform")
    def switching_log(self, system_id: str, novel_id: str) -> ToolResult:
        """Infer per scene which alter fronts (transform) — matched from the
        bound voice signatures against the scene body — plus the R-4
        micro-cue count (max 3 per bridge).

        Inputs: system_id, novel_id.
        Returns: ``{scenes: [{scene_id, chapter, inferred_alter, confidence,
                 micro_cue_count, exceeds_cue_cap}], summary}``.
        chain_next: revise over-cued scenes; ``novel.check_alter_recognition``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        voiced = [(a, a.get("voice_profile_id", ""))
                  for a in self._alters(system_id)
                  if a.get("voice_profile_id")]
        chapters = {c["id"]: c for c in self.ctx.neighbors(novel_id,
                                                           "CHAPTER_OF")}
        rows: list[dict] = []
        ambiguous = 0
        for s in self.ctx.find("Scene"):
            if s.get("chapter") not in chapters or not s.get("body"):
                continue
            body = s["body"]
            scored: list[tuple] = []
            cue_count = 0
            for alter, pid in voiced:
                res = self.score_voice_match(alter["id"], body) \
                    if self._voice_profile(alter["id"]) else None
                profile = self.ctx.recall(pid) or {}
                phrases = [p.strip().lower() for p in
                           str(profile.get("signature_phrases") or
                               "").split(",") if p.strip()]
                cue_count += sum(1 for p in phrases if p in body.lower())
                if res is not None and res.ok:
                    scored.append((res.data["score"], alter["id"]))
            scored.sort(reverse=True)
            inferred, confidence = "", 0
            if scored:
                inferred = scored[0][1]
                confidence = scored[0][0] - (scored[1][0] if len(scored) > 1
                                             else 0)
                if len(scored) > 1 and confidence < 5:
                    ambiguous += 1
                    inferred = ""
            rows.append({
                "scene_id": s["id"],
                "chapter": int(chapters[s["chapter"]].get("number", 0)),
                "inferred_alter": inferred, "confidence": confidence,
                "micro_cue_count": cue_count,
                "exceeds_cue_cap": cue_count > MICRO_CUE_CAP})
        return ToolResult.success(data={
            "scenes": rows,
            "summary": {"total_scenes": len(rows),
                        "scenes_with_inference": sum(1 for r in rows
                                                     if r["inferred_alter"]),
                        "ambiguous": ambiguous}})

    @verb(role="transform")
    def validate_no_fusion(self, system_id: str) -> ToolResult:
        """The resolution invariant (transform): no alter may be marked
        fused/eliminated — the canonical end-state is functional multiplicity,
        a plural "Wir", never a merged single self.

        Inputs: system_id.
        Returns: ``{passed, violations: [{alter_id, name, status}]}``.
        chain_next: unmark the alter or revise the resolution.
        """
        if self.ctx.recall(system_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"system {system_id!r} not found")
        violations = [{"alter_id": a["id"], "name": a.get("name", ""),
                       "status": a.get("status", "")}
                      for a in self._alters(system_id)
                      if a.get("status") in ("fused", "eliminated")]
        return ToolResult.success(data={
            "passed": not violations, "violations": violations})
