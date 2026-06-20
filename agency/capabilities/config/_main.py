"""config — read & persist unified .agency/config.yaml values.

Config exposes get / set / list over the unified config resolver so an agent or
the CLI can inspect and change agency configuration without hand-editing the
file. Precedence is env over file over default; secrets stay env-only and are
never written to the file. Thin by design — all logic lives in agency._config;
these verbs are the user-facing surface over it.

Use when: you need to read or change an agency config value (e.g. frugal.level, a
capability's setting) from the agent surface or CLI instead of editing
.agency/config.yaml by hand.
Triggers:
- "what is <key> set to / where does its value come from"
- "set <key> to <value>" / "turn frugal to lite"
- "list all config and their sources"
Red flags:
- Writing a secret such as an API key → config refuses; set the env var instead.
"""
from __future__ import annotations

from ... import _config
from ...capability import CapabilityBase, verb


class ConfigCapability(CapabilityBase):
    name = "config"
    home = "capability"   # configures the capability substrate; records no graph artefacts

    @verb(role="act")
    def get(self, key: str) -> dict:
        """Resolve a config key to its live value + source.

        Inputs: key (str — dotted ``section.name``).
        Returns: ``{key, value, source}`` where source is ``env`` / ``file`` /
        ``default``; an unregistered key returns ``{error, key}`` (no traceback).
        """
        _config._ensure_all_registered()      # so any capability key resolves
        try:
            r = _config.config_resolve(key)
        except KeyError as exc:
            return {"error": str(exc), "key": key}
        return {"key": key, "value": r["value"], "source": r["source"]}

    @verb(role="act")
    def set(self, key: str, value: str) -> dict:
        """Persist a config value to ``.agency/config.yaml``, then re-resolve it.

        Inputs: key (str — dotted ``section.name``), value (str).
        Returns: ``{key, value, source}`` after the write. Refuses an unregistered
        key and a secret (env-only) with a clean ``{error, key}`` — secrets are
        never written to the file.
        """
        _config._ensure_all_registered()
        if _config._lookup(key) is None:
            return {"error": f"unregistered config key: {key!r}", "key": key}
        try:
            _config.config_set(key, value)
        except ValueError as exc:             # secret refusal at the trust boundary
            return {"error": str(exc), "key": key}
        r = _config.config_resolve(key)
        return {"key": key, "value": r["value"], "source": r["source"]}

    @verb(role="act")
    def list(self) -> dict:
        """Every registered config key → value + source, plus validation issues.

        Returns: ``{values: {key: {value, source}}, issues: [...]}``. Secrets are
        redacted to presence (``set`` / ``unset``) — the literal is never reported.
        """
        return {"values": _config.config_report(), "issues": _config.config_validate()}
