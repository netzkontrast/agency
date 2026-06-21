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
from ...toolresult import ToolResult

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
_FILTER_PROFILE_KIND = "filter-profile"   # Spec 350 Slice 3 — graph-stored FilterProfile Artefacts


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


def _graph_filter_profiles(memory) -> dict:
    """Current filter-profile Artefacts as {name: {profile, id}}.
    Bi-temporal: latest definition per name wins (supersede keeps history)."""
    out: dict = {}
    for a in memory.find("Artefact"):
        if a.get("kind") != _FILTER_PROFILE_KIND:
            continue
        out[a.get("name")] = {"profile": a.get("profile", ""), "id": a.get("id")}
    return out


def _resolve_templates(memory) -> dict:
    """Seeds ∪ graph templates, graph overriding a same-named seed (Spec 075).
    Each entry carries a `source` ∈ {seed, graph} so discovery can show provenance."""
    merged = {n: {**t, "source": "seed"} for n, t in _TEMPLATES.items()}
    for name, t in _graph_templates(memory).items():
        merged[name] = {"command": t["command"], "filter": t["filter"],
                        "doc": t["doc"], "tags": t["tags"], "source": "graph"}
    return merged



# AGENCY-DRIFT: shell-filter-profiles — the per-tool FilterProfile registry (Spec 337).
# Extend deliberately; add a new entry before the tool's fallback row (first-match wins).
# shape is a regex matched against the Bash command string; None = any command for this tool.
# For non-Bash tools, shape is always None (tool name alone drives the match).
_FILTER_PROFILES = [
    # Bash: git subcommands (shape regex matched against the command string)
    {"tool": "Bash", "shape": r"^git\s+status",      "strategy": r"grep:^[ MADRCU?]",
     "rationale": "porcelain file list; banner prose is not the signal"},
    {"tool": "Bash", "shape": r"^git\s+(diff|show)",  "strategy": "stat",
     "rationale": "change shape (files × ±lines); hunks live in output_json"},
    {"tool": "Bash", "shape": r"^git\s+log",          "strategy": "head:20",
     "rationale": "recent oneline window"},
    # Bash: pytest / python -m pytest
    {"tool": "Bash", "shape": r"^(pytest\b|python\b.*-m\s+pytest)",
     "strategy": r"grep:(FAILED|ERROR|passed|failed)",
     "rationale": "failures + summary line; never the dot stream"},
    # Bash: search / listing tools
    {"tool": "Bash", "shape": r"^(grep|rg)\b",  "strategy": "count+head:20",
     "rationale": "the count is the answer; a sample confirms"},
    {"tool": "Bash", "shape": r"^ls\b",          "strategy": "count+head:20",
     "rationale": "how many + a sample"},
    # Bash fallback (must be last Bash entry — catches any unmatched command)
    {"tool": "Bash", "shape": None, "strategy": "head:20",
     "rationale": "Spec 336 back-compat default"},
    # Read: keep only a locator (path + line count + sha16) — no body copy
    {"tool": "Read", "shape": None, "strategy": "locator",
     "rationale": "file is already on disk; keep its address only"},
    # Edit / Write: the diff is a BoundaryUse — keep just the path
    {"tool": "Edit",  "shape": None, "strategy": "fields:file_path",
     "rationale": "body diff already in BoundaryUse; don't re-copy"},
    {"tool": "Write", "shape": None, "strategy": "fields:file_path",
     "rationale": "body already in BoundaryUse; don't re-copy"},
    # ToolSearch: tool names only; the schema dump is recoverable on demand
    {"tool": "ToolSearch", "shape": None, "strategy": "names",
     "rationale": "selected tool names; schema dump is recoverable on demand"},
    # GitHub MCP: strip the envelope to the decision fields
    {"tool": "mcp__github__*", "shape": None,
     "strategy": "fields:number,state,conclusion,mergeable_state,sha",
     "rationale": "strip the envelope to the decision fields"},
    # CodeGraph: flow header; full source is re-queryable
    {"tool": "codegraph_*", "shape": None, "strategy": "head:40",
     "rationale": "flow header; full source is re-queryable"},
]


def _resolve_profile(tool: str, command: str) -> str:
    """First-match lookup in ``_FILTER_PROFILES``. Returns the strategy string.
    Bash shapes are regexes matched against the full command; non-Bash shapes are always None.
    Falls back to 'head:20' (Spec 336 back-compat) when no profile matches."""
    for profile in _FILTER_PROFILES:
        t = profile["tool"]
        s = profile.get("shape")
        # Tool match: exact or prefix-wildcard (e.g. "mcp__github__*")
        if t.endswith("*"):
            if not tool.startswith(t[:-1]):
                continue
        elif t != tool:
            continue
        # Shape match: None = any, else regex on the command string
        if s is not None:
            if not re.search(s, (command or "").strip()):
                continue
        return profile["strategy"]
    return "head:20"   # absolute fallback


