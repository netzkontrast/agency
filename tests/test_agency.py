"""The agency engine's proof. Runs on the REAL substrate (graphqlite + fastmcp).

Proves: the provenance moat; one graph carries two genuinely different
capabilities (the plugin-dev craft + the REAL Jules agent); bi-temporal memory;
COMPLETED != done (real Jules verify); code-mode IS the contract
(search/get_schema/execute); code-mode tool-chaining; gates via elicit;
bash<->MCP isomorphism; schemas & templates; a strictly-enforced ontology; a
micro-step skill walker with a hard gate; and the plugin-development capability —
the skill-creation + plugin-authoring disciplines,
plus a self-hosted Claude Code install that maps macroskills -> micro-skills.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile

import pytest
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult

from agency import install, ontology
from agency.capabilities.plugin import lint_skill
from agency.engine import Engine
from agency.skill import SkillRun

REPO_DIR = os.path.dirname(os.path.dirname(__file__))
# code that lints a (deliberately bad) skill and returns just the violation count
_LINT_CODE = (
    "r = await call_tool('capability_plugin_lint_skill', "
    "{{'name': '{name}', 'description': '{desc}', 'intent_id': '{iid}'}})\n"
    "v = r['result'] if isinstance(r, dict) and 'result' in r else r\n"
    "return len(v['violations'])\n"
)

NAME_RE = re.compile(r"^[a-zA-Z0-9_]{1,64}$")  # MCP / Claude-frontend strict


def fresh(jules_client=None) -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), jules_client=jules_client)


def _sc(result):
    sc = result.structured_content
    if isinstance(sc, dict):
        return sc.get("result", sc)
    if sc is not None:
        return sc
    # scalar returns (e.g. execute returning an int) arrive as text content
    if result.content:
        txt = result.content[0].text
        try:
            return json.loads(txt)
        except (ValueError, TypeError):
            return txt
    return None


class StubJulesClient:
    """Boundary stand-in for the external Jules API (deterministic tests). The
    default backend (`JulesClient` -> the vendored `_jules_api`) is what the
    engine uses in production."""
    def __init__(self, state: str = "completed"):
        self._state = state

    def create(self, prompt: str, source: str, starting_branch: str) -> dict:
        return {"id": "sessions/123", "state": self._state,
                "url": "https://jules.google.com/session/123"}

    def get(self, session: str) -> dict:
        return {"state": self._state, "url": "https://jules.google.com/session/123"}


def run_scenario(e: Engine) -> str:
    """capture→confirm intent, open an agent lifecycle, run two genuinely
    different capabilities (a plugin-dev transform + the agent), pass a gate,
    complete. Returns the intent id."""
    iid = e.intent.capture("ship green CI", "auth test passes", "tests green")
    e.intent.confirm(iid)
    lc = e.lifecycle.open(iid, agent="jules")
    # a craft capability — validate a candidate skill (the CSO linter)
    e.registry.invoke(e.memory, iid, "plugin", "lint_skill",
                      name="fix-auth", description="Use when the auth test fails")
    # the agent capability — really dispatches Jules (stand-in backend on the engine)
    e.registry.invoke(e.memory, iid, "jules", "dispatch", agent_id="agent:jules",
                      source="owner/repo", starting_branch="main", prompt="fix auth")
    assert e.lifecycle.move(lc, "tests-green", ok=True) == "working"
    assert e.lifecycle.complete(lc) == "completed"
    return iid


def test_provenance_moat():
    e = fresh(StubJulesClient())
    iid = run_scenario(e)
    prov = e.memory.provenance(iid)

    verbs = sorted(n["verb"] for n in prov["serves"] if "verb" in n)
    assert verbs == ["dispatch", "lint_skill"]              # two different crafts, one graph
    assert {n["role"] for n in prov["serves"] if "role" in n} == {"transform", "effect"}
    assert any(a["id"] == "agent:jules" for a in prov["agents"])     # the agent that ran it
    assert any(p["kind"] == "jules-session" for p in prov["artefacts"])  # what it produced
    assert any(g["name"] == "tests-green" for g in prov["gates"])    # the gate it passed
    e.memory.close()


def test_bitemporal_what_changes_why_holds():
    e = fresh()
    iid = e.intent.capture("ship green CI", "fix auth test", "tests green")
    before = e.memory._tick
    new_id = e.intent.amend(iid, deliverable="fix auth AND token refresh")
    # old version still reconstructable as-of `before`; purpose (why) unchanged
    old = e.memory.recall(iid, as_of=before)
    assert old["deliverable"] == "fix auth test"
    assert e.memory.recall(new_id)["deliverable"] == "fix auth AND token refresh"
    assert e.memory.recall(new_id)["purpose"] == "ship green CI"
    e.memory.close()


def test_completed_not_done():
    """COMPLETED != done: a Jules session reports state=completed even when it
    paused before pushing. `verify` returns done only when a branch is actually
    on remote — the silent-fail guard."""
    e = fresh(StubJulesClient(state="completed"))
    iid = e.intent.capture("x", "y", "z")
    disp, _ = e.registry.invoke(e.memory, iid, "jules", "dispatch", agent_id="agent:j",
                                source="o/r", starting_branch="main", prompt="do x")
    assert disp["status"] == "completed"
    # state says completed, but no branch on remote -> NOT done (the silent-fail)
    assert e.registry.invoke(e.memory, iid, "jules", "verify",
                             state=disp["status"], branch_on_remote=False)[0]["done"] is False
    # branch actually on origin -> done
    assert e.registry.invoke(e.memory, iid, "jules", "verify",
                             state=disp["status"], branch_on_remote=True)[0]["done"] is True
    e.memory.close()


def test_codemode_is_the_contract():
    """No four-verb surface. The engine exposes exactly search/get_schema/execute;
    tools are discovered via search and called from inside execute. Lean."""
    e = fresh()
    iid = e.intent.capture("a", "b", "c")
    mcp = e.build_mcp()                                       # default: code-mode IS the contract

    async def main():
        names = {t.name for t in await mcp.list_tools()}
        assert names == {"search", "get_schema", "execute"}  # the whole contract
        assert all(NAME_RE.match(n) for n in names)
        hits = str(_sc(await mcp.call_tool("search", {"query": "lint skill"})))
        assert "capability_plugin_lint_skill" in hits        # discovery via search
        out = _sc(await mcp.call_tool("execute", {
            "code": _LINT_CODE.format(name="Bad Name", desc="does stuff", iid=iid)}))
        return int(out)

    assert asyncio.run(main()) == 2                           # bad name + missing "Use when"
    assert any(x["verb"] == "lint_skill" for x in e.memory.provenance(iid)["serves"])
    e.memory.close()


def test_codemode_chaining_is_an_executable_graph():
    """Code-mode chains different tools in plain Python — the code IS an
    executable dataflow graph. Token efficiency: many tool calls run in-sandbox,
    only ONE small delta crosses into context. And because every call_tool records
    an Invocation, that executable graph is MIRRORED into the durable provenance
    graph (the transform's pick feeds the agent, both edged to the intent)."""
    e = Engine(tempfile.mktemp(suffix=".db"), jules_client=StubJulesClient())  # boundary stand-in
    iid = e.intent.capture("ship a clean skill", "skill authored + dispatched", "lint clean")
    e.intent.confirm(iid)
    e.lifecycle.open(iid, agent="jules")                      # so agent:jules exists
    mcp = e.build_mcp(codemode=True)

    async def main():
        names = {t.name for t in await mcp.list_tools()}
        assert names == {"search", "get_schema", "execute"}   # raw tools hidden
        code = (
            "def val(x):\n"
            "    return x['result'] if isinstance(x, dict) and 'result' in x else x\n"
            "cands = [('alpha skill', 'does things'), ('good-skill', 'Use when you ship code'), ('ok-skill', 'manage things')]\n"
            "scored = []\n"
            "for nm, desc in cands:\n"
            f"    r = val(await call_tool('capability_plugin_lint_skill', {{'name': nm, 'description': desc, 'intent_id': '{iid}'}}))\n"
            "    scored.append((len(r['violations']), nm))\n"
            "scored.sort()\n"
            "best_v, best_name = scored[0]\n"
            "# chain: the linter's pick feeds the agent capability\n"
            f"p = val(await call_tool('capability_jules_dispatch', {{'source': 'o/r', 'starting_branch': 'main', 'prompt': best_name, 'intent_id': '{iid}', 'agent_id': 'agent:jules'}}))\n"
            "return {'min_violations': best_v, 'chosen': best_name, 'status': p['status']}\n"
        )
        return _sc(await mcp.call_tool("execute", {"code": code}))

    delta = asyncio.run(main())
    # the single small delta returned from many in-sandbox calls (token-efficient)
    assert delta["min_violations"] == 0
    assert delta["chosen"] == "good-skill"
    assert delta["status"] == "completed"

    # the executable chain is now a connected provenance subgraph
    prov = e.memory.provenance(iid)
    verbs = sorted(n["verb"] for n in prov["serves"] if "verb" in n)
    assert verbs == ["dispatch", "lint_skill", "lint_skill", "lint_skill"]  # 3 transforms + 1 effect, chained
    assert any(a["id"] == "agent:jules" for a in prov["agents"])
    assert any(p["kind"] == "jules-session" for p in prov["artefacts"])
    e.memory.close()


def test_gate_elicits_human_in_flow():
    """A gate/intent-verification step ELICITS a decision mid-flow (askuser in the
    flow): a one-line prompt streams to the human/agent, the answer resumes the
    chain, and the outcome is recorded as a Gate in the provenance graph. This is
    the atomic, token-tiny human-in-the-loop step."""
    e = fresh()
    iid = e.intent.capture("ship the release", "v1 published", "human approves")
    e.intent.confirm(iid)
    lc = e.lifecycle.open(iid, agent="jules")
    mcp = e.build_mcp(codemode=False)

    async def approve(message, response_type, params, context):
        return ElicitResult(action="accept", content="approve")   # simulate the human

    async def main():
        async with Client(mcp, elicitation_handler=approve) as client:
            r = await client.call_tool("lifecycle_gate", {
                "question": "Approve release?", "intent_id": iid, "lifecycle_id": lc,
            })
            return _sc(r)

    out = asyncio.run(main())
    assert out["approved"] is True
    # the human-in-the-loop verification is now a gate in the provenance graph
    prov = e.memory.provenance(iid)
    assert any(g["name"] == "human-confirm" and g["passed"] for g in prov["gates"])
    e.memory.close()


def test_schemas_and_templates_typed_generative():
    """The typed/generative layer. A Template GENERATES an Artefact (the `act`),
    a Schema VALIDATES it (the typed contract) — both are ordinary nodes in the
    one graph; the artefact is DERIVED_FROM the template and VALIDATES_AGAINST the
    schema. The schema also bites: a missing field fails validation."""
    e = fresh()
    iid = e.intent.capture("make a doc", "doc for X", "valid doc")
    e.intent.confirm(iid)
    schema = e.memory.record("Schema", {"name": "doc-sheet", "required": "title,body"})
    template = e.memory.record("Template", {"name": "doc-sheet", "body": "# {title}\n\n{body}"})

    # generate the artefact from the template
    data = {"title": "Test Doc", "body": "the content"}
    body = e.memory.recall(template)["body"].format(**data)
    art = e.memory.record("Artefact", {"kind": "doc-sheet", **data})
    e.memory.link(art, template, "DERIVED_FROM")
    e.memory.link(art, iid, "SERVES")

    # validate against the schema (the typed layer)
    assert e.memory.validate_schema(art, schema) is True
    e.memory.link(art, schema, "VALIDATES_AGAINST")
    assert "# Test Doc" in body and "the content" in body

    # the schema bites: an artefact missing a required field fails
    bad = e.memory.record("Artefact", {"kind": "doc-sheet", "title": "x"})
    assert e.memory.validate_schema(bad, schema) is False

    # the typed/generative edges live in the one graph
    rows = e.memory.g.query(
        "MATCH (a:Artefact)-[:VALIDATES_AGAINST]->(s:Schema) RETURN s")
    assert any(r["s"]["properties"].get("name") == "doc-sheet" for r in rows)
    drv = e.memory.g.query("MATCH (a:Artefact)-[:DERIVED_FROM]->(t:Template) RETURN t")
    assert any(r["t"]["properties"].get("name") == "doc-sheet" for r in drv)
    e.memory.close()


def test_isomorphism_mcp_equals_bash_cli():
    """Harness-in-harness: the SAME code-mode contract, driven via MCP in-process
    AND via a bash-only subprocess (no MCP client, no Skill loader — what Jules
    has), over the SAME persisted graph, yields identical results — and both
    invocations land in one graph. MCP ≡ bash, proven."""
    db = tempfile.mktemp(suffix=".db")
    e = Engine(db)
    iid = e.intent.capture("ship green CI", "auth test passes", "tests green")
    e.intent.confirm(iid)
    code = _LINT_CODE.format(name="Bad Name", desc="does stuff", iid=iid)

    # (1) MCP path — code-mode contract in-process
    mcp_out = _sc(asyncio.run(e.build_mcp(codemode=True).call_tool("execute", {"code": code})))
    e.memory.close()                                          # release the lock for the subprocess

    # (2) bash path — the same contract via a shell-only invocation
    proc = subprocess.run(
        [sys.executable, "-m", "agency.cli", "--db", db, "execute", "--code", code],
        cwd=REPO_DIR, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": REPO_DIR},
    )
    assert proc.returncode == 0, proc.stderr
    cli_out = json.loads(proc.stdout)

    assert int(mcp_out) == int(cli_out) == 2                  # identical across harnesses
    # shared durable graph: both runs recorded into the one graph
    e2 = Engine(db)
    lints = [n for n in e2.memory.provenance(iid)["serves"] if n.get("verb") == "lint_skill"]
    assert len(lints) == 2                                    # one via MCP, one via bash CLI
    e2.memory.close()


def test_ontology_is_strictly_enforced():
    """The strict schemata are enforced on the real graph: an out-of-schema node
    and an unknown edge both raise — the ontology cannot silently drift."""
    e = fresh()
    with pytest.raises(ValueError):                          # missing required Intent fields
        e.memory.record("Intent", {"purpose": "x"})
    iid = e.intent.capture("a", "b", "c")
    agent = e.memory.record("Agent", {"runtime": "local"}, node_id="agent:x")
    with pytest.raises(ValueError):                          # unknown edge type
        e.memory.link(agent, iid, "FROBNICATES")
    e.memory.close()


# a generic, domain-agnostic skill schema for exercising the walker mechanics
_WALKER_SKILL = {
    "name": "example-walk", "kind": "discipline", "phases": [
        {"index": 1, "name": "gather", "produces": ["facts", "context"]},
        {"index": 2, "name": "draft", "produces": ["draft"]},
        {"index": 3, "name": "approve", "produces": ["user_confirmed"], "gate": "hard"},
    ],
}


def test_skill_walker_micro_steps_with_hard_gate():
    """A skill walks ONE phase at a time (progressive disclosure), validates each
    phase's required outputs before advancing, and the hard-gate final phase
    blocks until explicitly confirmed. The run records itself as provenance."""
    e = fresh()
    iid = e.intent.capture("walk a skill", "a completed run", "user confirms")
    run = SkillRun(e.memory, iid, _WALKER_SKILL)

    assert run.current()["name"] == "gather" and "facts" in run.current()["produces"]
    with pytest.raises(ValueError):                          # missing a required output
        run.submit({"facts": "x"})
    assert run.submit({"facts": "x", "context": "c"})["status"] == "working"
    assert run.submit({"draft": "d"})["status"] == "working"

    assert run.current()["gate"] == "hard"                   # final phase = hard gate
    assert run.submit({"user_confirmed": "yes"}, confirmed=False)["status"] == "input-required"
    assert run.submit({"user_confirmed": "yes"}, confirmed=True)["status"] == "completed"
    assert run.done

    rows = e.memory.g.query("MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) RETURN p")
    assert len(rows) == 3                                     # the whole run is provenance
    e.memory.close()


def test_real_skill_executes_tools():
    """The skill-creation skill as an executable micro-step skill: the
    Iron Law ("no skill without a failing test first") is enforced by ordering —
    the walker cannot reach GREEN (author_skill) until RED produced its baseline.
    The GREEN + lint phases run REAL capability verbs (recorded as Invocations)."""
    e = fresh()
    iid = e.intent.capture("write a skill", "deployed skill", "human approves")
    run = SkillRun(e.memory, iid, e.ontology.skill("skill-creation"), registry=e.registry)

    # RED: baseline first (the Iron Law, enforced by phase ordering)
    assert run.current()["name"] == "red-baseline"
    assert run.submit({"baseline": "agent skips the failing test",
                       "rationalizations": "'too simple to test'"})["status"] == "working"
    # GREEN: author the skill (a REAL act verb runs)
    assert run.current()["name"] == "green-author"
    assert run.submit({"name": "my-skill", "description": "Use when you need X",
                       "body": "# My Skill\nbody"})["status"] == "working"
    assert any(n.get("verb") == "author_skill" for n in e.memory.provenance(iid)["serves"])
    # lint against the CSO rules (a REAL transform verb runs)
    assert run.current()["name"] == "lint"
    assert run.submit({"name": "my-skill", "description": "Use when you need X"})["status"] == "working"
    assert any(n.get("verb") == "lint_skill" for n in e.memory.provenance(iid)["serves"])
    # REFACTOR
    assert run.submit({"rationalization_table": "| excuse | reality |",
                       "red_flags": "code before test"})["status"] == "working"
    # deploy hard gate (STOP before next skill)
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"}, confirmed=False)["status"] == "input-required"
    assert run.submit({"user_confirmed": "yes"}, confirmed=True)["status"] == "completed"
    assert run.done
    e.memory.close()


def test_strict_enums_enforced_on_both_write_paths():
    """Design-loop refinement: closed enums are ENFORCED, not decorative. A bad
    role or lifecycle state raises — on record AND on the update mutation path."""
    e = fresh()
    iid = e.intent.capture("a", "b", "c")
    with pytest.raises(ValueError):                          # role not in ROLES
        e.memory.record("Invocation", {"capability": "x", "verb": "y", "role": "banana"})
    with pytest.raises(ValueError):                          # state not in LIFECYCLE_STATES
        e.memory.record("Lifecycle", {"state": "bogus", "phase": 0})
    lc = e.lifecycle.open(iid)                                # valid state via record
    with pytest.raises(ValueError):                          # update path is guarded too
        e.memory.update(lc, {"state": "bogus"})
    e.memory.close()


def test_plugin_capability_generates_valid_artefacts():
    """The plugin-development capability (skill creation +
    plugin authoring): every `act` verb renders a REAL artefact from a strict
    template, recorded as provenance and validating against its strict Schema."""
    e = fresh()
    iid = e.intent.capture("author a plugin", "plugin files", "valid")
    e.intent.confirm(iid)
    reg, mem = e.registry, e.memory

    res, _ = reg.invoke(mem, iid, "plugin", "scaffold",
                        name="demo", version="0.1.0", description="A demo plugin")
    manifest = json.loads(res["result"])                     # a real, valid JSON manifest
    assert manifest["name"] == "demo" and manifest["version"] == "0.1.0"

    # the artefact is provenance and validates against a strict Schema
    art_id = next(a["id"] for a in mem.provenance(iid)["artefacts"] if a["kind"] == "plugin-manifest")
    schema = mem.record("Schema", {"name": "plugin-manifest",                # schema OWNED by the capability
                                   "required": ",".join(e.ontology.schemas["plugin-manifest"])})
    assert mem.validate_schema(art_id, schema) is True
    # the schema bites: a manifest missing `version` fails
    bad = mem.record("Artefact", {"kind": "plugin-manifest", "name": "x"})
    assert mem.validate_schema(bad, schema) is False

    sk, _ = reg.invoke(mem, iid, "plugin", "author_skill",
                       name="my-skill", description="Use when you need X", body="# My Skill\nbody")
    assert sk["result"].startswith("---\nname: my-skill")    # the skill creator emits frontmatter
    reg.invoke(mem, iid, "plugin", "author_command", name="go", description="Use when go", body="do it")
    me, _ = reg.invoke(mem, iid, "plugin", "marketplace_entry", name="demo", version="0.1.0",
                       description="d", source="https://github.com/netzkontrast/agency")
    src = json.loads(me["result"])["source"]                 # a github URL -> github object (spec)
    assert src == {"source": "github", "repo": "netzkontrast/agency"}
    reg.invoke(mem, iid, "plugin", "step_doc", step="manifest", output="written")

    kinds = {a["kind"] for a in mem.provenance(iid)["artefacts"]}
    assert {"plugin-manifest", "skill-md", "command-md", "marketplace-entry", "step-doc"} <= kinds
    e.memory.close()


def test_lint_skill_ports_cso_rules():
    """The CSO rules as ENFORCEABLE compute (judgment as
    code): a clean skill passes; bad name, missing 'Use when…', first person, and
    over-length descriptions are each flagged."""
    assert lint_skill("good-name", "Use when you ship code")["ok"] is True
    bad = lint_skill("Bad Name", "does stuff")
    assert bad["ok"] is False
    assert any("letters, numbers, hyphens" in v for v in bad["violations"])
    assert any("Use when" in v for v in bad["violations"])
    assert any("third person" in v for v in lint_skill("ok-name", "Use when I help you")["violations"])
    assert any("500" in v for v in lint_skill("ok-name", "Use when " + "x" * 600)["violations"])


def test_plugin_dev_skill_each_step_yields_a_document():
    """The plugin-dev chain walks one phase at a time and EACH step yields a
    prestructured document (the 'resulting document of each step' pattern,
    made strict + provenance-recorded): manifest → skill → command → marketplace
    entry → hard confirm gate."""
    e = fresh()
    iid = e.intent.capture("develop a plugin", "a Claude Code plugin", "user confirms")
    run = SkillRun(e.memory, iid, e.ontology.skill("plugin-dev"), registry=e.registry)

    assert run.current()["name"] == "manifest"
    assert run.submit({"name": "demo", "version": "0.1.0", "description": "A demo"})["status"] == "working"
    assert run.submit({"name": "demo-skill", "description": "Use when you demo", "body": "# Demo"})["status"] == "working"
    assert run.submit({"name": "go", "description": "Use when go", "body": "do it"})["status"] == "working"
    assert run.submit({"name": "demo", "version": "0.1.0", "description": "A demo",
                       "source": "netzkontrast/agency"})["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"}, confirmed=False)["status"] == "input-required"
    assert run.submit({"user_confirmed": "yes"}, confirmed=True)["status"] == "completed"

    kinds = {a["kind"] for a in e.memory.provenance(iid)["artefacts"]}
    assert {"plugin-manifest", "skill-md", "command-md", "marketplace-entry"} <= kinds
    e.memory.close()


