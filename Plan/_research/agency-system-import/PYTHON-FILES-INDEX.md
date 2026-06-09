# Python source files — links to the-agency-system upstream

> Iter-15 deleted 41 Python implementation files from the import to fix
> the CI token-budget overflow (see iter-15 commit). The files remain
> available upstream at `netzkontrast/the-agency-system`. This index
> maps the deleted paths to their GitHub blob URLs so implementation
> agents can fetch them via `WebFetch` / `git show` / clone when
> needed.
>
> **Canonical source repo**: `https://github.com/netzkontrast/the-agency-system`
> **Branch**: `Master` (the upstream default; per SOURCES.md the
> `claude/agency-plugin-refactor-PgMQ4` branch may have more recent
> work).
>
> Usage pattern (from an implementation agent):
>
> ```python
> # Via WebFetch:
> await call_tool("WebFetch", {
>     "url": "https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/cell_loader.py",
>     "prompt": "Extract the cell-loading procedure + name-derivation logic."
> })
>
> # Via git clone (one-shot):
> subprocess.run([
>     "git", "clone", "--depth=1",
>     "https://github.com/netzkontrast/the-agency-system.git",
>     "/tmp/the-agency-system-vendor"
> ])
> # Then read /tmp/the-agency-system-vendor/<path>
> ```

## File index (path → GitHub URL)

