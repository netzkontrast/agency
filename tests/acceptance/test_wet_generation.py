"""Acceptance — use-case model selection + OpenRouter-first generation (Spec 348).

All selection logic is network-free. `generate` is exercised with a stub
OpenRouter client (no network); the live SDK boundary (`_openrouter_models`,
`_send`) is `# pragma: no cover - network`. Code in `agency/_llm.py`.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from agency import _llm
from agency.capability import DriverRegistry, DriverMissing

scenarios("features/wet_generation.feature")


@pytest.fixture
def ctx() -> dict:
    return {}


# ── the registry ──────────────────────────────────────────────────────────────
@given("the built-in model registry")
def _builtin_registry(ctx):
    ctx["registry"] = _llm.default_registry()


@then('every model id ends with ":free"')
def _all_free(ctx):
    assert ctx["registry"]
    assert all(p.id.endswith(":free") for p in ctx["registry"])


@then("every model declares at least one use-case")
def _all_have_uc(ctx):
    assert all(len(p.use_cases) >= 1 for p in ctx["registry"])


@when(parsers.parse('I select a model for use-case "{uc}"'))
def _select(ctx, uc):
    ctx["chosen"] = _llm.select_model(uc, registry=ctx.get("registry"))


@when(parsers.parse('I select a model for use-case "{uc}" against the live catalogue'))
def _select_live(ctx, uc):
    ctx["chosen"] = _llm.select_model(uc, registry=ctx.get("registry"),
                                      live_ids=ctx["live_ids"])


@given("the top reasoning model is not live-available")
def _top_not_live(ctx):
    reg = _llm.default_registry()
    ctx["registry"] = reg
    reasoning = sorted([p for p in reg if "reasoning" in p.use_cases],
                       key=lambda p: p.priority)
    ctx["dropped"] = reasoning[0].id
    ctx["live_ids"] = {p.id for p in reg} - {reasoning[0].id}


@then(parsers.parse('the chosen model declares the "{uc}" use-case'))
def _chosen_has_uc(ctx, uc):
    reg = ctx.get("registry") or _llm.default_registry()
    prof = next((p for p in reg if p.id == ctx["chosen"]), None)
    assert prof is not None, ctx["chosen"]
    assert uc in prof.use_cases, (uc, prof.use_cases)


@then('the chosen model id ends with ":free"')
def _chosen_free(ctx):
    assert ctx["chosen"].endswith(":free")


@then("the chosen model is a different live reasoning model")
def _chosen_diff_live(ctx):
    assert ctx["chosen"] != ctx["dropped"]
    assert ctx["chosen"] in ctx["live_ids"]


@given(parsers.parse('a config registry mapping use-case "{uc}" to "{mid}"'))
def _config_registry(ctx, uc, mid):
    ctx["registry"] = _llm.load_registry({"models": [
        {"id": mid, "use_cases": [uc], "priority": 5},
    ]})


@when(parsers.parse('I select a model for use-case "{uc}" from the config registry'))
def _select_config(ctx, uc):
    ctx["chosen"] = _llm.select_model(uc, registry=ctx["registry"])


@then(parsers.parse('the chosen model is "{mid}"'))
def _chosen_is(ctx, mid):
    assert ctx["chosen"] == mid


@when(parsers.parse('I select with an explicit non-free model "{mid}"'))
def _select_nonfree(ctx, mid):
    try:
        _llm.select_model("general", model=mid)
        ctx["raised"] = None
    except ValueError as e:
        ctx["raised"] = e


@then("a ValueError is raised about a free model")
def _value_error_free(ctx):
    assert isinstance(ctx["raised"], ValueError)
    assert "free" in str(ctx["raised"]).lower()


# ── select_text_generator ───────────────────────────────────────────────────
class _StubDriver:
    def __init__(self, name):
        self.name = name


def _drivers():
    reg = DriverRegistry()
    reg.register("llm", _StubDriver("llm"))
    reg.register("anthropic", _StubDriver("anthropic"))
    return reg


@given("OPENROUTER_API_KEY and ANTHROPIC_API_KEY are both set")
def _both_keys(ctx):
    ctx["env"] = {"OPENROUTER_API_KEY": "or", "ANTHROPIC_API_KEY": "an"}


@given("only OPENROUTER_API_KEY is set")
def _only_or(ctx):
    ctx["env"] = {"OPENROUTER_API_KEY": "or"}


@given("neither generation key is set")
def _no_keys(ctx):
    ctx["env"] = {}


@when("I select the text generator")
def _sel_gen(ctx):
    try:
        ctx["gen"] = _llm.select_text_generator(_drivers(), env=ctx["env"])
        ctx["raised"] = None
    except Exception as e:  # noqa: BLE001
        ctx["raised"] = e


@when(parsers.parse('I select the text generator requiring "{req}"'))
def _sel_gen_req(ctx, req):
    ctx["gen"] = _llm.select_text_generator(_drivers(), env=ctx["env"], require=req)


@then(parsers.parse('the generator name is "{name}"'))
def _gen_name(ctx, name):
    assert ctx["gen"][0] == name


@then("a dependency-missing error is raised")
def _dep_missing(ctx):
    from agency.toolresult import Codes
    assert ctx["raised"] is not None
    assert getattr(ctx["raised"], "code", "") == Codes.DEPENDENCY_MISSING or \
        "dependency_missing" in str(ctx["raised"]).lower()


# ── config-file registry ─────────────────────────────────────────────────────
@given(parsers.parse('a config file with an llm.models block mapping "{uc}" to "{mid}"'),
       target_fixture="cfg_path")
def _cfg_with_models(tmp_path, uc, mid):
    p = tmp_path / "config.yaml"
    p.write_text(
        "core:\n  db_path: .agency/session.db\n"
        f"llm:\n  models:\n    - id: {mid}\n      use_cases: [{uc}]\n"
        "      priority: 5\n",
        encoding="utf-8")
    return str(p)


@given("a config file with no llm block", target_fixture="cfg_path")
def _cfg_no_llm(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("core:\n  db_path: .agency/session.db\n", encoding="utf-8")
    return str(p)


@when("I load the registry from that config file")
def _load_from_cfg(ctx, cfg_path):
    ctx["registry"] = _llm.load_registry_from_config(cfg_path)


@then(parsers.parse('selecting "{uc}" from that registry yields "{mid}"'))
def _select_from_loaded(ctx, uc, mid):
    assert _llm.select_model(uc, registry=ctx["registry"]) == mid


@then("the loaded registry equals the built-in registry")
def _loaded_is_builtin(ctx):
    assert ctx["registry"] == _llm.default_registry()


@when("I validate that config file")
def _validate_cfg(ctx, cfg_path):
    from agency import _config
    ctx["issues"] = _config.config_validate(path=cfg_path)


@then(parsers.parse('no issue mentions "{needle}"'))
def _no_issue_mentions(ctx, needle):
    assert not any(needle in i for i in ctx["issues"]), ctx["issues"]


# ── generate (stub client, network-free) ────────────────────────────────────
class _StubResp:
    def __init__(self, text):
        self.choices = [type("C", (), {
            "message": type("M", (), {"content": text})(),
            "finish_reason": "stop",
        })()]


class _StubChat:
    def send(self, **kw):
        return _StubResp(f"generated for {kw.get('model')}")


class _StubClient:
    def __init__(self):
        self.chat = _StubChat()


@given("an LLMClient with a stub OpenRouter client")
def _stub_client(ctx):
    ctx["client"] = _llm.LLMClient(client=_StubClient())


@when(parsers.parse('I generate plain text for use-case "{uc}"'))
def _do_generate(ctx, uc):
    ctx["result"] = ctx["client"].generate("write a line", use_case=uc)


@then(parsers.parse('the result backend is "{backend}"'))
def _res_backend(ctx, backend):
    assert ctx["result"].backend == backend


@then(parsers.parse('the result model declares the "{uc}" use-case'))
def _res_model_uc(ctx, uc):
    reg = _llm.default_registry()
    prof = next((p for p in reg if p.id == ctx["result"].model), None)
    assert prof is not None and uc in prof.use_cases


@then('the result model id ends with ":free"')
def _res_model_free(ctx):
    assert ctx["result"].model.endswith(":free")


# ── free-first in the shared host-LLM seam (complete_or_delegate) ───────────
from agency._host_llm import complete_or_delegate, HostLLMRequest
from agency._drivers._anthropic import Completion


class _SeamDriver:
    """A driver whose backend()/complete() are deterministic — `complete`
    returns a marker so a test can prove the driver branch ran (not free)."""
    def __init__(self, backend: str):
        self._backend = backend

    def backend(self) -> str:
        return self._backend

    def complete(self, **kw):
        return Completion(text="DRIVER", stop_reason="end_turn")


@given("OPENROUTER_API_KEY is set in the seam environment")
def _seam_env(ctx):
    ctx["seam_env"] = {"OPENROUTER_API_KEY": "or"}


@given("AGENCY_GENERATE pins anthropic in the seam environment")
def _seam_pin_an(ctx):
    ctx["seam_env"]["AGENCY_GENERATE"] = "anthropic"


@given("the seam environment has no generation key")
def _seam_no_key(ctx):
    ctx["seam_env"] = {}


@given(parsers.parse('a stub LLMClient that generates for use-case "{uc}"'))
def _seam_llm(ctx, uc):
    ctx["seam_llm"] = _llm.LLMClient(client=_StubClient(), use_case=uc)


@given("a capable anthropic driver")
def _seam_driver(ctx):
    ctx["seam_driver"] = _SeamDriver("anthropic")


def _seam_call(ctx, **extra):
    driver = ctx.get("seam_driver") or _SeamDriver("none")
    return complete_or_delegate(
        driver,
        messages=[{"role": "user", "content": "draft this"}],
        env=ctx["seam_env"],
        llm=ctx.get("seam_llm"),
        use_case="prose",
        **extra)


@when("I complete-or-delegate plain text through the seam")
def _seam_plain(ctx):
    ctx["seam_out"] = _seam_call(ctx)


@when("I complete-or-delegate with an output schema through the seam")
def _seam_schema(ctx):
    ctx["seam_out"] = _seam_call(ctx, output_schema={"type": "object"})


@when(parsers.parse('I complete-or-delegate requiring "{req}" through the seam'))
def _seam_req(ctx, req):
    ctx["seam_out"] = _seam_call(ctx, require=req)


@when("I complete-or-delegate with a host completion through the seam")
def _seam_host(ctx):
    ctx["seam_out"] = _seam_call(ctx, host_completion={"text": "RESUMED"})


@then(parsers.parse('the completion stop reason is "{sr}"'))
def _seam_sr(ctx, sr):
    assert ctx["seam_out"].stop_reason == sr


@then('the completion model id ends with ":free"')
def _seam_free(ctx):
    assert ctx["seam_out"].model.endswith(":free")


@then("the completion text is from the driver")
def _seam_driver_text(ctx):
    assert ctx["seam_out"].text == "DRIVER"


@then("the seam returns a host-delegate envelope")
def _seam_envelope(ctx):
    assert isinstance(ctx["seam_out"], HostLLMRequest)
    assert ctx["seam_out"].kind == "llm_delegate"
