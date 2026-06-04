"""Jules dispatch-prompt preambles + Mode A/B assembler (Spec 013 Phase 2).

Per ``Plan/013-…/DESIGN.md`` "Design — `_jules_preambles.py`":

- **One canonical preamble** (``PREAMBLE``) carrying the per-dispatch
  must-name tool list + a literal pointer to AGENTS.md + AGENCY_PROTOCOL.md.
- The doctrine (the five invariants from ``AGENCY_PROTOCOL.md``) lives at
  the repo root and is paid for once per snapshot / clone — NOT once per
  dispatch.
- ``assemble(source, starting_branch, prompt, preset_name=...)`` chooses
  Mode A (dogfood, ``source == DISPATCH_SELF_SOURCE``) vs Mode B
  (delegate, anything else). Mode A relies on Jules's lexical scoping to
  pick up the root docs. Mode B prepends an explicit READ-ONLY clone
  instruction.

Underscore-prefixed file — skipped by capability discovery; called
directly by ``_jules_api.jules_create`` when ``protocol_preset`` is set.
"""
from __future__ import annotations

__all__ = [
    "DISPATCH_SELF_SOURCE",
    "DISPATCH_PROTOCOL_SOURCE_URL",
    "AGENCY_CLONE_PATH",
    "PREAMBLE",
    "REVIEW_COMMENT_TAIL",
    "assemble",
    "lint_must_name",
    "review_comment",
]

# Configurable via env in __main__ wiring; module-level for tests.
DISPATCH_SELF_SOURCE: str = "netzkontrast/agency"
DISPATCH_PROTOCOL_SOURCE_URL: str = "https://github.com/netzkontrast/agency.git"
AGENCY_CLONE_PATH: str = "~/work/vendor/agency"

# The five canonical Jules tools — see AGENCY_PROTOCOL.md §2.
_MUST_NAME_TOOLS: list[str] = [
    "pre_commit_instructions",
    "submit",
    "request_user_input",
    "replace_with_git_merge_diff",
    "request_code_review",
]


PREAMBLE: str = (
    "# Agency dispatch — canonical preamble\n"
    "\n"
    "Before drafting any plan, read the doctrine docs at the agency repo root:\n"
    "- AGENTS.md (repo conventions; verify via `git ls-remote`, never local HEAD).\n"
    "- AGENCY_PROTOCOL.md (remote-async-agent doctrine; COMPLETED ≠ done).\n"
    "\n"
    "Use these tool symbols literally in your work — prose alone leaves "
    "work in the VM (the silent-fail mode):\n"
    "- `pre_commit_instructions()` — mandatory pre-flight before submit.\n"
    "- `submit(branch_name, commit_message, title, description)` — the ONE\n"
    "  tool that publishes work to remote. Always name it literally.\n"
    "- `request_user_input(message)` — blocking ask. NEVER `message_user` for\n"
    "  questions.\n"
    "- `replace_with_git_merge_diff` — preferred multi-line edit primitive.\n"
    "- `request_code_review()` — triggers the Jules Critic before submit.\n"
    "- `reply_to_pr_comments(...)` — if you are responding to PR review\n"
    "  feedback, after `submit(...)` you MUST also call this to post a\n"
    "  one-paragraph summary on the review thread. The watching session\n"
    "  subscribes to PR-comment events; without your reply it is blind to\n"
    "  your push until the next poll (AGENCY_PROTOCOL.md §9).\n"
    "\n"
    "Scope is a hard allow-list: if you need a path outside the spec's "
    "`affects:`, emit a `BLOCKED:` PR explaining what extra paths are needed "
    "and stop. Don't silently expand scope.\n"
    "\n"
    "Verify before declaring done: `git ls-remote origin <branch>` is the "
    "source of truth — never trust local HEAD or in-chat SHAs.\n"
)


