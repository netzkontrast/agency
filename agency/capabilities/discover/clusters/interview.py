# agency-scaffold: v1
"""discover.interview — the adaptive elicitation engine (Spec 309).

Guided-exploration core of the Spec 307 program: turns a one-sentence seed into a
DRAFT Intent by running an adaptive beat-chain, recording every turn as graph
provenance (Goal 2 — *how the WHY was discovered*). Generalizes Spec 262's fixed
4-beat ``intent.managed_onboard`` into the adaptive ``discover.interview``.

The adaptivity seam (Spec 147): the next beat's question is derived from the
prior answers. With a Driver injected, the structured-output Driver returns the
next ``NextBeat``; with ``driver=None`` the DETERMINISTIC fallback walks the
``interview-beats.json`` library in ``turn_kind`` order and fills ``{prior}`` from
the previous answer — so the verb is fully exercised with ZERO LLM.

Answer-flow (Slice 1): a verb cannot block on a human, so the harness renders each
beat and the caller folds the verbatim answer back; the ``answers`` list IS that
seam (the Spec 310 ``ask`` payload + ``fold_answer`` round-trip is the wet path).
Each beat's question is built from the beat library (the legitimate 262-superseding
source); composing ``discover.ask`` for *choice*-beats (offering derived options)
is the documented wet-path refinement — forcing multiple-choice onto an open
``describe`` beat is the tension Slice 1 deliberately avoids.
"""
from __future__ import annotations

import json
from pathlib import Path

from agency.capability import verb
from agency.toolresult import ToolResult

# A complete Intent needs purpose + deliverable + acceptance — the triple's
# arity (3), NOT a magic beat count. Completeness is read from the derived
# triple, so a sharp user finishes early and a vague one runs the budget.
_TRIPLE_FIELDS = ("purpose", "deliverable", "acceptance")

_BEATS_CACHE: list | None = None


def _beat_library() -> list:
    """The Spec 309 beat library (cached). Supersedes 262's fixed four."""
    global _BEATS_CACHE
    if _BEATS_CACHE is None:
        path = Path(__file__).resolve().parent.parent / "data" / "interview-beats.json"
        _BEATS_CACHE = json.loads(path.read_text(encoding="utf-8"))["beats"]
    return _BEATS_CACHE


class InterviewCluster:
    """The ``interview`` verb — composed into ``DiscoverCapability``."""

    @verb(role="act")
    def interview(self, seed: str, answers: list | None = None,
                  max_beats: int = 6) -> ToolResult:
        """Run the adaptive elicitation interview → a DRAFT Intent (act).

        Opens a ``DiscoverySession``, runs up to ``max_beats`` beats (each beat's
        question derived from the prior answer — the adaptivity seam), records an
        ``ElicitationTurn`` per beat (``ELICITS`` edge), then mints a *draft*
        Intent (never confirmed — the clarity gate Spec 322 owns that) with a
        ``DISCOVERED`` edge from the session.

        Inputs:
          - seed (the one-sentence ask the interview sharpens)
          - answers (the verbatim user answers the harness folds back, in order;
            empty → an empty-but-recorded run)
          - max_beats (the budget; termination is data-driven, not this count)
        Returns: ``{session_id, intent_id, beats:[{turn_id,beat,kind,question,
                 answer}], terminated_by:"complete"|"max_beats", clarity_inputs}``.
        chain_next: ``discover.clarity`` (Spec 322) scores + the confirm gate
                    flips the draft Intent to confirmed.
        """
        answers = list(answers or [])
        session_id = self._session(seed)
        turns: list[dict] = []
        terminated_by = "max_beats"
        for i in range(max_beats):
            kind, template = self._next_beat(i, turns)
            prior = turns[-1]["answer"] if turns else seed
            question = template.replace("{seed}", seed).replace("{prior}", prior)
            answer = answers[i] if i < len(answers) else ""
            turn_id = self._record_turn(session_id, i + 1, kind, question, answer)
            turns.append({"turn_id": turn_id, "beat": i + 1, "kind": kind,
                          "question": question, "answer": answer})
            if self._triple_complete(turns):
                terminated_by = "complete"
                break

        triple = self._derive_triple(turns)
        intent_id = self.ctx.engine.intent.capture(
            triple["purpose"], triple["deliverable"], triple["acceptance"])
        self.ctx.link(session_id, intent_id, "DISCOVERED")

        return ToolResult.success(data={
            "session_id": session_id,
            "intent_id": intent_id,
            "beats": turns,
            "terminated_by": terminated_by,
            "clarity_inputs": self._clarity_inputs(turns, triple),
        })

    # ── beat selection (Spec 147 Driver seam behind the NextBeat shape) ──
    def _next_beat(self, beat_idx: int, prior_turns: list) -> tuple[str, str]:
        """Deterministic fallback: walk the beat library in ``turn_kind`` order.

        Returns ``(kind, template)``. The Spec 147 structured-output Driver
        overrides this to return an adaptive ``NextBeat`` from the session-so-far;
        both paths record the SAME node/edge surface (the seam never leaks).
        """
        lib = _beat_library()
        entry = lib[min(beat_idx, len(lib) - 1)]
        return entry["kind"], entry["template"]

    # ── triple derivation + data-driven termination ──
    @staticmethod
    def _filled(turns: list) -> list:
        """The non-empty verbatim answers, in order — the triple's raw inputs."""
        return [t["answer"] for t in turns if t["answer"].strip()]

    def _triple_complete(self, turns: list) -> bool:
        """Complete when the answers can fill the whole triple (3 inputs) — the
        triple's arity, NOT a beat count. A sharp user finishes early."""
        return len(self._filled(turns)) >= len(_TRIPLE_FIELDS)

    def _derive_triple(self, turns: list) -> dict:
        """Positional projection of the non-empty answers onto the triple —
        purpose ← 1st, deliverable ← 2nd, acceptance ← 3rd. Missing fields get a
        clear DRAFT placeholder so the draft Intent is a valid node (the clarity
        gate Spec 322 reads ``clarity_inputs`` to see what is still unelicited)."""
        vals = self._filled(turns)
        return {f: (vals[i] if i < len(vals)
                    else f"(draft — {f} not yet elicited)")
                for i, f in enumerate(_TRIPLE_FIELDS)}

    def _clarity_inputs(self, turns: list, triple: dict) -> dict:
        """The signal bag Spec 322's clarity score reads — derived, not pinned.
        ``fields_filled`` counts REAL answers (not the draft placeholders)."""
        filled = min(len(self._filled(turns)), len(_TRIPLE_FIELDS))
        return {"turns": len(turns), "fields_filled": filled,
                "total_fields": len(_TRIPLE_FIELDS),
                "answered": len(self._filled(turns))}
