"""novel.preflight — the pre-flight composite (Spec 145 + Spec 255).

The KP's daily-driver: TWO concentric pre-scene checklists (§9.M briefing-
level + §12 alter-level) collapsed into ONE read-only readiness audit across
the whole 137–144 stack. Pre-flight audits, it never authors — the cleanest
answer to Spec 142's cascading-walk question. The editorial gates run it
first; a critical pre-flight finding short-circuits the editorial pass.

Spec 255 — the verdict structure DERIVES from the registered audit phases:
any method (anywhere in the composed capability's MRO) decorated with
``@preflight_phase(...)`` auto-appears in the report with no edits here.
Each phase is timed; the report carries ``total_duration_ms``,
``audit_verb_set_hash`` and ``generated_at``. Preflight is GRAPH-ONLY by
doctrine — no driver is ever resolved. Recurring warnings with the same
``(phase, category)`` across run history mint a Spec-150 observation
Reflection (the amendment-classifier feed) exactly once per cluster.
"""
from __future__ import annotations

import hashlib
import json
import time

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

# Spec 255 — documented tunables (rule 8: budgets, not snapshots).
PREFLIGHT_BUDGET_MS = 200      # total wall-clock budget; overrun = PREFLIGHT_SLOW warning
RECURRENCE_N = 3               # same (phase, category) this many times → amendment feed

_phase_counter = [0]


def preflight_phase(phase_id: str, label: str = "",
                    source_labels: tuple = ()):
    """Mark a method as a registered preflight audit phase (Spec 255).

    ``phase_id`` keys the verdicts dict; ``label`` is the human blocker
    phase string (defaults to the id with hyphens); ``source_labels`` are
    the graph node labels the audit bites on — ``preflight_readiness``
    reports a phase wired when every label has ≥1 node for the novel.
    The decorated method takes ``(self, scene, chapter_id, novel_id)`` and
    returns ``{"verdict": {..., passed: bool}, "findings": [{severity:
    "blocker"|"warning", category, reason, advice}]}``.
    """
    def deco(fn):
        _phase_counter[0] += 1
        fn._preflight_phase = phase_id
        fn._preflight_label = label or phase_id.replace("_", "-")
        fn._preflight_sources = tuple(source_labels)
        fn._preflight_order = _phase_counter[0]
        return fn
    return deco