def test_help_maps_macroskills_to_microskills():
    """The `help` discovery surface maps the engine's capabilities (macroskills)
    to their verbs (the harness-in-harness micro-skills) over the LIVE registry —
    and a removed/unknown capability does not appear."""
    e = fresh()
    iid = e.intent.capture("discover", "the capability map", "ok")
    mcp = e.build_mcp(codemode=False)

    async def main():
        return _sc(await mcp.call_tool("capability_plugin_help", {"intent_id": iid}))

    out = asyncio.run(main())
    m = out["map"]
    assert {"plugin", "jules", "reflect"} <= set(m)
    assert "syllables" not in m
    assert {"scaffold", "author_skill", "lint_skill", "help"} <= set(m["plugin"])
    assert {"dispatch", "verify"} <= set(m["jules"])
    e.memory.close()


def test_agency_plugin_install_is_self_hosted():
    """The Agency Plugin for Claude Code install is SELF-HOSTED: the committed
    manifest, `help` macroskill, and command are exactly what the plugin-dev
    capability regenerates from the live registry — and the help skill passes its
    own CSO linter (the engine authors, and validates, its own plugin)."""
    e = fresh()
    files = install.generate(e)
    e.memory.close()
    for rel, content in files.items():                       # committed == regenerated (dogfood)
        with open(os.path.join(REPO_DIR, rel)) as f:
            assert f.read() == content, rel
    manifest = json.loads(files[".claude-plugin/plugin.json"])
    assert {"name", "version", "description"} <= set(manifest)
    assert lint_skill("help", install.HELP_DESC)["ok"] is True


