def _parse_diff_header_a_path(line: str) -> str | None:
    # Now expects a line starting with '--- a/' or '--- /dev/null'
    if line.startswith("--- /dev/null"):
        return None
    if not line.startswith("--- a/"):
        return None
    return line[6:].rstrip("\n")

def _parse_diff_header_b_path(line: str) -> str | None:
    # Now expects a line starting with '+++ b/' or '+++ /dev/null'
    if line.startswith("+++ /dev/null"):
        return None
    if not line.startswith("+++ b/"):
        return None
    return line[6:].rstrip("\n")

def parse_unidiff(diff: str) -> list[dict]:
    files = []
    current = None
    lines = diff.splitlines()

    in_hunk = False
    content_lines = []

    for line in lines:
        if line.startswith("diff --git "):
            if current:
                if current["op"] in ("add", "modify") or (current["op"] == "rename" and content_lines):
                    current["content"] = "\n".join(content_lines) + "\n" if content_lines else ""
                files.append(current)
            current = {"path": "", "op": "modify"}
            in_hunk = False
            content_lines = []
        elif line.startswith("--- "):
            if current:
                a_path = _parse_diff_header_a_path(line)
                if a_path:
                    current["path"] = a_path
        elif line.startswith("+++ "):
            if current:
                b_path = _parse_diff_header_b_path(line)
                if b_path:
                    if not current["path"]:
                        current["path"] = b_path
                    elif current["path"] != b_path:
                        current["new_path"] = b_path
        elif line.startswith("new file mode "):
            if current: current["op"] = "add"
        elif line.startswith("deleted file mode "):
            if current: current["op"] = "delete"
        elif line.startswith("rename from "):
            if current:
                current["op"] = "rename"
                current["path"] = line[12:].rstrip("\n")
        elif line.startswith("rename to "):
            if current:
                current["new_path"] = line[10:].rstrip("\n")
        elif line.startswith("@@ "):
            in_hunk = True
            if current and current["op"] == "modify":
                parts = line.split(" ")
                if len(parts) >= 3:
                    a_info = parts[1] # -start,count
                    b_info = parts[2] # +start,count
                    if not (a_info.startswith("-1,") or a_info == "-0,0" or a_info == "-1"):
                        raise ValueError("Partial modify patches require I/O to apply; unsupported in pure parser")
        elif in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                content_lines.append(line[1:])
            elif line.startswith(" ") or line == "":
                content_lines.append(line[1:] if line else "")

    if current:
        if not current.get("path"):
            raise ValueError("Malformed diff header")
        if current["op"] in ("add", "modify") or (current["op"] == "rename" and content_lines):
            current["content"] = "\n".join(content_lines) + "\n" if content_lines else ""
        files.append(current)

    if diff.strip() and not files:
        raise ValueError("Malformed patch")

    return files

def build_recovery_plan(
    outputs: list[dict],
    branch: str,
    base: str,
    owner: str,
    repo: str,
    sid: str = "",
) -> dict:
    ops = [{"tool": "mcp__github__create_branch", "args": {"owner": owner, "repo": repo, "branch": branch, "from_branch": base}}]

    # chaining is implicit via pushing sequentially to the same `branch`

    for out in outputs:
        diff = out.get("changeSet", {}).get("gitPatch", {}).get("unidiffPatch", "")
        if not diff:
            continue
        files = parse_unidiff(diff)

        upserts = [{"path": f["path"], "content": f.get("content", "")} for f in files if f["op"] in ("add", "modify")]
        renames = [(f["path"], f.get("new_path", ""), f.get("content", "")) for f in files if f["op"] == "rename"]

        if upserts:
            ops.append({
                "tool": "mcp__github__push_files",
                "args": {
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "files": upserts,
                    "message": f"recover({sid}) chunk"
                }
            })

        for src, dst, content in renames:
            ops.append({
                "tool": "mcp__github__push_files",
                "args": {
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "files": [{"path": dst, "content": content}],
                    "message": f"rename {src}->{dst}"
                }
            })
            ops.append({
                "tool": "mcp__github__delete_file",
                "args": {
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "path": src,
                    "message": f"rename source {src}"
                }
            })

        for f in files:
            if f["op"] == "delete":
                ops.append({
                    "tool": "mcp__github__delete_file",
                    "args": {
                        "owner": owner,
                        "repo": repo,
                        "branch": branch,
                        "path": f["path"],
                        "message": f"delete {f['path']}"
                    }
                })

    pr_title = f"Recover Jules session {sid}"
    pr_body = (
        f"Automated recovery of Jules session {sid}.\n\n"
        f"Co-authored-by: google-labs-jules[bot] <jules@google.com>"
    )

    ops.append({
        "tool": "mcp__github__create_pull_request",
        "args": {
            "owner": owner,
            "repo": repo,
            "base": base,
            "head": branch,
            "title": pr_title,
            "body": pr_body
        }
    })

    return {
        "branch": branch,
        "base_branch": base,
        "ops": ops,
        "pr_title": pr_title,
        "pr_body": pr_body
    }
