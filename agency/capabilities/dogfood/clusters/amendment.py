"""dogfood.amendment — Reflection→spec-amendment classifier (Spec 150/147/279).

Spec 286 P3 — extracted verbatim from ``dogfood/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single DogfoodCapability.

parse_amendment classifies recent Reflections into amendment proposals
(keyword fallback OR Spec 147 AnthropicDriver structured output via Spec 279's
complete_or_delegate); apply_amendment renders a ProposalPayload as a unified
diff and writes the provenance Artefact with PRODUCES_FROM edges to every
cited Reflection.
"""
from __future__ import annotations

import json
import re

# ────────────────────────────────────────────────────────────────────────────
# Spec 150 Slice 1 — amendment classifier + apply helpers (module-level).
# ────────────────────────────────────────────────────────────────────────────
# Keyword classifier rules. Each tuple is (regex, op, section, confidence).
# The keyword path is the documented fallback when the Spec 147 AnthropicDriver
# is unavailable (never silent no-op); Slice 2 swaps in structured-output
# classification through the driver.
import difflib
import hashlib

_CLASSIFIER_RULES: list[tuple[re.Pattern, str, str, float]] = [
    (re.compile(r"\bshould add\b", re.IGNORECASE), "add-done-when", "Done When", 0.7),
    (re.compile(r"\bpropose\b", re.IGNORECASE),    "add-done-when", "Done When", 0.65),
    (re.compile(r"\bshould be\b", re.IGNORECASE),  "add-done-when", "Done When", 0.6),
    (re.compile(r"\bmissing from spec\b", re.IGNORECASE),
                                                    "add-done-when", "Done When", 0.75),
    (re.compile(r"\bopen question\b", re.IGNORECASE),
                                                    "add-open-q", "Open questions", 0.65),
]


# ── Spec 150 Slice 2 — LLM classifier path ────────────────────────────────
# Documented amendment ops the LLM may emit. Kept aligned with the keyword
# path so the downstream `apply_amendment` flow is the same.
_LLM_OPS = ("add-done-when", "add-open-q", "edit-done-when", "edit-open-q")
_LLM_SECTIONS = ("Done When", "Open questions", "Followup", "row")


# JSON schema the AnthropicDriver enforces via structured outputs. Slice 2
# uses output_config.format=json_schema (Spec 147 claude-api skill).
_PROPOSAL_LIST_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["proposals"],
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["reflection_id", "spec_id", "section", "op",
                              "after", "rationale", "confidence"],
                "properties": {
                    "reflection_id": {"type": "string"},
                    "spec_id":       {"type": "string", "pattern": r"^\d{3}$"},
                    "section":       {"type": "string", "enum": list(_LLM_SECTIONS)},
                    "op":            {"type": "string", "enum": list(_LLM_OPS)},
                    "after":         {"type": "string", "minLength": 1},
                    "rationale":     {"type": "string", "minLength": 40},
                    "confidence":    {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    },
}


_CLASSIFIER_SYSTEM = (
    "You are the dogfood amendment classifier. You receive a JSON list of "
    "reflection objects (each with id + plan_slug + text + scope). For "
    "EVERY reflection whose text proposes a concrete amendment to a spec, "
    "emit one ProposalPayload — spec_id (NNN from plan_slug, 3-digit), "
    "section (one of Done When / Open questions / Followup / row), op (one "
    "of add-done-when / add-open-q / edit-done-when / edit-open-q), after "
    "(the proposed new text, 1+ chars), rationale (>= 40 chars, citing the "
    "reflection text), confidence in [0,1]. Skip neutral reflections "
    "(observations without an actionable proposal). Output strictly matches "
    "the schema; do not invent spec_ids that aren't in the input plan_slugs."
)


def _reflection_payload_for_llm(refl: dict) -> dict:
    """Trim a Reflection's properties to the fields the classifier needs.
    Keeps the LLM payload small (Spec 154 output-overflow discipline)."""
    return {
        "id":        refl.get("id") or "",
        "plan_slug": refl.get("plan_slug") or "",
        "scope":     refl.get("scope") or "",
        "text":      (refl.get("text") or "").strip()[:1200],
    }


def _build_classifier_messages(reflections: list[dict]) -> list[dict]:
    """Build the messages list for `complete_or_delegate`. The user
    message carries the reflections as JSON so the model parses
    deterministically."""
    payload = [_reflection_payload_for_llm(r) for r in reflections]
    user = (
        "Classify these reflections into ProposalPayload objects per the "
        "schema. Emit ONLY actionable proposals; skip neutral observations.\n\n"
        f"reflections = {json.dumps(payload, sort_keys=True)}"
    )
    return [{"role": "user", "content": user}]


