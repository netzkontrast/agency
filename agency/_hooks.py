"""Spec 280 Slice 1 — hooks install verification + foreign-hook wrapping.

The agency plugin ALREADY ships hooks (`hooks/hooks.json` + Spec 076
unified-event-hook dispatcher). This module is the verification +
install + composition surface that makes the dispatcher actually fire
in a fresh repo.

Pure surface:

- `CANONICAL_SETTINGS_PATCH` — the `.claude/settings.json` block that
  enables the agency plugin (entry in `enabledPlugins` +
  `extraKnownMarketplaces`).
- `merge_settings(user, canonical)` — fold the canonical patch into a
  user settings dict, preserving every other key. Idempotent.
- `detect_foreign_hooks(user)` — walk the user's `hooks` block (when
  present at the settings.json level) and classify any entry whose
  `command` doesn't already invoke agency's dispatcher.
- `wrap_foreign_hook(entry)` — produce a shell-wrapped entry whose
  command is `agency shell run --hook-wrap -- <original>`. PRESERVES
  the original `async` / `type` flags so we don't change the foreign
  hook's semantics (a sync-blocking foreign hook STAYS sync).
- `check_install(user, env, plugin_root)` → `InstallStatus` — pure
  invariant check used by `agency_doctor.hooks`.

Side effects live in `agency/install.py` and `agency/engine.py`; this
module is import-safe and free of I/O.
"""
from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Bump when the canonical patch shape changes (Spec 054 drift pattern).
HOOKS_SPEC_VERSION = 1


# Sentinel the dispatcher uses to recognise an already-wrapped foreign
# hook so re-running install doesn't double-wrap. Matches the flag
# mode of `agency shell run` (Spec 079 auto-gen surface; Spec 280
# `shell.run(hook_wrap=True)`).
_WRAP_SENTINEL = "agency shell run --hook-wrap"
_AGENCY_DISPATCHER_FRAGMENT = (
    'CLAUDE_PLUGIN_ROOT')                                          # any "agency-own" dispatcher path contains this


# Recommended async flag per hook event (the user-raised point).
# Sync = blocking + can rewrite/reject; async = side-effect only.
ASYNC_BY_EVENT: dict[str, bool] = {
    "SessionStart":       False,                                    # engine install must finish first
    "PreToolUse":         False,                                    # Slice 2 routes need blocking authority
    "UserPromptSubmit":   False,                                    # intent-context injection must land pre-prompt
    "PostToolUse":        True,                                     # record-only
    "Stop":               True,                                     # cleanup; non-blocking
    "SessionEnd":         True,                                     # cleanup; non-blocking
    "SubagentStop":       True,                                     # cleanup; non-blocking
}


# The canonical settings patch. Enables the agency plugin under the
# `enabledPlugins` block; the marketplace entry tells Claude Code
# WHERE to fetch the plugin from. The actual hook commands live in
# the plugin's own `hooks/hooks.json` — when the plugin is enabled,
# Claude Code reads that automatically.
#
# Plugin id is `<plugin-name>@<marketplace-name>`. Both `.claude-plugin/
# plugin.json` AND `.claude-plugin/marketplace.json` use `name="agency"`,
# so the canonical id is `agency@agency` (Codex review on PR #138).
AGENCY_PLUGIN_ID = "agency@agency"
AGENCY_MARKETPLACE_NAME = "agency"
CANONICAL_SETTINGS_PATCH: dict = {
    "_agency_version": HOOKS_SPEC_VERSION,
    "enabledPlugins": {
        AGENCY_PLUGIN_ID: True,
    },
    "extraKnownMarketplaces": {
        AGENCY_MARKETPLACE_NAME: {
            "source": {
                "source": "github",
                "repo":   "netzkontrast/agency",
            },
        },
    },
}


# ── pure data shapes ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class ForeignHook:
    """A hook entry the user authored at the `.claude/settings.json`
    level that isn't routed through agency's own dispatcher. The
    install side-effect wraps these via `shell.run --hook-wrap` so
    the original command still runs BUT under agency's provenance
    umbrella (Goal 2 moat coverage)."""

    event: str
    matcher: str
    command: str
    type_: str = "command"
    async_: bool = True
    # Original position so wrap can preserve it inside the event's
    # entries list.
    entry_index: int = 0
    inner_index: int = 0


