"""Spec 280 Slice 1 — Claude Code hooks (canonical block + check + merge).

The agency plugin is most powerful when Claude Code's hooks route raw
tools through the capability surface. Without hooks, the AI calls
`git commit` / `pytest` / `Edit` directly and the provenance moat
leaks (no Invocation, no Artefact, no SERVES edge).

This module is the single source of truth for what hooks SHOULD be
wired and provides pure functions for:

- `merge_hooks_into_settings(settings)` — fold the canonical hooks
  into an existing settings dict, preserving every other key.
- `check_hooks(settings)` → `HookStatus` — invariant check used by
  `agency_doctor`.

Slice 1 hooks are ADVISORY (exit 0, stderr suggestion). Slice 2
promotes the clearest routes to blocking per Spec 058 WARN→error
doctrine once the bypass-rate baseline is established.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Bump when the canonical block shape changes (Spec 054 drift pattern).
# Doctor surfaces drift when an installed block reports an older version.
HOOKS_VERSION = 1


# The canonical hooks block — matches Claude Code's settings.json schema.
# Commands are POSIX bash and use $CLAUDE_PROJECT_DIR for portability so
# a clone in any directory still resolves the script.
CANONICAL_HOOKS: dict = {
    "_version": HOOKS_VERSION,
    "PreToolUse": [
        {
            "matcher": "Bash",
            "hooks": [{
                "type":    "command",
                "command": (
                    'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/'
                    'bash-pretool.sh"'),
            }],
        },
        {
            "matcher": "Edit|Write",
            "hooks": [{
                "type":    "command",
                "command": (
                    'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/'
                    'edit-pretool.sh"'),
            }],
        },
    ],
    "SessionStart": [
        {
            "hooks": [{
                "type":    "command",
                "command": (
                    'bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/'
                    'session-start.sh"'),
            }],
        },
    ],
}


@dataclass(frozen=True)
class HookStatus:
    """The doctor's hooks report. `enabled` is True only when every
    canonical event/matcher is present in the live settings; `missing`
    lists the event names that aren't wired; `drift` lists names whose
    matcher set differs from the canonical."""

    enabled: bool
    missing: list[str] = field(default_factory=list)
    drift: list[str] = field(default_factory=list)
    installed_version: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled":           self.enabled,
            "missing":           list(self.missing),
            "drift":             list(self.drift),
            "installed_version": self.installed_version,
        }


def _matchers_of(event_entries: list[dict]) -> set[str]:
    """Collect the `matcher` values across an event's entries. Entries
    without a matcher count as a wildcard `""` so SessionStart (which
    has no matcher) is comparable across the canonical + installed
    blocks."""
    out: set[str] = set()
    for entry in event_entries or []:
        if isinstance(entry, dict):
            out.add(str(entry.get("matcher", "")))
    return out


def check_hooks(settings: dict,
                 canonical: dict | None = None) -> HookStatus:
    """Pure invariant check: does `settings` carry every canonical
    hook event with the expected matcher set?

    `enabled` is True ONLY when every canonical event is present AND
    every canonical matcher under it is wired. Extra matchers (user
    additions) don't break enabled; they're orthogonal.
    """
    canonical = canonical or CANONICAL_HOOKS
    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    if not isinstance(hooks, dict):
        return HookStatus(
            enabled=False,
            missing=[k for k in canonical if not k.startswith("_")],
            installed_version=0,
        )
    missing: list[str] = []
    drift: list[str] = []
    for event_name, canonical_entries in canonical.items():
        if event_name.startswith("_"):
            continue                                              # meta keys
        installed = hooks.get(event_name)
        if not isinstance(installed, list) or not installed:
            missing.append(event_name)
            continue
        installed_matchers = _matchers_of(installed)
        wanted_matchers = _matchers_of(canonical_entries)
        if not wanted_matchers.issubset(installed_matchers):
            drift.append(event_name)
    installed_version = int(hooks.get("_version", 0) or 0)
    return HookStatus(
        enabled=(not missing and not drift),
        missing=missing,
        drift=drift,
        installed_version=installed_version,
    )


def merge_hooks_into_settings(settings: dict,
                                canonical: dict | None = None) -> dict:
    """Return a NEW settings dict with the canonical hooks block
    merged in. Preserves every non-`hooks` key. Idempotent — calling
    twice yields a byte-identical result.

    Merge strategy:
    - The canonical event entries REPLACE same-name installed entries
      keyed by matcher (so re-running install resets the canonical
      hooks to known-good without duplicating).
    - Installed entries with matchers NOT in the canonical set
      survive — user additions are preserved.
    - The `_version` key on the canonical block lands on
      `settings["hooks"]["_version"]` so doctor can detect drift.
    """
    canonical = canonical or CANONICAL_HOOKS
    out = dict(settings) if isinstance(settings, dict) else {}
    hooks = dict(out.get("hooks") or {})
    # Carry the canonical version forward (and overwrite any prior).
    hooks["_version"] = canonical.get("_version", HOOKS_VERSION)
    for event_name, canonical_entries in canonical.items():
        if event_name.startswith("_"):
            continue
        canonical_matchers = _matchers_of(canonical_entries)
        installed_entries = hooks.get(event_name) or []
        # Drop installed entries whose matcher is canonical — the
        # canonical entry will be re-added (idempotent overwrite).
        kept: list[dict] = [
            e for e in installed_entries
            if isinstance(e, dict)
            and str(e.get("matcher", "")) not in canonical_matchers
        ]
        # Append canonical entries (deep-copied so the consumer can
        # safely mutate without poisoning the module-level constant).
        merged: list[dict] = kept + [
            {k: _deep_copy_json(v) for k, v in entry.items()}
            for entry in canonical_entries
        ]
        hooks[event_name] = merged
    out["hooks"] = hooks
    return out


def _deep_copy_json(value):
    """Cheap JSON-safe deep copy — handles dict/list/scalar; refuses
    to recurse into anything more exotic (callers pass JSON-shaped
    data only)."""
    if isinstance(value, dict):
        return {k: _deep_copy_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy_json(v) for v in value]
    return value
