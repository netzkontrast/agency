"""Spec 176 Slice 2 — the SessionStart intent-capture contract.

Slice 1 shipped the typed `IntentCapture` record (`_typed_shapes_wave1.py`) but
nothing populated it (dormant). This is the engine-side capture core the
SessionStart hook drives: it guarantees every session SERVES an Intent without
ever blocking the session.

The doctrine (spec Open-Question 1): **never block** — offer capture, but a
session always proceeds because an `auto_ad_hoc` Intent is the fallback; a later
`intent_bootstrap` supersedes it (Spec 014 amendment pattern). Capture is a pure
graph write (no network), so the non-blocking guarantee holds by construction.

Two entry points:
  - `open_intent_id(memory)` — the live session Intent, or "" (the idempotency
    read: an open Intent ⇒ the hook NO-OPs, no re-prompt).
  - `capture_session_intent(engine, …)` — idempotent capture. An open Intent ⇒
    NO-OP returning its `IntentCapture` (turns=0). Else mint the Intent (from the
    supplied turns, or an `auto_ad_hoc` default) and record one Artefact per
    captured turn (`PRODUCES` the Invocation + `SERVES` the Intent), so
    `len(artefact_ids) == turns` is the write-per-turn contract.

`AGENCY_INTENT` (Spec 018) is set to the resolved id for the session's lifetime.
"""
from __future__ import annotations

import os

from ._typed_shapes_wave1 import IntentCapture
from .toolresult import Codes

# The auto_ad_hoc fallback Intent — a session always has *something* to SERVE.
_AD_HOC_PURPOSE = "Ad-hoc session work (no intent captured at SessionStart)"
_AD_HOC_DELIVERABLE = "Whatever the session produces; supersede via intent_bootstrap"
_AD_HOC_ACCEPTANCE = "A later intent_bootstrap supersedes this default"


def open_intent_id(memory) -> str:
    """The most-recently-recorded LIVE Intent id, or "" when none is open.

    The idempotency read (Done-When invariant): an open Intent ⇒ the SessionStart
    hook NO-OPs (no re-prompt). ``Memory.find`` returns only live (un-superseded)
    nodes; the newest by ``vfrom`` is the session's working Intent.
    """
    intents = memory.find("Intent")
    if not intents:
        return ""
    newest = max(intents, key=lambda p: p.get("vfrom", 0))
    return newest.get("id", "") or ""


def capture_session_intent(engine, *, source: str = "auto_ad_hoc",
                           captured_at: str = "derived",
                           purpose: str = "", deliverable: str = "",
                           acceptance: str = "",
                           turns: "tuple[str, ...]" = ()) -> IntentCapture:
    """Idempotent session intent-capture. Returns the typed :class:`IntentCapture`.

    - **Idempotent re-entry:** an open Intent already in the graph ⇒ NO-OP — the
      existing Intent's capture is returned with ``turns=0`` (nothing minted).
    - **auto_ad_hoc fallback:** no open Intent + no supplied purpose ⇒ mint the
      default ad-hoc Intent so subsequent verbs have something to SERVE.
    - **Templated capture:** when ``turns`` (one prompt/answer line each) are
      supplied, one Artefact is recorded per turn (``PRODUCES`` the capture's
      Invocation, ``SERVES`` the Intent) so ``len(artefact_ids) == len(turns)``.

    ``AGENCY_INTENT`` (Spec 018) is set to the resolved id either way.
    """
    mem = engine.memory

    existing = open_intent_id(mem)
    if existing:
        # NO-OP: the session already serves an Intent — never re-prompt.
        os.environ["AGENCY_INTENT"] = existing
        return IntentCapture(intent_id=existing, captured_at=captured_at,
                             source=source, artefact_ids=(), turns=0)

    # No open Intent — mint one. A supplied purpose is a real capture; absent it,
    # the auto_ad_hoc default keeps the session non-orphan.
    real = bool(purpose.strip())
    iid = engine.intent.capture_and_confirm(
        purpose or _AD_HOC_PURPOSE,
        deliverable or _AD_HOC_DELIVERABLE,
        acceptance or _AD_HOC_ACCEPTANCE,
        owner="user")
    resolved_source = source if real or source != "auto_ad_hoc" else "auto_ad_hoc"

    # One Artefact per captured turn — the write-per-turn contract (Done-When).
    # The capture Invocation anchors the PRODUCES edges; each Artefact SERVES the
    # Intent so the transcript IS the chain of Artefacts (Open-Question 3).
    artefact_ids: list[str] = []
    inv_id = ""
    if turns:
        inv_id = mem.record("Invocation", {"capability": "intent",
                                           "verb": "sessionstart_capture",
                                           "role": "effect"})
        mem.link(inv_id, iid, "SERVES")
        for n, line in enumerate(turns):
            aid = mem.record("Artefact", {"kind": "capture_turn",
                                          "turn": n, "body": line})
            mem.link(aid, inv_id, "PRODUCES")
            mem.link(aid, iid, "SERVES")
            artefact_ids.append(aid)

    os.environ["AGENCY_INTENT"] = iid
    return IntentCapture(intent_id=iid, captured_at=captured_at,
                         source=resolved_source,
                         artefact_ids=tuple(artefact_ids),
                         turns=len(artefact_ids))


def capture_degraded(intent_id: str, captured_at: str, source: str,
                     artefact_ids: "tuple[str, ...]") -> dict:
    """Build the ``CAPTURE_DEGRADED`` failure payload — a capture driver failed
    mid-flow (e.g. RATE_LIMITED on turn 4 of 5): the already-written turns persist
    and the capture is resumable. Spec 176 failure mode + Spec 151 Codes."""
    return {"code": Codes.CAPTURE_DEGRADED, "intent_id": intent_id,
            "captured_at": captured_at, "source": source,
            "artefact_ids": list(artefact_ids), "turns": len(artefact_ids),
            "resumable": True}
