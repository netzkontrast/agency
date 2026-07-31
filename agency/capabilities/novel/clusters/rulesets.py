"""novel.rulesets — project rule-sets & motif discipline (Spec 140).

The KP runs a per-scene self-review checklist of author-authored R-rules
(R-1…R-N), each with a defect severity (critical = strike/rewrite; medium/low
= reviewer check). The engine ships FOUR decidable predicate kinds authors
compose WITHOUT code — mutual-exclusion (R-5 hot-polarity), per-scene-budget
(R-7 max 1 Genesis-echo), forbidden-verbatim (R-9), register-forbidden (R-8
AEGIS no metaphor/moral/affect/Ich). Judgement rules stay reviewer prompts.
Plus the motif echo-trail (max 1 per scene — stacking turns the novel into
allegory) and named foreshadowing anchors (plant → payoff).
"""
from __future__ import annotations

import json
import re

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

DEFECT_SEVERITY = {"critical", "medium", "low"}
PREDICATE_KIND = {"mutual-exclusion", "per-scene-budget",
                  "forbidden-verbatim", "register-forbidden"}

#: KP default: one motif echo per scene.
MOTIF_PER_SCENE_CAP = 1

_SEVERITY_ORDER = {"low": 0, "medium": 1, "critical": 2}


def _params_of(rule: dict) -> dict:
    raw = rule.get("params", "")
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}


def _terms_present(body: str, terms: list, ci: bool) -> list[str]:
    hay = body.lower() if ci else body
    out = []
    for t in terms or []:
        needle = str(t).lower() if ci else str(t)
        if needle and needle in hay:
            out.append(str(t))
    return out


