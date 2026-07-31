"""novel.dual_storyform — dual-storyform architecture, post-Dramatica (Spec 136).

The Kohärenz Protokoll runs TWO simultaneous, complete storyforms in one work,
related by an involutive Klein-c inversion (V₄ = Z₂(class) × Z₂(dynamics)),
with structured Vortex transitions and per-scene hard/soft routing.
``StoryformSet`` groups the members (N-ary by design); the checks verify the
inversion symmetry, transition legality (no driver-flip WITHIN a storyform),
and the bridge-frequency curve. Single-storyform novels are untouched —
the set is opt-in.
"""
from __future__ import annotations

import json

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

STORYFORM_TRANSITION_KIND = {"operative", "ontological", "synthesis"}
SCENE_ROUTE_MODE = {"hard", "soft"}

#: The involutive dynamics pairs (each a Z₂ flip; order-insensitive).
_DYNAMICS_INVERSE = {
    "resolve": {"Steadfast", "Change"},
    "growth": {"Stop", "Start"},
    "approach": {"Be-er", "Do-er"},
    "style": {"Holistic", "Linear"},
    "driver": {"Decision", "Action"},
    "limit": {"Optionlock", "Timelock"},
    "outcome": {"Success", "Failure"},
    "judgment": {"Good", "Bad"},
}

#: The class Z₂: Universe↔Mind and Physics↔Psychology.
_CLASS_INVERSE = {"Mind": "Universe", "Universe": "Mind",
                  "Physics": "Psychology", "Psychology": "Physics"}

#: Bridge-share deviation beyond this flags a block (spec: 0.15).
BRIDGE_DEVIATION_TOLERANCE = 0.15


def _body_of(node: dict) -> dict:
    raw = node.get("body") or ""
    try:
        return json.loads(raw) if isinstance(raw, str) and raw else (
            raw if isinstance(raw, dict) else {})
    except (TypeError, ValueError):
        return {}


