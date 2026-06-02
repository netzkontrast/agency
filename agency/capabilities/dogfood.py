"""dogfood — graph-native observation ledgers (Spec 017).

Spec 017 closes the **graph-vs-file inversion** documented in Spec 015
weaknesses W1 + W2: today the orchestrator writes
``Plan/<slug>/DOGFOOD-NOTES.md`` then `dogfood.collect` re-parses it
into Reflection nodes. That's "markdown as primary store" — exactly
the anti-pattern Vision/GOALS.md goal #7 names.

The corrected flow:
  - `dogfood.note(observation, plan_slug)` writes a Reflection
    DIRECTLY to the graph (scope='observation', plan_slug=...).
  - `dogfood.render(plan_slug)` projects matching Reflection nodes
    into the DOGFOOD-NOTES.md markdown format — on demand, when
    humans need it.
  - `dogfood.collect` stays for backward compatibility (Spec 014's
    observation→amendment pipeline) but the docstring marks it
    deprecated; new code uses `note`+`render`.

The capability owns NO ontology fragment of its own. Observations are
recorded into the graph by `reflect`'s Reflection node (Spec 045 adds
plan_slug as an optional property — backward-compatible).
"""
from __future__ import annotations

import os
import re

from ..capability import CapabilityBase, verb


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
    """cl100k tokens via tiktoken; char//4 proxy when tiktoken absent.

    Same shape as Spec 043's _index_repo._count_tokens — token-budget
    discipline matches the document.* family.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except (ImportError, KeyError):
        return max(1, len(text) // 4)


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


class DogfoodCapability(CapabilityBase):
    name = "dogfood"
    home = "memory"

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
        rows = self.ctx.memory.g.query(
            "MATCH (r:Reflection) WHERE r.plan_slug = $slug "
            "AND r.scope = $scope RETURN r",
            {"slug": plan_slug, "scope": "observation"})
        notes = [r["r"]["properties"] for r in rows]
        notes.sort(key=lambda r: r.get("vfrom", 0))
        parts = [f"# DOGFOOD-NOTES — {plan_slug}\n"]
        if not notes:
            parts.append("\n(none yet)\n")
            return {"content": "".join(parts), "count": 0,
                    "omitted": 0, "tokens": _count_tokens("".join(parts)),
                    "plan_slug": plan_slug}
        # Render with mid-loop budget check (sc:sc-analyze F3 review finding).
        rendered_count = 0
        for i, n in enumerate(notes, 1):
            chunk = (
                f"\n**Observation {i} — graph-native**\n\n"
                f"{n.get('text', '')}\n"
            )
            parts.append(chunk)
            rendered_count = i
            if _count_tokens("".join(parts)) > max_tokens * 0.92:
                break
        omitted = max(0, len(notes) - rendered_count)
        if omitted:
            parts.append(
                f"\n_… ({omitted} more observations omitted to fit "
                f"max_tokens={max_tokens})_\n")
        content = "".join(parts)
        return {"content": content, "count": rendered_count,
                "omitted": omitted, "tokens": _count_tokens(content),
                "plan_slug": plan_slug}

    # -----------------------------------------------------------------
    # Spec 017 — collect kept for backward-compat (Spec 014 pipeline).
    # -----------------------------------------------------------------

    @verb(role="transform")
    def collect(self, plan_dir: str = "Plan") -> dict:
        """Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

        Deprecated for ongoing use — prefer ``dogfood.note`` (graph-
        native authoring) + ``dogfood.render`` (markdown projection
        on demand). This verb stays for backward-compatibility with
        Spec 014's observation→spec-amendment pipeline AND for
        one-shot migrations of existing DOGFOOD-NOTES.md files into
        the graph (call this then ``reflect.batch_note`` to seed).

        Returns ``{observations, texts, count, plans, warnings}``:
        - ``observations`` — list of ``{plan, kind, index, title, text}``.
        - ``texts`` — flat list of just the observation bodies (handy for
          chaining into ``reflect.batch_note`` which takes a text list).
        - ``count`` — total observations across all plans.
        - ``plans`` — list of plan-directory names scanned.

        Errors (missing dir, unreadable file) are tolerated and reported
        in a ``warnings`` list rather than raising — this verb is meant to
        feed self-improvement workflows that should degrade gracefully
        when a plan has no DOGFOOD-NOTES.md yet.
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