def test_ontology_extends_strictly_from_capabilities():
    """The ontology is EXTENSIBLE: the core defines a base, and each capability
    contributes its own node types/skills/schemas, merged strictly onto the core.
    A bare core lacks `Plugin`; the engine's effective ontology has it (from the
    plugin capability) and enforces it in Memory; redefining a core node raises."""
    core = ontology.Ontology.core()
    assert "Intent" in core.nodes and "Plugin" not in core.nodes      # Plugin is NOT core
    assert "skill-creation" not in core.skills                        # nor is the skill-creation skill

    e = fresh()
    assert "Plugin" in e.ontology.nodes                               # contributed by the plugin capability
    assert {"skill-creation", "plugin-dev", "tdd"} <= set(e.ontology.skills)   # capability-owned
    # the extension is LIVE in Memory: the contributed node type is enforced
    with pytest.raises(ValueError):
        e.memory.record("Plugin", {"name": "x"})                      # missing version + description
    assert e.memory.record("Plugin", {"name": "x", "version": "0.1.0", "description": "d"})

    # strict: an extension may not redefine a core node with different fields
    with pytest.raises(ValueError):
        core.extend(ontology.OntologyExtension(nodes={"Intent": ["only_purpose"]}), owner="bad")
    e.memory.close()


def test_reflect_capability_writes_and_recalls():
    """The `reflect` capability — durable cross-session memory, added by DROPPING A
    FILE in capabilities/. It owns
    its ontology (a Reflection node + scope enum), the engine injects `memory`, and
    its writes are provenance (OBSERVED_DURING the intent)."""
    e = fresh()
    iid = e.intent.capture("learn from the run", "durable notes", "ok")
    e.intent.confirm(iid)
    reg, mem = e.registry, e.memory
    reg.invoke(mem, iid, "reflect", "note", scope="technical",
               text="graphqlite autocommits across connections")
    reg.invoke(mem, iid, "reflect", "note", scope="user", text="prefers terse updates")

    alln = reg.invoke(mem, iid, "reflect", "recall")[0]["result"]
    assert {n["scope"] for n in alln} == {"technical", "user"}            # newest-first list
    tech = reg.invoke(mem, iid, "reflect", "recall", scope="technical")[0]["result"]
    assert len(tech) == 1 and "graphqlite" in tech[0]["text"]
    hits = reg.invoke(mem, iid, "reflect", "search", query="terse")[0]["result"]
    assert len(hits) == 1 and hits[0]["scope"] == "user"

    with pytest.raises(ValueError):                                       # scope enum (owned) bites
        reg.invoke(mem, iid, "reflect", "note", scope="bogus", text="x")
    rows = mem.g.query("MATCH (r:Reflection)-[:OBSERVED_DURING]->(i:Intent) "
                       "WHERE i.id = $iid RETURN r", {"iid": iid})
    assert len(rows) == 2                                                 # reflections are provenance
    e.memory.close()


