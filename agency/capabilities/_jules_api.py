"""Minimal, self-contained Jules REST client (vendored into the agency plugin).

A thin client for the Jules REST API — the two calls the `jules` capability needs
(`jules_create` and `jules_get`). Built on `httpx` (the HTTP client the FastMCP
stack already ships). The agency plugin owns its Jules integration end to end; it
depends on no external orchestrator package.

Auth: set `JULES_API_KEY` in the environment. Base URL overridable via
`JULES_API_BASE_URL` (default `https://jules.googleapis.com`).
"""
from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

BASE_URL = os.environ.get("JULES_API_BASE_URL", "https://jules.googleapis.com")


class JulesAPIError(RuntimeError):
    """Non-2xx from the Jules REST API; carries the HTTP status code."""

    def __init__(self, status: int, message: str, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


def _api_key() -> str:
    key = os.environ.get("JULES_API_KEY", "")
    if not key:
        raise RuntimeError(
            "JULES_API_KEY is not set. Export it in the shell that launched the "
            "engine, then retry."
        )
    return key


def _translate_http_error(code: int, body: str) -> str:
    mapping = {
        400: "400 Bad Request — malformed payload. Body: ",
        401: "401 Unauthorized — JULES_API_KEY rejected. Re-export the key.",
        403: "403 Permission Denied — Jules cannot access the source. Connect the GitHub repo via the Jules GitHub app.",
        404: "404 Not Found — resource does not exist.",
        405: "405 Method Not Allowed — endpoint exists but does not accept this verb.",
        409: "409 Conflict — illegal state transition. Check current session state first.",
        429: "429 Quota Exceeded — pause polling and check billing/quota.",
    }
    if 500 <= code < 600:
        return f"5xx Server Error ({code}) — retryable. Body: {body[:300]}"
    base = mapping.get(code, f"HTTP {code}")
    if code == 400 and body:
        return base + body[:500]
    return base


def _request(method: str, path: str, body: Optional[dict] = None,
             params: Optional[dict] = None) -> dict:
    headers = {"x-goog-api-key": _api_key()}
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        resp = client.request(method, path, json=body, params=params, headers=headers)
    if resp.status_code >= 400:
        raise JulesAPIError(resp.status_code,
                            _translate_http_error(resp.status_code, resp.text), resp.text)
    return resp.json() if resp.text else {}


def _paginate(path: str, params: dict, max_pages: int = 10) -> list[dict]:
    items: list[dict] = []
    token = ""
    pages = 0
    array_key: Optional[str] = None
    while pages < max_pages:
        q = dict(params)
        if token:
            q["pageToken"] = token
        raw = _request("GET", path, params=q)
        pages += 1
        if array_key is None:
            array_key = next((k for k, v in raw.items() if isinstance(v, list)), None)
            if array_key is None:
                break
        items.extend(raw.get(array_key, []) or [])
        token = raw.get("nextPageToken", "")
        if not token:
            break
    return items


def _short_id(name_or_id: str) -> str:
    """Accept 'sessions/123' or '123' and return '123'."""
    return name_or_id.rsplit("/", 1)[-1]


def _resolve_github_source(owner: str, repo: str) -> dict:
    """Resolve a GitHub owner/repo to its opaque `sources/{id}` name (not
    documented; must be looked up via sources.list)."""
    for s in _paginate("/v1alpha/sources", {"pageSize": 100}):
        gh = s.get("githubRepo") or {}
        if gh.get("owner") == owner and gh.get("repo") == repo:
            return {"source": s.get("name", ""), "github": {"owner": owner, "repo": repo}}
    return {"error": (f"no Jules source connected for github.com/{owner}/{repo}. "
                      "Connect the repository via the Jules GitHub app, then retry.")}


def _coerce_source(source: str) -> str:
    """Translate 'sources/<id>' | 'owner/repo' | a github URL into the opaque
    `sources/<id>` form Jules expects."""
    s = (source or "").strip()
    if not s:
        raise RuntimeError("source is required ('sources/<id>', 'owner/repo', or a GitHub URL).")
    if s.startswith("sources/") and s.count("/") == 1:
        return s
    owner = repo = None
    if s.startswith("sources/github/"):
        rest = s[len("sources/github/"):]
        if rest.count("/") == 1:
            owner, repo = rest.split("/", 1)
    elif urlparse(s).hostname in ("github.com", "www.github.com"):   # real host, not a substring
        path = urlparse(s).path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        parts = path.split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
    elif "/" in s:
        parts = s.split("/")
        if len(parts) == 2:
            owner, repo = parts
    if owner and repo:
        resolved = _resolve_github_source(owner, repo)
        if "error" in resolved:
            raise RuntimeError(resolved["error"])
        return resolved["source"]
    raise RuntimeError(f"could not parse source {source!r}.")


_AUTO_CREATE_PR_DEPRECATION_FIRED = False


def jules_create(prompt: str, source: str, starting_branch: str,
                 title: str = "", require_plan_approval: bool = True,
                 auto_create_pr: bool = False,
                 automation_mode: str = "",
                 protocol_preset: str = "") -> dict:
    """Create a Jules session. Returns the session resource (id, state, url, ...).

    Spec 013 Phase 4: ``automation_mode`` is the canonical Jules-side field
    name (``"" | "AUTO_CREATE_PR"``). ``auto_create_pr=True`` is a back-compat
    alias that maps to ``automation_mode="AUTO_CREATE_PR"`` with a one-shot
    ``DeprecationWarning``. ``protocol_preset`` non-empty prepends the
    assembled Mode-A/B preamble to ``prompt`` via
    ``_jules_preambles.assemble(...)``.
    """
    # Back-compat alias: auto_create_pr=True -> automation_mode="AUTO_CREATE_PR".
    # If both supplied, automation_mode wins (explicit canonical name).
    if auto_create_pr and not automation_mode:
        global _AUTO_CREATE_PR_DEPRECATION_FIRED
        if not _AUTO_CREATE_PR_DEPRECATION_FIRED:
            import warnings
            warnings.warn(
                "`auto_create_pr=True` is deprecated; use "
                "`automation_mode=\"AUTO_CREATE_PR\"` instead. The alias "
                "will be removed in a future spec.",
                DeprecationWarning,
                stacklevel=2,
            )
            _AUTO_CREATE_PR_DEPRECATION_FIRED = True
        automation_mode = "AUTO_CREATE_PR"

    # Preset-driven preamble: prepend Mode-A/B preamble to the prompt when
    # a preset is named. Empty preset_name = no prepend (caller assembled
    # their own prompt).
    if protocol_preset:
        from . import _jules_preambles
        prompt = _jules_preambles.assemble(
            source=source, starting_branch=starting_branch,
            prompt=prompt, preset_name=protocol_preset,
        )

    body: dict[str, Any] = {
        "prompt": prompt,
        "sourceContext": {
            "source": _coerce_source(source),
            "githubRepoContext": {"startingBranch": starting_branch},
        },
        "requirePlanApproval": bool(require_plan_approval),
    }
    if title:
        body["title"] = title
    if automation_mode:
        body["automationMode"] = automation_mode
    return _request("POST", "/v1alpha/sessions", body)


def jules_get(session_id: str) -> dict:
    """Fetch a session's current state + metadata."""
    s = _request("GET", f"/v1alpha/sessions/{_short_id(session_id)}")
    return {
        "id": s.get("id") or _short_id(s.get("name", "")),
        "state": s.get("state"),
        "title": s.get("title", ""),
        "source": (s.get("sourceContext") or {}).get("source"),
        "branch": ((s.get("sourceContext") or {}).get("githubRepoContext") or {}).get("startingBranch"),
        "url": s.get("url", ""),
        "has_outputs": bool(s.get("outputs")),
    }


def jules_list(page_size: int = 20, page_token: str = "") -> dict:
    """List sessions on the account, trimmed to {id,state,title,url} so a listing
    cannot blow the context window. Returns {"sessions": [...], "nextPageToken": ...}.
    A single page only — pass the returned token back to walk further (the listing
    can truncate; never assume the first page is the whole account)."""
    q: dict[str, Any] = {"pageSize": max(1, min(page_size, 100))}
    if page_token:
        q["pageToken"] = page_token
    raw = _request("GET", "/v1alpha/sessions", params=q)
    sessions = [{
        "id": s.get("id") or _short_id(s.get("name", "")),
        "state": s.get("state"),
        "title": s.get("title", ""),
        "url": s.get("url", ""),
    } for s in (raw.get("sessions") or [])]
    return {"sessions": sessions, "nextPageToken": raw.get("nextPageToken", "")}


# Keys on an Activity that are NOT the polymorphic event-type field — meta that
# can co-occur with the real event kind and must not be mistaken for it.
_ACTIVITY_META_KEYS = {
    "name", "id", "createTime", "updateTime", "originator", "description", "artifacts",
}
# The Activity.activity oneof per the Jules v1alpha schema.
_ACTIVITY_KINDS = {
    "agentMessaged", "userMessaged", "planGenerated", "planApproved",
    "progressUpdated", "sessionCompleted", "sessionFailed",
}


def _activity_kind(a: dict) -> str:
    """The activity's event kind — prefer a known oneof member; fall back to the
    first non-meta key only when none matches."""
    for k in _ACTIVITY_KINDS:
        if k in a:
            return k
    for k in a:
        if k not in _ACTIVITY_META_KEYS:
            return k
    return "unknown"


def _activity_summary(a: dict) -> dict:
    """Trim one activity to {id, originator, kind, summary} — the activities stream
    is the single most context-expensive Jules read; never return it raw by default."""
    kind = _activity_kind(a)
    payload = a.get(kind) if isinstance(a.get(kind), dict) else {}
    text = a.get("description") or ""
    if not text and isinstance(payload, dict):
        text = payload.get("description") or payload.get("message") or payload.get("title") or ""
    return {
        "id": a.get("id") or _short_id(a.get("name", "")),
        "originator": a.get("originator", ""),
        "kind": kind,
        "summary": str(text)[:280],
    }


def jules_activities(session_id: str, page_size: int = 10, only_kinds: str = "",
                     page_token: str = "", summary_only: bool = True) -> dict:
    """List a session's activities, aggressively trimmed (summary_only=True →
    {id,originator,kind,summary}). `only_kinds` is a comma list to keep, e.g.
    'planGenerated,agentMessaged,sessionFailed'. Reads can lag / oscillate under
    eventual consistency — poll ≥2 cycles before trusting a transition."""
    sid = _short_id(session_id)
    q: dict[str, Any] = {"pageSize": max(1, min(page_size, 100))}
    if page_token:
        q["pageToken"] = page_token
    raw = _request("GET", f"/v1alpha/sessions/{sid}/activities", params=q)
    wanted = {k.strip() for k in only_kinds.split(",") if k.strip()}
    out: list[dict] = []
    for a in (raw.get("activities") or []):
        kind = _activity_kind(a)
        if wanted and kind not in wanted:
            continue
        out.append(_activity_summary(a) if summary_only else a)
    return {"activities": out, "nextPageToken": raw.get("nextPageToken", "")}


def jules_plan(session_id: str, max_pages: int = 5, include_descriptions: bool = False) -> dict:
    """Fetch the latest plan (the newest planGenerated activity, by createTime).
    Use it to show the plan before approve_plan while a session is in
    AWAITING_PLAN_APPROVAL — at that point NO PR exists yet, so this is the only
    way to see what Jules intends. Returns {"steps":[...], "create_time":...} or
    {"error":"no planGenerated activity found"}."""
    sid = _short_id(session_id)
    items = _paginate(f"/v1alpha/sessions/{sid}/activities", {"pageSize": 100}, max_pages=max_pages)
    best: Optional[dict] = None
    best_time = ""
    for a in items:
        pg = a.get("planGenerated")
        if not pg:
            continue
        ct = a.get("createTime", "")
        if best is None or ct > best_time:
            best, best_time = pg, ct
    if best is None:
        return {"error": "no planGenerated activity found"}
    steps = []
    for s in ((best.get("plan") or {}).get("steps") or []):
        step = {"title": s.get("title", "")}
        if include_descriptions:
            step["description"] = s.get("description", "")
        steps.append(step)
    return {"steps": steps, "create_time": best_time}


def jules_approve_plan(session_id: str) -> dict:
    """Approve the plan on a session in AWAITING_PLAN_APPROVAL. That is the ONE
    state with a timeout/discard window — the backend appears to drop sessions whose
    plan is never approved (they end COMPLETED with empty outputs) — so approve
    promptly after surfacing the plan. Returns {"ok": true, "session": id}."""
    sid = _short_id(session_id)
    _request("POST", f"/v1alpha/sessions/{sid}:approvePlan", body={})
    return {"ok": True, "session": sid}


def jules_get_full(session_id: str) -> dict:
    """The RAW session response — the trimmed `jules_get` discards `outputs`,
    `sourceContext`, `requirePlanApproval` etc. The watcher + the patch
    planner need the full shape (esp. `outputs[*].changeSet.gitPatch.unidiffPatch`).
    Spec 012 Phase 2."""
    return _request("GET", f"/v1alpha/sessions/{_short_id(session_id)}")


def jules_resolve_source_public(owner: str, repo: str) -> dict:
    """Public wrapper over `_resolve_github_source` so the capability can expose
    a `jules.resolve_source` verb. Returns {"source": "sources/<id>", "github":
    {"owner", "repo"}} on success, {"error": ...} on no-match. Spec 012 Phase 2."""
    return _resolve_github_source(owner, repo)


def jules_status_all(page_size: int = 100, max_pages: int = 20) -> dict:
    """List every session on the account (up to `max_pages` of `page_size`) and
    group by `state` for operational hygiene. Returns:
        {"by_state": {state: [{"id","state","title","url"}, ...]},
         "totals": {state: count}, "truncated": bool, "total": int}
    Spec 012 Phase 2."""
    items = _paginate("/v1alpha/sessions", {"pageSize": max(1, min(page_size, 100))},
                      max_pages=max(1, max_pages))
    by_state: dict[str, list[dict]] = {}
    for s in items:
        sid = s.get("id") or _short_id(s.get("name", ""))
        row = {"id": sid, "state": s.get("state"), "title": s.get("title", ""),
               "url": s.get("url", "")}
        by_state.setdefault(row["state"] or "STATE_UNSPECIFIED", []).append(row)
    totals = {k: len(v) for k, v in by_state.items()}
    return {"by_state": by_state, "totals": totals,
            "total": sum(totals.values()),
            "truncated": len(items) >= page_size * max_pages}


def jules_approve_awaiting(limit: int = 0) -> dict:
    """Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`,
    0 = all). Returns {"approved": [sid, ...], "skipped": [(sid, error), ...]}.
    Spec 012 Phase 2."""
    all_sessions = jules_status_all().get("by_state", {})
    awaiting = all_sessions.get("AWAITING_PLAN_APPROVAL", [])
    if limit and limit > 0:
        awaiting = awaiting[:limit]
    approved: list[str] = []
    skipped: list[tuple] = []
    for row in awaiting:
        sid = _short_id(row["id"])
        try:
            _request("POST", f"/v1alpha/sessions/{sid}:approvePlan", body={})
            approved.append(sid)
        except JulesAPIError as exc:
            skipped.append((sid, f"{exc.status}: {exc}"))
    return {"approved": approved, "skipped": skipped}


def _today_iso() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().strftime("%Y-%m-%d")


def jules_quota(daily_limit: int = 0) -> dict:
    """Operational hygiene: count sessions created today (UTC) by `createTime`
    prefix-match. `daily_limit` is a caller-supplied budget (API does not
    expose one); a positive value enables a `headroom` field. Returns:
        {"active_today": int, "daily_limit": int, "headroom": int,
         "truncated": bool}
    Spec 012 Phase 2."""
    items = _paginate("/v1alpha/sessions", {"pageSize": 100}, max_pages=20)
    day = _today_iso()
    active = sum(1 for s in items if str(s.get("createTime", "")).startswith(day))
    return {"active_today": active, "daily_limit": int(daily_limit),
            "headroom": max(0, int(daily_limit) - active) if daily_limit else 0,
            "truncated": len(items) >= 100 * 20}


def jules_patch_extract(session_id: str) -> dict:
    """Extract patch metadata from a session's `outputs[*].changeSet.gitPatch.
    unidiffPatch`. Returns per-output summary stats (files/lines/bytes) but NO
    body — bodies are too large to cross the agent boundary by default; use
    `jules_get_full(sid)["outputs"][i]["changeSet"]["gitPatch"]["unidiffPatch"]`
    for the bytes when the recovery flow needs them. Spec 012 Phase 2."""
    s = jules_get_full(session_id)
    outs = s.get("outputs") or []
    summary = []
    total_files = total_lines = total_bytes = 0
    for i, out in enumerate(outs):
        diff = (((out or {}).get("changeSet") or {}).get("gitPatch") or {}).get("unidiffPatch") or ""
        files = sum(1 for ln in diff.splitlines() if ln.startswith("diff --git "))
        lines = sum(1 for ln in diff.splitlines() if ln and ln[0] in "+-" and not ln.startswith(("+++", "---")))
        b = len(diff.encode("utf-8"))
        summary.append({"output_index": i, "files": files, "lines": lines, "bytes": b})
        total_files += files; total_lines += lines; total_bytes += b
    return {"sid": _short_id(session_id), "outputs": summary,
            "total_files": total_files, "total_lines": total_lines, "total_bytes": total_bytes}


def jules_message(session_id: str, prompt: str) -> dict:
    """Send a user message into a session's history (answer a question, request a
    plan revision, nudge a COMPLETED session to push). INPUT ONLY, not a control
    plane: it injects context, but state transitions (COMPLETED/AWAITING→IN_PROGRESS)
    are racy and unreliable — poll state after sending, do not assume it resumed.
    Never use it to revive a FAILED session (dispatch fresh) or to cancel one
    (there is no cancel — see jules_stop). Returns {"ok": true, "session": id}."""
    sid = _short_id(session_id)
    _request("POST", f"/v1alpha/sessions/{sid}:sendMessage", body={"prompt": prompt})
    return {"ok": True, "session": sid}