class RulesetsMixin:
    """Rulesets cluster — author-authored R-rules, motifs, anchors."""

    # ── the four decidable predicates (pure over body + params) ────────────

    def _pred_mutual_exclusion(self, scene: dict, params: dict) -> str:
        ci = bool(params.get("case_insensitive", True))
        body = scene.get("body", "")
        hits_a = _terms_present(body, params.get("set_a", []), ci)
        hits_b = _terms_present(body, params.get("set_b", []), ci)
        if hits_a and hits_b:
            return (f"mutual-exclusion breached: {hits_a} co-occur "
                    f"with {hits_b}")
        return ""

    def _pred_per_scene_budget(self, scene: dict, params: dict) -> str:
        cap = int(params.get("cap", 1))
        kind = params.get("count_kind", "substring")
        body = scene.get("body", "")
        if kind == "motif-edge":
            count = len(self.ctx.neighbors(scene["id"], "ECHOES_IN",
                                           direction="in"))
        elif kind == "regex":
            count = len(re.findall(params.get("pattern", ""), body))
        else:
            count = sum(body.lower().count(str(t).lower())
                        for t in params.get("terms", []))
        if count > cap:
            return (f"per-scene budget exceeded: {count} × "
                    f"{params.get('tag', kind)} (cap {cap})")
        return ""

    def _pred_forbidden_verbatim(self, scene: dict, params: dict) -> str:
        if scene.get("id") in (params.get("exemptions") or []):
            return ""
        ci = bool(params.get("case_insensitive", False))
        hits = _terms_present(scene.get("body", ""),
                              params.get("phrases", []), ci)
        if hits:
            return f"forbidden verbatim phrase(s): {hits}"
        return ""

    def _pred_register_forbidden(self, scene: dict, params: dict) -> str:
        tag = params.get("speaker_tag", "")
        if not tag:
            return ""
        lines = [ln for ln in scene.get("body", "").splitlines()
                 if re.match(rf"\s*{re.escape(tag)}\s*[:—-]", ln)]
        class_terms = params.get("class_terms", {}) or {}
        violations = []
        for ln in lines:
            for cls in params.get("forbidden_classes", []) or []:
                # word-boundary match: "ich" must not fire inside "Abweichung"
                hits = [t for t in class_terms.get(cls, []) or []
                        if re.search(rf"\b{re.escape(str(t))}\b", ln,
                                     re.IGNORECASE)]
                if hits:
                    violations.append(f"{cls}: {hits}")
        if violations:
            return f"register breach in {tag!r} lines — " + "; ".join(
                sorted(set(violations)))
        return ""

    _PREDICATES = {
        "mutual-exclusion": "_pred_mutual_exclusion",
        "per-scene-budget": "_pred_per_scene_budget",
        "forbidden-verbatim": "_pred_forbidden_verbatim",
        "register-forbidden": "_pred_register_forbidden",
    }

    # ── rule registry ───────────────────────────────────────────────────────

    @verb(role="effect")
    def register_project_rule(self, novel_id: str, rule_id: str, name: str,
                              severity: str, predicate_kind: str,
                              params: dict | None = None,
                              rationale: str = "") -> ToolResult:
        """Author an R-rule (effect) — upsert keyed by (novel, rule_id).

        Inputs: novel_id, rule_id (stable handle, e.g. "R-5"), name,
                severity (critical|medium|low), predicate_kind
                (mutual-exclusion|per-scene-budget|forbidden-verbatim|
                register-forbidden), params (the predicate's config dict),
                rationale.
        Returns: ``{rule_node_id, rule_id, was_update}``.
        chain_next: ``novel.run_project_rules(scene_id)`` per scene.
        """
        if severity not in DEFECT_SEVERITY:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"severity={severity!r} not in {sorted(DEFECT_SEVERITY)}")
        if predicate_kind not in PREDICATE_KIND:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"predicate_kind={predicate_kind!r} not in "
                f"{sorted(PREDICATE_KIND)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        props = {"novel": novel_id, "rule_id": rule_id, "name": name,
                 "severity": severity, "predicate_kind": predicate_kind,
                 "params": json.dumps(params or {}, sort_keys=True),
                 "rationale": rationale}
        existing = next((r for r in self.ctx.find("ProjectRule")
                         if r.get("novel") == novel_id
                         and r.get("rule_id") == rule_id), None)
        if existing is not None:
            self.ctx.memory.update(existing["id"], props)
            return ToolResult.success(data={
                "rule_node_id": existing["id"], "rule_id": rule_id,
                "was_update": True})
        nid = self.ctx.record("ProjectRule", props)
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "rule_node_id": nid, "rule_id": rule_id, "was_update": False})

    @verb(role="transform")
    def list_project_rules(self, novel_id: str,
                           severity: str = "") -> ToolResult:
        """The rule registry (transform), optionally filtered by severity.

        Inputs: novel_id, severity (optional filter).
        Returns: ``{rules: [{rule_id, name, severity, predicate_kind,
                 rationale}], count}``.
        chain_next: ``novel.run_project_rules`` — the checklist executable.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        rules = [r for r in self.ctx.find("ProjectRule")
                 if r.get("novel") == novel_id
                 and (not severity or r.get("severity") == severity)]
        rules.sort(key=lambda r: r.get("rule_id", ""))
        return ToolResult.success(data={
            "rules": [{"rule_id": r.get("rule_id"), "name": r.get("name"),
                       "severity": r.get("severity"),
                       "predicate_kind": r.get("predicate_kind"),
                       "rationale": r.get("rationale", "")} for r in rules],
            "count": len(rules)})

    @verb(role="transform")
    def run_project_rules(self, scene_id: str) -> ToolResult:
        """Run EVERY registered R-rule over one scene (transform) — the §10.3
        per-scene self-review checklist made executable.

        Inputs: scene_id.
        Returns: ``{passed, findings: [{rule_id, severity, message}]}`` —
                 ``passed`` is False only on findings (any severity).
        chain_next: fix critical findings (strike/rewrite); medium/low go to
                    the reviewer.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = ch.get("novel", "")
        findings: list[dict] = []
        for rule in self.ctx.find("ProjectRule"):
            if rule.get("novel") != novel_id:
                continue
            pred = getattr(self,
                           self._PREDICATES[rule.get("predicate_kind", "")],
                           None)
            if pred is None:
                continue
            message = pred(dict(scene, id=scene_id), _params_of(rule))
            if message:
                findings.append({"rule_id": rule.get("rule_id"),
                                 "severity": rule.get("severity"),
                                 "message": message})
        findings.sort(key=lambda f: -_SEVERITY_ORDER.get(f["severity"], 0))
        return ToolResult.success(data={
            "passed": not findings, "findings": findings})

    @verb(role="transform")
    def project_rule_gate(self, novel_id: str,
                          block_at: str = "critical") -> ToolResult:
        """Composite manuscript gate (transform): fails iff any scene carries
        a finding AT or ABOVE ``block_at``; lower severities surface as
        warnings (§10.2 — critical strikes, medium/low reviewer-check).

        Inputs: novel_id, block_at (critical|medium|low).
        Returns: ``{passed, blocking: [{scene_id, rule_id, severity,
                 message}], warnings: [...]}``.
        chain_next: rewrite the blocking scenes; re-run.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        threshold = _SEVERITY_ORDER.get(block_at, 2)
        blocking: list[dict] = []
        warnings: list[dict] = []
        chapters = {c["id"] for c in self.ctx.neighbors(novel_id,
                                                        "CHAPTER_OF")}
        for s in self.ctx.find("Scene"):
            if s.get("chapter") not in chapters:
                continue
            res = self.run_project_rules(s["id"])
            if not res.ok:
                continue
            for f in res.data["findings"]:
                row = dict(f, scene_id=s["id"])
                if _SEVERITY_ORDER.get(f["severity"], 0) >= threshold:
                    blocking.append(row)
                else:
                    warnings.append(row)
        return ToolResult.success(data={
            "passed": not blocking, "blocking": blocking,
            "warnings": warnings})

    # ── motif discipline ────────────────────────────────────────────────────

    @verb(role="effect")
    def record_motif_echo(self, scene_id: str, motif_slug: str) -> ToolResult:
        """Log a motif echo in a scene (effect); mints the Motif on first
        sight (its ``first_event_chapter`` = this scene's chapter).

        Inputs: scene_id, motif_slug (e.g. rauschen|form|klick|phantom|
                resonanz — open set).
        Returns: ``{motif_id, scene_id, motif_slug}``.
        chain_next: ``novel.motif_echo_report(novel_id)`` for the cap audit.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = ch.get("novel", "")
        motif = next((m for m in self.ctx.find("Motif")
                      if m.get("novel") == novel_id
                      and m.get("slug") == motif_slug), None)
        if motif is None:
            mid = self.ctx.record("Motif", {
                "novel": novel_id, "slug": motif_slug,
                "first_event_chapter": int(ch.get("number", 0)),
                "per_scene_cap": MOTIF_PER_SCENE_CAP})
            self.ctx.link(mid, self.ctx.intent_id, "SERVES")
        else:
            mid = motif["id"]
        self.ctx.link(mid, scene_id, "ECHOES_IN")
        return ToolResult.success(data={
            "motif_id": mid, "scene_id": scene_id, "motif_slug": motif_slug})

    @verb(role="transform")
    def motif_echo_report(self, novel_id: str) -> ToolResult:
        """Per-scene echo counts + per-motif trail (transform); flags scenes
        over the cap (stacking = allegory).

        Inputs: novel_id.
        Returns: ``{over_cap: [{scene_id, count, cap}], trails:
                 {slug: [chapter, …]}}``.
        chain_next: thin the over-cap scenes to one echo.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = {c["id"]: int(c.get("number", 0))
                    for c in self.ctx.neighbors(novel_id, "CHAPTER_OF")}
        per_scene: dict[str, int] = {}
        trails: dict[str, list[int]] = {}
        for m in self.ctx.find("Motif"):
            if m.get("novel") != novel_id:
                continue
            cap = int(m.get("per_scene_cap") or MOTIF_PER_SCENE_CAP)
            trail: list[int] = []
            for s in self.ctx.neighbors(m["id"], "ECHOES_IN",
                                        direction="out"):
                per_scene[s["id"]] = per_scene.get(s["id"], 0) + 1
                trail.append(chapters.get(s.get("chapter", ""), 0))
            trails[m.get("slug", "")] = sorted(trail)
        over = [{"scene_id": sid, "count": n, "cap": MOTIF_PER_SCENE_CAP}
                for sid, n in sorted(per_scene.items())
                if n > MOTIF_PER_SCENE_CAP]
        return ToolResult.success(data={"over_cap": over, "trails": trails})

    # ── foreshadowing anchors ───────────────────────────────────────────────

    @verb(role="effect")
    def plant_anchor(self, scene_id: str, name: str) -> ToolResult:
        """Plant a named foreshadowing anchor in a scene (effect) — earliest
        plant kept; re-planting adds a PLANTS edge without moving the origin.

        Inputs: scene_id, name (e.g. "734", "Telefon-Stille").
        Returns: ``{anchor_id, name, planted_chapter}``.
        chain_next: ``novel.pay_off_anchor`` at the payoff scene;
                    ``novel.anchor_status_report`` for the audit.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = ch.get("novel", "")
        number = int(ch.get("number", 0))
        anchor = next((a for a in self.ctx.find("Anchor")
                       if a.get("novel") == novel_id
                       and a.get("name") == name), None)
        if anchor is None:
            aid = self.ctx.record("Anchor", {
                "novel": novel_id, "name": name,
                "planted_chapter": number, "payoff_chapter": 0})
            self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        else:
            aid = anchor["id"]
        self.ctx.link(aid, scene_id, "PLANTS")
        return ToolResult.success(data={
            "anchor_id": aid, "name": name,
            "planted_chapter": (anchor or {}).get("planted_chapter",
                                                  number)})

    @verb(role="effect")
    def pay_off_anchor(self, scene_id: str, name: str) -> ToolResult:
        """Record an anchor's payoff scene (effect).

        Inputs: scene_id, name.
        Returns: ``{anchor_id, name, payoff_chapter}``.
        chain_next: ``novel.anchor_status_report(novel_id)``.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = ch.get("novel", "")
        anchor = next((a for a in self.ctx.find("Anchor")
                       if a.get("novel") == novel_id
                       and a.get("name") == name), None)
        if anchor is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"anchor {name!r} was never planted in {novel_id!r}")
        number = int(ch.get("number", 0))
        self.ctx.memory.update(anchor["id"], {"payoff_chapter": number})
        self.ctx.link(anchor["id"], scene_id, "PAYS_OFF")
        return ToolResult.success(data={
            "anchor_id": anchor["id"], "name": name,
            "payoff_chapter": number})

    @verb(role="transform")
    def anchor_status_report(self, novel_id: str) -> ToolResult:
        """The Chekhov's-gun audit for NAMED anchors (transform): planted-
        but-unpaid anchors are the open foreshadowing debt.

        Inputs: novel_id.
        Returns: ``{anchors: [{name, planted_chapter, payoff_chapter,
                 open}], open_count}``.
        chain_next: pay off or strike the open anchors before publication.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        rows = []
        for a in self.ctx.find("Anchor"):
            if a.get("novel") != novel_id:
                continue
            payoff = int(a.get("payoff_chapter") or 0)
            rows.append({"name": a.get("name", ""),
                         "planted_chapter": int(a.get("planted_chapter")
                                                or 0),
                         "payoff_chapter": payoff, "open": payoff == 0})
        rows.sort(key=lambda r: r["planted_chapter"])
        return ToolResult.success(data={
            "anchors": rows,
            "open_count": sum(1 for r in rows if r["open"])})
