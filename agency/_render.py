"""Spec 283 Slice 1 — the capability render substrate (graph → markdown view).

A capability declares a `RenderSpec`: a list of `RenderRule`s binding a node
`label` to (output_path, frontmatter, body, kind). The substrate renders graph
entities to markdown files and mints one `Artefact` per file — closing
CLAUDE.md rule 2 ("the graph is the store; files are a rendered view") and
Workstream F (the graph/disk provenance split: every rendered file gets an
`Artefact` + `PRODUCES` edge).

Slice 1 ships the substrate + the on-demand full-rebuild path (a capability
`render_all`-style verb). The auto-render-on-every-mutation hook in
`Registry.invoke` is Slice 2 — it lands on the parallel OOP-refactor's
post-invocation `ResultProcessor` seam (PR #141 coordination), with the
render-cost coalescing question (Spec 283 OQ1) resolved there.

`RenderDriver` mirrors the established driver pattern (Spec 117/124):
`FileRenderDriver` (production) + `FakeRenderDriver` (tests, in-memory).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from agency import _frontmatter


@dataclass(frozen=True)
class RenderRule:
    """Binds a node `label` to its rendered-file projection.

    - `output_path(node) -> str` — path RELATIVE to the capability render root.
    - `frontmatter(node) -> dict` — typed frontmatter (includes the node id +
      parent edge so `from_frontmatter` round-trips).
    - `body(node) -> str` — the rendered body.
    - `kind` — the `Artefact.kind` minted for files of this rule.
    """
    label: str
    output_path: Callable[[dict], str]
    frontmatter: Callable[[dict], dict]
    body: Callable[[dict], str]
    kind: str = "render"


@dataclass
class RenderSpec:
    """A capability's render ruleset (declared on the capability; read by the
    substrate). Adding a `RenderSpec` is all a new capability needs to gain
    file rendering — the drop-in-capability bar (CLAUDE.md)."""
    rules: list[RenderRule] = field(default_factory=list)

    def rule_for(self, label: str) -> RenderRule | None:
        return next((r for r in self.rules if r.label == label), None)

    @property
    def labels(self) -> set[str]:
        return {r.label for r in self.rules}


@runtime_checkable
class RenderDriver(Protocol):
    """Writes a rendered file. `write` is idempotent — a byte-identical
    re-render is a no-op."""
    def write(self, path: str, frontmatter: dict, body: str) -> str: ...


class FakeRenderDriver:
    """In-memory render driver for tests — no disk. Records a call log + the
    rendered content per path (mirrors FakeFormatDriver)."""
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.calls: list[str] = []

    def write(self, path: str, frontmatter: dict, body: str) -> str:
        self.files[path] = _frontmatter.emit(frontmatter, body)
        self.calls.append(path)
        return path


class FileRenderDriver:
    """Production render driver — writes under `root`, idempotent (a
    byte-identical re-render skips the write)."""
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser()

    def write(self, path: str, frontmatter: dict, body: str) -> str:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = _frontmatter.emit(frontmatter, body)
        if target.exists() and target.read_text(encoding="utf-8") == content:
            return str(target)                 # idempotent no-op
        target.write_text(content, encoding="utf-8")
        return str(target)


def render_node(rule: RenderRule, node: dict) -> tuple[str, dict, str]:
    """Apply a rule to a node → ``(path, frontmatter, body)``. Pure (no I/O,
    no graph) so it is trivially unit-testable + reusable by both the
    on-demand and (Slice 2) auto-render paths."""
    return rule.output_path(node), rule.frontmatter(node), rule.body(node)
