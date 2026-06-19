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


def _resolve_spec_path_from_archive(spec_id: str) -> str | None:
    """Check the git archive branch for a shipped spec path (dry-run fallback).

    Specs that have been shipped are deleted from ``Plan/`` but preserved in
    ``archive/plan-specs-pre-cleanup``.  For dry-run amendment proposals the
    path is only used as the diff-header filename, so the file need not exist
    on disk — we just need the canonical path string.
    """
    import subprocess
    try:
        out = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only",
             "archive/plan-specs-pre-cleanup", "--", "Plan/"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        for line in out.stdout.splitlines():
            parts = line.split("/")
            if (len(parts) == 3 and parts[0] == "Plan"
                    and parts[1].startswith(f"{spec_id}-")
                    and parts[2] == "spec.md"):
                return line
    except Exception:
        pass
    return None


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


def _norm_heading(text: str) -> str:
    """Normalise a heading/section name for tolerant matching:
    ``## Done-When (if built)`` and ``Done When`` both → ``done when``."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _find_section_bounds(lines: list, section: str):
    """Locate ``## <section>`` in markdown ``lines`` (tolerant of case,
    punctuation, and heading suffixes). Returns ``(heading_idx, end_idx)``
    where ``end_idx`` is the next same-or-higher-level heading (or EOF), or
    ``None`` when no heading matches — so the caller NEVER blind-writes."""
    target = _norm_heading(section)
    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    start = level = None
    for i, line in enumerate(lines):
        m = heading_re.match(line.rstrip("\n"))
        if not m:
            continue
        if start is None:
            if target and target in _norm_heading(m.group(2)):
                start, level = i, len(m.group(1))
            continue
        # past the section heading — the section ends at the next heading of
        # the same or a higher level (fewer/equal '#').
        if len(m.group(1)) <= level:
            return start, i
    if start is None:
        return None
    return start, len(lines)


def _format_bullet(section: str, after: str) -> str:
    """A new bullet for an ``add-*`` op. ``after`` already authored as a bullet
    (starts with ``-``/``*``) keeps its own marker; otherwise a checkbox bullet
    is used for a Done-When section, a plain bullet elsewhere. A multi-line
    ``after`` stays inside ONE list item: only the first line carries the
    marker, continuation lines are indented (2 spaces) so they never land bare
    at the list margin (self-review fix)."""
    rows = after.rstrip("\n").split("\n")
    first = rows[0]
    if first.lstrip().startswith(("-", "*")):
        head = first
    elif "done" in _norm_heading(section):
        head = f"- [ ] {first}"
    else:
        head = f"- {first}"
    out = [head]
    for ln in rows[1:]:
        out.append(("  " + ln) if ln.strip() else ln)
    return "\n".join(out) + "\n"


def apply_amendment_to_text(text: str, *, section: str, op: str,
                            before: str = "", after: str = "") -> str:
    """Fold an amendment into a spec.md body, returning the NEW text — the
    decidable live-write that closes Goal 6 (Spec 150). Pure: no I/O.

    ``add-*`` appends a bullet at the end of the named section (before the
    section's trailing blank lines / the next heading). ``edit-*`` replaces the
    first line in the section containing ``before`` with ``after`` (indentation
    preserved). Raises ``ValueError('amendment_no_section: …')`` when the
    section heading is absent and ``amendment_before_absent`` when an ``edit``
    target is not found — the spec file is never corrupted by a blind write."""
    lines = text.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, section)
    if bounds is None:
        raise ValueError(
            f"amendment_no_section: no heading matching '{section}' in the spec")
    start, end = bounds
    if op.startswith("add-"):
        insert_at = end
        while insert_at - 1 > start and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        bullet = _format_bullet(section, after)
        head = lines[:insert_at]
        # Guard the EOF/no-trailing-newline case: the bullet must start on its
        # own line, never fuse onto the section's last line (self-review fix).
        if head and not head[-1].endswith("\n"):
            head = head[:-1] + [head[-1] + "\n"]
        return "".join(head + [bullet] + lines[insert_at:])
    if op.startswith("edit-"):
        needle = before.strip()
        if not needle:
            raise ValueError("amendment_before_absent: edit op needs `before`")
        for i in range(start + 1, end):
            if needle in lines[i]:
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                lines[i] = f"{indent}{after.rstrip()}\n"
                return "".join(lines)
        raise ValueError(
            f"amendment_before_absent: {before!r} not found in the section")
    raise ValueError(f"amendment_unknown_op: {op!r}")


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
        """Render a ProposalPayload as a unified diff, recorded as a provenance Artefact.

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
        chain_next: review the diff, then re-call with ``dry_run=False`` +
                    ``confirm_token`` to write the amendment.
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
            # Spec may have been shipped and deleted from Plan/ — check archive.
            archived_path = _resolve_spec_path_from_archive(spec_id)
            if archived_path is None:
                raise RuntimeError(f"amendment_bad_spec: no spec dir for "
                                   f"spec_id={spec_id!r}")
            if not dry_run:
                raise RuntimeError(
                    f"amendment_bad_spec: spec {spec_id!r} is archived "
                    f"(shipped; no longer in Plan/); live amendment requires "
                    f"the spec file on disk")
            spec_path = archived_path
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
        art_id = self.ctx.record_and_serve("Artefact", {
            "kind": "amendment-proposal",
            "spec_id": spec_id,
            "op": payload.get("op", ""),
            "payload_hash": payload_hash,
        })
        for rid in sources:
            self.ctx.link(art_id, rid, "PRODUCES_FROM")
        result: dict = {"diff": diff, "artefact_id": art_id,
                        "payload_hash": payload_hash}
        # Live write (Spec 150 — closes Goal 6's fold-back loop). The
        # confirm_token already matched the payload id-hash above; now fold the
        # amendment into the spec file via the pure section-surgery helper and
        # write it back. A section/edit-target miss raises (never blind-writes).
        if not dry_run:
            import pathlib
            path = pathlib.Path(spec_path)
            original = path.read_text(encoding="utf-8")
            try:
                new_text = apply_amendment_to_text(
                    original,
                    section=payload.get("section", ""),
                    op=payload.get("op", ""),
                    before=payload.get("before") or "",
                    after=payload.get("after") or "")
            except ValueError as exc:
                raise RuntimeError(str(exc))
            path.write_text(new_text, encoding="utf-8")
            result["written_path"] = spec_path
            # The recorded diff is now the REAL file change, not the synthetic
            # preview — the Artefact's provenance matches what landed on disk.
            result["diff"] = "".join(difflib.unified_diff(
                original.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{spec_path}", tofile=f"b/{spec_path}"))
        return result