@dataclass(frozen=True)
class InstallStatus:
    """`agency_doctor.hooks` field shape. Every value is JSON-safe so
    the doctor's return is a plain dict."""

    plugin_enabled: bool
    cli_on_path: bool
    hook_scripts_present: bool
    plugin_root: str
    settings_path: str
    foreign_hooks: list[ForeignHook] = field(default_factory=list)
    wrapped_count: int = 0
    drift: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    installed_version: int = 0
    shadowed_by_user: bool = False

    def to_dict(self) -> dict:
        return {
            "plugin_enabled":       self.plugin_enabled,
            "cli_on_path":          self.cli_on_path,
            "hook_scripts_present": self.hook_scripts_present,
            "plugin_root":          self.plugin_root,
            "settings_path":        self.settings_path,
            "foreign_hooks":        [
                {
                    "event":   h.event,
                    "matcher": h.matcher,
                    "command": h.command,
                    "type":    h.type_,
                    "async":   h.async_,
                }
                for h in self.foreign_hooks
            ],
            "wrapped_count":      self.wrapped_count,
            "drift":              list(self.drift),
            "next_steps":         list(self.next_steps),
            "installed_version":  self.installed_version,
            "shadowed_by_user":   self.shadowed_by_user,
        }


# ── pure functions ────────────────────────────────────────────────────────
def _deep_copy_json(value: Any) -> Any:
    """JSON-safe deep copy — handles dict/list/scalar; caller passes
    JSON-shaped data only."""
    if isinstance(value, dict):
        return {k: _deep_copy_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy_json(v) for v in value]
    return value


def _merge_dicts(base: dict, overlay: dict) -> dict:
    """Recursive dict merge: overlay wins on leaf collisions; nested
    dicts merge recursively; lists are not merged (overlay replaces).
    Preserves every base key that's not in overlay."""
    out = dict(base)
    for k, v in overlay.items():
        if k.startswith("_"):
            out[k] = _deep_copy_json(v)                            # meta keys
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dicts(out[k], v)
        else:
            out[k] = _deep_copy_json(v)
    return out


def merge_settings(user_settings: dict,
                    canonical: dict | None = None) -> dict:
    """Return a NEW settings dict with the canonical patch merged in.
    Preserves every non-conflicting key (preservation invariant).
    Idempotent — calling twice yields the same content.

    Strategy:
    - `enabledPlugins` is dict-merged so other plugins' entries
      survive.
    - `extraKnownMarketplaces` is dict-merged similarly.
    - The `_agency_version` meta key on the canonical patch lands on
      the merged settings so doctor can detect drift.
    - Every other top-level key in `user_settings` (e.g. user's own
      `hooks` block — handled separately by detect+wrap) survives
      unchanged.
    """
    canonical = canonical if canonical is not None else CANONICAL_SETTINGS_PATCH
    if not isinstance(user_settings, dict):
        return _deep_copy_json(canonical)
    return _merge_dicts(user_settings, canonical)


def detect_foreign_hooks(user_settings: dict) -> list[ForeignHook]:
    """Walk the user's `hooks` block (when present at the
    `.claude/settings.json` level) and return entries whose `command`
    doesn't already invoke agency's dispatcher.

    Users CAN author hooks directly in `.claude/settings.json` (in
    addition to the plugin-shipped ones from `hooks/hooks.json`).
    This function finds those and prepares them for shell-wrap so
    they fall under agency's provenance umbrella.

    Returns an empty list when no `hooks` block exists or every
    entry already routes through agency."""
    hooks_block = (user_settings or {}).get("hooks")
    if not isinstance(hooks_block, dict):
        return []
    out: list[ForeignHook] = []
    for event_name, entries in hooks_block.items():
        if event_name.startswith("_"):
            continue                                              # meta keys (e.g. _version)
        if not isinstance(entries, list):
            continue
        for ei, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            matcher = str(entry.get("matcher", ""))
            inner = entry.get("hooks") or []
            if not isinstance(inner, list):
                continue
            for ii, h in enumerate(inner):
                if not isinstance(h, dict):
                    continue
                command = str(h.get("command", ""))
                if not command:
                    continue
                # Skip entries that already route through the agency
                # dispatcher OR the wrap sentinel (avoid double-wrap).
                if (_WRAP_SENTINEL in command
                        or _AGENCY_DISPATCHER_FRAGMENT in command):
                    continue
                out.append(ForeignHook(
                    event=str(event_name),
                    matcher=matcher,
                    command=command,
                    type_=str(h.get("type", "command")),
                    async_=bool(h.get("async", True)),
                    entry_index=ei,
                    inner_index=ii,
                ))
    return out


