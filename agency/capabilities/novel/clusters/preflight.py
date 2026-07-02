"""novel.preflight — the pre-flight composite (Spec 145).

The KP's daily-driver: TWO concentric pre-scene checklists (§9.M briefing-
level + §12 alter-level) collapsed into ONE read-only readiness audit across
the whole 137–144 stack. Pre-flight audits, it never authors — the cleanest
answer to Spec 142's cascading-walk question. The editorial gates run it
first; a critical pre-flight finding short-circuits the editorial pass.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import Codes, ToolResult


class PreflightMixin:
    """Preflight cluster — the composite readiness verdict."""

    @verb(role="act")
    def preflight_report(self, scene_id: str) -> ToolResult:
        """The pre-scene readiness audit (act) — five read-only verdicts over
        the 137–144 stack, one composite ``{ready, blockers, warnings}``, and
        a recorded ``pre-flight`` Artefact. Nothing is authored or mutated.

        Inputs: scene_id.
        Returns: ``{scene_id, chapter_id, ready, verdicts, blockers,
                 warnings, artefact_id}`` (spec §Composite verdict shape).
        chain_next: resolve the blockers, re-run; then draft
                    (``prompt.compose_voice_locked_brief``).
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        chapter_id = scene.get("chapter", "")
        chapter = self.ctx.recall(chapter_id) or {}
        novel_id = chapter.get("novel", "")
        number = int(chapter.get("number", 0))
        blockers: list[dict] = []
        warnings: list[dict] = []

        # 1. briefing-ready (Spec 141)
        b = self.briefing_checklist(chapter_id)
        b_missing = b.data.get("missing", []) if b.ok else ["checklist failed"]
        briefing_ready = {"passed": not b_missing, "missing": b_missing,
                          "advice": "novel.render_chapter_briefing after "
                                    "resolving the missing items"}
        for m in b_missing:
            blockers.append({"phase": "briefing-ready", "reason": m,
                             "advice": briefing_ready["advice"]})

        # 2. canon-clean (Spec 137)
        c = self.canon_audit(novel_id)
        cd = c.data if c.ok else {"counts": {}, "gaps": [], "unmarked": []}
        open_gaps = len(cd.get("gaps", []))
        unmarked = len(cd.get("unmarked", []))
        canon_clean = {"passed": open_gaps == 0, "open_gaps": open_gaps,
                       "unmarked": unmarked,
                       "advice": "consult novel.lock_index; set_canon_status "
                                 "per gap/unmarked node"}
        if open_gaps:
            blockers.append({"phase": "canon-clean",
                             "reason": f"{open_gaps} [L] gap(s) unresolved",
                             "advice": canon_clean["advice"]})
        if unmarked:
            warnings.append({"phase": "canon-clean",
                             "reason": f"{unmarked} node(s) unmarked",
                             "advice": canon_clean["advice"]})

        # 3. reveal-clear (Spec 139)
        v = self.check_veil(novel_id)
        veil_ok = bool(v.ok and v.data.get("passed", True))
        premature: list[str] = []
        for rule in self.ctx.find("RevealRule"):
            if rule.get("novel") != novel_id:
                continue
            res = self.check_reveal_timing(scene_id, rule.get("fact", ""))
            if res.ok and not res.data.get("ok", True):
                premature.append(rule.get("fact", ""))
        reveal_clear = {"passed": veil_ok and not premature,
                        "premature_facts": premature, "veil_ok": veil_ok}
        if not veil_ok:
            blockers.append({"phase": "reveal-clear",
                             "reason": "multiplicity-veil breached",
                             "advice": "re-channel the leak (kp.channel.*)"})
        for f in premature:
            blockers.append({"phase": "reveal-clear",
                             "reason": f"premature reveal: {f}",
                             "advice": "move the reveal later or adjust "
                                       "the rule"})

        # 4. r-rules-dry-run (Spec 140) — over the last-known draft body
        r = self.run_project_rules(scene_id)
        counts = {"critical": 0, "medium": 0, "low": 0}
        for f in (r.data.get("findings", []) if r.ok else []):
            sev = f.get("severity", "low")
            counts[sev] = counts.get(sev, 0) + 1
            row = {"phase": "r-rules-dry-run",
                   "reason": f"{f.get('rule_id')}: {f.get('message')}",
                   "advice": "strike/rewrite (critical) or reviewer-check"}
            (blockers if sev == "critical" else warnings).append(row)
        r_rules_clean = {"passed": counts["critical"] == 0, **counts}

        # 5. voice-ready (Spec 138/144) — the hard gate
        alter_id = scene.get("pov_character_id", "")
        alter = self.ctx.recall(alter_id) if alter_id else None
        voiced = bool(alter and (alter.get("voice_profile_id")
                                 or self._voice_profile(alter_id)))
        taboo_count = len([t for t in
                           str((alter or {}).get("taboo_rules") or "")
                           .split(",") if t.strip()])
        rec = self.check_alter_recognition(scene_id)
        rec_ok = bool(rec.ok and rec.data.get("passed", True))
        voice_ready = {"passed": bool(alter) and voiced and rec_ok,
                       "alter_id": alter_id, "taboo_count": taboo_count,
                       "recognition_ok": rec_ok}
        if not alter:
            blockers.append({"phase": "voice-ready",
                             "reason": "no fronting alter on the scene",
                             "advice": "set pov_character_id"})
        elif not voiced:
            blockers.append({"phase": "voice-ready",
                             "reason": "fronting alter has no bound voice",
                             "advice": "novel.assign_voice_to_alter"})
        if not rec_ok:
            blockers.append({"phase": "voice-ready",
                             "reason": "alter-recognition violations in the "
                                       "draft stub",
                             "advice": "novel.check_alter_recognition lists "
                                       "the spans"})
        if alter and taboo_count == 0:
            warnings.append({"phase": "voice-ready",
                             "reason": "alter has no taboo rules",
                             "advice": "author the anti-cliché negatives"})

        ready = not blockers
        aid = self.ctx.record("Artefact", {
            "kind": "pre-flight", "scene_id": scene_id, "ready": ready})
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return ToolResult.success(data={
            "scene_id": scene_id, "chapter_id": chapter_id, "ready": ready,
            "verdicts": {"briefing_ready": briefing_ready,
                         "canon_clean": canon_clean,
                         "reveal_clear": reveal_clear,
                         "r_rules_clean": r_rules_clean,
                         "voice_ready": voice_ready},
            "blockers": blockers, "warnings": warnings,
            "artefact_id": aid})
