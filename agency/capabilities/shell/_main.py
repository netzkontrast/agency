# agency-scaffold: v1
"""shell — a token-efficient, recorded, templated host-command boundary (Spec 073).

Shell is a token-efficient host-command boundary: allowlisted execution, output filtering, and definable templates that bundle a command with its token-saving filter.

Use when: running a host CLI command whose output should be token-filtered and recorded — an allowlisted command, a reusable template, or a pure output filter.
Triggers:
- A bash command whose full output would flood the context
- A common command rerun often enough to template
- Host output that needs trimming before it crosses back
Red flags:
- Dumping a long command's full output → trim it via capability_shell_filter
- Re-composing the same command and filter → save it with capability_shell_define
"""
from __future__ import annotations

import re
import shlex

from ..._capture import keep_full
from ...capability import CapabilityBase, verb

# AGENCY-DRIFT: shell-allowlist — the tools shell.run may invoke (command's first
# token). Extend deliberately; wire input is NEVER executed unless its tool is here.
_ALLOWED_TOOLS = {
    "python", "pytest", "git", "grep", "rg", "ls", "cat", "head", "tail", "wc",
    "find", "ruff", "sed", "awk", "echo", "diff", "sort", "uniq", "nl",
    "scripts/check-drift", "scripts/test-cap", "scripts/test-changed",
}

# AGENCY-DRIFT: shell-templates — named query recipes (write-less) SEED set. The
# agent calls run(template="…") instead of composing the command + filter each
# time. Spec 075: this dict is only the SEED — `shell.define` adds graph-stored
# templates (Artefact{kind:"command-template"}) that EXTEND/override these, so the
# registry is definable (CLAUDE.md #8), not a frozen surface.
_TEMPLATES = {
    "tests":          {"command": "python -m pytest -n auto -m 'not e2e' -q", "filter": "tail:4", "doc": "full pytest slice → summary line"},
    "test-failures":  {"command": "python -m pytest -m 'not e2e' -q",          "filter": "grep:FAILED", "doc": "only the FAILED test lines"},
    "drift":          {"command": "scripts/check-drift",                       "filter": "tail:3", "doc": "drift-gate verdict"},
    "changed":        {"command": "scripts/test-changed",                      "filter": "tail:4", "doc": "tests for changed capabilities"},
    "recent-commits": {"command": "git log --oneline -10",                     "filter": "full", "doc": "last 10 commits"},
    # Spec 075 — common bash recipes surveyed from recent sessions, each with the
    # filter that makes it token-cheap (documented config per CLAUDE.md #8).
    "status":         {"command": "git status --short",                        "filter": "full", "doc": "working-tree changes (terse)"},
    "diffstat":       {"command": "git diff --stat",                           "filter": "full", "doc": "changed files + line counts"},
    "grep-hits":      {"command": "rg -n",                                     "filter": "head:40", "doc": "ripgrep matches (append PATTERN PATH via args); first 40"},
}
_MAX_OUTPUT = 4000   # hard token guard on returned/recorded output

_TEMPLATE_KIND = "command-template"   # Spec 075 — graph-stored template Artefacts


def _first_token(command: str):
    """The command's first token (the allowlist key) or '' when unparseable.
    Returns (tool, error|None) so callers share one parse + allowlist check."""
    try:
        argv = shlex.split(command or "")
    except ValueError as e:
        return "", f"unparseable command: {e}"
    return (argv[0] if argv else ""), None


def _graph_templates(memory) -> dict:
    """Current command-template Artefacts as {name: {command, filter, doc, tags, id}}.
    Bi-temporal: `find` returns only the currently-valid version (a redefine
    supersedes the prior), so the latest definition per name wins."""
    out: dict = {}
    for a in memory.find("Artefact"):
        if a.get("kind") != _TEMPLATE_KIND:
            continue
        out[a.get("name")] = {
            "command": a.get("command", ""), "filter": a.get("filter", ""),
            "doc": a.get("doc", ""), "tags": a.get("tags", ""), "id": a.get("id"),
        }
    return out