def test_develop_capability_ships_walkable_dev_skills():
    """The `develop` capability implements the development disciplines as
    first-class agency skills: the engine walks one (tdd) phase by
    phase through its hard gate, recording provenance, and `checklist` returns a
    discipline's steps. The Iron Law (RED before GREEN) is enforced by ordering."""
    e = fresh()
    iid = e.intent.capture("develop the system", "a tested change", "tests pass")

    # checklist is real compute over the shipped schemas
    cl = e.registry.invoke(e.memory, iid, "develop", "checklist", discipline="tdd")[0]["result"]
    assert [s["name"] for s in cl["steps"]] == ["red", "green", "refactor", "verify"]

    # the discipline is a walkable agency skill (a Lifecycle template)
    run = SkillRun(e.memory, iid, e.ontology.skill("tdd"))
    assert run.current()["name"] == "red"                      # RED first (the Iron Law, by ordering)
    assert run.submit({"failing_test": "test_x asserts behavior"})["status"] == "working"
    assert run.submit({"implementation": "minimal code"})["status"] == "working"
    assert run.submit({"refactored": "cleaned"})["status"] == "working"
    assert run.current()["gate"] == "hard"                     # verify is a hard gate
    assert run.submit({"tests_pass": "yes"}, confirmed=False)["status"] == "input-required"
    assert run.submit({"tests_pass": "yes"}, confirmed=True)["status"] == "completed"

    # all seven dev disciplines ship as skills, and `develop` is a macroskill
    assert {"brainstorm", "plan", "tdd", "debug", "verify", "spec-panel", "review"} <= set(e.ontology.skills)
    caps = {n: list(e.registry.get(n).verbs) for n in e.registry.names()}
    assert "develop" in caps and "checklist" in caps["develop"]
    e.memory.close()


