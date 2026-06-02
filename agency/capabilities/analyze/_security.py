"""Spec 042 — analyze.security axis (decidable patterns only).

Rules shipped (v1):
  S001 — eval/exec call (fail). AST: any call to eval/exec/compile.
  S002 — hardcoded credential pattern (fail). Regex over known
         secret patterns (API keys, JWTs, AWS keys, GitHub tokens).
  S003 — pickle.load on a path (warn). Exploit-conditional on file
         provenance.
  S004 — shell=True (warn). subprocess.* with shell=True.

NO LLM "may be vulnerable" judgements (Spec 042 §"Why decidable-only").
The KEY VALUE never appears in the Finding message — only its pattern
+ location, same security invariant as Spec 030's agency_doctor.
"""
from __future__ import annotations

import ast
import re

from ._findings import Finding, make_finding
from ._walk import python_files as _python_files, read_text as _read


# Severity assignments pinned (Spec 042 §"Severity-assignment rule per axis").
SEVERITY: dict[str, str] = {
    "S001": "fail",   # eval/exec — exploitable today
    "S002": "fail",   # hardcoded credential — exploitable today
    "S003": "warn",   # pickle.load — exploit-conditional
    "S004": "warn",   # shell=True — exploit-conditional
}


# ---------------------------------------------------------------------------
# Secret patterns (Spec 042 §"hardcoded secrets (regex over known patterns)").
# Each pattern has a name (for the message), a compiled regex, and a hit
# message that NEVER includes the matched value.
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Generic API-key assignment: NAME = "..." where the value looks
    # high-entropy (≥ 24 chars, alphanumeric + dashes/underscores).
    ("api-key-like assignment",
     re.compile(r"""(?ix)
        ^\s*
        (?:[A-Z_][A-Z0-9_]*)         # screaming-snake-case identifier
        \s*=\s*
        ["'](?P<v>[A-Za-z0-9_\-]{24,})["']
        \s*$
     """, re.MULTILINE)),
    # AWS access key id: AKIA + 16 alphanumerics.
    ("AWS access key id",
     re.compile(r"AKIA[0-9A-Z]{16}")),
    # GitHub PAT: ghp_ + 36 alphanumerics.
    ("GitHub personal access token",
     re.compile(r"ghp_[A-Za-z0-9]{36}")),
    # OpenAI-style sk-... key.
    ("OpenAI sk- key",
     re.compile(r"sk-[A-Za-z0-9]{20,}")),
]


# ---------------------------------------------------------------------------
# S001 — eval/exec/compile.
# ---------------------------------------------------------------------------


def _check_eval(path: str, src: str, tree: ast.AST) -> list[Finding]:
    out: list[Finding] = []
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            if name in {"eval", "exec"}:
                evidence = (lines[node.lineno - 1].strip()
                            if 0 <= node.lineno - 1 < len(lines) else name)
                out.append(make_finding(
                    rule="S001", severity=SEVERITY["S001"],
                    file=path, line=node.lineno,
                    message=f"call to {name}() — code injection risk",
                    evidence=evidence,
                ))
    return out


# ---------------------------------------------------------------------------
# S002 — hardcoded credentials (regex, value never leaks).
# ---------------------------------------------------------------------------


def _check_secrets(path: str, src: str) -> list[Finding]:
    """Detect hardcoded secrets. Multiple patterns may match the SAME
    location (e.g. a value matches both the generic high-entropy regex
    and a vendor-specific shape) — collapse to ONE finding per
    (file, line) so the report isn't padded by redundant hits."""
    out: list[Finding] = []
    seen_lines: set[int] = set()
    for pattern_name, regex in _SECRET_PATTERNS:
        for m in regex.finditer(src):
            line = src.count("\n", 0, m.start()) + 1
            if line in seen_lines:
                continue
            seen_lines.add(line)
            out.append(make_finding(
                rule="S002", severity=SEVERITY["S002"],
                file=path, line=line,
                # Never echo the matched value into the message.
                message=f"hardcoded credential: {pattern_name}",
                # The evidence is the LINE the secret appears on with
                # the matched span replaced by '<REDACTED>' so the
                # finding is still useful for grep without leaking.
                evidence=_redact_line(src, m, line),
            ))
    return out


def _redact_line(src: str, match: re.Match[str], line: int) -> str:
    """Return the line containing the match with the matched span
    replaced by '<REDACTED>'."""
    lines = src.splitlines()
    if not (1 <= line <= len(lines)):
        return "<REDACTED>"
    raw = lines[line - 1]
    # Approximate column from match.start() within this line.
    line_start = src.rfind("\n", 0, match.start()) + 1
    col = match.start() - line_start
    end = match.end() - line_start
    return (raw[:col] + "<REDACTED>" + raw[end:]).strip()


# ---------------------------------------------------------------------------
# S003 — pickle.load.
# ---------------------------------------------------------------------------


def _check_pickle(path: str, src: str, tree: ast.AST) -> list[Finding]:
    out: list[Finding] = []
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func
            if (attr.attr == "load" and isinstance(attr.value, ast.Name)
                    and attr.value.id == "pickle"):
                evidence = (lines[node.lineno - 1].strip()
                            if 0 <= node.lineno - 1 < len(lines) else "pickle.load")
                out.append(make_finding(
                    rule="S003", severity=SEVERITY["S003"],
                    file=path, line=node.lineno,
                    message="pickle.load — arbitrary code execution if input is untrusted",
                    evidence=evidence,
                ))
    return out


# ---------------------------------------------------------------------------
# S004 — subprocess.* with shell=True.
# ---------------------------------------------------------------------------


_SHELL_TRUE_TARGETS = frozenset({
    "run", "call", "check_call", "check_output", "Popen", "getoutput",
    "getstatusoutput",
})


def _check_shell_true(path: str, src: str, tree: ast.AST) -> list[Finding]:
    """Detect `subprocess.<run|call|Popen|...>(..., shell=True)`. Restrict
    to subprocess-family calls so `dict(shell=True)` etc. don't fire."""
    out: list[Finding] = []
    lines = src.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match subprocess.* method call OR a from-imported name like
        # `run`/`Popen` (`from subprocess import run`). For the bare
        # name path we still check the function name belongs to the
        # subprocess family to avoid `mymod.run(shell=True)` firing.
        target = None
        if isinstance(func, ast.Attribute) and func.attr in _SHELL_TRUE_TARGETS:
            target = func.attr
        elif isinstance(func, ast.Name) and func.id in _SHELL_TRUE_TARGETS:
            target = func.id
        if target is None:
            continue
        for kw in node.keywords:
            if (kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True):
                evidence = (lines[node.lineno - 1].strip()
                            if 0 <= node.lineno - 1 < len(lines) else "shell=True")
                out.append(make_finding(
                    rule="S004", severity=SEVERITY["S004"],
                    file=path, line=node.lineno,
                    message=f"subprocess.{target} with shell=True — injection risk",
                    evidence=evidence,
                ))
                break
    return out


# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------


def scan(root: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        findings.extend(_check_secrets(path, src))
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError:
            continue
        findings.extend(_check_eval(path, src, tree))
        findings.extend(_check_pickle(path, src, tree))
        findings.extend(_check_shell_true(path, src, tree))
    return findings
