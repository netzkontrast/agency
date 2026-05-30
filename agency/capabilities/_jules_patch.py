def _parse_diff_header_a_path(line: str) -> str | None:
    body = line[len("diff --git "):].rstrip("\n")
    parts = body.split(" ")
    if len(parts) < 2: return None
    p = parts[-2]
    if not p.startswith("a/"): return None
    return p[2:]

def _parse_diff_header_b_path(line: str) -> str | None:
    body = line[len("diff --git "):].rstrip("\n")
    parts = body.split(" ")
    if len(parts) < 2: return None
    p = parts[-1]
    if not p.startswith("b/"): return None
    return p[2:]

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
            a_path = _parse_diff_header_a_path(line)
            b_path = _parse_diff_header_b_path(line)
            if not a_path or not b_path:
                raise ValueError("Malformed diff header")
            current = {"path": a_path, "op": "modify"}
            if a_path != b_path:
                current["new_path"] = b_path
            in_hunk = False
            content_lines = []
        elif line.startswith("new file mode "):
            if current: current["op"] = "add"
        elif line.startswith("deleted file mode "):
            if current: current["op"] = "delete"
        elif line.startswith("rename from "):
            if current: current["op"] = "rename"
        elif line.startswith("@@ "):
            in_hunk = True
        elif in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                content_lines.append(line[1:])
            elif line.startswith(" ") or line == "":
                content_lines.append(line[1:] if line else "")

    if current:
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
    sid: str = "",
) -> dict:
    ops = [{"tool": "mcp__github__create_branch", "args": {"branch": branch, "from_branch": base}}]
    current_base = base
    for out in outputs:
        diff = out.get("changeSet", {}).get("gitPatch", {}).get("unidiffPatch", "")
        if not diff:
            continue
        files = parse_unidiff(diff)

        upserts = [(f["path"], f.get("content", "")) for f in files if f["op"] in ("add", "modify")]
        renames = [(f["path"], f.get("new_path", ""), f.get("content", "")) for f in files if f["op"] == "rename"]

        if upserts:
            ops.append({
                "tool": "mcp__github__push_files",
                "args": {
                    "branch": branch,
                    "files": upserts,
                    "message": f"recover({sid}) chunk"
                }
            })

        for src, dst, content in renames:
            ops.append({
                "tool": "mcp__github__push_files",
                "args": {
                    "branch": branch,
                    "files": [(dst, content)],
                    "message": f"rename {src}->{dst}"
                }
            })
            ops.append({
                "tool": "mcp__github__delete_file",
                "args": {
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
                        "branch": branch,
                        "path": f["path"],
                        "message": f"delete {f['path']}"
                    }
                })

        current_base = branch

    pr_title = f"Recover Jules session {sid}"
    pr_body = (
        f"Automated recovery of Jules session {sid}.\n\n"
        f"Co-authored-by: google-labs-jules[bot] <jules@google.com>"
    )

    ops.append({
        "tool": "mcp__github__create_pull_request",
        "args": {
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
