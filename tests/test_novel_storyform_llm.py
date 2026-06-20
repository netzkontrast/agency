import pytest
from agency.capabilities.novel.llm_assist import suggest_storyform, AssistCodes

def test_suggest_storyform_converges():
    responses = [
        {"storyform": {"fail_check": "OS-throughline-consistency"}}, # round 1 fails
        {"storyform": {"mc_resolve": "Change", "os_outcome": "Success"}} # round 2 passes
    ]
    res = suggest_storyform("mock premise", mock_driver_responses=responses)

    assert res.ok is True
    assert res.data["iterations"] == 2
    assert res.data["coherent"] is True
    assert res.data["checks"][0]["name"] == "OS-throughline-consistency"

def test_suggest_storyform_dual_partner():
    responses = [
        {"storyform": {"mc_resolve": "Change", "os_outcome": "Success"}}
    ]
    res = suggest_storyform("mock premise", dual=True, mock_driver_responses=responses)
    assert res.data["dual_partner"] is not None
    assert res.data["dual_partner"]["mc_resolve"] == "Steadfast"
    assert res.data["dual_partner"]["os_outcome"] == "Failure"

def test_suggest_storyform_ontology_missing():
    responses = [
        {"hallucinated_label": "Stagnation"}
    ]
    res = suggest_storyform("mock premise", mock_driver_responses=responses)
    assert res.ok is False
    assert res.error.code == AssistCodes.ONTOLOGY_MISSING

def test_suggest_storyform_nonconvergent():
    responses = [
        {"storyform": {"fail_check": "OS-throughline-consistency"}} # always fails
    ]
    res = suggest_storyform("mock premise", mock_driver_responses=responses)
    assert res.ok is False
    assert res.error.code == AssistCodes.STORYFORM_NONCONVERGENT
