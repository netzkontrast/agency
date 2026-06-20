import json
from typing import Any, Dict, List, Optional, Literal
from agency.toolresult import ToolResult, TypedError

MAX_REPAIR_ROUNDS = 5

class AssistCodes:
    STORYFORM_NONCONVERGENT = "STORYFORM_NONCONVERGENT"
    ONTOLOGY_MISSING = "ONTOLOGY_MISSING"

# Mock registry for checks
MOCK_CHECKS_REGISTRY = [
    "OS-throughline-consistency",
    "MC-resolve",
    "theme-validation"
]

def check_storyform_coherence(storyform: Dict[str, Any]) -> ToolResult:
    # This is a mock coherence checker
    # If the storyform has a "fail_check" field, it fails that check
    checks_result = []
    coherent = True

    for check in MOCK_CHECKS_REGISTRY:
        if storyform.get("fail_check") == check:
            checks_result.append({"name": check, "pass": False, "evidence": "Mock failed check"})
            coherent = False
        else:
            checks_result.append({"name": check, "pass": True, "evidence": "Mock passed check"})

    return ToolResult(data={"coherent": coherent, "checks": checks_result})

def suggest_storyform(premise: str, dual: bool = False, driver: Literal["spec147", "fake"] = "fake", mock_driver_responses: Optional[List[Dict[str, Any]]] = None) -> ToolResult:
    """
    Spec 219
    Proposes an NCP storyform using the given driver. Iterates against novel_coherence_check
    until coherent or MAX_REPAIR_ROUNDS is reached.
    """
    iterations = 0
    storyform = {}
    checks = []

    # Simple loop
    while iterations < MAX_REPAIR_ROUNDS:
        iterations += 1

        # Call mock driver
        if mock_driver_responses:
            if len(mock_driver_responses) >= iterations:
                response = mock_driver_responses[iterations - 1]
            else:
                response = mock_driver_responses[-1]

            if "hallucinated_label" in response:
                return ToolResult(
                    data=None,
                    ok=False,
                    error=TypedError(code=AssistCodes.ONTOLOGY_MISSING, message=f"Unknown label: {response['hallucinated_label']}")
                )

            storyform = response.get("storyform", {})
        else:
            # Default fallback mock response
            storyform = {"mc_resolve": "Change", "os_outcome": "Success"}

        check_res = check_storyform_coherence(storyform)
        checks = check_res.data["checks"]

        if check_res.data["coherent"]:
            break

    if not check_res.data["coherent"]:
        return ToolResult(
            data=None,
            ok=False,
            error=TypedError(
                code=AssistCodes.STORYFORM_NONCONVERGENT,
                message="Could not converge on a coherent storyform"
            ),
            # Return last failing check set as evidence via warnings or similar, or just attach to error
        )

    dual_partner = None
    if dual:
        dual_partner = dict(storyform)
        if dual_partner.get("mc_resolve") == "Change":
            dual_partner["mc_resolve"] = "Steadfast"
        else:
            dual_partner["mc_resolve"] = "Change"

        if dual_partner.get("os_outcome") == "Success":
            dual_partner["os_outcome"] = "Failure"
        else:
            dual_partner["os_outcome"] = "Success"

    return ToolResult(
        data={
            "intent_id": "mock_intent",
            "storyform": storyform,
            "coherent": True,
            "iterations": iterations,
            "checks": checks,
            "dual_partner": dual_partner,
            "driver": driver,
            "refusal": None
        }
    )
