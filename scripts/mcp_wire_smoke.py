"""Drive the agency MCP server over stdio with raw JSON-RPC. Verifies:
   1) initialize handshake
   2) tools/list returns exactly {search, get_schema, execute}
   3) search reaches the registry
   4) execute with code-mode reaches a substrate tool (agency_welcome)
   5) execute with code-mode reaches a capability verb (dispatch_decision)
"""
import json
import os
import subprocess
import sys
import time


def _send(p, msg):
    line = json.dumps(msg) + "\n"
    p.stdin.write(line.encode()); p.stdin.flush()


def _recv(p, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = p.stdout.readline()
        if not chunk:
            time.sleep(0.05); continue
        try:
            return json.loads(chunk.decode())
        except json.JSONDecodeError:
            continue
    raise TimeoutError(f"no response within {timeout}s")


def main():
    env = os.environ.copy(); env["PYTHONUNBUFFERED"] = "1"
    p = subprocess.Popen(
        [sys.executable, "-m", "agency"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, cwd="/home/user/agency")
    try:
        # 1. initialize
        _send(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05",
                             "capabilities": {}, "clientInfo": {"name": "smoke", "version": "0"}}})
        r = _recv(p)
        print(f"[1] initialize: proto={r['result']['protocolVersion']} server={r['result']['serverInfo']['name']}")
        _send(p, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        time.sleep(0.2)
        # 2. tools/list
        _send(p, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        r = _recv(p)
        tools = sorted(t["name"] for t in r["result"]["tools"])
        print(f"[2] tools/list = {tools}")
        assert tools == ["execute", "get_schema", "search"], f"unexpected: {tools}"
        # 3. search
        _send(p, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": "search",
                             "arguments": {"query": "dispatch_decision"}}})
        r = _recv(p)
        body = r["result"]["content"][0]["text"]
        assert "capability_delegate_dispatch_decision" in body
        print("[3] search → dispatch_decision found")
        # 4. execute → substrate tool agency_welcome
        _send(p, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                  "params": {"name": "execute",
                             "arguments": {"code": "return await call_tool(\"agency_welcome\", {})"}}})
        r = _recv(p, timeout=15)
        body = r["result"]["content"][0]["text"]
        assert "state" in body or "capabilities" in body
        print(f"[4] execute/agency_welcome OK: {body[:120]}...")
        # 5. execute → capability verb dispatch_decision (Spec 040)
        _send(p, {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                  "params": {"name": "execute",
                             "arguments": {"code": (
                                 "i = await call_tool(\"intent_bootstrap\", "
                                 "{\"purpose\": \"mcp wire smoke for Spec 040\", "
                                 "\"deliverable\": \"6-field payload returned\", "
                                 "\"acceptance\": \"signals_fired non-empty for dispatch case\"}); "
                                 "r = await call_tool(\"capability_delegate_dispatch_decision\", "
                                 "{\"intent_id\": i[\"intent_id\"], "
                                 "\"expected_return_tokens\": 6000, \"parallelism\": 4, "
                                 "\"read_only\": True}); "
                                 "return r")}}})
        r = _recv(p, timeout=15)
        body = r["result"]["content"][0]["text"]
        assert "dispatch" in body and "signals_fired" in body
        print(f"[5] execute/dispatch_decision OK: {body[:200]}...")
        print("\nALL WIRE CHECKS PASS — MCP server serves the 3-tool contract correctly")
    finally:
        try: p.terminate(); p.wait(timeout=3)
        except Exception: p.kill()


main()