def _walk_to_completion(run, schema):
    for ph in schema["phases"]:
        outputs = {k: "x" for k in ph["produces"]}
        if ph.get("gate") == "hard":
            assert run.submit(outputs, confirmed=False)["status"] == "input-required"
            assert run.submit(outputs, confirmed=True)["status"] == "completed"
        else:
            assert run.submit(outputs)["status"] == "working"


def test_every_dev_skill_walks_to_a_hard_gate():
    """Each development discipline is a walkable Lifecycle template ending in a
    hard gate that blocks until explicitly confirmed."""
    from agency.capabilities.develop import DEV_SKILLS
    for name, schema in DEV_SKILLS.items():
        assert schema["phases"][-1].get("gate") == "hard", name
        e = fresh()
        iid = e.intent.capture("develop", "a run", "ok")
        run = SkillRun(e.memory, iid, e.ontology.skill(name))
        _walk_to_completion(run, schema)
        assert run.done, name
        e.memory.close()


def test_checklist_returns_steps_and_handles_unknown():
    e = fresh(); iid = e.intent.capture("a", "b", "c"); reg, mem = e.registry, e.memory
    for d in ("brainstorm", "plan", "tdd", "debug", "verify", "spec-panel", "review"):
        r = reg.invoke(mem, iid, "develop", "checklist", discipline=d)[0]["result"]
        assert r["discipline"] == d and r["steps"] and r["steps"][-1]["gate"] == "hard"
    bad = reg.invoke(mem, iid, "develop", "checklist", discipline="nope")[0]["result"]
    assert "error" in bad and "brainstorm" in bad["available"]
    e.memory.close()


