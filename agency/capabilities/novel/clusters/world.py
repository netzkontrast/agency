"""novel.world — World cluster — world sub-graph: cultures, religions, languages, magic, axioms (Spec 123).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes
from .._main import (
    WORLD_AXIOM_SEVERITY,
    _CHARACTER_WORLD_EDGES,
    _word_tokens,
)


class WorldMixin:
    """World cluster — world sub-graph: cultures, religions, languages, magic, axioms (Spec 123)."""

    @verb(role="effect")
    def create_world(self, slug: str, name: str) -> ToolResult:
        """Mint a World node + SERVES intent (effect).

        Inputs: slug (URL-safe handle), name (human label).
        Returns: ``{world_id, slug, name}``.
        chain_next: ``novel.create_culture`` / ``create_religion`` /
                    ``create_language`` / ``create_magic_system`` /
                    ``create_world_axiom`` to populate it.
        """
        wid = self.ctx.record("World", {"slug": slug, "name": name})
        self.ctx.link(wid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "world_id": wid, "slug": slug, "name": name,
        })

    @verb(role="effect")
    def create_culture(self, world_id: str, slug: str,
                        name: str) -> ToolResult:
        """Mint a Culture under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{culture_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Culture", slug, name, return_key="culture_id")

    @verb(role="effect")
    def create_religion(self, world_id: str, slug: str,
                         name: str) -> ToolResult:
        """Mint a Religion under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{religion_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Religion", slug, name, return_key="religion_id")

    @verb(role="effect")
    def create_language(self, world_id: str, slug: str,
                         name: str) -> ToolResult:
        """Mint a Language under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{language_id, world_id, slug, name}``.
        chain_next: continue populating the world.
        """
        return self._create_world_child(
            world_id, "Language", slug, name, return_key="language_id")

    @verb(role="effect")
    def create_magic_system(self, world_id: str, slug: str,
                             name: str) -> ToolResult:
        """Mint a MagicSystem under a World + PART_OF_WORLD edge (effect).

        Inputs: world_id, slug, name.
        Returns: ``{magic_system_id, world_id, slug, name}``.
        chain_next: ``novel.create_world_axiom`` to encode its rules.
        """
        return self._create_world_child(
            world_id, "MagicSystem", slug, name,
            return_key="magic_system_id")

    def _create_world_child(self, world_id: str, label: str, slug: str,
                              name: str, *, return_key: str) -> ToolResult:
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"world_id={world_id!r} not found")
        nid = self.ctx.record(label, {"slug": slug, "name": name})
        self.ctx.link(nid, world_id, "PART_OF_WORLD")
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            return_key: nid, "world_id": world_id,
            "slug": slug, "name": name,
        })

    @verb(role="effect", param_enums={"severity": WORLD_AXIOM_SEVERITY})
    def create_world_axiom(self, world_id: str, text: str,
                            severity: str = "hard") -> ToolResult:
        """Encode a WorldAxiom (rule) under a World (effect).

        Inputs: world_id, text (the rule body — concise),
                severity (one of ``WORLD_AXIOM_SEVERITY``: hard | soft).
        Returns: ``{axiom_id, world_id, severity, text}``.
        chain_next: ``novel.find_axiom_contradictions`` after several land.
        """
        if severity not in WORLD_AXIOM_SEVERITY:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"severity={severity!r} not in {sorted(WORLD_AXIOM_SEVERITY)}")
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"world_id={world_id!r} not found")
        aid = self.ctx.record("WorldAxiom", {
            "text": text, "severity": severity,
        })
        self.ctx.link(aid, world_id, "PART_OF_WORLD")
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "axiom_id": aid, "world_id": world_id,
            "severity": severity, "text": text,
        })

    @verb(role="transform")
    def list_world(self, world_id: str) -> ToolResult:
        """Render a tree of a World's contents (transform).

        Walks PART_OF_WORLD edges (Spec 125 `ctx.neighbors`) and groups
        the children by label.

        Inputs: world_id.
        Returns: ``{world, cultures, religions, languages, magic_systems,
                  axioms}``.
        chain_next: ``novel.find_axiom_contradictions`` for the rule audit.
        """
        world = self.ctx.recall(world_id)
        if world is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"world_id={world_id!r} not found")
        children = self.ctx.neighbors(world_id, "PART_OF_WORLD")
        groups = {
            "cultures": [], "religions": [], "languages": [],
            "magic_systems": [], "axioms": [],
        }
        label_to_key = {
            "Culture": "cultures", "Religion": "religions",
            "Language": "languages", "MagicSystem": "magic_systems",
            "WorldAxiom": "axioms",
        }
        for c in children:
            # The child's "labels" aren't on the props dict; look up the
            # node to discover its label set.
            for label in self.ctx.labels_of(c.get("id", "")):
                if label in label_to_key:
                    groups[label_to_key[label]].append(c)
                    break
        return ToolResult.success(data={
            "world": {"id": world_id, "slug": world.get("slug"),
                       "name": world.get("name")},
            **groups,
        })

    @verb(role="effect")
    def find_axiom_contradictions(self, world_id: str) -> ToolResult:
        """Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect).

        Per Open Q2 (resolved as v1 decidable): flags axiom pairs whose
        bodies share ≥ 2 motif words AND one carries a negation marker
        the other lacks (``not``, ``never``, ``no``). The judgement pass
        (full red_team) is a future xcap to ``thinking.red_team``.

        Inputs: world_id.
        Returns: ``{passed, contradictions: [{a_id, b_id, a_text, b_text}]}``.
        chain_next: walk pairs; refine wording; rerun.
        """
        if self.ctx.recall(world_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"world_id={world_id!r} not found")
        axioms = [a for a in self.ctx.neighbors(world_id, "PART_OF_WORLD")
                   if "text" in a and "severity" in a]
        contradictions: list[dict] = []
        negations = {"not", "never", "no", "cannot", "without"}
        for i, a in enumerate(axioms):
            a_words = {w.lower() for w in _word_tokens(a.get("text", ""))}
            a_neg = bool(a_words & negations)
            for b in axioms[i + 1:]:
                b_words = {w.lower() for w in _word_tokens(b.get("text", ""))}
                b_neg = bool(b_words & negations)
                shared = a_words & b_words - negations
                # Two axioms share motif words AND exactly one carries
                # a negation marker → likely contradiction.
                if len(shared) >= 2 and (a_neg ^ b_neg):
                    contradictions.append({
                        "a_id": a.get("id"), "b_id": b.get("id"),
                        "a_text": a.get("text"),
                        "b_text": b.get("text"),
                    })
                    # Record CONTRADICTS edge so the relationship is
                    # queryable from the graph (not just the verb return).
                    self.ctx.link(a.get("id"), b.get("id"), "CONTRADICTS")
        return ToolResult.success(data={
            "passed": not contradictions,
            "contradictions": contradictions,
        })

    @verb(role="effect")
    def link_character_to_world(self, character_id: str, target_id: str,
                                 edge_kind: str = "BELONGS_TO") -> ToolResult:
        """Add a typed edge from Character → World child (effect).

        ``edge_kind`` is constrained to the documented set:
        ``BELONGS_TO`` (catch-all), ``INHABITS`` (lives in / Culture),
        ``WORSHIPS`` (Religion), ``SPEAKS`` (Language), ``WIELDS``
        (MagicSystem). The orchestrator picks one matching the target's
        label.

        Inputs: character_id, target_id, edge_kind.
        Returns: ``{character_id, target_id, edge_kind}``.
        chain_next: continue weaving the character into the world.
        """
        if edge_kind not in _CHARACTER_WORLD_EDGES:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"edge_kind={edge_kind!r} not in "
                f"{sorted(_CHARACTER_WORLD_EDGES)}")
        # Character node doesn't exist in the ontology yet (Slice 2);
        # accept any node id pending the character-psychology layer.
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"character_id={character_id!r} not found")
        if self.ctx.recall(target_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"target_id={target_id!r} not found")
        self.ctx.link(character_id, target_id, edge_kind)
        return ToolResult.success(data={
            "character_id": character_id, "target_id": target_id,
            "edge_kind": edge_kind,
        })
