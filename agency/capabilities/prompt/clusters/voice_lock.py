"""prompt.voice_lock — the voice-locked drafting prompt (Spec 144).

The KP Sprach-DNA discipline as a single composer: one call per scene emits a
brief so tightly bound to an alter's voice that a one-shot LLM call drafts in
that voice. The taboo block is NON-truncatable (truncating it defeats the
purpose — the budget is generous instead; truncation drops §EXAMPLES first,
then §SIGNATURE, never §TABOO). The co-front guard refuses to compose a brief
that lets two max-phobia alters share a frontstage — the scene the discipline
forbids is never assembled. ``voice_drift_audit`` closes the loop defensively.
"""
from __future__ import annotations

import hashlib
import re

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

from ._base import _approx_tokens

#: Voice-locked briefs get a raised cap (spec §Lint) — the lock block is bulky.
VOICE_LOCK_TOKEN_CAP = 3000


def _csv(value) -> list[str]:
    return [w.strip() for w in str(value or "").split(",") if w.strip()]


class VoiceLockMixin:
    """Voice-lock cluster — compose, exemplars, drift audit (Spec 144)."""

    def _profile_for(self, alter_id: str) -> dict | None:
        return next((p for p in self.ctx.find("VoiceProfile")
                     if p.get("character") == alter_id), None)

    def _system_alters(self, alter: dict) -> list[dict]:
        sys_id = alter.get("system_id", "")
        return [a for a in self.ctx.find("Alter")
                if a.get("system_id") == sys_id] if sys_id else []

    @verb(role="act")
    def compose_voice_locked_brief(self, scene_id: str, alter_id: str,
                                   allow_max_pair: bool = False,
                                   max_tokens: int = VOICE_LOCK_TOKEN_CAP
                                   ) -> ToolResult:
        """Compose the §-structured voice-locked drafting brief for one scene
        and one fronting alter (act). Refuses when the scene's cast pairs the
        alter with a max-intensity phobia partner (unless ``allow_max_pair``)
        — the forbidden scene is never assembled.

        Inputs: scene_id, alter_id, allow_max_pair (explicit override),
                max_tokens (cap 3000; §EXAMPLES truncate first, then
                §SIGNATURE, never §TABOO).
        Returns: ``{brief, artefact_id, sections}`` or ``{refused: True,
                 reason, pair, advice}``.
        chain_next: run the draft, then ``prompt.voice_drift_audit(scene_id)``.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        alter = self.ctx.recall(alter_id)
        if alter is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"alter {alter_id!r} not found")
        # co-front guard — cast = the scene's declared cast ∪ the front
        cast = set(_csv(scene.get("cast"))) | {alter_id}
        if len(cast) >= 2 and not allow_max_pair:
            for c in self.ctx.find("AlterConflict"):
                if c.get("intensity") != "max":
                    continue
                pair = {c.get("a"), c.get("b")}
                if pair <= cast:
                    return ToolResult.success(data={
                        "refused": True, "reason": "max-pair-cofront",
                        "pair": sorted(pair),
                        "advice": "split into two scenes or pass "
                                  "allow_max_pair=True"})
        profile = self._profile_for(alter_id) or {}
        exemplars = self.exemplar_pool(alter_id).data.get("examples", [])
        scene_brief = ""
        try:
            sb = self.assemble_scene_brief(scene_id)
            if sb.ok:
                scene_brief = str(sb.data.get("brief", "")
                                  or sb.data.get("content", ""))
        except Exception:                     # noqa: BLE001 — brief optional
            scene_brief = ""

        head = (f"§VOICE-LOCK: {alter.get('name', alter_id)}  "
                f"(category={alter.get('category', '—')}  "
                f"layer={alter.get('layer', '—')}  "
                f"function={alter.get('function', '—')})")
        taboo = ", ".join(_csv(alter.get("taboo_rules"))
                          + _csv(profile.get("taboo_words"))) or "—"
        sections = {
            "voice-lock": head,
            "syntax": f"§SYNTAX: {profile.get('sentence_shape') or '—'}",
            "lexicon-preferred":
                f"§LEXICON-PREFERRED: "
                f"{profile.get('vocabulary_preferred') or '—'}",
            "lexicon-forbidden":
                f"§LEXICON-FORBIDDEN: "
                f"{profile.get('vocabulary_forbidden') or '—'}",
            "somatik": f"§SOMATIK: {alter.get('somatik_tags') or '—'}",
            "taboo": f"§TABOO (HARD): {taboo}",
            "signature": f"§SIGNATURE: "
                         f"{profile.get('signature_phrases') or '—'}",
            "examples": "§EXAMPLES:\n" + "\n".join(
                f"  {i}) {ex}" for i, ex in enumerate(exemplars, 1)),
            "scene-brief": f"§SCENE BRIEF: {scene_brief or '—'}",
            "instruction":
                f"§INSTRUCTION: Draft the scene in "
                f"{alter.get('name', alter_id)}'s voice. Honor every §TABOO "
                f"absolutely. Match the §SYNTAX rhythm. Use "
                f"§LEXICON-PREFERRED; avoid §LEXICON-FORBIDDEN.",
        }
        order = ["voice-lock", "syntax", "lexicon-preferred",
                 "lexicon-forbidden", "somatik", "taboo", "signature",
                 "examples", "scene-brief", "instruction"]
        # truncate §EXAMPLES first, then §SIGNATURE — NEVER §TABOO
        def _total() -> int:
            return sum(_approx_tokens(sections[k]) for k in order
                       if k in sections)
        for drop in ("examples", "signature"):
            if _total() > max_tokens and drop in sections:
                del sections[drop]
        brief = "\n".join(sections[k] for k in order if k in sections)
        aid = self.ctx.record("Artefact", {
            "kind": "voice-locked-brief", "scene_id": scene_id,
            "alter_id": alter_id})
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return ToolResult.success(data={
            "brief": brief, "artefact_id": aid,
            "sections": [k for k in order if k in sections],
            "tokens": _approx_tokens(brief)})

    @verb(role="transform")
    def exemplar_pool(self, alter_id: str, n: int = 3) -> ToolResult:
        """N example sentences from the alter's Sprach-DNA pool (transform),
        rotated deterministically by intent-id hash so successive drafts see
        varied exemplars — never the same three every call.

        Inputs: alter_id, n (default 3).
        Returns: ``{examples: [str], pool_size}``.
        chain_next: ``prompt.compose_voice_locked_brief`` embeds them.
        """
        profile = self._profile_for(alter_id) or {}
        pool = [e.strip() for e in
                str(profile.get("example_sentences") or "").split(";")
                if e.strip()]
        if not pool:
            return ToolResult.success(data={"examples": [], "pool_size": 0})
        seed = int(hashlib.sha256(
            f"{self.ctx.intent_id}:{alter_id}".encode()).hexdigest()[:8], 16)
        start = seed % len(pool)
        rotated = pool[start:] + pool[:start]
        return ToolResult.success(data={
            "examples": rotated[:n], "pool_size": len(pool)})

    @verb(role="act")
    def voice_drift_audit(self, scene_id: str) -> ToolResult:
        """Post-draft defensive audit (act): scan the drafted body against
        the assigned alter's profile — forbidden lexicon, taboo violations,
        signature presence, a register score — and flag
        ``leaked-other-alter`` when the body matches a DIFFERENT bound
        alter's voice better. Findings persist as a Reflection.

        Inputs: scene_id.
        Returns: ``{passed, forbidden_lexicon_hits, taboo_violations,
                 signature_phrase_presence, register_match_score, verdict}``.
        chain_next: redraft on ``drifted``/``leaked-other-alter``.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        alter_id = scene.get("pov_character_id", "")
        alter = self.ctx.recall(alter_id) if alter_id else None
        if alter is None:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"scene {scene_id!r} has no fronting alter")
        body = scene.get("body", "")
        low = body.lower()
        profile = self._profile_for(alter_id) or {}

        forbidden = [w for w in _csv(profile.get("vocabulary_forbidden"))
                     if re.search(rf"\b{re.escape(w.lower())}\b", low)]
        taboo_violations = []
        for rule in _csv(alter.get("taboo_rules")) + \
                _csv(profile.get("taboo_words")):
            m = re.search(re.escape(rule.lower()), low)
            if m:
                taboo_violations.append({
                    "rule": rule, "span": [m.start(), m.end()],
                    "snippet": body[max(0, m.start() - 20):m.end() + 20]})
        signatures = _csv(profile.get("signature_phrases"))
        sig_present = any(s.lower() in low for s in signatures) \
            if signatures else False

        def _score(aid: str) -> int:
            res, _ = self.ctx.registry.invoke(
                self.ctx.memory, self.ctx.intent_id, "novel",
                "score_voice_match", agent_id=self.ctx.agent_id,
                character_id=aid, body=body)
            return int(res["score"]) if res else -1

        own = _score(alter_id)
        leaked_to = ""
        for other in self._system_alters(alter):
            if other["id"] == alter_id:
                continue
            if self._profile_for(other["id"]) is None:
                continue
            if _score(other["id"]) > own + 10:
                leaked_to = other["id"]
                break
        register = max(0.0, min(1.0, (own if own >= 0 else 0) / 100))
        verdict = ("leaked-other-alter" if leaked_to
                   else "in-voice" if not forbidden and not taboo_violations
                   and register >= 0.7
                   else "drifted")
        rid = self.ctx.record("Reflection", {
            "scope": "technical", "kind": "voice-drift-audit",
            "text": f"scene {scene_id}: verdict={verdict}, "
                    f"forbidden={forbidden}, taboo={len(taboo_violations)}"})
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return ToolResult.success(data={
            "passed": verdict == "in-voice",
            "forbidden_lexicon_hits": forbidden,
            "taboo_violations": taboo_violations,
            "signature_phrase_presence": sig_present,
            "register_match_score": round(register, 2),
            "verdict": verdict})