def _parse_llm_proposals(parsed: dict | None,
                          reflections_by_id: dict[str, dict],
                          limit: int) -> list[dict]:
    """Convert the LLM's structured output into the canonical
    ProposalPayload shape (matching the keyword path's `proposals` list).
    Drops any proposal whose reflection_id isn't in the input set —
    defense against the LLM hallucinating reflections."""
    if not isinstance(parsed, dict):
        return []
    raw = parsed.get("proposals") or []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        rid = p.get("reflection_id") or ""
        refl = reflections_by_id.get(rid)
        if refl is None:
            continue                                              # hallucination — drop
        # Codex review on PR #136: host_completion bypasses the
        # driver-side JSON-schema enforcement, so validate the same
        # invariants HERE — enum-bound section + op, [0,1] confidence,
        # 40-char rationale floor. Drop the proposal on any miss.
        section = str(p.get("section") or "")
        op = str(p.get("op") or "")
        if section not in _LLM_SECTIONS or op not in _LLM_OPS:
            continue
        try:
            confidence = float(p.get("confidence") or 0.0)
        except (TypeError, ValueError):
            continue
        if not (0.0 <= confidence <= 1.0):
            continue
        rationale = str(p.get("rationale") or "")
        if len(rationale) < 40:
            continue
        after = str(p.get("after") or "").strip()
        if not after:
            continue
        # Codex review on PR #136: derive spec_id from the cited
        # reflection's plan_slug rather than trusting the model. A
        # classifier mistake could route apply_amendment to the wrong
        # spec while provenance points at a different plan — silently
        # mis-attributing the amendment. The plan_slug is the
        # ground-truth source.
        derived_spec_id = _spec_id_from_slug(refl.get("plan_slug") or "")
        if not derived_spec_id:
            continue
        model_spec_id = str(p.get("spec_id") or "")
        if model_spec_id and model_spec_id != derived_spec_id:
            continue                                              # mismatch — drop
        out.append({
            "spec_id":            derived_spec_id,
            "section":            section,
            "op":                 op,
            "before":             "",
            "after":              after,
            "rationale":          rationale,
            "source_reflections": [rid],
            "confidence":         confidence,
        })
        if len(out) >= limit:
            break
    return out


def _classify_reflection(text: str) -> dict:
    """Classify ONE reflection text into an amendment op + section + confidence.

    Returns ``{"op": None}`` for neutral observations (no amendment). The
    keyword path is deliberately CONSERVATIVE: false positives erode trust.
    """
    for rule, op, section, conf in _CLASSIFIER_RULES:
        m = rule.search(text or "")
        if m:
            return {"op": op, "section": section, "confidence": conf,
                    "matched": m.group(0)}
    return {"op": None}


def _spec_id_from_slug(plan_slug: str) -> str:
    """Extract the NNN spec-id from a `NNN-slug` plan_slug."""
    head = (plan_slug or "").split("-", 1)[0]
    return head if head.isdigit() else ""


def _resolve_spec_path(spec_id: str) -> str | None:
    """Find ``Plan/<spec_id>-*/spec.md`` on disk; return None when missing."""
    import glob
    if not spec_id or not spec_id.isdigit():
        return None
    matches = sorted(glob.glob(f"Plan/{spec_id}-*/spec.md"))
    return matches[0] if matches else None


def _payload_hash(payload: dict) -> str:
    """Stable id-hash for a proposal — used by the confirm_token live-write
    gate. Hashed over (spec_id, section, op, after) so a re-classification
    that proposes the same edit yields the same token."""
    key = "|".join([payload.get("spec_id", ""),
                    payload.get("section", ""),
                    payload.get("op", ""),
                    (payload.get("after") or "").strip()])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _render_unified_diff(spec_path: str, *, before: str, after: str,
                          spec_id: str) -> str:
    """Render an amendment as a unified-diff hunk. The dry-run output the
    reviewer reads. For Slice 1 we emit a SYNTHETIC unified diff that names
    the spec file + the proposed before/after — enough for a reviewer to
    decide; the file-line surgery is Slice 2 (needs a proper section
    locator).
    """
    before_lines = (before + "\n").splitlines(keepends=True) if before else []
    after_lines = (after + "\n").splitlines(keepends=True) if after else []
    diff_iter = difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"a/{spec_path}",
        tofile=f"b/{spec_path}",
        n=0,
    )
    diff = "".join(diff_iter)
    if not diff:
        diff = f"--- a/{spec_path}\n+++ b/{spec_path}\n@@ -0,0 +1 @@\n+{after}\n"
    return diff


from agency.capability import verb