class DualStoryformMixin:
    """Dual-storyform cluster — set, inversion, transitions, routing."""

    def _set_members(self, set_id: str) -> list[dict]:
        return self.ctx.neighbors(set_id, "MEMBER_OF", direction="in")

    def _member_by_role(self, set_id: str, role: str) -> dict | None:
        return next((m for m in self._set_members(set_id)
                     if m.get("role") == role), None)

    @verb(role="effect")
    def create_storyform_set(self, novel_id: str, label: str,
                             count: int = 2) -> ToolResult:
        """Mint a ``StoryformSet`` grouping N simultaneous storyforms
        (effect). N-ary by design — the KP needs 2, the node doesn't care.

        Inputs: novel_id, label, count (default 2).
        Returns: ``{set_id, label, count}``.
        chain_next: ``novel.add_storyform_to_set`` per member storyform.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        sid = self.ctx.record("StoryformSet", {
            "novel": novel_id, "label": label, "count": count})
        self.ctx.link(sid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "set_id": sid, "label": label, "count": count})

    @verb(role="effect")
    def add_storyform_to_set(self, storyform_id: str, set_id: str,
                             role: str) -> ToolResult:
        """Mint ``MEMBER_OF`` + stamp ``Storyform.role`` (effect). A role
        collision with an existing member is rejected.

        Inputs: storyform_id, set_id, role (primary | secondary | …).
        Returns: ``{storyform_id, set_id, role, set_membership_count}``.
        chain_next: ``novel.check_klein_c_inversion(set_id)`` once both
                    members are in.
        """
        if self.ctx.recall(storyform_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"storyform {storyform_id!r} not found")
        if self.ctx.recall(set_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"set {set_id!r} not found")
        if self._member_by_role(set_id, role) is not None:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"role {role!r} already taken in set {set_id!r}")
        self.ctx.memory.update(storyform_id, {"role": role})
        self.ctx.link(storyform_id, set_id, "MEMBER_OF")
        return ToolResult.success(data={
            "storyform_id": storyform_id, "set_id": set_id, "role": role,
            "set_membership_count": len(self._set_members(set_id)),
        })

    @verb(role="transform")
    def check_klein_c_inversion(self, storyform_set_id: str) -> ToolResult:
        """Verify the involutive Klein-c symmetry between the set's primary
        and secondary storyforms (transform). Two independent Z₂ flips:
        the class-pair swap (MC and OS classes exchanged along
        Universe↔Mind / Physics↔Psychology) AND all eight dynamics inverse.

        Inputs: storyform_set_id.
        Returns: ``{passed, class_pair, dynamics, non_inverted}``.
        chain_next: ``novel.dual_storyform_coherence_check`` for the
                    composite verdict.
        """
        a = self._member_by_role(storyform_set_id, "primary")
        b = self._member_by_role(storyform_set_id, "secondary")
        if a is None or b is None:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                "klein-c needs a primary AND a secondary member")
        ab, bb = _body_of(a), _body_of(b)
        # Spec 246 — degenerate set: neither classes nor dynamics present on
        # both members means there is nothing to invert. Fail typed, never
        # crash.
        if not ((ab.get("classes") or ab.get("dynamics"))
                and (bb.get("classes") or bb.get("dynamics"))):
            return ToolResult.success(data={
                "passed": False, "class_pair": {"inverted": False},
                "dynamics": {}, "non_inverted": [],
                "flip_class": "broken", "flip_dynamics": "broken",
                "diagnostic": "insufficient_slots"})
        non_inverted: list[dict] = []

        a_mc = ab.get("classes", {}).get("mc", "")
        a_os = ab.get("classes", {}).get("os", "")
        b_mc = bb.get("classes", {}).get("mc", "")
        b_os = bb.get("classes", {}).get("os", "")
        class_ok = (_CLASS_INVERSE.get(a_mc) == b_mc
                    and _CLASS_INVERSE.get(a_os) == b_os)
        if not class_ok:
            non_inverted.append({"slot": "class-pair",
                                 "a_value": f"{a_mc}/{a_os}",
                                 "b_value": f"{b_mc}/{b_os}"})

        dynamics: dict[str, dict] = {}
        unknown: list[str] = []
        for slot, pair in _DYNAMICS_INVERSE.items():
            av = ab.get("dynamics", {}).get(slot, "")
            bv = bb.get("dynamics", {}).get(slot, "")
            for v in (av, bv):
                if v and v not in pair:
                    unknown.append(f"{slot}={v}")
            inverted = bool(av and bv and av != bv and {av, bv} == pair)
            dynamics[slot] = {"a": av, "b": bv, "inverted": inverted}
            if not inverted:
                non_inverted.append({"slot": slot, "a_value": av,
                                     "b_value": bv})
        # Spec 246 — the diagnostic names WHICH Z₂ generator broke, and the
        # two flips report independently (V₄ = Z₂(class) × Z₂(dynamics)).
        dyn_ok = all(d["inverted"] for d in dynamics.values())
        flip_class = "preserved" if class_ok else "broken"
        flip_dynamics = "preserved" if dyn_ok else "broken"
        if unknown:
            diagnostic = f"unknown_slot: {', '.join(sorted(unknown))}"
        elif class_ok and dyn_ok:
            diagnostic = ""
        else:
            broken_slots = [d["slot"] for d in non_inverted]
            gen = ("class" if not class_ok else "dynamics") \
                if class_ok != dyn_ok else "class+dynamics"
            diagnostic = (f"Z2 generator on {gen} violated: "
                          f"{', '.join(broken_slots)} not inverted")
        return ToolResult.success(data={
            "passed": class_ok and dyn_ok,
            "class_pair": {"a_mc": a_mc, "b_mc": b_mc, "a_os": a_os,
                           "b_os": b_os, "inverted": class_ok},
            "dynamics": dynamics,
            "non_inverted": non_inverted,
            "flip_class": flip_class,
            "flip_dynamics": flip_dynamics,
            "diagnostic": diagnostic,
        })

    @verb(role="effect")
    def record_storyform_transition(self, storyform_set_id: str,
                                    from_role: str, to_role: str,
                                    at_chapter: int, kind: str) -> ToolResult:
        """Record a Vortex — where one storyform overtakes another (effect).

        Inputs: storyform_set_id, from_role, to_role, at_chapter, kind
                (operative | ontological | synthesis).
        Returns: ``{transition_id, from_role, to_role, at_chapter, kind}``.
        chain_next: ``novel.check_driver_transition_legality(transition_id)``.
        """
        if kind not in STORYFORM_TRANSITION_KIND:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"kind={kind!r} not in {sorted(STORYFORM_TRANSITION_KIND)}")
        if self.ctx.recall(storyform_set_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"set {storyform_set_id!r} not found")
        tid = self.ctx.record("StoryformTransition", {
            "storyform_set_id": storyform_set_id, "from_role": from_role,
            "to_role": to_role, "at_chapter": at_chapter, "kind": kind})
        self.ctx.link(tid, storyform_set_id, "TRANSITIONS")
        self.ctx.link(tid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "transition_id": tid, "from_role": from_role, "to_role": to_role,
            "at_chapter": at_chapter, "kind": kind})

    @verb(role="transform")
    def check_driver_transition_legality(self,
                                         transition_id: str) -> ToolResult:
        """The KP driver rule (transform): a driver-flip WITHIN one storyform
        is illegal (Dramatica forbids it); only a storyform *transition*
        (e.g. B(Action)→A(Decision)) is legal.

        Inputs: transition_id.
        Returns: ``{passed, from_driver, to_driver, same_storyform,
                 verdict}``.
        chain_next: ``novel.dual_storyform_coherence_check``.
        """
        t = self.ctx.recall(transition_id)
        if t is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"transition {transition_id!r} not found")
        set_id = t.get("storyform_set_id", "")
        frm = self._member_by_role(set_id, t.get("from_role", ""))
        to = self._member_by_role(set_id, t.get("to_role", ""))
        same = t.get("from_role") == t.get("to_role")
        from_driver = _body_of(frm or {}).get("dynamics", {}).get("driver", "")
        to_driver = _body_of(to or {}).get("dynamics", {}).get("driver", "")
        return ToolResult.success(data={
            "passed": not same,
            "from_driver": from_driver, "to_driver": to_driver,
            "same_storyform": same,
            "verdict": ("illegal-within-storyform" if same
                        else "legal-transition"),
        })

    @verb(role="effect")
    def route_scene_storyform(self, scene_id: str, set_id: str,
                              primary_role: str, mode: str = "hard",
                              secondary_role: str = "") -> ToolResult:
        """Route a scene between the live storyforms (effect). ``hard`` =
        exactly one storyform owns the scene; ``soft`` = a bridge scene whose
        two readings are simultaneously true (two ``ROUTED_TO`` edges).

        Inputs: scene_id, set_id, primary_role, mode (hard | soft),
                secondary_role (required + distinct for soft).
        Returns: ``{scene_id, mode, routed_storyforms}``.
        chain_next: ``novel.bridge_frequency_report(novel_id)``.
        """
        if mode not in SCENE_ROUTE_MODE:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"mode={mode!r} not in {sorted(SCENE_ROUTE_MODE)}")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        primary = self._member_by_role(set_id, primary_role)
        if primary is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"no member with role {primary_role!r} in {set_id!r}")
        targets = [primary]
        if mode == "soft":
            if not secondary_role or secondary_role == primary_role:
                return ToolResult.failure(
                    Codes.INVALID_ARGUMENT,
                    "soft routing needs a distinct secondary_role")
            secondary = self._member_by_role(set_id, secondary_role)
            if secondary is None:
                return ToolResult.failure(
                    Codes.NOT_FOUND,
                    f"no member with role {secondary_role!r} in {set_id!r}")
            targets.append(secondary)
        for sf in targets:
            self.ctx.link(scene_id, sf["id"], "ROUTED_TO", {"mode": mode})
        self.ctx.memory.update(scene_id, {"route_mode": mode})
        return ToolResult.success(data={
            "scene_id": scene_id, "mode": mode,
            "routed_storyforms": [sf["id"] for sf in targets]})

    @verb(role="transform")
    def bridge_frequency_report(self, novel_id: str) -> ToolResult:
        """Per mode-block share of soft-routed (bridge) scenes (transform).
        Blocks come from Spec 141 ``ModeBlock`` nodes when present; without
        them each chapter is its own block. ``curve_intact`` verifies the
        documented monotone non-decreasing bridge curve; a block whose share
        deviates > 0.15 from its target is flagged.

        Inputs: novel_id.
        Returns: ``{blocks: [{label, from_chapter, to_chapter, soft_share,
                 target, deviation, verdict}], curve_intact}``.
        chain_next: adjust routing / mode-block targets, re-run.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(self.ctx.neighbors(novel_id, "CHAPTER_OF"),
                          key=lambda c: int(c.get("number", 0)))
        mode_blocks = [b for b in self.ctx.find("ModeBlock")
                       if b.get("novel") == novel_id]
        if mode_blocks:
            blocks = [{"label": b.get("label", ""),
                       "from_chapter": int(b.get("from_chapter", 0)),
                       "to_chapter": int(b.get("to_chapter", 0)),
                       "target": float(b.get("bridge_frequency_target") or 0)}
                      for b in sorted(mode_blocks,
                                      key=lambda x: int(x.get("from_chapter",
                                                              0)))]
        else:
            blocks = [{"label": c.get("title", f"ch{c.get('number')}"),
                       "from_chapter": int(c.get("number", 0)),
                       "to_chapter": int(c.get("number", 0)),
                       "target": None} for c in chapters]
        rows = []
        for blk in blocks:
            scenes = [s for c in chapters
                      if blk["from_chapter"] <= int(c.get("number", 0))
                      <= blk["to_chapter"]
                      for s in self.ctx.neighbors(c["id"], "SCENE_OF",
                                                  direction="in")]
            routed = [s for s in scenes if s.get("route_mode")]
            soft = [s for s in routed if s.get("route_mode") == "soft"]
            share = (len(soft) / len(routed)) if routed else 0.0
            target = blk["target"]
            deviation = (abs(share - target)
                         if target is not None else 0.0)
            rows.append({"label": blk["label"],
                         "from_chapter": blk["from_chapter"],
                         "to_chapter": blk["to_chapter"],
                         "soft_share": round(share, 3),
                         "target": target,
                         "deviation": round(deviation, 3),
                         "verdict": ("flagged" if target is not None
                                     and deviation
                                     > BRIDGE_DEVIATION_TOLERANCE
                                     else "ok")})
        shares = [r["soft_share"] for r in rows]
        return ToolResult.success(data={
            "blocks": rows,
            "curve_intact": shares == sorted(shares),
        })

    @verb(role="act")
    def dual_storyform_coherence_check(self,
                                       storyform_set_id: str) -> ToolResult:
        """Composite (act): ``novel_coherence_check`` on EACH member +
        Klein-c inversion + legality of every recorded transition; records
        a ``dual-storyform-report`` Artefact.

        Inputs: storyform_set_id.
        Returns: ``{passed, members, inversion, transitions, bridge,
                 artefact_id}``.
        chain_next: fix the listed non-inverted slots / illegal transitions.
        """
        st = self.ctx.recall(storyform_set_id)
        if st is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"set {storyform_set_id!r} not found")
        novel_id = st.get("novel", "")
        members = []
        for m in self._set_members(storyform_set_id):
            # novel_coherence_check takes the member's NCP body, not the id.
            coh = self.novel_coherence_check(_body_of(m))
            members.append({"role": m.get("role", ""),
                            "storyform_id": m["id"],
                            "coherence": coh.data if coh.ok else
                            {"passed": False}})
        inversion = self.check_klein_c_inversion(storyform_set_id).data
        transitions = []
        for t in self.ctx.find("StoryformTransition"):
            if t.get("storyform_set_id") != storyform_set_id:
                continue
            leg = self.check_driver_transition_legality(t["id"])
            transitions.append({"transition_id": t["id"],
                                "legality": leg.data})
        bridge = self.bridge_frequency_report(novel_id)
        bridge_data = bridge.data if bridge.ok else {}
        passed = (bool(inversion.get("passed"))
                  and all(tr["legality"].get("passed")
                          for tr in transitions))
        aid = self.ctx.record("Artefact", {
            "kind": "dual-storyform-report",
            "storyform_set_id": storyform_set_id,
            "passed": passed,
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return ToolResult.success(data={
            "passed": passed, "members": members, "inversion": inversion,
            "transitions": transitions, "bridge": bridge_data,
            "artefact_id": aid,
        })