def _apply_filter(text: str, spec: str) -> str:
    """Reduce text to the requested slice (the token-economy core).

    spec ∈ full | tail:N | head:N | head+tail:N | grep:PAT | lines:A-B |
           count | count+head:N | last | stat | fields:A,B,... | names |
           relevance:<JSON profile>   (Spec 350 — content-aware, include/exclude)
    """
    import json as _json
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
        n = int(spec[5:] or 0)
        out = "\n".join(lines[:n])
    elif spec.startswith("head+tail:"):
        n = int(spec[10:] or 0)
        if n and len(lines) > 2 * n:
            elided = len(lines) - 2 * n
            marker = f"… {elided} lines elided (full output retained in output_json) …"
            out = "\n".join(lines[:n] + [marker] + lines[-n:])
        else:
            out = "\n".join(lines)
    elif spec.startswith("count+head:"):
        n = int(spec[11:] or 0)
        count = len([ln for ln in lines if ln.strip()])
        sample = "\n".join(lines[:n])
        out = f"{count} lines\n\n{sample}" if sample else f"{count} lines"
    elif spec.startswith("grep:"):
        pat = re.compile(spec[5:])
        out = "\n".join(ln for ln in lines if pat.search(ln))
    elif spec.startswith("lines:"):
        a, _, b = spec[6:].partition("-")
        out = "\n".join(lines[int(a) - 1:int(b or a)])
    elif spec == "stat":
        # Keep git --stat lines; drop diff hunk content (+/-/@@/diff/index/---/+++)
        stat_lines = []
        for ln in lines:
            if ln.startswith(("diff --git ", "index ", "--- ", "+++ ", "@@ ")):
                continue
            if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---")):
                continue
            stat_lines.append(ln)
        out = "\n".join(stat_lines)
    elif spec.startswith("fields:"):
        field_names = [f.strip() for f in spec[7:].split(",") if f.strip()]
        try:
            data = _json.loads(text)
            if isinstance(data, dict):
                out = "\n".join(
                    f"{k}: {data[k]}" if k in data else f"{k}: (missing)"
                    for k in field_names)
            else:
                out = "\n".join(lines[:20])
        except Exception:                                   # noqa: BLE001
            out = "\n".join(lines[:20])
    elif spec == "names":
        try:
            data = _json.loads(text)
            if isinstance(data, list):
                names = [
                    (item.get("name") or str(item)) if isinstance(item, dict) else str(item)
                    for item in data]
                out = "\n".join(names[:50])
            elif isinstance(data, dict):
                out = "\n".join(list(data.keys())[:50])
            else:
                out = str(data)[:200]
        except Exception:                                   # noqa: BLE001
            out = "\n".join(ln for ln in lines if ln.strip())[:200]
    elif spec.startswith("relevance:"):
        # Spec 350 — content-aware include/exclude filter (fail-open on bad profile)
        try:
            profile = _json.loads(spec[10:])
        except Exception:                                   # noqa: BLE001
            profile = {}
        from ..._relevance import relevance_filter as _rf
        r = _rf(text, profile)
        out = r["kept"]
    else:
        out = "\n".join(lines)
    return out[:_MAX_OUTPUT]


def capture_filter(command: str, output: str, *,
                   tool: str = "Bash", spec: str | None = None) -> str:
    """Spec 336 S3 / Spec 337 — a per-tool token-filtered VIEW for the ephemeral
    capture's ``filtered`` column (the cheap structured view the export prefers).

    The FULL payload is stored separately via ``keep_full``; this VIEW loses no data.

    - ``tool`` selects the FilterProfile registry (Spec 337).
    - ``spec=None`` (the hook path default) auto-resolves via ``_resolve_profile``;
      an explicit ``spec=`` still wins so callers and tests keep full control.
    - For Read, the ``locator`` strategy returns path + line-count + sha16 (no body).
    - For Bash (unknown command), falls back to Spec 336 ``head:20``.

    Returns a tool-appropriate header line + the distilled view body.
    """
    import hashlib as _hashlib
    if spec is None:
        spec = _resolve_profile(tool, command)
    # Build the header line
    if tool == "Bash":
        head = f"$ {command}".rstrip()
    elif tool == "Read":
        head = f"[Read {command}]"
    elif tool in ("Edit", "Write"):
        head = f"[{tool} {command}]"
    else:
        head = f"[{tool}]"
    # Build the body: locator is special (needs command as path + sha of output)
    if spec == "locator":
        body_text_raw = output or ""
        n = len(body_text_raw.splitlines())
        sha16 = _hashlib.sha256(body_text_raw.encode()).hexdigest()[:16]
        path = command or "?"
        body = f"{path} — {n} lines — sha16:{sha16}"
    else:
        body = _apply_filter(output or "", spec) if output else ""
        # Spec 350 Slice 2 — apply config filters.shell relevance profile for Bash
        # (OPT-IN: only runs when the user has set filters.shell in config.yaml)
        if tool == "Bash" and body:
            try:
                from ..._relevance import load_filter_profile as _lfp, relevance_filter as _rf
                _sp = _lfp("shell")
                if _sp:
                    body = _rf(body, _sp)["kept"]
            except Exception:  # noqa: BLE001 - fail-open on hook path
                pass
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

    @verb(role="act")
    def define_profile(self, name: str, profile: str) -> dict:
        """Define a named filter profile (include/exclude/context/budget) in the graph.

        Records an ``Artefact{kind:"filter-profile", name, profile=<JSON>}`` so named
        profiles can be referenced by name via ``load_filter_profile`` (Spec 350 Slice 3).
        Re-defining a name SUPERSEDES the prior version (bi-temporal trail kept).
        Graph-stored profiles override same-named config-file profiles.

        Inputs: name (str), profile (JSON string — ``{include, exclude, context, budget}``).
        Returns: ``{profile_id, name}``; or ``{error}`` on invalid JSON.
        chain_next: reference by name in relevance calls.
        """
        import json as _json
        try:
            _json.loads(profile)   # validate JSON
        except Exception as e:
            return ToolResult.success(data={"error": f"invalid JSON profile: {e}"})
        props = {"kind": _FILTER_PROFILE_KIND, "name": name, "profile": profile}
        existing = _graph_filter_profiles(self.ctx.memory).get(name)
        if existing:
            pid = self.ctx.memory.supersede(existing["id"], props)
        else:
            pid = self.ctx.record("Artefact", props)
        self.ctx.link(pid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={"profile_id": pid, "name": name})

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