class AmendmentMixin:
    """Spec 150 — dogfood amendment classifier (close Goal 6)."""

    # ════════════════════════════════════════════════════════════════════════
    # Spec 150 Slice 1 — dogfood amendment classifier (close Goal 6).
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def parse_amendment(self, scope: str = "", since: str = "",
                         limit: int = 20, use_llm: bool = True,
                         prefer_delegate: bool = False,
                         host_completion: dict | None = None) -> dict:
        """Classify recent Reflections into amendment proposals.

        Slice 1 shipped the keyword classifier (the documented fallback
        path). Slice 2 (this) swaps in Spec 147 AnthropicDriver
        structured-output classification — same ProposalPayload shape,
        sharper recall — wrapped through Spec 279's ``complete_or_delegate``
        so the no-key host (Claude Code) can run inference itself
        instead of degrading to keywords.

        Three paths (resume wins):

        1. ``host_completion`` supplied — the host already ran inference
           after a prior delegation; parse the result into proposals.
        2. ``use_llm=True`` AND an AnthropicDriver is wired AND capable:
           structured-output ``complete()`` call.
        3. ``use_llm=True`` AND ``prefer_delegate=True`` AND driver backend
           is ``"none"`` → return a ``llm_delegate`` envelope so the host
           (Claude Code) can run inference and re-call (Spec 279). When
           ``prefer_delegate=False`` (default), backend ``"none"`` silently
           degrades to keyword — backwards-compat default so tests +
           non-host callers don't have to handle the envelope.
        4. else / ``use_llm=False`` / no driver — keyword classifier
           fallback (Slice 1 path).

        Inputs: scope (substring filter on plan_slug), since (reserved
                bi-temporal cursor), limit (caps proposals; default 20),
                use_llm (default True; set False to force keyword path),
                host_completion (Spec 279 resume envelope from Claude
                Code — ``{text, parsed?}`` where ``parsed`` is the
                ProposalPayload list).
        Returns: ``{proposals: [ProposalPayload], classifier: str,
                    kind?: "llm_delegate", request?: HostLLMRequest dict}``.
        chain_next: ``dogfood.apply_amendment(payload, dry_run=True)``.
        """
        reflections = self.ctx.query_nodes("Reflection", {"scope": "observation"})
        if scope:
            reflections = [r for r in reflections
                           if scope in (r.get("plan_slug") or "")]

        # ── LLM path (Slice 2) ────────────────────────────────────────
        if use_llm and reflections:
            llm_result = self._llm_classify(
                reflections, limit, host_completion, prefer_delegate)
            if llm_result is not None:
                return llm_result

        # ── Keyword fallback (Slice 1 path) ───────────────────────────
        proposals: list[dict] = []
        for refl in reflections:
            tag = _classify_reflection(refl.get("text") or "")
            if tag["op"] is None:
                continue
            spec_id = _spec_id_from_slug(refl.get("plan_slug") or "")
            if not spec_id:
                continue
            proposals.append({
                "spec_id":      spec_id,
                "section":      tag["section"],
                "op":           tag["op"],
                "before":       "",
                "after":        (refl.get("text") or "").strip(),
                "rationale":    (
                    f"Classifier promoted this Reflection based on a strong-"
                    f"intent keyword (`{tag['matched']}`). Source observation "
                    f"text: {(refl.get('text') or '')[:200]}"),
                "source_reflections": [refl.get("id") or ""],
                "confidence":   tag["confidence"],
            })
            if len(proposals) >= limit:
                break
        return {"proposals": proposals, "classifier": "keyword"}

    def _llm_classify(self, reflections: list[dict], limit: int,
                       host_completion: dict | None,
                       prefer_delegate: bool) -> dict | None:
        """Slice 2 LLM classification via `complete_or_delegate`. Returns:

        - dict with `{proposals, classifier: "llm"}` on driver-capable
          path or `{proposals, classifier: "host"}` on host resume.
        - dict with `{proposals: [], classifier: "llm-delegate",
          kind: "llm_delegate", request: …}` when ``prefer_delegate`` is
          True AND the driver backend is "none" — Spec 279 envelope so
          Claude Code runs inference.
        - None when the LLM path can't run AND the keyword fallback
          should take over (no driver wired AND no host_completion;
          OR driver backend "none" AND `prefer_delegate=False`;
          OR a driver failure that we recover from gracefully).
        """
        # Resolve the anthropic driver (None when not wired).
        driver = None
        try:
            reg = getattr(self.ctx, "drivers", None)
            if reg is not None and reg.has("anthropic"):
                driver = reg.get("anthropic")
        except Exception:
            driver = None
        # No driver AND no resume → keyword fallback.
        if driver is None and host_completion is None:
            return None
        # Driver present but not capable AND not opting into delegation
        # AND no resume → silent keyword degrade (spec contract).
        if (driver is not None and host_completion is None
                and not prefer_delegate
                and driver.backend() == "none"):
            return None

        from agency._host_llm import (
            complete_or_delegate, HostLLMRequest, HostDelegateError,
        )
        # Driver may be None when we have a host_completion to resume —
        # complete_or_delegate's resume branch ignores the driver.
        if driver is None:
            class _NoDriver:
                def backend(self) -> str:
                    return "none"
            driver = _NoDriver()

        messages = _build_classifier_messages(reflections)
        reflections_by_id = {r.get("id") or "": r for r in reflections}
        try:
            result = complete_or_delegate(
                driver,
                messages=messages,
                system=_CLASSIFIER_SYSTEM,
                output_schema=_PROPOSAL_LIST_SCHEMA,
                host_completion=host_completion,
                host=self.ctx.host,        # Spec 285 — real MCP sampling when available
            )
        except HostDelegateError:
            raise                                                  # bubble up
        except Exception:
            return None                                            # graceful degrade

        if isinstance(result, HostLLMRequest):
            return {
                "proposals":  [],
                "classifier": "llm-delegate",
                "kind":       result.kind,
                "request":    result.to_dict(),
            }
        parsed = result.parsed
        if parsed is None and result.text:
            try:
                parsed = json.loads(result.text)
            except (ValueError, TypeError):
                parsed = None
        proposals = _parse_llm_proposals(parsed, reflections_by_id, limit)
        classifier = ("host" if result.stop_reason == "host_provided"
                      else "llm")
        return {"proposals": proposals, "classifier": classifier}

    @verb(role="effect")
    def apply_amendment(self, payload: dict, dry_run: bool = True,
                         confirm_token: str = "") -> dict:
        """Render a ProposalPayload as a unified diff; provenance Artefact.

        v1 always renders the diff and writes an
        `Artefact(kind="amendment-proposal")` with PRODUCES_FROM edges
        to every cited Reflection so a reviewer can trace any amendment
        back to its source observations (the provenance moat invariant).

        Inputs: payload (dict — ProposalPayload schema; see Plan/150),
                dry_run (bool — default True; False requires
                  ``confirm_token`` to match the payload id-hash),
                confirm_token (str — opt-in live-write gate).
        Returns: ``{diff, artefact_id, written_path?}``.
        Failure modes: ``AMENDMENT_BAD_SPEC`` (no such spec dir),
                       ``AMENDMENT_NO_SOURCE`` (citations empty),
                       ``AMENDMENT_VAGUE`` (rationale < 40 chars),
                       ``AMENDMENT_UNCONFIRMED`` (live write requested,
                       confirm_token does not match the payload id-hash).
        """
        # Hard-coded constants are tunable budgets (rule 8):
        _RATIONALE_FLOOR = 40   # documented in Plan/150 §"Done When"
        sources = payload.get("source_reflections") or []
        if not sources:
            raise RuntimeError("amendment_no_source: "
                               "payload.source_reflections is empty — every "
                               "amendment must trace to ≥ 1 Reflection")
        if len(payload.get("rationale", "")) < _RATIONALE_FLOOR:
            raise RuntimeError(
                f"amendment_vague: rationale below the "
                f"{_RATIONALE_FLOOR}-char floor "
                f"(got {len(payload.get('rationale', ''))})")
        spec_id = payload.get("spec_id", "")
        spec_path = _resolve_spec_path(spec_id)
        if spec_path is None:
            raise RuntimeError(f"amendment_bad_spec: no spec dir for "
                               f"spec_id={spec_id!r}")
        # Live-write requires confirm_token matching the payload id-hash.
        payload_hash = _payload_hash(payload)
        if not dry_run and confirm_token != payload_hash:
            raise RuntimeError(
                f"amendment_unconfirmed: confirm_token mismatch; expected "
                f"id-hash={payload_hash!r} for this proposal")
        # Render the diff (dry-run path is the same; only the final write
        # branch differs by `dry_run`).
        diff = _render_unified_diff(spec_path,
                                    before=payload.get("before") or "",
                                    after=payload.get("after") or "",
                                    spec_id=spec_id)
        # Record the provenance Artefact + PRODUCES_FROM edges.
        art_id = self.ctx.record("Artefact", {
            "kind": "amendment-proposal",
            "spec_id": spec_id,
            "op": payload.get("op", ""),
            "payload_hash": payload_hash,
        })
        self.ctx.link(art_id, self.ctx.intent_id, "SERVES")
        for rid in sources:
            self.ctx.link(art_id, rid, "PRODUCES_FROM")
        result: dict = {"diff": diff, "artefact_id": art_id,
                        "payload_hash": payload_hash}
        # Live write is Slice 2; v1 records the Artefact + returns the diff.
        return result
