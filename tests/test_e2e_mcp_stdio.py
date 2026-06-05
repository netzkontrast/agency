"""Spec 039 §"End-to-end tests" — real JSON-RPC stdio roundtrip.

Marked @pytest.mark.e2e (slow); run via `pytest -q -m e2e`. Verifies
the WIRE contract that pytest's in-process tests can't reach:

  1. initialize handshake (protocolVersion + serverInfo.name='agency')
  2. tools/list returns exactly {search, get_schema, execute} (per
     CLAUDE.md doctrine — substrate tools reached via execute+code-mode)
  3. execute → call_tool('agency_welcome') round-trips
  4. execute → call_tool('capability_delegate_dispatch_decision')
     returns the Spec 040 six-field payload

The fixture resolves agency-mcp via the same logic as bin/agency-mcp's
discovery shim: PATH > .venv > bin/. Subprocess lifecycle uses
try/finally for guaranteed termination (no zombie processes).
"""
import json
import os
import select
import shutil
import subprocess
import time

import pytest


_TIMEOUT_RECV = 10.0    # per-message timeout
_TIMEOUT_PROC = 60.0    # total subprocess lifetime (kill threshold)


@pytest.fixture(scope="module")
def agency_mcp_binary():
    """Resolve the agency-mcp binary: PATH > plugin-venv > bin/.

    Spec 065 (pipx-direct doctrine): `agency-mcp` resolves from PATH
    only — the legacy `bin/agency-mcp` shim AND the Spec 063
    `.agency/.venv` fallback are both gone. Pipx install puts the
    console-script on PATH; that's the only resolution path.

    Raises pytest.skip if `agency-mcp` isn't on PATH (slim CI image
    where pipx hasn't run) so the test stays optional and doesn't
    block the default suite.
    """
    p = shutil.which("agency-mcp")
    if p:
        return p
    pytest.skip("agency-mcp not on PATH (Spec 065: pipx install required)")


def _send(p: subprocess.Popen, msg: dict) -> None:
    p.stdin.write((json.dumps(msg) + "\n").encode())
    p.stdin.flush()


def _recv(p: subprocess.Popen, timeout: float = _TIMEOUT_RECV) -> dict:
    """Read one newline-delimited JSON-RPC response.

    Uses select() to poll stdout so a hung server (no newline ever
    written) reliably times out at ``timeout`` seconds — a blocking
    ``readline()`` would otherwise sit forever and survive the
    surrounding deadline loop.
    """
    deadline = time.time() + timeout
    fd = p.stdout.fileno()
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError(f"no response within {timeout}s")
        ready, _, _ = select.select([fd], [], [], remaining)
        if not ready:
            raise TimeoutError(f"no response within {timeout}s")
        line = p.stdout.readline()
        if not line:
            # EOF — the server exited. Give it a tiny grace window
            # before declaring no response, in case more bytes arrive.
            if p.poll() is not None:
                raise TimeoutError(
                    f"server exited (rc={p.returncode}) without response")
            time.sleep(0.01)
            continue
        try:
            return json.loads(line.decode())
        except json.JSONDecodeError:
            continue


@pytest.fixture()
def mcp_proc(agency_mcp_binary):
    """Spawn agency-mcp; tear it down with try/finally so zombies
    don't survive test failures (Spec 039 §"Subprocess lifecycle
    discipline")."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Pin AGENCY_DB to in-memory so the test doesn't pollute the
    # working tree's .agency/session.db.
    env["AGENCY_DB"] = ":memory:"
    proc = subprocess.Popen(
        [agency_mcp_binary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )
    try:
        yield proc
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)


@pytest.mark.e2e
def test_initialize_returns_agency_servername(mcp_proc):
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "e2e", "version": "0"}}})
    r = _recv(mcp_proc)
    assert r["result"]["serverInfo"]["name"] == "agency"
    assert r["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.e2e
def test_tools_list_returns_the_three_wire_tools(mcp_proc):
    """CLAUDE.md doctrine: the MCP wire contract is exactly three tools
    (search/get_schema/execute). Substrate tools come through `execute`
    with code-mode, NOT as top-level MCP tools."""
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "e2e", "version": "0"}}})
    _recv(mcp_proc)
    _send(mcp_proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    time.sleep(0.2)
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list",
                     "params": {}})
    r = _recv(mcp_proc)
    tools = sorted(t["name"] for t in r["result"]["tools"])
    assert tools == ["execute", "get_schema", "search"]


@pytest.mark.e2e
def test_execute_reaches_substrate_via_code_mode(mcp_proc):
    """execute → call_tool('agency_welcome', {}) round-trips. This is
    THE doctrinal entry path for substrate tools (code-mode IS the
    contract)."""
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "e2e", "version": "0"}}})
    _recv(mcp_proc)
    _send(mcp_proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    time.sleep(0.2)
    code = ("return await call_tool(\"agency_welcome\", {})")
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": "execute",
                                "arguments": {"code": code}}})
    r = _recv(mcp_proc, timeout=15)
    body = r["result"]["content"][0]["text"]
    # The agency_welcome payload includes 'state' (fresh|in_progress)
    # and 'capabilities' map.
    assert "state" in body or "capabilities" in body


@pytest.mark.e2e
def test_execute_reaches_capability_verb_via_code_mode(mcp_proc):
    """execute reaches a CAPABILITY verb (Spec 040 dispatch_decision)
    after an intent_bootstrap chain. End-to-end proof the wire is
    intact for downstream verbs."""
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "e2e", "version": "0"}}})
    _recv(mcp_proc)
    _send(mcp_proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    time.sleep(0.2)
    code = (
        "i = await call_tool(\"intent_bootstrap\", "
        "{\"purpose\": \"e2e\", \"deliverable\": \"x\", \"acceptance\": \"x\"}); "
        "r = await call_tool(\"capability_delegate_dispatch_decision\", "
        "{\"intent_id\": i[\"intent_id\"], "
        "\"expected_return_tokens\": 6000, \"parallelism\": 4, "
        "\"read_only\": True}); "
        "return r"
    )
    _send(mcp_proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": "execute", "arguments": {"code": code}}})
    r = _recv(mcp_proc, timeout=15)
    body = r["result"]["content"][0]["text"]
    # Spec 040 six-field payload.
    assert "dispatch" in body
    assert "signals_fired" in body
    assert "driver" in body