def test_all_shipped_skills_are_lint_clean():
    """Every installable SKILL.md the plugin ships passes the engine's own CSO
    linter — the engine validates its own skills."""
    skills_dir = os.path.join(REPO_DIR, "skills")
    found = 0
    for name in os.listdir(skills_dir):
        path = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.exists(path):
            continue
        text = open(path).read()
        nm = re.search(r"^name:\s*(.+)$", text, re.M).group(1).strip()
        desc = re.search(r"^description:\s*(.+)$", text, re.M).group(1).strip()
        res = lint_skill(nm, desc)
        assert res["ok"], (name, res["violations"])
        found += 1
    assert found >= 8


def test_templates_render_expected_shapes():
    e = fresh(); iid = e.intent.capture("a", "b", "c"); reg, mem = e.registry, e.memory
    cmd = reg.invoke(mem, iid, "plugin", "author_command",
                     name="go", description="Use when go", body="do it")[0]["result"]
    assert cmd.startswith("---\ndescription: Use when go") and "do it" in cmd
    doc = reg.invoke(mem, iid, "plugin", "step_doc",
                     step="manifest", output="written", inputs="name", notes="n")[0]["result"]
    assert "## Inputs" in doc and "## Output" in doc and "## Notes" in doc
    for path in ("./local", "plugins/agency"):           # relative paths stay strings, never auto-github'd
        rel = json.loads(reg.invoke(mem, iid, "plugin", "marketplace_entry",
                                    name="x", version="0.1.0", description="d", source=path)[0]["result"])
        assert rel["source"] == path
    e.memory.close()


