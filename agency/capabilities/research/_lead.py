"""research.lead — scope the question + plan specialists.

Pure planner. Picks the specialist set based on depth and a
deterministic heuristic over the question shape. Does NOT execute
specialists — that's the walker's next phase via delegate.dispatch.
"""
from __future__ import annotations


_DEPTH_SPECIALISTS = {
    # Spec 044 §"Done When" line 86-90.
    "brief":    ["codebase"],
    "standard": ["codebase", "prior-reflections"],
    "deep":     ["codebase", "prior-reflections", "doc-corpus", "web"],
}


def plan(question: str, depth: str = "standard") -> tuple[list[str], str]:
    """Return (specialists, plan_text) for a research question.

    Adds 'web' to the specialist set when the question mentions
    external concepts (URLs, real-world facts). v1 heuristic: if the
    word 'http' or 'https' appears in the question, add web. Beyond
    that, the depth-driven default set is final.
    """
    specialists = list(_DEPTH_SPECIALISTS.get(depth, _DEPTH_SPECIALISTS["standard"]))
    # If the question explicitly cites a URL, include web.
    if "http" in (question or "").lower() and "web" not in specialists:
        specialists.append("web")
    text = (
        f"plan(depth={depth!r}): {len(specialists)} specialist(s) "
        f"= {', '.join(specialists)}. "
        f"Each specialist runs ONE bounded sub-search; the verifier "
        f"adversarially checks citations before publish."
    )
    return specialists, text
