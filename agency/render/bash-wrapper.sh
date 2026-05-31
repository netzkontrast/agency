#!/usr/bin/env bash
# agency-generated: v$gen_version — capability_${cap_name}_${verb_name}
# $brief
# Usage: $usage
set -euo pipefail

iid="$${AGENCY_INTENT_ID:-}"
args=()
while [ $$# -gt 0 ]; do
  case "$$1" in
    --intent-id) iid="$$2"; shift 2;;
    --) shift; args+=("$$@"); break;;
    *) args+=("$$1"); shift;;
  esac
done

if [ -z "$$iid" ]; then
  echo "error: --intent-id or AGENCY_INTENT_ID required" >&2
  exit 1
fi

$arg_check

kwargs=$$(python3 -c '
import json, sys
print(json.dumps({$kwargs_pairs}))
' "$$iid" "$${args[@]}") || { echo "error: failed to build kwargs JSON" >&2; exit 3; }

exec python -m agency.cli execute --code "
import json
return await call_tool('capability_${cap_name}_${verb_name}', json.loads(r'''$${kwargs}'''))
"