def test_ontology_collisions_and_enum_widening():
    from agency.ontology import Ontology, OntologyExtension
    o = Ontology.core()
    o.extend(OntologyExtension(skills={"s": {"name": "s", "kind": "x", "phases": []}}), "a")
    with pytest.raises(ValueError):                      # duplicate skill name
        o.extend(OntologyExtension(skills={"s": {"name": "s", "kind": "x", "phases": []}}), "b")
    o.extend(OntologyExtension(templates={"t": "x"}), "a")
    with pytest.raises(ValueError):                      # duplicate template name
        o.extend(OntologyExtension(templates={"t": "y"}), "b")
    o2 = Ontology.core()
    o2.extend(OntologyExtension(enums={("N", "f"): {"a"}}), "a")
    o2.extend(OntologyExtension(enums={("N", "f"): {"b"}}), "b")   # enums WIDEN, never collide
    assert o2.enums[("N", "f")] == {"a", "b"}


def test_ontology_extension_contract_all_six_kinds():
    """The defined extension contract: a capability extends the ontology in six
    ways (nodes, edges, enums, skills, schemas, templates), each merged onto the
    core and enforced live in Memory."""
    from agency.ontology import Ontology, OntologyExtension
    from agency.memory import Memory
    ext = OntologyExtension(
        nodes={"Widget": ["name", "size"]},
        edges={"ATTACHES_TO"},
        enums={("Widget", "size"): {"s", "m", "l"}},
        skills={"assemble": {"name": "assemble", "kind": "x",
                             "phases": [{"index": 1, "name": "build", "produces": ["part"]}]}},
        schemas={"widget-doc": ["name", "size"]},
        templates={"widget": "# $name"},
    )
    ont = Ontology.core().extend(ext, owner="widgets")
    assert "Widget" in ont.nodes and "ATTACHES_TO" in ont.edges
    assert ont.enums[("Widget", "size")] == {"s", "m", "l"}
    assert "assemble" in ont.skills and ont.schemas["widget-doc"] == ["name", "size"]
    assert ont.templates["widget"] == "# $name"

    mem = Memory(tempfile.mktemp(suffix=".db"), ont=ont)
    with pytest.raises(ValueError):                       # missing required 'size'
        mem.record("Widget", {"name": "w"})
    with pytest.raises(ValueError):                       # size not in the contributed enum
        mem.record("Widget", {"name": "w", "size": "xl"})
    w = mem.record("Widget", {"name": "w", "size": "m"})
    a = mem.record("Widget", {"name": "a", "size": "s"})
    mem.link(w, a, "ATTACHES_TO")                         # the contributed edge is allowed
    with pytest.raises(ValueError):                       # an edge NOT in the effective set still raises
        mem.link(w, a, "NOPE")
    mem.close()