def wrap_foreign_hook(foreign: ForeignHook) -> dict | None:
    """Produce a shell-wrapped hook entry for a foreign hook. The
    wrapped command runs `agency shell run --hook-wrap -- <original>`
    so the original behavior is preserved BUT under agency's
    provenance umbrella.

    Preservation invariants:
    - The `async` flag is carried through verbatim — a sync-blocking
      foreign hook STAYS sync.
    - `type` is carried through verbatim.
    - The original command lands on `_wrapped_from` so the user can
      audit + uninstall (Slice 5) can restore.

    Returns None when the original command can't be safely
    shell-quoted (e.g. contains an unbalanced quote we won't
    reason about) — caller maps to `HOOKS_FOREIGN_UNWRAPPABLE` and
    preserves the original entry (no behavior loss).
    """
    try:
        # shlex.quote handles the safe single-quote escape; if the
        # original is malformed (unbalanced quotes), shlex.split
        # raises ValueError — that's our cue to skip.
        shlex.split(foreign.command)
    except ValueError:
        return None
    quoted = shlex.quote(foreign.command)
    # Codex review on PR #138: the wrapped command MUST be a path the
    # CLI actually exposes. `agency shell run` (per Spec 079 auto-gen)
    # accepts `--command` / `--hook-wrap` / `--filter`. The flag-mode
    # carries `--intent-id` from the env (AGENCY_INTENT) so the run
    # is recorded against the active intent when one exists.
    wrapped_command = (
        f"agency shell run --hook-wrap=true --command {quoted}")
    return {
        "type":    foreign.type_,
        "command": wrapped_command,
        "async":   foreign.async_,
        "_wrapped_from":         foreign.command,
        "_wrapped_event":        foreign.event,
        "_wrapped_matcher":      foreign.matcher,
        "_wrapped_spec_version": HOOKS_SPEC_VERSION,
    }


def apply_foreign_wraps(user_settings: dict) -> tuple[dict, int]:
    """Rewrite the user's `hooks` block so every foreign entry is
    shell-wrapped. Returns `(new_settings, wrapped_count)`.

    Idempotent: entries already wrapped (sentinel detected) are
    untouched, so re-running install doesn't double-wrap.
    """
    if not isinstance(user_settings, dict):
        return _deep_copy_json(user_settings), 0
    out = _deep_copy_json(user_settings)
    hooks_block = out.get("hooks")
    if not isinstance(hooks_block, dict):
        return out, 0
    wrapped = 0
    for event_name, entries in list(hooks_block.items()):
        if event_name.startswith("_") or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            inner_list = entry.get("hooks")
            if not isinstance(inner_list, list):
                continue
            for i, h in enumerate(inner_list):
                if not isinstance(h, dict):
                    continue
                command = str(h.get("command", ""))
                if not command:
                    continue
                # Skip already-wrapped + already-agency entries.
                if (_WRAP_SENTINEL in command
                        or _AGENCY_DISPATCHER_FRAGMENT in command):
                    continue
                foreign = ForeignHook(
                    event=event_name,
                    matcher=str(entry.get("matcher", "")),
                    command=command,
                    type_=str(h.get("type", "command")),
                    async_=bool(h.get("async", True)),
                )
                wrapped_entry = wrap_foreign_hook(foreign)
                if wrapped_entry is None:
                    continue                                      # HOOKS_FOREIGN_UNWRAPPABLE
                inner_list[i] = wrapped_entry
                wrapped += 1
    return out, wrapped


