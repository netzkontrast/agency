import pytest
from agency.capabilities.jules.patch import parse_unidiff, build_recovery_plan

def test_parse_add_only():
    with open("tests/fixtures/jules/add_only.patch") as f:
        diff = f.read()
    files = parse_unidiff(diff)
    assert len(files) == 1
    assert files[0] == {"path": "new_file.txt", "op": "add", "content": "hello world\n"}

def test_parse_mixed():
    with open("tests/fixtures/jules/mixed_add_modify.patch") as f:
        diff = f.read()
    files = parse_unidiff(diff)
    assert len(files) == 2
    assert files[0] == {"path": "new_file.txt", "op": "add", "content": "hello world\n"}
    assert files[1] == {"path": "existing_file.txt", "op": "modify", "content": "new content\n"}

def test_parse_rename():
    with open("tests/fixtures/jules/rename.patch") as f:
        diff = f.read()
    files = parse_unidiff(diff)
    assert len(files) == 1
    assert files[0]["path"] == "old_name.txt"
    assert files[0]["op"] == "rename"
    assert files[0]["new_path"] == "new_name.txt"

def test_parse_delete():
    with open("tests/fixtures/jules/delete.patch") as f:
        diff = f.read()
    files = parse_unidiff(diff)
    assert len(files) == 1
    assert files[0] == {"path": "deleted_file.txt", "op": "delete"}

def test_parse_malformed():
    with open("tests/fixtures/jules/malformed.patch") as f:
        diff = f.read()
    with pytest.raises(ValueError, match="Malformed diff header"):
        parse_unidiff(diff)

def test_parse_modify_partial_raises():
    with open("tests/fixtures/jules/modify_partial.patch") as f:
        diff = f.read()
    with pytest.raises(ValueError, match="Partial modify patches require I/O to apply; unsupported in pure parser"):
        parse_unidiff(diff)

def test_build_recovery_plan_single_output_add():
    with open("tests/fixtures/jules/add_only.patch") as f:
        diff = f.read()
    outputs = [{"changeSet": {"gitPatch": {"unidiffPatch": diff}}}]
    plan = build_recovery_plan(outputs, "recover-123", "main", "testowner", "testrepo", "123")
    assert plan["branch"] == "recover-123"
    assert plan["base_branch"] == "main"
    assert len(plan["ops"]) == 3
    assert plan["ops"][0] == {"tool": "mcp__github__create_branch", "args": {"owner": "testowner", "repo": "testrepo", "branch": "recover-123", "from_branch": "main"}}
    assert plan["ops"][1]["tool"] == "mcp__github__push_files"
    assert plan["ops"][1]["args"]["owner"] == "testowner"
    assert plan["ops"][1]["args"]["repo"] == "testrepo"
    assert plan["ops"][1]["args"]["branch"] == "recover-123"
    assert plan["ops"][1]["args"]["files"] == [{"path": "new_file.txt", "content": "hello world\n"}]
    assert plan["ops"][2]["tool"] == "mcp__github__create_pull_request"

def test_build_recovery_plan_multi_output_chaining():
    with open("tests/fixtures/jules/add_only.patch") as f1, \
         open("tests/fixtures/jules/delete.patch") as f2:
        outputs = [
            {"changeSet": {"gitPatch": {"unidiffPatch": f1.read()}}},
            {"changeSet": {"gitPatch": {"unidiffPatch": f2.read()}}}
        ]
    plan = build_recovery_plan(outputs, "recover-456", "main", "testowner", "testrepo", "456")
    ops = plan["ops"]
    assert ops[0] == {"tool": "mcp__github__create_branch", "args": {"owner": "testowner", "repo": "testrepo", "branch": "recover-456", "from_branch": "main"}}
    assert ops[1]["tool"] == "mcp__github__push_files"
    assert ops[1]["args"]["owner"] == "testowner"
    assert ops[1]["args"]["repo"] == "testrepo"
    assert ops[1]["args"]["branch"] == "recover-456"
    assert ops[1]["args"]["files"] == [{"path": "new_file.txt", "content": "hello world\n"}]
    assert ops[2]["tool"] == "mcp__github__delete_file"
    assert ops[2]["args"]["owner"] == "testowner"
    assert ops[2]["args"]["repo"] == "testrepo"
    assert ops[2]["args"]["branch"] == "recover-456"
    assert ops[2]["args"]["path"] == "deleted_file.txt"
    assert ops[3]["tool"] == "mcp__github__create_pull_request"
    assert plan["pr_title"] == "Recover Jules session 456"