def test_music_capability_owns_conceptualizer():
    """The `music` DOMAIN capability owns the conceptualizer — a 7-phase gated
    planning skill — plus an `Album` node type with a closed `type` enum. Proof a
    domain capability extends the ontology (skill + node + enum) without touching
    the core."""
    from agency.capabilities.music import ALBUM_TYPES
    e = fresh()
    iid = e.intent.capture("plan an album", "album concept", "user confirms")

    sk = e.ontology.skill("album-concept")                   # owned by music, not core
    assert len(sk["phases"]) == 7 and sk["phases"][-1].get("gate") == "hard"
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"artist": "a", "genre": "g", "type": "thematic", "scale": "ep", "theme": "t", "true_story": "no"},
        {"key_subjects": "k", "emotional_core": "e", "why": "w"},
        {"references": "r", "production_style": "p", "vocal_approach": "v",
         "instrumentation": "i", "mood": "m", "target_duration": "4:00"},
        {"tracklist": "t", "sequencing": "s", "energy_map": "e"},
        {"visual_concept": "v", "palette": "p", "symbols": "s"},
        {"album_title": "t", "track_titles": "t", "research_needs": "n",
         "explicit": "no", "distributor_genres": "g"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"}, confirmed=True)["status"] == "completed"

    e.intent.confirm(iid)
    res, _ = e.registry.invoke(e.memory, iid, "music", "conceptualize",
                               artist="A", title="T", type="narrative", theme="x")
    assert "# T" in res["result"]
    assert any(a["kind"] == "album-concept" for a in e.memory.provenance(iid)["artefacts"])
    with pytest.raises(ValueError):                          # the capability-owned type enum bites
        e.memory.record("Album", {"artist": "A", "title": "T", "type": "polka"})
    e.memory.close()


def test_rejected_gate_pauses_lifecycle_and_is_provenance():
    """A rejected human gate pauses the Lifecycle at input-required AND records a
    blocked Gate that provenance surfaces."""
    e = fresh()
    iid = e.intent.capture("ship the release", "v1 published", "human approves")
    e.intent.confirm(iid)
    lc = e.lifecycle.open(iid, agent="jules")
    mcp = e.build_mcp(codemode=False)

    async def reject(message, response_type, params, context):
        return ElicitResult(action="accept", content="reject")

    async def main():
        async with Client(mcp, elicitation_handler=reject) as client:
            return _sc(await client.call_tool("lifecycle_gate", {
                "question": "Approve?", "intent_id": iid, "lifecycle_id": lc}))

    out = asyncio.run(main())
    assert out["approved"] is False
    assert e.lifecycle.status(lc) == "input-required"        # rejected gate pauses the lifecycle
    gates = e.memory.provenance(iid)["gates"]
    assert any(g["name"] == "human-confirm" and not g["passed"] for g in gates)   # blocked gate is provenance
    e.memory.close()


def test_lifecycle_gate_guards_mismatched_intent():
    e = fresh()
    iid = e.intent.capture("a", "b", "c")
    other = e.intent.capture("x", "y", "z")
    lc = e.lifecycle.open(iid)
    mcp = e.build_mcp(codemode=False)

    async def approve(message, response_type, params, context):
        return ElicitResult(action="accept", content="approve")

    async def main():
        async with Client(mcp, elicitation_handler=approve) as client:
            return _sc(await client.call_tool("lifecycle_gate", {
                "question": "?", "intent_id": other, "lifecycle_id": lc}))   # lc serves iid, not other

    out = asyncio.run(main())
    assert out["approved"] is False and "error" in out
    e.memory.close()


def test_failed_move_records_a_blocked_gate():
    e = fresh()
    iid = e.intent.capture("a", "b", "c")
    lc = e.lifecycle.open(iid)
    assert e.lifecycle.move(lc, "tests-green", ok=False) == "input-required"
    gates = e.memory.provenance(iid)["gates"]
    assert any(g["name"] == "tests-green" and not g["passed"] for g in gates)
    e.memory.close()


def test_provenance_follows_the_amend_chain():
    """After `amend` (a supersede that forks a new intent id), provenance from
    EITHER id gathers actions across the whole SUPERSEDED_BY chain."""
    e = fresh()
    iid = e.intent.capture("ship", "v1", "ok")
    e.intent.confirm(iid)
    e.registry.invoke(e.memory, iid, "plugin", "lint_skill", name="a", description="Use when a")
    new = e.intent.amend(iid, deliverable="v2")
    e.registry.invoke(e.memory, new, "plugin", "lint_skill", name="b", description="Use when b")
    for q in (iid, new):
        verbs = [n.get("verb") for n in e.memory.provenance(q)["serves"] if n.get("verb")]
        assert verbs.count("lint_skill") == 2                # both pre- and post-amend invocations
    e.memory.close()


def test_agent_node_recorded_once_across_opens():
    e = fresh()
    iid = e.intent.capture("a", "b", "c")
    e.lifecycle.open(iid, agent="jules")
    before = e.memory.recall("agent:jules")
    e.lifecycle.open(iid, agent="jules")                     # reuse the node, don't rewrite its history
    after = e.memory.recall("agent:jules")
    assert before["vfrom"] == after["vfrom"]
    e.memory.close()


def test_cli_emits_json_on_error():
    db = tempfile.mktemp(suffix=".db")
    proc = subprocess.run(
        [sys.executable, "-m", "agency.cli", "--db", db, "execute", "--code", "raise ValueError('boom')"],
        cwd=REPO_DIR, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": REPO_DIR})
    assert proc.returncode == 1
    out = json.loads(proc.stdout)                            # ONE JSON document, never a raw traceback
    assert "error" in out


def test_reflect_is_the_class_form():
    """The reference migration: `reflect` is authored as a CapabilityBase subclass,
    yet registers + behaves identically (verbs note/recall/search)."""
    from agency.capability import CapabilityBase
    from agency.capabilities.reflect import ReflectCapability
    assert issubclass(ReflectCapability, CapabilityBase)
    e = fresh()
    assert set(e.registry.get("reflect").verbs) == {"note", "recall", "search"}
    e.memory.close()


def test_capability_context_delegates_with_provenance_and_guards_recursion():
    """A CapabilityBase verb reaches everything via `self.ctx`: `ctx.call` delegates
    to a sibling capability and the delegated Invocation is provenance too; a
    self-call is stopped by the recursion-depth guard."""
    from agency.capability import CapabilityBase, verb

    class Compose(CapabilityBase):
        name = "compose"
        home = "capability"

        @verb(role="act")
        def lint_then_note(self, name: str, description: str) -> dict:
            res = self.ctx.call("plugin", "lint_skill", name=name, description=description)
            rid = self.ctx.record("Reflection", {"scope": "technical", "text": f"ok={res['ok']}"})
            self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
            return {"result": {"ok": res["ok"], "note": rid}}

    class Loop(CapabilityBase):
        name = "loop"
        home = "capability"

        @verb(role="transform")
        def go(self) -> dict:
            return {"result": self.ctx.call("loop", "go")}

    e = fresh()
    e.registry.register(Compose.as_capability())             # opportunistic late registration
    e.registry.register(Loop.as_capability())
    iid = e.intent.capture("compose", "a clean skill", "ok")
    e.intent.confirm(iid)

    out, _ = e.registry.invoke(e.memory, iid, "compose", "lint_then_note",
                               name="good-name", description="Use when you ship code")
    assert out["result"]["ok"] is True
    # both the compose verb AND the delegated lint_skill are recorded as SERVING the intent
    verbs = [n.get("verb") for n in e.memory.provenance(iid)["serves"] if n.get("verb")]
    assert "lint_then_note" in verbs and "lint_skill" in verbs

    with pytest.raises(ValueError):                          # ctx.call recursion guard
        e.registry.invoke(e.memory, iid, "loop", "go")
    e.memory.close()