def _resolve_templates(memory) -> dict:
    """Seeds ∪ graph templates, graph overriding a same-named seed (Spec 075).
    Each entry carries a `source` ∈ {seed, graph} so discovery can show provenance."""
    merged = {n: {**t, "source": "seed"} for n, t in _TEMPLATES.items()}
    for name, t in _graph_templates(memory).items():
        merged[name] = {"command": t["command"], "filter": t["filter"],
                        "doc": t["doc"], "tags": t["tags"], "source": "graph"}
    return merged


def _apply_filter(text: str, spec: str) -> str:
    """Reduce command output to the requested slice (the token-economy core).
    spec ∈ full | tail:N | head:N | grep:PAT | lines:A-B | count | last."""
    lines = (text or "").splitlines()
    spec = (spec or "").strip()
    if spec == "count":
        return str(len([ln for ln in lines if ln.strip()]))
    if spec == "last":
        nonempty = [ln for ln in lines if ln.strip()]
        return nonempty[-1] if nonempty else ""
    if not spec or spec == "full":
        out = "\n".join(lines)
    elif spec.startswith("tail:"):
        out = "\n".join(lines[-int(spec[5:] or 0):]) if int(spec[5:] or 0) else ""
    elif spec.startswith("head:"):
        out = "\n".join(lines[:int(spec[5:] or 0)])
    elif spec.startswith("grep:"):
        pat = re.compile(re.escape(spec[5:]))
        out = "\n".join(ln for ln in lines if pat.search(ln))
    elif spec.startswith("lines:"):
        a, _, b = spec[6:].partition("-")
        out = "\n".join(lines[int(a) - 1:int(b or a)])
    else:
        out = "\n".join(lines)
    return out[:_MAX_OUTPUT]


def capture_filter(command: str, output: str, *, spec: str = "head:20") -> str:
    """Spec 336 S3 — a clean, token-filtered VIEW of a bash call for the ephemeral
    capture's ``filtered`` column (the cheap structured view the export prefers).

    The FULL command + output are stored separately in the tool-call store
    (``keep_full``); this is a derived convenience over the shell token-economy
    filter, so bounding the VIEW loses no data. Returns
    ``"$ <command>\\n<filtered output>"``. Used MANDATORILY by the hook capture
    path for every Bash call — execution is unchanged (capture & filter only).
    """
    head = f"$ {command}".rstrip()
    body = _apply_filter(output or "", spec) if output else ""
    return f"{head}\n{body}".rstrip() if body else head




