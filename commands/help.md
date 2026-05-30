---
description: Use when you want to list the agency capabilities and their verbs.
---

Map the agency engine's capabilities (macroskills) to their verbs (micro-skills). Use the plugin's `bin/agency` wrapper — it resolves the plugin venv + PYTHONPATH so the `agency` package is always importable (plain `python -m agency.cli` would fail in the user's project interpreter). Bootstrap an intent, then call the help verb with its id:

    AGENCY="${CLAUDE_PLUGIN_ROOT}/bin/agency"
    iid=$("$AGENCY" --db agency.db intent --purpose help --deliverable map --acceptance ok | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    "$AGENCY" --db agency.db execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

