---
description: Use when you want to list the agency capabilities and their verbs.
---

Map the agency engine's capabilities (macroskills) to their verbs (micro-skills). Bootstrap an intent, then call the help verb with its id:

    iid=$(python -m agency.cli --db agency.db intent --purpose help --deliverable map --acceptance ok | python -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    python -m agency.cli --db agency.db execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