class ShellCapability(CapabilityBase):
    name = "shell"
    home = "capability"

    @verb(role="transform")
    def templates(self, query: str = "") -> dict:
        """Discover named query templates — built-in seeds ∪ graph-defined (Spec 075).

        Inputs: query (optional — matches name/doc/tags, case-insensitive; ""=all).
        Returns: ``{result: [{name, command, filter, doc, tags, source}, …]}``
                 (``source`` ∈ seed|graph), name-sorted; ranked by match locus
                 when a query is given.
        chain_next: ``shell.run(template=<name>)`` or ``shell.define(…)`` to add one.
        """
        merged = _resolve_templates(self.ctx.memory)
        items = [{"name": n, "command": t.get("command", ""),
                  "filter": t.get("filter", ""), "doc": t.get("doc", ""),
                  "tags": t.get("tags", ""), "source": t.get("source", "seed")}
                 for n, t in merged.items()]

        def locus(it) -> int:
            q = query.lower()
            if q in it["name"].lower():
                return 0
            if q in str(it.get("tags", "")).lower():
                return 1
            if q in str(it.get("doc", "")).lower():
                return 2
            return 99

        if query:
            items = [it for it in items if locus(it) < 99]
            items.sort(key=lambda it: (locus(it), it["name"]))
        else:
            items.sort(key=lambda it: it["name"])
        return {"result": items}

    @verb(role="act")
    def define(self, name: str, command: str, filter: str,
               doc: str = "", tags: str = "") -> dict:
        """Define a named shell template (command + output filter + doc) in the graph.

        Records an ``Artefact{kind:"command-template", name, command, filter, doc,
        tags}`` so the registry is definable (CLAUDE.md #8), not a frozen dict.
        Re-defining a name SUPERSEDES the prior version (bi-temporal trail kept).
        The command's first token MUST be allowlisted — a template can't smuggle
        an un-allowlisted tool into ``run``.

        Inputs: name, command (first token allowlisted), filter (output slice —
                full|tail:N|head:N|grep:PAT|lines:A-B|count|last), doc, tags
                (space/comma-separated, for discovery).
        Returns: ``{name, template_id, command, filter}``; or ``{error, …}`` on a
                 disallowed tool / unparseable command.
        chain_next: ``shell.run(template=<name>)`` or ``shell.templates(query=)``.
        """
        tool, err = _first_token(command)
        if err:
            return {"result": {"error": err}}
        if tool not in _ALLOWED_TOOLS:
            return {"result": {"error": f"tool {tool!r} not allowlisted",
                               "allowed": sorted(_ALLOWED_TOOLS)}}
        props = {"kind": _TEMPLATE_KIND, "name": name, "command": command,
                 "filter": filter, "doc": doc, "tags": tags}
        existing = _graph_templates(self.ctx.memory).get(name)
        if existing:                                   # redefine → supersede the prior version
            tid = self.ctx.memory.supersede(existing["id"], props)
        else:
            tid = self.ctx.record("Artefact", props)
        self.ctx.link(tid, self.ctx.intent_id, "SERVES")
        self.ctx.link(tid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"result": {"name": name, "template_id": tid,
                           "command": command, "filter": filter}}

    @verb(role="transform")
    def filter(self, text: str, spec: str = "tail:20") -> dict:
        """Filter text to a token-bounded slice — pure, no execution (hook-ready).

        Inputs: text (raw output), spec (full|tail:N|head:N|grep:PAT|lines:A-B|count|last).
        Returns: ``{result: {output, lines, spec}}``.
        chain_next: forward the trimmed output (e.g. from a PostToolUse hook).
        """
        filtered = _apply_filter(text, spec)
        return {"result": {"output": filtered, "lines": len(filtered.splitlines()), "spec": spec}}

    @verb(role="effect", inject=["runner"])
    def run(self, runner, command: str = "", template: str = "", args: str = "",
            filter: str = "") -> dict:
        """Run an ALLOWLISTED command (or a named template), FILTER its output, record it.

        Inputs: command (raw — its first token MUST be allowlisted) OR template (a
                name from ``shell.templates``); args (appended); filter (output
                slice; defaults to the template's filter, else 'tail:20').
        Returns: ``{exit_code, output, lines, run_id, template?}`` — the FILTERED
                 delta (full output is bounded, never dumped); or ``{error, …}`` on
                 a disallowed tool / unknown template.
        chain_next: inspect the recorded command-run Artefact (``recall(run_id)``).
        """
        if template:
            merged = _resolve_templates(self.ctx.memory)   # Spec 075 — graph first, then seeds
            t = merged.get(template)
            if t is None:
                return {"result": {"error": f"unknown template {template!r}",
                                   "templates": sorted(merged)}}
            command = t["command"]
            filter = filter or t["filter"]
        if not command:
            return {"result": {"error": "command or template required"}}
        try:
            argv = shlex.split(command) + (shlex.split(args) if args else [])
        except ValueError as e:
            return {"result": {"error": f"unparseable command: {e}"}}
        tool = argv[0] if argv else ""
        if tool not in _ALLOWED_TOOLS:
            return {"result": {"error": f"tool {tool!r} not allowlisted",
                               "allowed": sorted(_ALLOWED_TOOLS)}}
        res = runner.run(argv)
        raw = (res.get("stdout", "") or "") + (("\n" + res["stderr"]) if res.get("stderr") else "")
        filtered = _apply_filter(raw, filter or "tail:20")
        rid = self.ctx.record("Artefact", {
            "kind": "command-run", "tool": tool,
            "command": keep_full(command, label="shell command"),
            "exit_code": res.get("exit_code"), "duration_s": res.get("duration_s", 0.0),
            "tail": filtered[:_MAX_OUTPUT]})
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        out = {"exit_code": res.get("exit_code"), "output": filtered,
               "lines": len(filtered.splitlines()), "run_id": rid}
        if template:
            out["template"] = template
        return {"result": out}
