# agency-scaffold: v1
"""document — graph-native rendering + briefing (Spec 043).

Three verbs:
  render     (transform) — graph → markdown projection (4 scopes)
  explain    (act)       — code → educational text via composition
  index_repo (act)       — 94%-reduction repo briefing

NO LLM. Every output is a deterministic projection of structured state.
"""
from __future__ import annotations

import os
import time

from agency.capability import CapabilityBase, verb
from agency.ontology import OntologyExtension

from . import _explain, _index_repo, _render


_REPO_BRIEFING_SKILL = {
    "name": "repo-briefing",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "scope", "produces": ["path", "max_tokens"]},
        {"index": 2, "name": "scan", "produces": ["index_id", "tokens"]},
        {"index": 3, "name": "render", "produces": ["content"]},
        {"index": 4, "name": "publish", "produces": ["written"], "gate": "hard"},
    ],
}


_SUPPORTED_SCOPES = frozenset({
    "install-artefacts", "reflections", "provenance", "capability-catalogue",
})


class DocumentCapability(CapabilityBase):
    name = "document"
    home = "memory"
    ontology = OntologyExtension(
        nodes={
            "RepoIndex": ["path", "content_sha", "token_count", "generated_at"],
        },
        edges={"INDEXES"},
        schemas={
            "repo-index": {"name": "repo-index",
                           "required": ["path", "content_sha", "token_count"]},
            "explanation": {"name": "explanation",
                            "required": ["target", "depth", "content"]},
        },
        skills={"repo-briefing": _REPO_BRIEFING_SKILL},
    )

    @verb(role="transform")
    def render(self, scope: str, for_intent_id: str = "",
               format: str = "markdown") -> dict:
        """Project graph state to markdown; deterministic.

        Inputs: scope (str — one of install-artefacts | reflections |
                provenance | capability-catalogue),
                for_intent_id (str — required for provenance, optional
                filter for reflections; named `for_intent_id` rather
                than `intent_id` because the substrate already injects
                intent_id for SERVES discipline),
                format (str — 'markdown' in v1).
        Returns: ``{content, tokens, node_count, scope}``.
        chain_next: caller writes to disk (graph stays canonical).
        """
        if format != "markdown":
            return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                    "error": f"format={format!r} not supported in v1"}
        if scope not in _SUPPORTED_SCOPES:
            return {"content": "", "tokens": 0, "node_count": 0, "scope": scope,
                    "error": f"unknown scope {scope!r}; supported: "
                             f"{sorted(_SUPPORTED_SCOPES)}"}
        memory = self.ctx.memory
        if scope == "install-artefacts":
            content, node_count = _render.render_install_artefacts(memory)
        elif scope == "reflections":
            content, node_count = _render.render_reflections(memory, for_intent_id)
        elif scope == "provenance":
            content, node_count = _render.render_provenance(memory, for_intent_id)
        else:  # capability-catalogue
            content, node_count = _render.render_capability_catalogue(self.ctx.registry)
        return {
            "content": content,
            "tokens": _explain._count_tokens(content),
            "node_count": node_count,
            "scope": scope,
        }

    @verb(role="act")
    def explain(self, target: str, depth: str = "standard") -> dict:
        """Deterministic code → markdown explanation; emits a Reflection.

        Inputs: target (str — file path | module | module.symbol),
                depth (str — brief | standard | deep).
        Returns: ``{reflection_id, content, tokens}``.
        chain_next: caller renders or stores the content.
        """
        if depth not in _explain._DEPTH_BUDGETS:
            depth = "standard"
        try:
            out = _explain.explain(target, depth=depth)
        except (ValueError, FileNotFoundError) as exc:
            return {"error": str(exc), "target": target, "depth": depth}
        rid = self.ctx.record("Reflection", {
            "scope": "technical",
            "kind": "explanation",
            "target": target,
            "depth": depth,
            "text": out["content"],
        })
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")
        return {
            "reflection_id": rid,
            "content": out["content"],
            "tokens": out["tokens"],
        }

    @verb(role="act")
    def index_repo(self, path: str = ".", apply: bool = False,
                   max_tokens: int = 3000) -> dict:
        """94%-reduction repo briefing — deterministic; ≤ max_tokens.

        Inputs: path (str), apply (bool — write PROJECT_INDEX.md),
                max_tokens (int — budget; default 3000).
        Returns: ``{index_id, content, tokens, files_scanned, writeup}``.
        chain_next: caller publishes via ``apply=True`` after review.
        """
        content, tokens, files_scanned = _index_repo.render(
            path, self.ctx.memory, intent_id=self.ctx.intent_id,
            max_tokens=max_tokens)
        sha = _index_repo.content_sha(content)
        index_id = self.ctx.record("RepoIndex", {
            "path": os.path.abspath(path),
            "content_sha": sha,
            "token_count": tokens,
            "generated_at": int(time.time()),
        })
        self.ctx.link(index_id, self.ctx.intent_id, "SERVES")
        writeup = "planning-only"
        if apply:
            target = os.path.join(os.path.abspath(path), "PROJECT_INDEX.md")
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                writeup = f"wrote {target}"
            except OSError as exc:
                writeup = f"write failed: {exc}"
        return {
            "index_id": index_id,
            "content": content,
            "tokens": tokens,
            "files_scanned": files_scanned,
            "writeup": writeup,
        }