class PreflightMixin:
    """Preflight cluster — the composite readiness verdict."""

    # ── Spec 255: the phase registry (derived, never hand-listed) ────────

    def _registered_audit_verbs(self) -> list:
        """Every ``@preflight_phase`` method reachable on this capability,
        in declaration order — the SOLE source of the verdicts structure."""
        phases = []
        for name in dir(type(self)):
            fn = getattr(type(self), name, None)
            if getattr(fn, "_preflight_phase", None):
                phases.append(fn)
        return sorted(phases, key=lambda f: f._preflight_order)

    # ── the five Spec-145 audits, now registered phases ──────────────────

    @preflight_phase("briefing_ready", source_labels=("ModeBlock",))
    def _audit_briefing_ready(self, scene, chapter_id, novel_id) -> dict:
        """Spec 141 — the chapter briefing checklist must be clean."""
        b = self.briefing_checklist(chapter_id)
        missing = b.data.get("missing", []) if b.ok else ["checklist failed"]
        advice = ("novel.render_chapter_briefing after resolving the "
                  "missing items")
        return {"verdict": {"passed": not missing, "missing": missing,
                            "advice": advice},
                "findings": [{"severity": "blocker",
                              "category": "missing_item",
                              "reason": m, "advice": advice}
                             for m in missing]}

    @preflight_phase("canon_clean")
    def _audit_canon_clean(self, scene, chapter_id, novel_id) -> dict:
        """Spec 137 — no open [L] gaps; unmarked nodes are warnings."""
        c = self.canon_audit(novel_id)
        cd = c.data if c.ok else {"counts": {}, "gaps": [], "unmarked": []}
        open_gaps = len(cd.get("gaps", []))
        unmarked = len(cd.get("unmarked", []))
        advice = ("consult novel.lock_index; set_canon_status per "
                  "gap/unmarked node")
        findings = []
        if open_gaps:
            findings.append({"severity": "blocker", "category": "open_gap",
                             "reason": f"{open_gaps} [L] gap(s) unresolved",
                             "advice": advice})
        if unmarked:
            findings.append({"severity": "warning", "category": "unmarked",
                             "reason": f"{unmarked} node(s) unmarked",
                             "advice": advice})
        return {"verdict": {"passed": open_gaps == 0,
                            "open_gaps": open_gaps, "unmarked": unmarked,
                            "advice": advice},
                "findings": findings}

    @preflight_phase("reveal_clear", source_labels=("RevealRule",))
    def _audit_reveal_clear(self, scene, chapter_id, novel_id) -> dict:
        """Spec 139 — veil intact, no premature reveals for this scene."""
        v = self.check_veil(novel_id)
        veil_ok = bool(v.ok and v.data.get("passed", True))
        premature: list[str] = []
        for rule in self.ctx.find("RevealRule"):
            if rule.get("novel") != novel_id:
                continue
            res = self.check_reveal_timing(scene["id"],
                                           rule.get("fact", ""))
            if res.ok and not res.data.get("ok", True):
                premature.append(rule.get("fact", ""))
        findings = []
        if not veil_ok:
            findings.append({"severity": "blocker",
                             "category": "veil_breach",
                             "reason": "multiplicity-veil breached",
                             "advice": "re-channel the leak (kp.channel.*)"})
        findings.extend({"severity": "blocker",
                         "category": "premature_reveal",
                         "reason": f"premature reveal: {f}",
                         "advice": "move the reveal later or adjust the rule"}
                        for f in premature)
        return {"verdict": {"passed": veil_ok and not premature,
                            "premature_facts": premature,
                            "veil_ok": veil_ok},
                "findings": findings}

    @preflight_phase("r_rules_clean", label="r-rules-dry-run",
                     source_labels=("ProjectRule",))
    def _audit_r_rules(self, scene, chapter_id, novel_id) -> dict:
        """Spec 140 — project R-rules dry-run over the last-known body."""
        r = self.run_project_rules(scene["id"])
        counts = {"critical": 0, "medium": 0, "low": 0}
        findings = []
        for f in (r.data.get("findings", []) if r.ok else []):
            sev = f.get("severity", "low")
            counts[sev] = counts.get(sev, 0) + 1
            findings.append({
                "severity": "blocker" if sev == "critical" else "warning",
                "category": f"rule:{f.get('rule_id', '?')}",
                "reason": f"{f.get('rule_id')}: {f.get('message')}",
                "advice": "strike/rewrite (critical) or reviewer-check"})
        return {"verdict": {"passed": counts["critical"] == 0, **counts},
                "findings": findings}

    @preflight_phase("voice_ready", source_labels=("VoiceProfile",))
    def _audit_voice_ready(self, scene, chapter_id, novel_id) -> dict:
        """Spec 138/144 — fronting alter voiced, recognition clean."""
        alter_id = scene.get("pov_character_id", "")
        alter = self.ctx.recall(alter_id) if alter_id else None
        voiced = bool(alter and (alter.get("voice_profile_id")
                                 or self._voice_profile(alter_id)))
        taboo_count = len([t for t in
                           str((alter or {}).get("taboo_rules") or "")
                           .split(",") if t.strip()])
        rec = self.check_alter_recognition(scene["id"])
        rec_ok = bool(rec.ok and rec.data.get("passed", True))
        findings = []
        if not alter:
            findings.append({"severity": "blocker", "category": "no_alter",
                             "reason": "no fronting alter on the scene",
                             "advice": "set pov_character_id"})
        elif not voiced:
            findings.append({"severity": "blocker", "category": "unvoiced",
                             "reason": "fronting alter has no bound voice",
                             "advice": "novel.assign_voice_to_alter"})
        if not rec_ok:
            findings.append({"severity": "blocker",
                             "category": "recognition",
                             "reason": "alter-recognition violations in "
                                       "the draft stub",
                             "advice": "novel.check_alter_recognition "
                                       "lists the spans"})
        if alter and taboo_count == 0:
            findings.append({"severity": "warning", "category": "no_taboo",
                             "reason": "alter has no taboo rules",
                             "advice": "author the anti-cliché negatives"})
        return {"verdict": {"passed": bool(alter) and voiced and rec_ok,
                            "alter_id": alter_id,
                            "taboo_count": taboo_count,
                            "recognition_ok": rec_ok},
                "findings": findings}

    # ── the composite ─────────────────────────────────────────────────────

    @verb(role="act")
    def preflight_report(self, scene_id: str, budget_ms: int = 0,
                         recurrence_n: int = 0,
                         debug: bool = False) -> ToolResult:
        """The pre-scene readiness audit (act) — every REGISTERED audit phase
        run read-only over the 137–144 stack, one composite ``{ready,
        blockers, warnings}``, and a recorded ``pre-flight`` Artefact.
        Nothing is authored or mutated; NO driver is ever resolved
        (graph-only doctrine). Spec 255: the verdicts dict derives from the
        ``@preflight_phase`` registry — a new audit auto-appears; each phase
        is timed; a phase that raises marks its verdict ``status="fail"``
        with the exception text while the others continue; recurring
        warnings (same phase+category ≥ N across run history) mint ONE
        Spec-150 observation Reflection per cluster.

        Inputs: scene_id; budget_ms (0 → PREFLIGHT_BUDGET_MS; overrun emits
                a PREFLIGHT_SLOW warning, never truncates); recurrence_n
                (0 → RECURRENCE_N); debug (assert derivation parity at
                runtime).
        Returns: ``{scene_id, chapter_id, ready, verdicts (per-phase:
                 legacy fields + status + findings + duration_ms),
                 blockers, warnings, audit_verbs, audit_verb_set_hash,
                 total_duration_ms, generated_at, proposals_minted,
                 artefact_id}``.
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
        budget = budget_ms or PREFLIGHT_BUDGET_MS
        n_recur = recurrence_n or RECURRENCE_N

        phases = self._registered_audit_verbs()
        verdicts: dict = {}
        blockers: list[dict] = []
        warnings: list[dict] = []
        t_total = time.perf_counter()
        for fn in phases:
            pid = fn._preflight_phase
            label = fn._preflight_label
            t0 = time.perf_counter()
            try:
                res = fn(self, scene, chapter_id, novel_id)
            except Exception as exc:      # audit fails, the others continue
                res = {"verdict": {"passed": False},
                       "findings": [{"severity": "blocker",
                                     "category": "audit_exception",
                                     "reason": f"{type(exc).__name__}: {exc}",
                                     "advice": "fix the audit verb"}]}
            dur = int((time.perf_counter() - t0) * 1000)
            findings = res.get("findings", [])
            has_block = any(f["severity"] == "blocker" for f in findings)
            has_warn = any(f["severity"] == "warning" for f in findings)
            status = ("fail" if has_block
                      else "warn" if has_warn else "pass")
            verdicts[pid] = {**res.get("verdict", {}), "status": status,
                             "findings": findings, "duration_ms": dur}
            for f in findings:
                row = {"phase": label, "reason": f["reason"],
                       "advice": f["advice"], "category": f["category"]}
                (blockers if f["severity"] == "blocker"
                 else warnings).append(row)
        total_ms = int((time.perf_counter() - t_total) * 1000)
        if total_ms > budget:
            warnings.append({"phase": "preflight",
                             "category": "slow",
                             "code": Codes.PREFLIGHT_SLOW,
                             "reason": f"total {total_ms}ms exceeds the "
                                       f"{budget}ms budget",
                             "advice": "profile the slowest phase "
                                       "(duration_ms per verdict)"})
        audit_verbs = [fn._preflight_phase for fn in phases]
        if debug:
            assert set(verdicts) == set(audit_verbs), \
                "derivation parity broken: verdicts != registered phases"
        set_hash = hashlib.sha256(
            ",".join(sorted(audit_verbs)).encode()).hexdigest()[:16]

        ready = not blockers
        index_tokens = sorted({f'{r["phase"]}|{r["category"]}'
                               for r in blockers + warnings})
        aid = self.ctx.record("Artefact", {
            "kind": "pre-flight", "scene_id": scene_id, "novel": novel_id,
            "ready": ready, "findings_index": json.dumps(index_tokens)})
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")

        proposals = self._mint_recurrence_reflections(novel_id, n_recur)
        return ToolResult.success(data={
            "scene_id": scene_id, "chapter_id": chapter_id, "ready": ready,
            "verdicts": verdicts,
            "blockers": blockers, "warnings": warnings,
            "audit_verbs": audit_verbs,
            "audit_verb_set_hash": set_hash,
            "total_duration_ms": total_ms,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "proposals_minted": proposals,
            "artefact_id": aid})

    def _mint_recurrence_reflections(self, novel_id: str, n: int) -> int:
        """Spec 255 × Spec 150 — a ``(phase, category)`` recurring ≥ n times
        across this novel's pre-flight run history becomes ONE observation
        Reflection (the amendment-classifier feed). Idempotent: a cluster
        already reflected is never re-minted."""
        counts: dict[str, int] = {}
        for a in self.ctx.find("Artefact"):
            if a.get("kind") != "pre-flight" or a.get("novel") != novel_id:
                continue
            try:
                tokens = json.loads(a.get("findings_index") or "[]")
            except ValueError:
                tokens = []
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
        already = {r.get("cluster") for r in self.ctx.find("Reflection")
                   if r.get("kind") == "preflight-recurrence"
                   and r.get("novel") == novel_id}
        minted = 0
        for token, cnt in sorted(counts.items()):
            if cnt < n or token in already:
                continue
            rid = self.ctx.record("Reflection", {
                "scope": "observation", "kind": "preflight-recurrence",
                "novel": novel_id, "cluster": token,
                "text": f"pre-flight finding {token!r} recurred {cnt}x "
                        f"(threshold {n}) across novel {novel_id} — "
                        f"consider a canon Lock or rule refinement "
                        f"(Spec 247/140)"})
            self.ctx.link(rid, self.ctx.intent_id, "SERVES")
            self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
            minted += 1
        return minted

    @verb(role="transform")
    def preflight_readiness(self, novel_id: str) -> ToolResult:
        """Preflight readiness for a novel (transform) — per registered audit
        phase, is its graph substrate present (Spec 255 × Spec 170)? A phase
        with no declared source labels is always wired; readiness =
        wired / total.

        Inputs: novel_id.
        Returns: ``{phases: [{phase, wired, missing_labels}], wired, total,
                 readiness}``.
        chain_next: seed the missing substrate (e.g. ``set_reveal_rule``,
                    ``register_project_rule``), then ``preflight_report``.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"novel_id={novel_id!r} not found")
        rows = []
        for fn in self._registered_audit_verbs():
            # a node without a `novel` prop is scoped by other means
            # (e.g. VoiceProfile per character) and counts for any novel.
            missing = [lbl for lbl in fn._preflight_sources
                       if not any(x.get("novel", novel_id) == novel_id
                                  for x in self.ctx.find(lbl))]
            rows.append({"phase": fn._preflight_phase,
                         "wired": not missing,
                         "missing_labels": missing})
        wired = sum(1 for r in rows if r["wired"])
        return ToolResult.success(data={
            "phases": rows, "wired": wired, "total": len(rows),
            "readiness": round(wired / len(rows), 3) if rows else 1.0})