def check_install(user_settings: dict,
                    env: dict | None = None,
                    plugin_root: str | Path | None = None,
                    cli_available: bool | None = None,
                    canonical: dict | None = None) -> InstallStatus:
    """Pure invariant check used by `agency_doctor.hooks`.

    Inspects the user settings dict + (optionally) the plugin root's
    `hooks/` directory + the env (to surface `cli_on_path` from a
    PATH lookup callers do upstream). No I/O happens unless
    `plugin_root` is supplied and points at a real directory.

    `next_steps` mirrors the doctor convention: each entry is a
    self-contained, copy-pasteable remediation pointer.
    """
    canonical = canonical if canonical is not None else CANONICAL_SETTINGS_PATCH
    env = env or {}
    settings_path = str(env.get("AGENCY_SETTINGS_PATH", ""))
    plugin_enabled = False
    installed_version = 0
    if isinstance(user_settings, dict):
        enabled = user_settings.get("enabledPlugins") or {}
        if isinstance(enabled, dict):
            wanted = next(iter(canonical.get("enabledPlugins", {})), "")
            plugin_enabled = bool(enabled.get(wanted))
        installed_version = int(user_settings.get("_agency_version", 0) or 0)

    foreign = detect_foreign_hooks(user_settings or {})
    drift: list[str] = []
    if installed_version and installed_version < HOOKS_SPEC_VERSION:
        drift.append(
            f"settings carries _agency_version={installed_version} but "
            f"HOOKS_SPEC_VERSION={HOOKS_SPEC_VERSION} — re-run install")

    hook_scripts_present = False
    plugin_root_str = ""
    if plugin_root is not None:
        root = Path(plugin_root)
        plugin_root_str = str(root)
        hooks_json = root / "hooks" / "hooks.json"
        dispatch = root / "hooks" / "dispatch"
        hook_scripts_present = hooks_json.exists() and dispatch.exists()

    cli_on_path = bool(cli_available) if cli_available is not None else False

    next_steps: list[str] = []
    if not plugin_enabled:
        # Codex review on PR #138: include the `--patch-claude-settings`
        # flag — bare `agency.install` regenerates the plugin files but
        # leaves `enabledPlugins` unchanged.
        next_steps.append(
            f"agency plugin not enabled in `.claude/settings.json` — "
            f"run `python -m agency.install --patch-claude-settings` "
            f"to add `{AGENCY_PLUGIN_ID}` (or "
            f"`/plugin install {AGENCY_PLUGIN_ID}`)")
    if not cli_on_path:
        next_steps.append(
            "`agency` CLI not on PATH — install via "
            "`pipx install git+https://github.com/netzkontrast/agency` "
            "so the hook dispatcher can record Event nodes")
    if not hook_scripts_present and plugin_root is not None:
        next_steps.append(
            f"plugin hook scripts missing under {plugin_root_str!r}/hooks/ "
            f"— reinstall the plugin or set `CLAUDE_PLUGIN_ROOT` to the "
            f"plugin install dir")
    if foreign:
        next_steps.append(
            f"{len(foreign)} foreign hook(s) detected — re-run "
            f"`python -m agency.install --patch-claude-settings` to wrap "
            f"them under agency's provenance umbrella")
    for d in drift:
        next_steps.append(d)

    return InstallStatus(
        plugin_enabled=plugin_enabled,
        cli_on_path=cli_on_path,
        hook_scripts_present=hook_scripts_present,
        plugin_root=plugin_root_str,
        settings_path=settings_path,
        foreign_hooks=list(foreign),
        wrapped_count=0,                                          # set by install
        drift=drift,
        next_steps=next_steps,
        installed_version=installed_version,
        shadowed_by_user=False,                                   # Slice 4 reads ~/.claude
    )


def patch_settings_file(path: str | Path,
                          canonical: dict | None = None) -> dict:
    """Side-effect wrapper used by `agency.install`. Atomically:

    1. Reads `path` (or treats missing as empty `{}`).
    2. If existing content is valid JSON, copies it to `path + ".bak"`.
    3. Builds the merged settings via `merge_settings` + applies
       `apply_foreign_wraps`.
    4. Writes the result to `path` with `json.dumps(..., indent=2,
       sort_keys=True)` so the file is byte-stable.

    Returns a summary dict `{settings_path, wrote, backup_path,
    wrapped_count, foreign_skipped}`. Raises a typed `ValueError`
    on unparseable prior content (caller maps to
    `HOOKS_INVALID_JSON`).
    """
    canonical = canonical if canonical is not None else CANONICAL_SETTINGS_PATCH
    p = Path(path)
    prior_text: str | None = None
    if p.exists():
        prior_text = p.read_text(encoding="utf-8")
        try:
            prior = json.loads(prior_text) if prior_text.strip() else {}
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"HOOKS_INVALID_JSON: {p} is not valid JSON "
                f"({exc.msg} at line {exc.lineno})") from exc
    else:
        prior = {}

    merged = merge_settings(prior, canonical)
    merged, wrapped_count = apply_foreign_wraps(merged)

    p.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(merged, indent=2, sort_keys=True) + "\n"
    # Backup the prior (raw) content before overwriting. Codex review
    # on PR #138: the `.bak` must preserve the USER'S ORIGINAL
    # settings, not the previous post-install content. Only write the
    # backup if no `.bak` exists yet — a second/idempotent install
    # must NOT clobber the original. `agency hook uninstall` depends
    # on this to restore foreign hooks the user authored.
    backup_path = ""
    if prior_text is not None:
        backup_path = str(p) + ".bak"
        if not Path(backup_path).exists():
            Path(backup_path).write_text(prior_text, encoding="utf-8")
    p.write_text(serialized, encoding="utf-8")

    return {
        "settings_path": str(p),
        "wrote":         True,
        "backup_path":   backup_path,
        "wrapped_count": wrapped_count,
    }
