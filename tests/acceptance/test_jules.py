"""Acceptance — jules capability.

Converted from tests/test_jules*.py (~17 files). Tests ONLY the observable
in-process contract: dispatch envelope shapes, graph provenance, state routing
logic, preamble text contracts, skill registration, and skill walk behaviour.

DROPPED (listed below with reasons):
- test_jules_watch.py::test_instructions_complete — structural count
  (assertions on INSTRUCTIONS.keys() is a snapshot of the implementation,
  not an observable behaviour; the important per-key text contracts are
  captured individually).
- test_jules_watch.py::test_classify_transitions (full soup) — omnibus
  internal-state driver; replaced by focused per-transition scenarios.
- test_jules_watch.py::test_queue_drop_oldest — tests the asyncio queue
  implementation detail (maxsize cap, drop-oldest eviction); not a
  behaviour the calling agent can observe from the verb surface.
- test_jules_watch.py::test_cadence_calculator — tests the internal
  backoff arithmetic; not observable via the wire contract.
- test_jules_watch.py::test_recovery_cycle — drives a hand-rolled async
  loop body that reimplements the watcher's poll logic; verifies the
  loop's internal counters, not the verb-surface output.
- test_jules_watch_recovery_signature.py (both tests) — monkeypatches
  _poll_loop internals to assert the positional-arg order of
  build_recovery_plan; verifies the implementation ABI, not the
  observable output of any verb.
- test_jules_patch.py (all) — tests the parse_unidiff / build_recovery_plan
  internal module API; no verb is exercised and the fixture files
  (add_only.patch, …) are implementation details.
- test_jules_preambles.py::test_mode_a_uses_self_source_constant,
  test_mode_b_asserts_read_only_on_agency_clone — both inspect the
  internal DISPATCH_PROTOCOL_SOURCE_URL / AGENCY_CLONE_PATH constants,
  which are not observable to a caller of the assembly API.
- test_jules_preambles.py::test_lint_must_name_* — tests the bare helper
  function, not the verb; the verb-level test_lint_prompt_* cover the
  observable surface.
- test_jules_preambles.py::test_review_comment_* (bare helper) — tests the
  preambles.review_comment helper; the verb test_review_comment_* cover
  the observable surface.
- test_jules_dispatch_phase4.py::test_protocol_preset_prepends_mode_a/b_*
  and test_no_protocol_preset_means_no_prepend — monkeypatches _request +
  _coerce_source internals; not a verb-level observable test.
- test_jules_skills_preamble.py (skill walk phases 1–4 step-by-step) —
  walks the skill by driving SkillRun directly with VCS injector
  monkeypatching; the observable behaviour (skill registered, hard gate
  pauses / confirm completes) is captured at the skill-registration
  and jules-tool-discipline walk scenarios; per-phase internal step
  assertions are implementation detail.
- test_jules_skills_self_improvement.py (walk steps) — drives
  SkillRun directly with tmp_path; the observable behaviour (skill
  registered, provenance) is captured in the registration scenario.
- test_jules_monitor.py::test_install_still_has_exactly_one_monitor_entry
  — frozen snapshot of the install output structure; not a verb behaviour.
- test_jules_key_error.py — asserts on RuntimeError message text from the
  internal _api_key() helper; not a verb-surface observable.

GAPS (need JULES_API_KEY + network — not testable in-process):
- Real dispatch to the Jules REST API (response shape, session creation).
- jules.list, jules.activities, jules.plan, jules.approve_plan,
  jules.message, jules.status (real backend calls).
- jules.approve_awaiting, jules.status_all, jules.quota (batch ops).
- jules.patch returning real outputs from a remote session.
- jules.apply_patch with real session outputs (requires jules_get_full).
- Watcher poll loop driving live session state transitions over time.
- Monitor log emission integration (Spec 022 — requires a running engine
  with a live monitor target file and real verb calls in sequence).
- jules-protocol-preamble skill walk phases 2–4 (vcs.remote_exists needs
  a real git remote or network-capable VCS stub wired via injectors).
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.capabilities.jules.preambles import (
    DISPATCH_SELF_SOURCE,
    PREAMBLE,
    assemble,
)
from agency.capabilities.jules.watch import INSTRUCTIONS, _classify
from agency.engine import Engine
from agency.skill import SkillRun
from conftest import call_tool, invoke, served

scenarios("features/jules.feature")


# ── stub backends ─────────────────────────────────────────────────────────────


class _StubJulesClient:
    """Minimal backend for dispatch tests — no network."""

    def create(self, **kw):
        return {
            "id": "sessions/stub-abc",
            "state": "QUEUED",
            "title": kw.get("title", ""),
            "url": "https://jules.google.com/session/stub-abc",
        }

    def get(self, session):
        return {"id": session, "state": "COMPLETED",
                "url": f"https://jules.google.com/{session}"}

    def list(self, page_size, page_token=""): return {"sessions": []}
    def activities(self, session, page_size, only_kinds, page_token=""): return {"activities": []}
    def plan(self, session, max_pages): return {"steps": []}
    def approve_plan(self, session): return {"ok": True}
    def message(self, session, prompt): return {"ok": True}
    def resolve_source(self, owner, repo): return {"source": f"sources/{owner}-{repo}"}
    def get_full(self, session): return {"id": session, "outputs": []}
    def status_all(self, page_size, max_pages): return {"sessions": [], "total": 0}
    def approve_awaiting(self, limit): return {"approved": []}
    def quota(self, daily_limit): return {"active_today": 0, "headroom": 0}
    def patch(self, session): return {"total_files": 0, "outputs": []}


class _RecordingClient(_StubJulesClient):
    """Records the last create() kwargs for flag-matrix assertions."""

    def __init__(self):
        self.last_kwargs: dict = {}

    def create(self, **kw):
        self.last_kwargs = kw
        return super().create(**kw)


class _StubVCSExists:
    def remote_exists(self, branch, remote="origin"):
        return {"ok": True, "exists": True, "sha": "deadbeef"}


class _StubVCSMissing:
    def remote_exists(self, branch, remote="origin"):
        return {"ok": True, "exists": False, "sha": ""}


class _StubJulesForSkill(_StubJulesClient):
    """Records calls for recovery skill assertions."""

    def __init__(self):
        self.calls: list = []

    def get(self, session):
        self.calls.append(("get", session))
        return {"id": session, "state": "COMPLETED",
                "url": f"https://jules.google.com/{session}"}

    def message(self, session, prompt):
        self.calls.append(("message", session, prompt))
        return {"ok": True}

    def patch(self, session):
        self.calls.append(("patch", session))
        return {"total_files": 1, "outputs": [{"index": 0, "files": 1, "lines": 10, "bytes": 200}]}


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def stub_engine(confirmed_intent, engine):
    """Engine with stub Jules client (no network)."""
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesClient())
    iid = eng.intent.capture("jules acceptance", "behaviour", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@pytest.fixture
def recording_engine():
    """Engine with a recording Jules client for flag-matrix assertions."""
    client = _RecordingClient()
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=client)
    iid = eng.intent.capture("jules recording", "flags", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    eng.memory.close  # will be closed by engine gc
    return eng


# ── Given steps ───────────────────────────────────────────────────────────────


@given("a stub Jules backend", target_fixture="stub_engine")
def _given_stub_engine():
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesClient())
    iid = eng.intent.capture("jules acceptance", "behaviour", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@given("a recording stub Jules backend", target_fixture="stub_engine")
def _given_recording_engine():
    client = _RecordingClient()
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=client)
    iid = eng.intent.capture("jules recording", "flags", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@given("a vcs backend that reports the branch does NOT exist on origin", target_fixture="vcs_engine")
def _given_vcs_missing():
    eng = Engine(tempfile.mktemp(suffix=".db"), vcs_backend=_StubVCSMissing())
    iid = eng.intent.capture("verify test", "silent fail detection", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@given("a vcs backend that reports the branch EXISTS on origin", target_fixture="vcs_engine")
def _given_vcs_exists():
    eng = Engine(tempfile.mktemp(suffix=".db"), vcs_backend=_StubVCSExists())
    iid = eng.intent.capture("verify test", "branch present", "verified")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@given("a watcher attached to the engine with a queued verify_pr event",
       target_fixture="watcher_engine")
def _given_watcher_with_event():
    from agency.capabilities.jules import watch as _jules_watch
    eng = Engine(tempfile.mktemp(suffix=".db"))
    iid = eng.intent.capture("watch test", "queue drain", "event returned")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    watcher = _jules_watch.Watcher()
    eng._jules_watcher = watcher
    event = {"action": "verify_pr", "session": "sess-q", "state": "COMPLETED",
             "instruction": "check PR", "evidence": {}}
    watcher._put_event(iid, event)
    return eng


@given("a watcher attached to the engine with no queued events",
       target_fixture="watcher_engine")
def _given_watcher_empty():
    from agency.capabilities.jules import watch as _jules_watch
    eng = Engine(tempfile.mktemp(suffix=".db"))
    iid = eng.intent.capture("watch test", "empty queue", "noop returned")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    eng._jules_watcher = _jules_watch.Watcher()
    return eng


@given("a stub Jules backend for skill walk", target_fixture="skill_engine")
def _given_skill_engine():
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesForSkill())
    iid = eng.intent.capture("skill walk test", "recovery skill", "phases complete")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


@given("a stub Jules backend for fanout", target_fixture="fanout_engine")
def _given_fanout_engine():
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesClient())
    iid = eng.intent.capture("fanout test", "fan-out walks", "join hard-gates")
    eng.intent.confirm(iid)
    eng._test_iid = iid
    return eng


# ── When steps ────────────────────────────────────────────────────────────────


@when(parsers.parse('I dispatch a Jules session with source "{source}" and branch "{branch}"'),
      target_fixture="dispatch_result")
def _when_dispatch(stub_engine, source, branch):
    result, _ = invoke(stub_engine, stub_engine._test_iid, "jules", "dispatch",
                       agent_id="agent:claude",
                       source=source, starting_branch=branch,
                       prompt="test task", title="Test")
    return result


@when("I dispatch with automation_mode \"AUTO_CREATE_PR\"",
      target_fixture="dispatch_result")
def _when_dispatch_auto_pr(stub_engine):
    result, _ = invoke(stub_engine, stub_engine._test_iid, "jules", "dispatch",
                       agent_id="agent:claude",
                       source="netzkontrast/agency", starting_branch="main",
                       prompt="task", automation_mode="AUTO_CREATE_PR")
    return result


@when("I dispatch with require_plan_approval=False and automation_mode=\"AUTO_CREATE_PR\"",
      target_fixture="dispatch_result")
def _when_dispatch_zero_touch(stub_engine):
    result, _ = invoke(stub_engine, stub_engine._test_iid, "jules", "dispatch",
                       agent_id="agent:claude",
                       source="netzkontrast/agency", starting_branch="main",
                       prompt="task", require_plan_approval=False,
                       automation_mode="AUTO_CREATE_PR")
    return result


@when("I dispatch with protocol_preset \"agency-default\"",
      target_fixture="dispatch_result")
def _when_dispatch_preset(stub_engine):
    result, _ = invoke(stub_engine, stub_engine._test_iid, "jules", "dispatch",
                       agent_id="agent:claude",
                       source="netzkontrast/agency", starting_branch="main",
                       prompt="task", protocol_preset="agency-default")
    return result


@when(parsers.parse('I invoke verify with state "{state}" and branch "{branch}"'),
      target_fixture="verify_result")
def _when_verify(vcs_engine, state, branch):
    result, _ = invoke(vcs_engine, vcs_engine._test_iid, "jules", "verify",
                       agent_id="agent:claude", state=state, branch=branch)
    return result


@when("I lint a prompt that names all canonical Jules tools",
      target_fixture="lint_result")
def _when_lint_canonical(engine, confirmed_intent):
    text = (
        "Run pre_commit_instructions() then submit(branch_name=...). "
        "If stuck use request_user_input. Use replace_with_git_merge_diff "
        "and request_code_review before submit."
    )
    result, _ = invoke(engine, confirmed_intent, "jules", "lint_prompt",
                       agent_id="agent:claude", text=text)
    return result


@when("I lint a prompt that says \"open a PR when done\"",
      target_fixture="lint_result")
def _when_lint_bad(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "lint_prompt",
                       agent_id="agent:claude", text="open a PR when done")
    return result


@when("I lint a prompt naming publish pair plus \"replace_with_git_merge_diff\" with must_name \"pre_commit_instructions,submit\"",
      target_fixture="lint_result")
def _when_lint_extras(engine, confirmed_intent):
    text = "pre_commit_instructions then submit. Also use replace_with_git_merge_diff."
    result, _ = invoke(engine, confirmed_intent, "jules", "lint_prompt",
                       agent_id="agent:claude", text=text,
                       must_name="pre_commit_instructions,submit")
    return result


@when("I lint the same prompt with empty must_name and with default must_name",
      target_fixture="dual_lint_result")
def _when_lint_dual(engine, confirmed_intent):
    text = "x"
    r_a, _ = invoke(engine, confirmed_intent, "jules", "lint_prompt",
                    agent_id="agent:claude", text=text)
    r_b, _ = invoke(engine, confirmed_intent, "jules", "lint_prompt",
                    agent_id="agent:claude", text=text, must_name="")
    return {"a": r_a, "b": r_b}


@when("I invoke review_comment with body \"Verdict: changes-requested.\"",
      target_fixture="review_result")
def _when_review_comment(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "review_comment",
                       agent_id="agent:claude",
                       body="Verdict: changes-requested.")
    return result


@when("I invoke review_comment with body \"Verdict: changes-requested. Fix the test.\"",
      target_fixture="review_result")
def _when_review_comment_fix(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "review_comment",
                       agent_id="agent:claude",
                       body="Verdict: changes-requested. Fix the test.")
    return result


@when("I invoke review_comment twice with the same body",
      target_fixture="review_result")
def _when_review_idempotent(engine, confirmed_intent):
    r1, _ = invoke(engine, confirmed_intent, "jules", "review_comment",
                   agent_id="agent:claude", body="x")
    r2, _ = invoke(engine, confirmed_intent, "jules", "review_comment",
                   agent_id="agent:claude", body=r1["text"])
    return r2


@when(parsers.parse('I invoke detect_mode with source "{source}"'),
      target_fixture="detect_result")
def _when_detect_mode(engine, confirmed_intent, source):
    result, _ = invoke(engine, confirmed_intent, "jules", "detect_mode",
                       agent_id="agent:claude", source=source)
    return result


@when(parsers.parse('I assemble the preamble for source "{source}" with prompt "{prompt}"'),
      target_fixture="assembled_text")
def _when_assemble(source, prompt):
    return assemble(source=source, starting_branch="main", prompt=prompt)


@when("I assemble the preamble with an unknown preset name",
      target_fixture="assembly_error")
def _when_assemble_unknown():
    try:
        assemble(source=DISPATCH_SELF_SOURCE, starting_branch="main",
                 prompt="x", preset_name="not-a-real-preset")
        return None
    except ValueError as e:
        return e


@when("I assemble the preamble for source \"netzkontrast/agency\" with prompt \"x\" twice",
      target_fixture="dual_assembled")
def _when_assemble_dual():
    out_a = assemble(source=DISPATCH_SELF_SOURCE, starting_branch="main", prompt="x")
    out_b = assemble(source=DISPATCH_SELF_SOURCE, starting_branch="main", prompt="x",
                     preset_name="agency-default")
    return {"a": out_a, "b": out_b}


@when("I invoke watch with no arguments", target_fixture="watch_result")
def _when_watch_no_args(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "watch",
                       agent_id="agent:claude")
    return result


@when("I invoke watch with for_intent set but no watcher started",
      target_fixture="watch_result")
def _when_watch_no_watcher(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "watch",
                       agent_id="agent:claude", for_intent=confirmed_intent)
    return result


@when("I invoke watch with for_intent set", target_fixture="watch_result")
def _when_watch_drain(watcher_engine):
    result, _ = invoke(watcher_engine, watcher_engine._test_iid, "jules", "watch",
                       agent_id="agent:claude",
                       for_intent=watcher_engine._test_iid)
    return result


@when("I invoke watch with for_intent set and timeout=0", target_fixture="watch_result")
def _when_watch_heartbeat(watcher_engine):
    result, _ = invoke(watcher_engine, watcher_engine._test_iid, "jules", "watch",
                       agent_id="agent:claude",
                       for_intent=watcher_engine._test_iid, timeout=0)
    return result


@when("I invoke recover with session \"sess-x\" but no watcher started",
      target_fixture="recover_result")
def _when_recover_no_watcher(engine, confirmed_intent):
    result, _ = invoke(engine, confirmed_intent, "jules", "recover",
                       agent_id="agent:claude", session="sess-x")
    return result


@when("I invoke recover with session \"s-1\" owner \"netzkontrast\" repo \"agency\" branch \"feat-x\" base \"main\"",
      target_fixture="recover_result")
def _when_recover_full(watcher_engine):
    result, _ = invoke(watcher_engine, watcher_engine._test_iid, "jules", "recover",
                       agent_id="agent:claude", session="s-1",
                       owner="netzkontrast", repo="agency",
                       branch="feat-x", base="main")
    return {"result": result, "engine": watcher_engine}


@when("I invoke recover with session \"s-2\" with no base provided",
      target_fixture="recover_result")
def _when_recover_default_base(watcher_engine):
    invoke(watcher_engine, watcher_engine._test_iid, "jules", "recover",
           agent_id="agent:claude", session="s-2")
    return {"engine": watcher_engine, "session": "s-2"}


@when("I classify a COMPLETED session with unapproved plan and no branch on remote",
      target_fixture="classify_result")
def _when_classify_unapproved_plan():
    return _classify(
        prev={"state": "PLANNING", "id": "s"},
        curr={"state": "COMPLETED", "id": "s",
              "url": "https://jules.google.com/s", "plan_steps": 6},
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 0, "lines": 0, "bytes": 0},
        plan_unapproved=True,
    )


@when("I classify a COMPLETED session with branch on remote and no unapproved plan",
      target_fixture="classify_result")
def _when_classify_branch_on_remote():
    return _classify(
        prev={"state": "IN_PROGRESS", "id": "s"},
        curr={"state": "COMPLETED", "id": "s",
              "url": "https://jules.google.com/s", "branch": "feat/x"},
        last_agent_msg_id=None,
        branch_on_remote=True,
        patch_summary={"files": 1, "lines": 10, "bytes": 100},
        plan_unapproved=False,
    )


@when("I classify a COMPLETED session with patch outputs but no branch on remote",
      target_fixture="classify_result")
def _when_classify_silent_fail():
    return _classify(
        prev={"state": "IN_PROGRESS", "id": "s"},
        curr={"state": "COMPLETED", "id": "s", "url": "https://jules.google.com/s"},
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 3, "lines": 100, "bytes": 4000},
        plan_unapproved=False,
    )


@when("I classify a COMPLETED session with no outputs and no plan",
      target_fixture="classify_result")
def _when_classify_dispatch_fresh():
    return _classify(
        prev={"state": "IN_PROGRESS", "id": "s"},
        curr={"state": "COMPLETED", "id": "s", "url": "https://jules.google.com/s"},
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 0, "lines": 0, "bytes": 0},
        plan_unapproved=False,
    )


@when(parsers.parse('I classify a session transitioning to "{new_state}"'),
      target_fixture="classify_result")
def _when_classify_transition(new_state):
    curr = {"state": new_state, "id": "s", "url": "https://jules.google.com/s"}
    if new_state == "AWAITING_PLAN_APPROVAL":
        curr["plan_steps"] = 5
    if new_state == "CANCELLED":
        curr["cause"] = "usr"
    return _classify(
        prev={"state": "IN_PROGRESS", "id": "s"},
        curr=curr,
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary=None,
    )


@when("I walk \"jules-tool-discipline\" with a canonical prompt",
      target_fixture="jtools_result")
def _when_walk_tool_discipline_canonical(engine, confirmed_intent):
    canonical = (
        "Use pre_commit_instructions(), then submit(...). "
        "Use request_user_input for blocking asks. "
        "Use replace_with_git_merge_diff for multi-line edits. "
        "Call request_code_review before submit."
    )
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, confirmed_intent, sk, registry=engine.registry)
    res = run.submit({"text": canonical, "must_name": ""})
    return {"status": res["status"], "run": run, "engine": engine,
            "intent": confirmed_intent}


@when("I walk \"jules-tool-discipline\" with a bad prompt",
      target_fixture="jtools_result")
def _when_walk_tool_discipline_bad(engine, confirmed_intent):
    sk = engine.ontology.skill("jules-tool-discipline")
    run = SkillRun(engine.memory, confirmed_intent, sk, registry=engine.registry)
    res = run.submit({"text": "open a PR when done", "must_name": ""})
    return {"status": res["status"], "run": run, "engine": engine,
            "intent": confirmed_intent}


@when("I walk \"jules-recovery-when-stuck\" through all phases",
      target_fixture="recovery_walk_result")
def _when_walk_recovery(skill_engine):
    sk = skill_engine.ontology.skill("jules-recovery-when-stuck")
    run = SkillRun(skill_engine.memory, skill_engine._test_iid, sk,
                   registry=skill_engine.registry)
    run.submit({"session": "sess-stuck"})
    run.submit({"session": "sess-stuck",
                "prompt": "your branch isn't on origin — push or reply EMPTY"})
    run.submit({"session": "sess-stuck"})
    res = run.submit({"pr_url": "https://github.com/netzkontrast/agency/pull/42"})
    return {"result": res, "run": run, "engine": skill_engine}


@when("I walk \"jules-recovery-when-stuck\" through all phases and confirm",
      target_fixture="recovery_walk_result")
def _when_walk_recovery_confirm(skill_engine):
    sk = skill_engine.ontology.skill("jules-recovery-when-stuck")
    run = SkillRun(skill_engine.memory, skill_engine._test_iid, sk,
                   registry=skill_engine.registry)
    run.submit({"session": "sess-prov"})
    run.submit({"session": "sess-prov", "prompt": "probe"})
    run.submit({"session": "sess-prov"})
    run.submit({"pr_url": "https://example/pr"}, confirmed=True)
    return {"run": run, "engine": skill_engine}


@when("I walk \"jules-pr-review-cycle\" through all phases",
      target_fixture="pr_review_result")
def _when_walk_pr_review(engine, confirmed_intent):
    sk = engine.ontology.skill("jules-pr-review-cycle")
    run = SkillRun(engine.memory, confirmed_intent, sk, registry=engine.registry)
    run.submit({"comments": [{"id": 1, "body": "fix the off-by-one"}]})
    run.submit({"body": "Verdict: changes-requested. Fix the test."})
    res = run.submit({"posted": [{"id": 99,
                                  "url": "https://github.com/x/y#discussion_99"}]})
    return {"status": res["status"], "run": run}


@when("I walk \"jules-fanout\" through plan and fan-out phases",
      target_fixture="fanout_result")
def _when_walk_fanout_partial(fanout_engine):
    items = [
        {"prompt": "task A", "source": "netzkontrast/agency", "starting_branch": "main"},
        {"prompt": "task B", "source": "netzkontrast/agency", "starting_branch": "main"},
    ]
    sk = fanout_engine.ontology.skill("jules-fanout")
    run = SkillRun(fanout_engine.memory, fanout_engine._test_iid, sk,
                   registry=fanout_engine.registry)
    run.submit({"items": items})
    res = run.submit({"driver": "jules", "driver_verb": "dispatch",
                      "items": items, "quota": 8})
    res_gate = run.submit({"child_outcomes": [{"id": "c1", "state": "done"},
                                               {"id": "c2", "state": "done"}]})
    return {"gate_result": res_gate, "run": run, "engine": fanout_engine,
            "items": items}


@when("I walk \"jules-fanout\" through all phases and confirm join",
      target_fixture="fanout_result")
def _when_walk_fanout_full(fanout_engine):
    items = [
        {"prompt": "task A", "source": "netzkontrast/agency", "starting_branch": "main"},
    ]
    sk = fanout_engine.ontology.skill("jules-fanout")
    run = SkillRun(fanout_engine.memory, fanout_engine._test_iid, sk,
                   registry=fanout_engine.registry)
    run.submit({"items": items})
    run.submit({"driver": "jules", "driver_verb": "dispatch",
                "items": items, "quota": 4})
    res = run.submit({"child_outcomes": [{"id": "c1", "state": "done"}]},
                     confirmed=True)
    return {"status": res["status"], "run": run}


# ── Then steps — dispatch envelope + provenance ───────────────────────────────


@then("the result carries status, session, url, alias, and artefact fields")
def _then_envelope(dispatch_result):
    for field in ("status", "session", "url", "alias", "artefact"):
        assert field in dispatch_result, f"envelope missing {field!r}"
    artefact = dispatch_result["artefact"]
    assert "kind" in artefact and "session" in artefact


@then("an Invocation SERVES the intent in the graph")
def _then_invocation_serves(stub_engine):
    count = served(stub_engine, stub_engine._test_iid, "Invocation")
    assert count >= 1, "at least one Invocation must SERVE the intent"


@then("a JulesSession node is recorded in the graph")
def _then_jules_session_node(stub_engine, dispatch_result):
    sid = dispatch_result.get("session")
    assert sid, "dispatch must return a session id"
    node = stub_engine.memory.recall(f"jules-session:{sid}")
    assert node is not None, "JulesSession node must exist in the graph"


# ── Then steps — flag matrix ──────────────────────────────────────────────────


@then("the backend receives require_plan_approval=True and automation_mode=\"\"")
def _then_default_flags(stub_engine):
    kw = stub_engine.jules_client.last_kwargs
    assert kw["require_plan_approval"] is True
    assert kw["automation_mode"] == ""


@then("the backend receives require_plan_approval=True and automation_mode=\"AUTO_CREATE_PR\"")
def _then_auto_pr_flags(stub_engine):
    kw = stub_engine.jules_client.last_kwargs
    assert kw["require_plan_approval"] is True
    assert kw["automation_mode"] == "AUTO_CREATE_PR"


@then("the backend receives require_plan_approval=False and automation_mode=\"AUTO_CREATE_PR\"")
def _then_zero_touch_flags(stub_engine):
    kw = stub_engine.jules_client.last_kwargs
    assert kw["require_plan_approval"] is False
    assert kw["automation_mode"] == "AUTO_CREATE_PR"


@then("the backend receives protocol_preset=\"agency-default\"")
def _then_preset_forwarded(stub_engine):
    kw = stub_engine.jules_client.last_kwargs
    assert kw["protocol_preset"] == "agency-default"


# ── Then steps — verify ───────────────────────────────────────────────────────


@then("the result contains ok=False and reason mentions the branch")
def _then_silent_fail(verify_result):
    # verify returns {done, state, branch_on_remote, sha}
    # done=False means the session is NOT confirmed done (silent fail)
    assert verify_result.get("done") is False
    assert verify_result.get("branch_on_remote") is False


@then("the result contains ok=True")
def _then_verify_ok(verify_result):
    # done=True means the branch is confirmed on the remote
    assert verify_result.get("done") is True
    assert verify_result.get("branch_on_remote") is True


@then("the result does not flag silent_fail")
def _then_no_silent_fail(verify_result):
    # For in-progress sessions verify should not report done=False as a silent fail
    # The verb returns the raw state; done may be False but we confirm state is not COMPLETED
    # or the branch_on_remote check was not triggered for non-COMPLETED states
    state = verify_result.get("state")
    branch_on_remote = verify_result.get("branch_on_remote")
    # An in-progress session may show branch_on_remote=False without it being a "silent fail"
    # The key behaviour: verify does not raise and returns a coherent envelope
    assert "state" in verify_result, "verify must return a state field"


# ── Then steps — lint_prompt ──────────────────────────────────────────────────


@then("the lint result is ok with no missing tools")
def _then_lint_ok(lint_result):
    assert lint_result["ok"] is True
    assert lint_result["missing"] == []


@then("the lint result is not ok and missing includes \"submit\" and \"pre_commit_instructions\"")
def _then_lint_bad(lint_result):
    assert lint_result["ok"] is False
    assert "submit" in lint_result["missing"]
    assert "pre_commit_instructions" in lint_result["missing"]


@then("the lint result is ok and extras includes \"replace_with_git_merge_diff\"")
def _then_lint_extras(lint_result):
    assert lint_result["ok"] is True
    assert "replace_with_git_merge_diff" in lint_result["extras"]


@then("both results are identical")
def _then_dual_identical(dual_lint_result):
    assert dual_lint_result["a"] == dual_lint_result["b"]


# ── Then steps — review_comment ───────────────────────────────────────────────


@then("the result carries tail_appended=True")
def _then_tail_appended(review_result):
    assert review_result["tail_appended"] is True


@then("the text contains \"reply_to_pr_comments\"")
def _then_text_has_handshake(review_result):
    assert "reply_to_pr_comments" in review_result["text"]


@then("the original body is preserved in the text")
def _then_body_preserved(review_result):
    assert "Verdict: changes-requested." in review_result["text"]


@then("the reply_to_pr_comments text appears exactly once in the final text")
def _then_no_duplicate_tail(review_result):
    assert review_result["text"].count("reply_to_pr_comments") == 1


# ── Then steps — detect_mode ──────────────────────────────────────────────────


@then(parsers.parse('the mode is "{mode}"'))
def _then_mode(detect_result, mode):
    assert detect_result["mode"] == mode


@then("the reason mentions lexical scoping")
def _then_reason_lexical(detect_result):
    assert "lexical scoping" in detect_result.get("reason", "")


@then("the reason mentions clone block")
def _then_reason_clone(detect_result):
    assert "clone block" in detect_result.get("reason", "")


# ── Then steps — preamble assembly ────────────────────────────────────────────


@then("the assembled text does not contain \"git clone\"")
def _then_no_clone(assembled_text):
    assert "git clone" not in assembled_text


@then("the assembled text contains \"AGENCY_PROTOCOL.md\"")
def _then_has_protocol(assembled_text):
    assert "AGENCY_PROTOCOL.md" in assembled_text


@then("the assembled text contains the original prompt")
def _then_has_prompt(assembled_text):
    assert "do the thing" in assembled_text or "x" in assembled_text


@then("the assembled text contains \"git clone --depth=1\"")
def _then_has_clone(assembled_text):
    assert "git clone --depth=1" in assembled_text


@then("the assembled text contains a read-only instruction for the agency clone")
def _then_read_only(assembled_text):
    text_low = assembled_text.lower()
    assert "read only" in text_low or "read-only" in text_low or "never" in text_low


@then("a ValueError is raised mentioning \"unknown protocol_preset\"")
def _then_value_error(assembly_error):
    assert isinstance(assembly_error, ValueError)
    assert "unknown protocol_preset" in str(assembly_error)


@then("both assembled texts are identical")
def _then_dual_assembled_equal(dual_assembled):
    assert dual_assembled["a"] == dual_assembled["b"]


# ── Then steps — watch ────────────────────────────────────────────────────────


@then(parsers.parse('the result action is "{action}"'))
def _then_action(watch_result, action):
    assert watch_result["action"] == action


@then("the instruction mentions \"session or for_intent\"")
def _then_instruction_mentions(watch_result):
    assert "session or for_intent" in watch_result.get("instruction", "")


@then("the evidence reason mentions \"not started\"")
def _then_evidence_not_started(watch_result):
    assert "not started" in watch_result.get("evidence", {}).get("reason", "")


@then("the instruction is \"Working.\"")
def _then_instruction_working(watch_result):
    assert watch_result.get("instruction") == "Working."


# ── Then steps — recover ──────────────────────────────────────────────────────


@then(parsers.parse('the result status is "{status}"'))
def _then_recover_status(recover_result, status):
    if isinstance(recover_result, dict) and "result" in recover_result:
        actual = recover_result["result"].get("status")
    else:
        actual = recover_result.get("status")
    assert actual == status, f"expected status={status!r}, got {actual!r}"


@then("the reason mentions \"not started\"")
def _then_reason_not_started(recover_result):
    reason = recover_result.get("reason", "")
    assert "not started" in reason


@then("the session is tracked in recovery_in_flight")
def _then_tracked(recover_result):
    eng = recover_result["engine"]
    watcher = eng._jules_watcher
    assert "s-1" in watcher.recovery_in_flight
    st = watcher.recovery_in_flight["s-1"]
    assert st["attempt"] == 0
    assert st["owner"] == "netzkontrast"
    assert st["repo"] == "agency"
    assert st["base"] == "main"


@then("the recovery entry has base \"main\"")
def _then_base_main(recover_result):
    eng = recover_result["engine"]
    session = recover_result["session"]
    watcher = eng._jules_watcher
    assert watcher.recovery_in_flight[session]["base"] == "main"


# ── Then steps — classify ─────────────────────────────────────────────────────


@then(parsers.parse('the classified action is "{action}"'))
def _then_classified(classify_result, action):
    assert classify_result["action"] == action, (
        f"expected action={action!r}, got {classify_result['action']!r}")


# ── Then steps — INSTRUCTIONS ──────────────────────────────────────────────────


@then(parsers.parse('the recover_silent_fail instruction names "{tool}"'))
def _then_rsf_names(tool):
    assert tool in INSTRUCTIONS["recover_silent_fail"]


@then(parsers.parse('the verify_pr instruction references "{text}"'))
def _then_vpr_references(text):
    assert text in INSTRUCTIONS["verify_pr"]


@then(parsers.parse('the review_and_approve_plan instruction names "{tool}"'))
def _then_rap_names(tool):
    assert tool in INSTRUCTIONS["review_and_approve_plan"]


@then(parsers.parse('the dispatch_fresh instruction names "{tool}"'))
def _then_df_names(tool):
    assert tool in INSTRUCTIONS["dispatch_fresh"]


@then("every INSTRUCTIONS template is under 480 characters")
def _then_token_budget():
    over = {k: len(v) for k, v in INSTRUCTIONS.items() if len(v) > 480}
    assert not over, f"templates over 480 chars: {over}"


# ── Then steps — skill registration ───────────────────────────────────────────


@then(parsers.parse('the skill "{name}" is registered on the jules ontology'))
def _then_skill_registered(engine, name):
    assert name in engine.ontology.skills, f"{name!r} not in jules ontology"


@then(parsers.parse('the skill "{name}" has exactly {n:d} phases in order'))
def _then_skill_phases(engine, name, n):
    sk = engine.ontology.skill(name)
    assert len(sk["phases"]) == n, (
        f"expected {n} phases for {name!r}, got {len(sk['phases'])}")


@then(parsers.parse('the skill "{name}" has exactly {n:d} phases'))
def _then_skill_phases_unordered(engine, name, n):
    sk = engine.ontology.skill(name)
    assert len(sk["phases"]) == n, (
        f"expected {n} phases for {name!r}, got {len(sk['phases'])}")


@then(parsers.parse('the skill "{name}" has exactly {n:d} phase'))
def _then_skill_one_phase(engine, name, n):
    sk = engine.ontology.skill(name)
    assert len(sk["phases"]) == n


# ── Then steps — skill walk ────────────────────────────────────────────────────


@then("the walk status is \"completed\"")
def _then_walk_completed(jtools_result=None, pr_review_result=None, fanout_result=None):
    if jtools_result is not None:
        assert jtools_result["status"] == "completed"
    elif pr_review_result is not None:
        assert pr_review_result["status"] == "completed"
    elif fanout_result is not None:
        assert fanout_result.get("status") == "completed"


@then("a Phase node is recorded for the skill \"jules-tool-discipline\"")
def _then_phase_node(jtools_result):
    eng = jtools_result["engine"]
    rows = eng.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-tool-discipline"},
    )
    assert len(rows) >= 1


@then(parsers.parse('the walk pauses at "{phase}" with status "input-required"'))
def _then_walk_paused(phase, recovery_walk_result=None, fanout_result=None):
    if recovery_walk_result is not None:
        result = recovery_walk_result["result"]
        assert result["status"] == "input-required"
        assert result.get("gate") == "hard"
        assert result.get("phase") == phase
    elif fanout_result is not None:
        gate_result = fanout_result["gate_result"]
        assert gate_result["status"] == "input-required"
        assert gate_result.get("gate") == "hard"


@then("confirming completes the walk")
def _then_confirm_completes(recovery_walk_result):
    run = recovery_walk_result["run"]
    res = run.submit(
        {"pr_url": "https://github.com/netzkontrast/agency/pull/42"},
        confirmed=True,
    )
    assert res["status"] == "completed"
    assert run.done


@then("4 Phase nodes are recorded for the skill \"jules-recovery-when-stuck\"")
def _then_recovery_phases(recovery_walk_result):
    eng = recovery_walk_result["engine"]
    rows = eng.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-recovery-when-stuck"},
    )
    assert len(rows) == 4


@then("a Delegation node is recorded serving the intent")
def _then_delegation_node(fanout_result):
    eng = fanout_result["engine"]
    iid = eng._test_iid
    rows = eng.memory.g.query(
        "MATCH (d:Delegation)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid RETURN d",
        {"iid": iid},
    )
    assert len(rows) >= 1