def _mode_b_clone_block() -> str:
    """The Mode-B-only prepend: clone agency READ-ONLY + read both docs."""
    return (
        "# Mode B (delegate) — read agency doctrine first\n"
        "\n"
        "You are working in another project (the dispatch `source`). The "
        "agency repo is REFERENCE ONLY. Before drafting any plan:\n"
        "\n"
        "```bash\n"
        f"git clone --depth=1 {DISPATCH_PROTOCOL_SOURCE_URL} {AGENCY_CLONE_PATH}\n"
        "```\n"
        "\n"
        "Then read both root docs:\n"
        f"- `read_file('{AGENCY_CLONE_PATH}/AGENTS.md')`\n"
        f"- `read_file('{AGENCY_CLONE_PATH}/AGENCY_PROTOCOL.md')`\n"
        "\n"
        f"Writes happen in the target repo (`source`) only — NEVER in "
        f"{AGENCY_CLONE_PATH}. The agency clone is read-only.\n"
        "\n"
    )


def assemble(
    source: str,
    starting_branch: str,
    prompt: str,
    preset_name: str = "agency-default",
) -> str:
    """Assemble the dispatch text.

    Mode A (``source == DISPATCH_SELF_SOURCE``): prepend ``PREAMBLE`` only.
    AGENTS.md + AGENCY_PROTOCOL.md are inherited via Jules's lexical
    scoping (`_jules_reference.md §2`).

    Mode B (any other source): prepend the explicit clone block + ``PREAMBLE``.
    Jules clones agency READ-ONLY into ``AGENCY_CLONE_PATH`` and reads
    both root docs before drafting the plan.

    `preset_name` is currently always ``"agency-default"`` (the single
    preset per Spec 013 Phase C REVIEW must-fix #1). Reserved for future
    presets when a real distinct caller materialises.

    Raises ``ValueError`` on an unknown preset (forward-compat safety).
    """
    if preset_name != "agency-default":
        raise ValueError(
            f"unknown protocol_preset: {preset_name!r}; "
            f"only 'agency-default' is supported (spec 013 Phase D)"
        )

    if source == DISPATCH_SELF_SOURCE:
        return f"{PREAMBLE}\n---\n{prompt}"

    return f"{_mode_b_clone_block()}{PREAMBLE}\n---\n{prompt}"


REVIEW_COMMENT_TAIL: str = (
    "\n\n"
    "---\n"
    "After you push the fix, **REPLY to this thread via "
    "`reply_to_pr_comments(...)`** with a one-paragraph summary of what you "
    "addressed (and what you deferred). This is how this session learns your "
    "changes landed — without the reply we are blind to your push until the "
    "next poll (AGENCY_PROTOCOL.md §9).\n"
)


def review_comment(body: str) -> str:
    """Compose an @jules-style review-comment body with the mandatory tail.

    Per AGENCY_PROTOCOL.md §9: every agency-posted PR review comment MUST
    end with the explicit `reply_to_pr_comments(...)` instruction. The
    tail is the wake mechanism — without it, the watching session is
    blind to Jules's push until the next poll.

    Idempotent: if ``body`` already contains the tail, it is returned
    unchanged. This makes the helper safe to apply twice (e.g. once at
    draft time, once at post time).
    """
    if REVIEW_COMMENT_TAIL.strip() in body:
        return body
    return body.rstrip() + REVIEW_COMMENT_TAIL


def lint_must_name(text: str, must_name: list[str] | None = None) -> dict:
    """Predicate: does ``text`` literally name every canonical tool?

    Returns ``{"ok": bool, "missing": [str], "extras": [str]}``. ``extras``
    is informational — tools named in the prompt but NOT in the canonical
    must-name set. (A prompt naming additional Jules tools is fine; it's
    naming *fewer* than the canon that risks silent-fail.)

    Used by ``jules.lint_prompt`` (Phase 3) — and the canonical must-name
    list is exposed here so callers don't need to duplicate it.
    """
    must = must_name if must_name is not None else _MUST_NAME_TOOLS
    missing = [t for t in must if t not in text]
    # extras: any of the *full* canon set that's named but isn't in the
    # caller's reduced must-name list (rare; here for completeness).
    extras = [
        t for t in _MUST_NAME_TOOLS if t in text and t not in must
    ]
    return {"ok": not missing, "missing": missing, "extras": extras}
