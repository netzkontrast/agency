"""dogfood — read observations from the agency's own DOGFOOD-NOTES.md ledger.

A small capability that closes the self-improvement loop: walks a plan
tree (default ``Plan``) for ``DOGFOOD-NOTES.md`` files, parses each for
``**Observation N — TITLE**`` and ``**Dogfood lesson N — TITLE**``
markdown patterns, and returns the observations as data the orchestrator
can fold back into specs or persist via ``reflect.batch_note``.

The capability owns no ontology fragment of its own — observations are
recorded into the graph by ``reflect``, not here. This keeps the
``dogfood`` capability scoped to "read the markdown ledger" (an effect
on the filesystem, not the graph).
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

    @verb(role="transform")
    def collect(self, plan_dir: str = "Plan") -> dict:
        """Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

        Returns ``{observations, texts, count, plans}``:
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
