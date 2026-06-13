"""Spec 042 — analyze.security (the security axis).

Decidable security findings: eval/exec/shell=True, hardcoded
credentials, pickle.load, yaml.load without SafeLoader, SQL
string-format. NO LLM judgement.
"""
import os

from agency.capabilities.analyze import _security


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def test_eval_call_flagged_as_fail(tmp_path):
    body = (
        "def run(user_input):\n"
        "    return eval(user_input)\n"
    )
    _write(str(tmp_path), "e.py", body)
    findings = _security.scan(str(tmp_path))
    eval_hits = [f for f in findings if f.rule == "S001"]
    assert len(eval_hits) == 1
    assert eval_hits[0].severity == "fail"


def test_hardcoded_api_key_flagged_as_fail(tmp_path):
    body = 'API_KEY = "sk-1234567890abcdef1234567890abcdef"\n'
    _write(str(tmp_path), "secret.py", body)
    findings = _security.scan(str(tmp_path))
    key_hits = [f for f in findings if f.rule == "S002"]
    assert len(key_hits) >= 1
    assert key_hits[0].severity == "fail"
    # The KEY VALUE must NOT be in the message (only the pattern + location).
    assert "sk-1234567890abcdef" not in key_hits[0].message


def test_pickle_load_flagged_as_warn(tmp_path):
    body = (
        "import pickle\n"
        "def load(path):\n"
        "    return pickle.load(open(path, 'rb'))\n"
    )
    _write(str(tmp_path), "p.py", body)
    findings = _security.scan(str(tmp_path))
    p_hits = [f for f in findings if f.rule == "S003"]
    assert len(p_hits) == 1
    assert p_hits[0].severity == "warn"


def test_shell_true_flagged(tmp_path):
    body = (
        "import subprocess\n"
        "subprocess.run('rm -rf /tmp', shell=True)\n"
    )
    _write(str(tmp_path), "sh.py", body)
    findings = _security.scan(str(tmp_path))
    sh_hits = [f for f in findings if f.rule == "S004"]
    assert len(sh_hits) == 1


def test_shell_true_not_flagged_outside_subprocess(tmp_path):
    """Code-review F12: `shell=True` as a keyword on non-subprocess
    calls (e.g. `dict(shell=True)`, `MyConfig(shell=True)`) must NOT
    fire S004 — that's a false positive."""
    body = (
        "config = dict(shell=True, verbose=True)\n"
        "obj = SomeOther(shell=True)\n"
    )
    _write(str(tmp_path), "ok.py", body)
    findings = _security.scan(str(tmp_path))
    assert not [f for f in findings if f.rule == "S004"]


def test_two_fail_severity_fixture(tmp_path):
    """Spec 042 §Tests: fixture with 1 eval(...) + 1 hardcoded API key
    pattern; assert 2 fail-severity findings."""
    body = (
        'KEY = "sk-1234567890abcdef1234567890abcdef"\n'
        "def run(x): return eval(x)\n"
    )
    _write(str(tmp_path), "k.py", body)
    findings = _security.scan(str(tmp_path))
    fails = [f for f in findings if f.severity == "fail"]
    assert len(fails) == 2
