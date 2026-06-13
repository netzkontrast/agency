"""dogfood.observe — graph-native observation ledgers (Spec 017).

Spec 286 P3 — extracted verbatim from ``dogfood/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single DogfoodCapability.

The note → render → collect path keeps observation ledgers graph-native:
notes recorded as Reflection nodes, projected to DOGFOOD-NOTES.md markdown on
demand, with a legacy markdown-collect fallback for one-shot migration.
"""
from __future__ import annotations

import os
import re


# Match the bolded observation/lesson headers we use in DOGFOOD-NOTES.md.
# Three shapes seen in the wild:
#   **Observation 1 — title text.** body...
#   **Observation 5 (architectural):** body...
#   **Dogfood lesson 5 — title text.**
# Group 3 captures everything between the index and the closing `**` so we
# can handle any separator (em-dash, hyphen, colon, parenthetical, …) at
# the orchestrator boundary by trimming leading punctuation.
_HEADER_RE = re.compile(
    r"\*\*(Observation|Dogfood lesson)\s+(\d+)([^*]*)\*\*",
    re.IGNORECASE,
)


def _count_tokens(text: str) -> int:
    """Spec 082 — route through the ONE token-count boundary (count_tokens →
    tiktoken → proxy); was a duplicate of the document.* inline proxy."""
    from ...._tokens import count_tokens
    return count_tokens(text)


def _clean_title(raw: str) -> str:
    """Strip leading separator punctuation + trailing period from the
    header tail so a heading like ` — dispatch hardcodes …. ` becomes
    `dispatch hardcodes …`."""
    t = raw.strip()
    while t and t[0] in " -–—:":
        t = t[1:].lstrip()
    return t.rstrip(".")