| Local path (deleted) | Upstream path | Blob URL |
|---|---|---|
| `Plan/_research/agency-system-import/. document.index_repo walks .py` | `. document.index_repo walks .py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/. document.index_repo walks .py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/. document.index_repo walks .py) |
| `Plan/_research/agency-system-import/agentic/__init__.py` | `agentic/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/__init__.py) |
| `Plan/_research/agency-system-import/agentic/_bootloader.py` | `agentic/_bootloader.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_bootloader.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_bootloader.py) |
| `Plan/_research/agency-system-import/agentic/_harness/__init__.py` | `agentic/_harness/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_harness/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/__init__.py) |
| `Plan/_research/agency-system-import/agentic/_harness/cell_loader.py` | `agentic/_harness/cell_loader.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_harness/cell_loader.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/cell_loader.py) |
| `Plan/_research/agency-system-import/agentic/_harness/codemode.py` | `agentic/_harness/codemode.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_harness/codemode.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/codemode.py) |
| `Plan/_research/agency-system-import/agentic/_harness/fastmcp_boot.py` | `agentic/_harness/fastmcp_boot.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_harness/fastmcp_boot.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/fastmcp_boot.py) |
| `Plan/_research/agency-system-import/agentic/_harness/name_deriver.py` | `agentic/_harness/name_deriver.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/_harness/name_deriver.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/_harness/name_deriver.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/__init__.py` | `agentic/jules/handlers/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/__init__.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/_session_state.py` | `agentic/jules/handlers/_session_state.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/_session_state.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/_session_state.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/await_plan.py` | `agentic/jules/handlers/await_plan.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/await_plan.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/await_plan.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/dispatch.py` | `agentic/jules/handlers/dispatch.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/dispatch.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/dispatch.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/integrate.py` | `agentic/jules/handlers/integrate.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/integrate.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/integrate.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/monitor.py` | `agentic/jules/handlers/monitor.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/monitor.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/monitor.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/query.py` | `agentic/jules/handlers/query.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/query.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/query.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/recover.py` | `agentic/jules/handlers/recover.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/recover.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/recover.py) |
| `Plan/_research/agency-system-import/agentic/jules/handlers/verify.py` | `agentic/jules/handlers/verify.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/agentic/jules/handlers/verify.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/agentic/jules/handlers/verify.py) |
| `Plan/_research/agency-system-import/context/__init__.py` | `context/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/__init__.py) |
| `Plan/_research/agency-system-import/context/_drivers/__init__.py` | `context/_drivers/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_drivers/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_drivers/__init__.py) |
| `Plan/_research/agency-system-import/context/_drivers/fs.py` | `context/_drivers/fs.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_drivers/fs.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_drivers/fs.py) |
| `Plan/_research/agency-system-import/context/_drivers/protocol.py` | `context/_drivers/protocol.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_drivers/protocol.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_drivers/protocol.py) |
| `Plan/_research/agency-system-import/context/_hooks/__init__.py` | `context/_hooks/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_hooks/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_hooks/__init__.py) |
| `Plan/_research/agency-system-import/context/_hooks/post_tool_use.py` | `context/_hooks/post_tool_use.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_hooks/post_tool_use.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_hooks/post_tool_use.py) |
| `Plan/_research/agency-system-import/context/_hooks/pre_tool_use.py` | `context/_hooks/pre_tool_use.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_hooks/pre_tool_use.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_hooks/pre_tool_use.py) |
| `Plan/_research/agency-system-import/context/_shared/error_codes.py` | `context/_shared/error_codes.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_shared/error_codes.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_shared/error_codes.py) |
| `Plan/_research/agency-system-import/context/_store/__init__.py` | `context/_store/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_store/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_store/__init__.py) |
| `Plan/_research/agency-system-import/context/_store/sqlite.py` | `context/_store/sqlite.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/context/_store/sqlite.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/context/_store/sqlite.py) |
| `Plan/_research/agency-system-import/skills/theagencysystem/scripts/provision_bitwize.py` | `skills/theagencysystem/scripts/provision_bitwize.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/skills/theagencysystem/scripts/provision_bitwize.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/skills/theagencysystem/scripts/provision_bitwize.py) |
| `Plan/_research/agency-system-import/workflow/__init__.py` | `workflow/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/__init__.py) |
| `Plan/_research/agency-system-import/workflow/_runner/__init__.py` | `workflow/_runner/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/__init__.py) |
| `Plan/_research/agency-system-import/workflow/_runner/envelope.py` | `workflow/_runner/envelope.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/envelope.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/envelope.py) |
| `Plan/_research/agency-system-import/workflow/_runner/evaluators/__init__.py` | `workflow/_runner/evaluators/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/evaluators/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/evaluators/__init__.py) |
| `Plan/_research/agency-system-import/workflow/_runner/evaluators/frontmatter_status.py` | `workflow/_runner/evaluators/frontmatter_status.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/evaluators/frontmatter_status.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/evaluators/frontmatter_status.py) |
| `Plan/_research/agency-system-import/workflow/_runner/evaluators/schema_match.py` | `workflow/_runner/evaluators/schema_match.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/evaluators/schema_match.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/evaluators/schema_match.py) |
| `Plan/_research/agency-system-import/workflow/_runner/gate.py` | `workflow/_runner/gate.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/gate.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/gate.py) |
| `Plan/_research/agency-system-import/workflow/_runner/manifest.py` | `workflow/_runner/manifest.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/manifest.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/manifest.py) |
| `Plan/_research/agency-system-import/workflow/_runner/pipeline.py` | `workflow/_runner/pipeline.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/_runner/pipeline.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/_runner/pipeline.py) |
| `Plan/_research/agency-system-import/workflow/jules/gates/__init__.py` | `workflow/jules/gates/__init__.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/jules/gates/__init__.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/jules/gates/__init__.py) |
| `Plan/_research/agency-system-import/workflow/jules/gates/patch_applied.py` | `workflow/jules/gates/patch_applied.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/jules/gates/patch_applied.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/jules/gates/patch_applied.py) |
| `Plan/_research/agency-system-import/workflow/jules/gates/plan_approved.py` | `workflow/jules/gates/plan_approved.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/jules/gates/plan_approved.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/jules/gates/plan_approved.py) |
| `Plan/_research/agency-system-import/workflow/jules/gates/research_complete.py` | `workflow/jules/gates/research_complete.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/jules/gates/research_complete.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/jules/gates/research_complete.py) |
| `Plan/_research/agency-system-import/workflow/jules/gates/session_completed.py` | `workflow/jules/gates/session_completed.py` | [view](https://github.com/netzkontrast/the-agency-system/blob/Master/workflow/jules/gates/session_completed.py) · [raw](https://raw.githubusercontent.com/netzkontrast/the-agency-system/Master/workflow/jules/gates/session_completed.py) |

## Files grouped by area

### `agentic/` — bootloader + harness + handlers (15 files)

The agentic column root + harness-in-harness implementation +
jules-row handlers. Read for: cell-loading procedure, FastMCP boot
sequence, name derivation rules, jules dispatch/monitor/recover/
verify/integrate handlers.

### `context/` — Store + drivers + hooks (11 files)

The context column root + SQLite-backed Store + FS/Protocol drivers +
pre/post tool-use hooks + shared error codes. Read for: Store
abstraction shape, driver protocol, hook chain pattern.

### `workflow/` — Runner + evaluators + gates (14 files)

The workflow column runner (pipeline.py is the graph-walker), gate
evaluators (frontmatter_status, schema_match), and jules-row gates
(patch_applied, plan_approved, research_complete, session_completed).
Read for: phase-as-graph-node implementation, gate evaluator pattern.

### `skills/theagencysystem/scripts/` — Provisioning script (1 file)

`provision_bitwize.py` — bitwize provisioning helper for the DNA
gate-and-loader pattern. Read alongside `skills/theagencysystem/
SKILL.md`.

## When to fetch

Per Spec 113's selective-port discipline, fetch only when:

1. A pattern surfaces during ingestion (Phase 4 design-review)
2. AND the pattern passes the three-stage fit filter (vision / goal /
   architecture)
3. AND the implementation procedure references one of these files as
   source-material

Otherwise: treat these files as available-on-demand reference, not
required reading. The `.md` source material in the import (charter,
specs, research session docs, RESEARCH-PATTERNS) carries the
architectural intent without needing the implementation.

## How implementation agents fetch

```python
# Pattern 1: WebFetch single file
result = await call_tool("WebFetch", {
    "url": "<raw URL from table>",
    "prompt": "<what to extract>",
})

# Pattern 2: Bash + curl for offline grep
import subprocess
subprocess.run(["curl", "-fsS", "<raw URL>", "-o", "/tmp/file.py"],
               check=True)

# Pattern 3: Shallow clone for multi-file investigation
subprocess.run([
    "git", "clone", "--depth=1",
    "https://github.com/netzkontrast/the-agency-system.git",
    "/tmp/the-agency-system-vendor"
], check=True)
# Then read /tmp/the-agency-system-vendor/<upstream_path>
```

Pattern 3 is the canonical approach for large investigations (per
SOURCES.md's `~/work/vendor/<name>/` convention).