def _parse_observations(text: str) -> list[dict]:
    """Extract observations from one DOGFOOD-NOTES.md body.

    Each entry runs from its header to the next header OR a blank-line
    paragraph break before the next ``**`` boundary. Returns a list of
    ``{kind, index, title, text}`` dicts; ``text`` includes the body
    paragraph the header introduces (best-effort first paragraph after
    the header line).
    """
    out: list[dict] = []
    matches = list(_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        # Stop at the first blank line so we capture only the immediate
        # paragraph; downstream sub-paragraphs frequently introduce other
        # subjects.
        first_para = body.split("\n\n", 1)[0].strip()
        out.append({
            "kind": m.group(1).lower(),                       # "observation" | "dogfood lesson"
            "index": int(m.group(2)),
            "title": _clean_title(m.group(3) or ""),
            "text": first_para,
        })
    return out


from agency.capability import verb


class ObserveMixin:
    """Spec 017 — graph-native authoring path: note / render / collect."""

    # -----------------------------------------------------------------
    # Spec 017 — graph-native authoring path.
    # -----------------------------------------------------------------

    @verb(role="act")
    def note(self, observation: str, plan_slug: str) -> dict:
        """Record an observation Reflection tagged with plan_slug.

        Inputs: observation (str — the body text), plan_slug (str — the
        Plan/NNN-slug directory name; used to scope render() queries).
        Returns: ``{reflection_id, plan_slug}``.
        chain_next: ``dogfood.render(plan_slug)`` when humans need the
                    DOGFOOD-NOTES.md projection.
        """
        rid = self.ctx.record("Reflection", {
            "scope": "observation",
            "text": observation,
            "plan_slug": plan_slug,
        })
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return {"reflection_id": rid, "plan_slug": plan_slug}

    @verb(role="transform")
    def render(self, plan_slug: str, max_tokens: int = 5000) -> dict:
        """Project plan_slug observations into DOGFOOD-NOTES.md.

        Inputs: plan_slug (str — same shape as note's tag),
                max_tokens (int — wire-payload cap; default 5000 cl100k;
                            additional observations get omitted with a
                            "_… (N more omitted)_" marker).
        Returns: ``{content, count, omitted, plan_slug, tokens}``. Empty
        plan returns clean markdown with "(none yet)" — never raises.
        Only Reflections with BOTH ``plan_slug == <slug>`` AND
        ``scope == 'observation'`` are surfaced (matches dogfood.note's
        write shape). Other-scope reflections + reflections without
        plan_slug are deliberately excluded.
        chain_next: caller writes ``Plan/<slug>/DOGFOOD-NOTES.md`` IF
                    a file projection is wanted (graph stays canonical).
        """
        # Query observation-scoped reflections matching plan_slug.
        # Both literals parametrized for parametrize-once-injection-
        # always-safe discipline (sc:sc-analyze F1 review finding).
        notes = self.ctx.query_nodes(
            "Reflection", {"plan_slug": plan_slug, "scope": "observation"})
        notes.sort(key=lambda r: r.get("vfrom", 0))
        # Spec 060 — render via `ctx.template('dogfood-notes')` so the
        # markdown shape lives as a file and iterating it is a markdown
        # commit, not a Python edit. Strip the `<!-- AGENT: -->` blocks
        # from the human-facing output (Spec 060 §Renderers strip blocks
        # for human-facing output).
        import re as _re
        tpl = self.ctx.template("dogfood-notes")
        if not notes:
            content = tpl.substitute(plan_slug=plan_slug, body="\n(none yet)\n")
            content = _re.sub(r"<!--.*?-->", "", content, flags=_re.DOTALL).strip()
            return {"content": content + "\n", "count": 0,
                    "omitted": 0, "tokens": _count_tokens(content),
                    "plan_slug": plan_slug}
        # Build the body string with mid-loop budget check.
        body_parts: list[str] = []
        rendered_count = 0
        for i, n in enumerate(notes, 1):
            chunk = (
                f"\n**Observation {i} — graph-native**\n\n"
                f"{n.get('text', '')}\n"
            )
            # PR review (round 7): probe BEFORE committing the chunk so
            # an oversize single observation can't push the rendered
            # payload past the cap. Trim the chunk if the probe overshoots
            # and stop iteration (the budget marker is appended later).
            probe = tpl.substitute(
                plan_slug=plan_slug,
                body="".join(body_parts) + chunk,
            )
            if _count_tokens(probe) > max_tokens * 0.92:
                # Compute remaining headroom and truncate this chunk to fit.
                current = tpl.substitute(
                    plan_slug=plan_slug, body="".join(body_parts))
                headroom_tokens = max(0, int(max_tokens * 0.92) - _count_tokens(current))
                # Token-budget proxy: ~4 chars per token (mirrors _count_tokens
                # fallback). Trim chunk to that char budget.
                char_cap = max(0, headroom_tokens * 4)
                if char_cap > 0 and rendered_count == 0:
                    # Always render at least a truncated form of the FIRST
                    # observation (so callers get SOMETHING back).
                    truncated = chunk[:char_cap] + "\n_…(truncated)_\n"
                    body_parts.append(truncated)
                    rendered_count = i
                break
            body_parts.append(chunk)
            rendered_count = i
        omitted = max(0, len(notes) - rendered_count)
        if omitted:
            body_parts.append(
                f"\n_… ({omitted} more observations omitted to fit "
                f"max_tokens={max_tokens})_\n")
        content = tpl.substitute(plan_slug=plan_slug, body="".join(body_parts))
        # Strip AGENT instruction blocks for the human-view output.
        content = _re.sub(r"<!--.*?-->", "", content, flags=_re.DOTALL).strip() + "\n"
        return {"content": content, "count": rendered_count,
                "omitted": omitted, "tokens": _count_tokens(content),
                "plan_slug": plan_slug}

    # -----------------------------------------------------------------
    # Spec 017 — collect kept for backward-compat (Spec 014 pipeline).
    # -----------------------------------------------------------------

    @verb(role="transform")
    def collect(self, plan_dir: str = "Plan") -> dict:
        """Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

        Inputs: plan_dir (str — root dir of plans; default ``Plan``).
        Returns: ``{observations: [{plan, kind, index, title, text}],
                 texts: [str], count, plans: [str], warnings: [str]}``.
        chain_next: ``reflect.batch_note(scope='observation', texts=)`` to
                    seed the graph from one-shot migration of legacy files.

        Deprecated for ongoing use — prefer ``dogfood.note`` (graph-
        native authoring) + ``dogfood.render`` (markdown projection on
        demand). Errors (missing dir, unreadable file) degrade into
        the ``warnings`` list rather than raising.
        """
        observations: list[dict] = []
        plans: list[str] = []
        warnings: list[str] = []

        if not os.path.isdir(plan_dir):
            return {"observations": [], "texts": [], "count": 0,
                    "plans": [], "warnings": [f"plan_dir not found: {plan_dir}"]}

        for entry in sorted(os.listdir(plan_dir)):
            plan_path = os.path.join(plan_dir, entry)
            notes_path = os.path.join(plan_path, "DOGFOOD-NOTES.md")
            if not os.path.isfile(notes_path):
                continue
            plans.append(entry)
            try:
                with open(notes_path, encoding="utf-8") as fh:
                    body = fh.read()
            except OSError as e:
                warnings.append(f"{notes_path}: {e}")
                continue
            for obs in _parse_observations(body):
                obs["plan"] = entry
                observations.append(obs)

        texts = [o["text"] for o in observations if o["text"]]
        return {
            "observations": observations,
            "texts": texts,
            "count": len(observations),
            "plans": plans,
            "warnings": warnings,
        }
