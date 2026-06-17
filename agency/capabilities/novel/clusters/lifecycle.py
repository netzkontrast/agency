"""novel.lifecycle — Lifecycle cluster — concept -> novel -> chapter -> scene -> render + idea/session (Spec 101/102).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency._enums import project_enum
from agency._frontmatter import frontmatter_hash
from agency.capability import verb
from agency.toolresult import ToolResult
from .._main import (
    CHAPTER_STATUS,
    IDEA_STATUS,
    NOVEL_RENDER_SPEC,
    NOVEL_STATUS,
    SCENE_POV,
    _DEFAULT_SCENE_SYSTEM,
    _POV_ALIASES,
)


class LifecycleMixin:
    """Lifecycle cluster — concept -> novel -> chapter -> scene -> render + idea/session (Spec 101/102)."""

    @verb(role="act")
    def conceptualize(self, title: str, author: str,
                       premise: str = "",
                       central_question: str = "") -> ToolResult:
        """Render a novel-concept document, the first verb of the MVN flow (act).

        Inputs: title, author, premise, central_question.
        Returns: ``{result, artefact}`` novel-concept artefact.
        chain_next: ``novel.create_novel`` to mint the Novel node.
        """
        body = (f"# {title}\n\n**Author:** {author}\n\n"
                f"## Premise\n{premise}\n\n"
                f"## Central question\n{central_question}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "novel-concept",
                         "title": title, "premise": premise,
                         "central_question": central_question,
                         "body": body},
        })

    @verb(role="effect")
    def create_novel(self, title: str, author: str,
                      genre: str = "novel") -> ToolResult:
        """Record a Novel node SERVING the intent, materialising disk on production.

        Inputs: title, author, genre (default "novel"; routes the disk
                layout `works/{author}/works/{genre}/{slug}/`).
        Returns: ``{novel_id, title, status, work_path?}`` — ``work_path``
                appears when the production driver is wired (Spec 121).
        chain_next: ``novel.create_chapter`` once outline is ready.
        """
        nid = self.ctx.record_and_serve("Novel", {
            "title": title, "author": author,
            "genre": genre, "status": "concept",
        })
        out: dict = {"novel_id": nid, "title": title, "status": "concept"}
        drv = self._maybe_state_driver()
        if drv is not None:
            disk = drv.create_work(author, genre, title)
            out["work_path"] = disk["path"]
            out["work_slug"] = disk["slug"]
        return ToolResult.success(data=out)

    @verb(role="effect")
    def create_chapter(self, novel_id: str, number: int,
                        title: str, body: str = "") -> ToolResult:
        """Record a Chapter graph node + CHAPTER_OF the parent Novel (effect).

        Inputs: novel_id, number (1-indexed), title, body (optional draft body).
        Returns: ``{chapter_id, novel_id, number, title, status}``.
        chain_next: ``novel.chapter_report`` to aggregate state.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cid = self.ctx.record_and_serve("Chapter", {
            "novel": novel_id, "number": number, "title": title,
            "status": "outlined", "body": body,
        }, parent=novel_id, edge="CHAPTER_OF")
        drv = self._maybe_state_driver()
        if drv is not None:
            drv.create_chapter(
                novel_node.get("author", ""),
                novel_node.get("genre", "novel"),
                novel_node.get("title", ""),
                number, title, body=body)
        return ToolResult.success(data={
            "chapter_id": cid, "novel_id": novel_id,
            "number": number, "title": title, "status": "outlined",
        })

    @verb(role="transform")
    def chapter_report(self, novel_id: str) -> ToolResult:
        """Read-only aggregate over the novel's chapters (transform).

        Inputs: novel_id.
        Returns: ``{novel_id, chapter_count, word_count_total, by_status}``.
        chain_next: revise chapters then ``novel.render_manuscript``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # Find chapters of this novel
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        word_count = sum(len((c.get("body") or "").split())
                         for c in chapters)
        by_status: dict[str, int] = {}
        for c in chapters:
            s = c.get("status", "outlined")
            by_status[s] = by_status.get(s, 0) + 1
        return ToolResult.success(data={
            "novel_id": novel_id,
            "chapter_count": len(chapters),
            "word_count_total": word_count,
            "by_status": by_status,
        })

    @verb(role="act")
    def render_manuscript(self, novel_id: str) -> ToolResult:
        """Concatenate chapters into a manuscript artefact (act).

        Inputs: novel_id.
        Returns: ``{result, artefact}`` manuscript artefact with the assembled body.
        chain_next: terminal — deliver to the publishing path.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        title = novel_node.get("title", "Untitled")
        author = novel_node.get("author", "")
        parts = [f"# {title}\n", f"by {author}\n\n"]
        for c in chapters:
            parts.append(
                f"\n## Chapter {c.get('number', 0)}: {c.get('title', '')}\n\n"
                f"{c.get('body', '')}\n")
        body = "".join(parts)
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "manuscript",
                         "novel": novel_id,
                         "chapter_count": len(chapters),
                         "body": body},
        })

    @verb(role="effect")
    def render_all(self, novel_id: str) -> ToolResult:
        """Re-materialise a novel's full markdown tree from graph ground truth (effect).

        Spec 283 Slice 1 (Workstream F) — the on-demand full-rebuild path. Walks
        the novel `RenderSpec` (Novel → work.md, each Chapter →
        chapters/NN-slug.md), writes each file via the wired `render` driver
        (graph-only when none is wired — bare engines are unaffected), and mints
        ONE `Artefact{kind, path, entity_id, frontmatter_hash}` + `PRODUCES`
        edge per rendered entity. Closes the graph/disk provenance split (the
        evidence's 2-Artefacts-for-41-files drift): now #Artefacts == #files.
        Idempotent. Replaces the out-of-band `scripts/materialize_manuscript.py`.

        Inputs: novel_id.
        Returns: ``{novel_id, count, rendered: [{path, entity_id, artefact_id}],
                   wrote_disk}``.
        chain_next: ``novel.audit_novel_provenance`` to see the new Artefacts;
                    or any editorial gate.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        reg = self.ctx.drivers
        driver = reg.get("render") if (reg is not None and reg.has("render")) else None
        rendered: list[dict] = []
        # Novel (work.md), then each chapter in number order.
        self._render_entity(NOVEL_RENDER_SPEC.rule_for("Novel"), novel_node, driver, rendered)
        chapters = sorted(self.ctx.neighbors(novel_id, "CHAPTER_OF"),
                          key=lambda c: c.get("number", 0))
        crule = NOVEL_RENDER_SPEC.rule_for("Chapter")
        for c in chapters:
            self._render_entity(crule, c, driver, rendered)
        return ToolResult.success(data={
            "novel_id": novel_id, "count": len(rendered),
            "rendered": rendered, "wrote_disk": driver is not None,
        })

    def _render_entity(self, rule, node: dict, driver, rendered: list) -> None:
        """Render one node via its RenderRule: write (if a driver is wired) +
        mint the Artefact + PRODUCES edge. Shared by render_all (and, Slice 2,
        the auto-render hook)."""
        if rule is None or not node:
            return
        path = rule.output_path(node)
        fm = rule.frontmatter(node)
        body = rule.body(node)
        if driver is not None:
            driver.write(path, fm, body)
        aid = self.ctx.record("Artefact", {
            "kind": rule.kind, "path": path,
            "entity_id": node.get("id", ""),
            "frontmatter_hash": frontmatter_hash(fm),
        })
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        rendered.append({"path": path, "entity_id": node.get("id", ""),
                         "artefact_id": aid})

    @verb(role="effect")
    def capture_idea(self, text: str) -> ToolResult:
        """Record an Idea node SERVING the intent (effect).

        Pre-novel capture surface: free-text premise jotted before the
        gated conceptualizer runs. Default status ``new``.

        Inputs: text.
        Returns: ``{idea_id, text, status}``.
        chain_next: ``novel.promote_idea`` once the premise hardens.
        """
        iid = self.ctx.record_and_serve("Idea", {"text": text, "status": "new"})
        return ToolResult.success(data={
            "idea_id": iid, "text": text, "status": "new",
        })

    @verb(role="transform")
    def list_ideas(self, status: str = "") -> ToolResult:
        """List captured ideas with an optional status filter (transform).

        Inputs: status (one of ``IDEA_STATUS`` or ``""`` for all).
        Returns: ``{ideas: [...], count}``.
        chain_next: ``novel.promote_idea`` for any "new" idea ready to ship.
        """
        if status and status not in IDEA_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(IDEA_STATUS)}")
        ideas = [i for i in self.ctx.find("Idea")
                 if not status or i.get("status") == status]
        return ToolResult.success(data={"ideas": ideas, "count": len(ideas)})

    @verb(role="effect")
    def promote_idea(self, idea_id: str, title: str,
                      author: str) -> ToolResult:
        """Transition an Idea to a Novel, recording the PROMOTED_TO edge (effect).

        Flips the Idea's status to ``promoted``, mints a Novel node, and
        wires a PROMOTED_TO edge. Mirrors music's promote_idea / Idea-to-
        Album lineage.

        Inputs: idea_id, title, author.
        Returns: ``{idea_id, novel_id, title, status}``.
        chain_next: ``novel.create_chapter`` to start outlining.
        """
        node = self.ctx.recall(idea_id)
        if node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"idea_id={idea_id!r} not found")
        nid = self.ctx.record_and_serve("Novel", {
            "title": title, "author": author, "status": "concept",
        })
        self.ctx.link(idea_id, nid, "PROMOTED_TO")
        self.ctx.update(idea_id, {"status": "promoted"})
        return ToolResult.success(data={
            "idea_id": idea_id, "novel_id": nid,
            "title": title, "status": "concept",
        })

    @verb(role="transform")
    def find_novel(self, query: str = "") -> ToolResult:
        """Substring-match novel titles (transform, driver-free).

        Inputs: query (case-insensitive substring; ``""`` returns all).
        Returns: ``{novels: [{novel_id, title, author, status}], count}``.
        chain_next: ``novel.set_novel_status`` or ``novel.render_manuscript``.
        """
        q = query.lower()
        hits = []
        for n in self.ctx.find("Novel"):
            title = (n.get("title") or "").lower()
            if not q or q in title:
                hits.append({
                    "novel_id": n.get("id"),
                    "title": n.get("title"),
                    "author": n.get("author"),
                    "status": n.get("status"),
                })
        return ToolResult.success(data={"novels": hits, "count": len(hits)})

    @verb(role="effect", param_enums={"status": NOVEL_STATUS})
    def set_novel_status(self, novel_id: str, status: str) -> ToolResult:
        """Flip a Novel's enum-checked lifecycle status (effect).

        Inputs: novel_id, status (one of ``NOVEL_STATUS``).
        Returns: ``{novel_id, status}``.
        chain_next: continue per the new lifecycle phase.
        """
        if status not in NOVEL_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(NOVEL_STATUS)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        self.ctx.update(novel_id, {"status": status})
        return ToolResult.success(data={
            "novel_id": novel_id, "status": status,
        })

    @verb(role="transform")
    def list_chapters(self, novel_id: str) -> ToolResult:
        """List a novel's chapters ordered by number (transform).

        Inputs: novel_id.
        Returns: ``{chapters: [{chapter_id, number, title, status}], count}``.
        chain_next: ``novel.set_chapter_status`` or ``novel.create_scene``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        items = [{
            "chapter_id": c.get("id"),
            "number": c.get("number"),
            "title": c.get("title"),
            "status": c.get("status"),
        } for c in chapters]
        return ToolResult.success(data={"chapters": items, "count": len(items)})

    @verb(role="transform")
    def pov_options(self, keys: str = "") -> ToolResult:
        """Structured POV choices for an assumption-gate (transform).

        Spec 285 Part B — the `resolve_via` target for the `scene-writer`
        skill's `requires_input` POV gate: a FastMCP-annotated verb in the
        novel capability that sources the canonical `SCENE_POV` members so the
        walker can elicit a CHOICE from the user instead of assuming a POV.

        Inputs: keys (the missing requires_input keys, comma-joined; advisory).
        Returns: ``{options: [<SCENE_POV members>], keys}``.
        chain_next: the walker presents ``options`` via an elicit gate.
        """
        return ToolResult.success(data={"options": sorted(SCENE_POV), "keys": keys})

    @verb(role="effect", param_enums={"pov": SCENE_POV})
    def create_scene(self, chapter_id: str, slug: str,
                      pov: str) -> ToolResult:
        """Record a Scene node + SCENE_OF the parent Chapter (effect).

        Spec 284 — ``pov`` is a *projected enum*: it accepts rich free text
        (e.g. ``"auktorialer Erzähler"``) and projects it onto a canonical
        ``SCENE_POV`` member, preserving the original in ``pov_detail`` (the
        non-lossy contract). Input carrying no POV signal still fails
        PERMANENT, listing the members.

        Inputs: chapter_id, slug (scene-local short name), pov (a ``SCENE_POV``
                member or rich text projected onto one).
        Returns: ``{scene_id, chapter_id, slug, pov, pov_detail?}``.
        chain_next: ``novel.create_scene`` for next beat or back to
                    ``novel.set_chapter_status`` once the chapter's
                    scene set is complete.
        """
        canonical, detail = project_enum(pov, SCENE_POV, aliases=_POV_ALIASES)
        if canonical is None:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"pov={pov!r} carries no POV signal — not projectable onto "
                f"{sorted(SCENE_POV)}")
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        props = {"chapter": chapter_id, "slug": slug, "pov": canonical}
        if detail:
            props["pov_detail"] = detail
        sid = self.ctx.record_and_serve("Scene", props, parent=chapter_id, edge="SCENE_OF")
        out = {"scene_id": sid, "chapter_id": chapter_id,
               "slug": slug, "pov": canonical}
        if detail:
            out["pov_detail"] = detail
        return ToolResult.success(data=out)

    @verb(role="act")
    def generate_scene_body(self, scene_id: str = "", scene_brief: str = "",
                              alter_id: str = "", system: str = "",
                              host_completion: dict | None = None,
                              prefer_delegate: bool = False,
                              max_tokens: int = 8000) -> ToolResult:
        """Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279.

        Drives the Spec 130 scene-writer phase 3 (generate) with a real
        TextDriver backed by the AnthropicDriver. Three paths
        (resume wins):

        1. ``host_completion`` supplied — Claude Code already ran the
           inference after a prior delegation; parse the result.
        2. AnthropicDriver capable → ``driver.complete(messages,
           system)`` direct (Spec 147 Slice 1).
        3. Driver backend ``"none"`` AND ``prefer_delegate=True`` →
           return a ``kind="llm_delegate"`` envelope so the host runs
           inference and re-calls (Spec 279).

        The generated body is ALWAYS captured via Spec 154
        ``capture_overflow`` and returned through ``body_handle``
        (Artefact id) — never inline. A wrapping LLM driver fetches
        only the slice it needs (Spec 146 prefix discipline).

        Slice 1 ships the driver-bound generate path + the typed
        ``WetSceneResult`` shape. Slice 2+ adds the gate-driven
        regenerate loop (the shipped prose checks gate the output).

        Inputs:
          - scene_id (str — Scene node id; the body is recorded as
            an Artefact PRODUCES_FROM this Scene)
          - scene_brief (str — assembled scene brief from Spec 127;
            the scene-writer phase 1 output. Named to match the
            phase's produces key so the skill walker's input mapping
            forwards it verbatim.)
          - alter_id (str — when set, the scene is voice-locked via
            Spec 144; ``voice_locked=True`` in the result)
          - system (str — system prompt override)
          - host_completion (dict | None — Spec 279 resume envelope)
          - prefer_delegate (bool — when True + backend "none",
            emit the llm_delegate envelope instead of failing)
          - max_tokens (int — request budget for the LLM call)
        Returns: ``WetSceneResult`` dict with ``{intent_id, scene_id,
                 body_handle, wc, driver, voice_locked, refusal?,
                 kind?, request?, regen_count, passes_all, checks}``.
        chain_next: ``novel.integrate_scene_body(scene_id, body)``
                    after fetching via ``memory.recall_overflow_slice``.
        Failure modes: ``Codes.VOICE_BRIEF_MISSING`` (alter_id set but
                       brief empty); ``Codes.SCENE_OVERFLOW_LOST``
                       (capture failed); ``Codes.DRIVER_REFUSAL``
                       (Spec 147 propagates).
        """
        from agency._host_llm import (
            complete_or_delegate, HostLLMRequest, HostDelegateError,
            make_continuation_token,
        )
        from agency._overflow import capture_overflow
        from agency._tokens import count_tokens

        voice_locked = bool(alter_id)
        # Voice-lock fidelity invariant: when alter_id set, the brief
        # must come from Spec 144 (signaled by non-empty `brief`).
        if voice_locked and not scene_brief.strip():
            return ToolResult.failure(
                "VOICE_BRIEF_MISSING",
                f"alter_id={alter_id!r} requires a Spec 144 voice-locked "
                f"scene_brief; got empty scene_brief")

        # Codex review (P2): validate scene_id BEFORE spending LLM work.
        # A mistyped scene_id would otherwise burn a real Anthropic /
        # host generation and produce prose whose `body_handle` can't
        # be integrated downstream because the Scene doesn't exist.
        # Empty scene_id is allowed for stateless probe calls (tests).
        # Codex review on PR #137 round 2: use `recall_typed("Scene", …)`
        # (Spec 056 — <label>_id params must be label-checked). Passing
        # a Chapter or Intent id previously slipped past the bare
        # `recall` guard and would mis-attribute the body.
        if scene_id:
            scene_node = self.ctx.memory.recall_typed(scene_id, "Scene")
            if scene_node is None:
                return ToolResult.failure(
                    "NOT_FOUND",
                    f"scene_id={scene_id!r} not found as a Scene node — "
                    f"cannot route the generated body to a non-existent "
                    f"or wrong-label node; create the Scene with "
                    f"novel.create_scene first")

        # Resolve the anthropic driver (None when not wired).
        driver = None
        try:
            reg = getattr(self.ctx, "drivers", None)
            if reg is not None and reg.has("anthropic"):
                driver = reg.get("anthropic")
        except Exception:
            driver = None

        # No driver AND no resume → degrade to graceful failure so
        # tests/CI without a key path don't crash. The caller can
        # retry with prefer_delegate=True to opt into the envelope.
        if driver is None and host_completion is None:
            return ToolResult.failure(
                "DEPENDENCY_MISSING",
                "no anthropic driver wired and no host_completion "
                "supplied; pass prefer_delegate=True for host-LLM "
                "delegation (Spec 279) or wire an AnthropicDriver "
                "(Spec 147)")

        # When the driver isn't capable AND we're not opting into
        # delegation AND there's no resume, refuse cleanly.
        if (driver is not None and host_completion is None
                and not prefer_delegate
                and driver.backend() == "none"):
            return ToolResult.failure(
                "DEPENDENCY_MISSING",
                "anthropic driver backend is 'none' (no key, no client) "
                "and prefer_delegate=False; set ANTHROPIC_API_KEY or "
                "pass prefer_delegate=True for host-LLM delegation")

        # Build the LLM request. The brief carries the per-scene
        # instructions; system carries the role/voice directive.
        messages = [{"role": "user", "content": scene_brief or ""}]
        system_prompt = system or _DEFAULT_SCENE_SYSTEM
        if voice_locked:
            system_prompt = (
                f"{system_prompt}\n\nVoice-lock active for alter "
                f"`{alter_id}`; honour the §TABOO + §EXAMPLES "
                f"sections of the brief verbatim.")

        # Stable continuation token for the resume invariant
        # (Spec 279 single-Invocation moat).
        token = make_continuation_token(
            self.ctx.intent_id or "",
            "novel.generate_scene_body",
            {"scene_id": scene_id, "alter_id": alter_id})

        # Driver may be None when we have a host_completion to resume.
        if driver is None:
            class _NoDriver:
                def backend(self) -> str:
                    return "none"
            driver = _NoDriver()

        try:
            result = complete_or_delegate(
                driver,
                messages=messages,
                system=system_prompt,
                host_completion=host_completion,
                continuation_token=token,
                max_tokens=max_tokens,
                host=self.ctx.host,        # Spec 285 — real MCP sampling when available
            )
        except HostDelegateError as exc:
            return ToolResult.failure(
                "HOST_DELEGATE_MALFORMED" if exc.code ==
                HostDelegateError.MALFORMED else "HOST_DELEGATE_FAIL",
                str(exc))
        except Exception as exc:                                      # noqa: BLE001
            return ToolResult.failure(
                "DRIVER_REFUSAL",
                f"AnthropicDriver raised on scene-body generation: {exc}")

        # Branch 3: delegate envelope — return it so the wrapping host
        # (Claude Code) recognises the kind="llm_delegate" signal.
        if isinstance(result, HostLLMRequest):
            return ToolResult.success(data={
                "intent_id":      self.ctx.intent_id,
                "scene_id":       scene_id,
                "body_handle":    "",
                "wc":             0,
                "checks":         [],
                "passes_all":     False,
                "regen_count":    0,
                "driver":         "delegate",
                "voice_locked":   voice_locked,
                "refusal":        None,
                "kind":           result.kind,
                "request":        result.to_dict(),
            })

        # Branches 1+2: a Completion. Capture the body via Spec 154 so
        # it returns via handle, never inline (Spec 146 + Spec 154).
        body_text = result.text or ""
        try:
            ovf = capture_overflow(
                body_text, max_tokens=512, counter=count_tokens)
        except Exception as exc:                                      # noqa: BLE001
            return ToolResult.failure(
                "SCENE_OVERFLOW_LOST",
                f"capture_overflow failed: {exc}")

        # Record the body as an Artefact so a follow-up
        # `memory.recall_overflow_slice(handle)` serves the full body.
        artefact_id = self.ctx.record("Artefact", {
            "kind":             "scene-body",
            "scene_id":         scene_id,
            "voice_locked":     voice_locked,
            "alter_id":         alter_id,
            "total_tokens":     ovf.total_tokens,
            "full_body":        ovf.full_body,
            "stop_reason":      result.stop_reason,
            "driver":           ("host" if result.stop_reason ==
                                  "host_provided" else "spec147"),
        })
        if scene_id:
            self.ctx.link(artefact_id, scene_id, "PRODUCES_FROM")
        self.ctx.link(artefact_id, self.ctx.intent_id, "SERVES")

        # Word count (cheap, kept on the prefix per Spec 146).
        wc = len(body_text.split()) if body_text else 0

        return ToolResult.success(data={
            "intent_id":      self.ctx.intent_id,
            "scene_id":       scene_id,
            "body_handle":    artefact_id,
            "wc":             wc,
            "checks":         [],
            # Codex review (P2): empty `checks` means no gate was applied
            # — `passes_all=True` would be misleading. Slice 1 hasn't
            # wired the regenerate loop; report `unchecked` so callers
            # don't integrate the body assuming the gate ran.
            "passes_all":     False,
            "unchecked":      True,
            "regen_count":    0,
            "driver":         ("host" if result.stop_reason ==
                                "host_provided" else "spec147"),
            "voice_locked":   voice_locked,
            "refusal":        None,
        })

    @verb(role="transform")
    def fetch_scene_body(self, body_handle: str = "",
                          max_chars: int = 0) -> ToolResult:
        """Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact.

        ``novel.generate_scene_body`` returns the body via ``body_handle``
        (an Artefact id) instead of inlining the prose (Spec 146 prefix
        discipline + Spec 154 budget). This verb resolves the handle back
        to the body so the MCP/CLI surface has a documented fetch path —
        Codex review on PR #137 surfaced that ``memory.recall_overflow_slice``
        isn't registered as a verb, leaving the body stranded behind a
        graph-internal field.

        Inputs: body_handle (Artefact id), max_chars (0 = full body;
                positive = head-slice cap).
        Returns: ``{body, total_chars, total_tokens, voice_locked,
                 alter_id, scene_id, driver, stop_reason, truncated}``.
        chain_next: ``novel.integrate_scene_body(scene_id, body)``.
        Failure modes: ``NOT_FOUND`` (body_handle missing),
                       ``BAD_REQUEST`` (handle resolves to a non-scene-
                       body Artefact).
        """
        if not body_handle:
            return ToolResult.failure(
                "INVALID_ARGUMENT", "body_handle is required")
        art = self.ctx.recall(body_handle)
        if art is None:
            return ToolResult.failure(
                "NOT_FOUND", f"body_handle={body_handle!r} not found")
        if art.get("kind") != "scene-body":
            return ToolResult.failure(
                "BAD_REQUEST",
                f"body_handle={body_handle!r} is "
                f"kind={art.get('kind')!r}, not 'scene-body'")
        full = str(art.get("full_body") or "")
        truncated = False
        if max_chars and max_chars > 0 and len(full) > max_chars:
            body = full[:max_chars]
            truncated = True
        else:
            body = full
        return ToolResult.success(data={
            "body":          body,
            "total_chars":   len(full),
            "total_tokens":  int(art.get("total_tokens") or 0),
            "voice_locked":  bool(art.get("voice_locked")),
            "alter_id":      str(art.get("alter_id") or ""),
            "scene_id":      str(art.get("scene_id") or ""),
            "driver":        str(art.get("driver") or ""),
            "stop_reason":   str(art.get("stop_reason") or ""),
            "truncated":     truncated,
        })

    @verb(role="effect")
    def integrate_scene_body(self, scene_id: str, body: str) -> ToolResult:
        """Spec 130 phase 5 — write the generated body back to the Scene (effect).

        The scene-writer skill's hard-gate integrate phase: promotes a
        draft body (from skill phase 3's generate output) onto the Scene
        node and records a ``scene-integration`` Artefact for provenance.

        Inputs: scene_id, body (the prose body to commit).
        Returns: ``{scene_id, artefact_id, bytes}``.
        chain_next: terminal — the manuscript advances to the next scene.
        """
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        self.ctx.memory.update(scene_id, {"body": body})
        aid = self.ctx.record("Artefact", {
            "kind": "scene-integration",
            "scene_id": scene_id,
            "bytes": len(body),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, aid, "PRODUCES")
        return ToolResult.success(data={
            "scene_id": scene_id,
            "artefact_id": aid,
            "bytes": len(body),
        })

    @verb(role="effect", param_enums={"status": CHAPTER_STATUS})
    def set_chapter_status(self, chapter_id: str,
                            status: str) -> ToolResult:
        """Flip a Chapter's enum-checked lifecycle status (effect).

        Inputs: chapter_id, status (one of ``CHAPTER_STATUS``).
        Returns: ``{chapter_id, status}``.
        chain_next: ``novel.novel_progress`` to see the aggregate shift.
        """
        if status not in CHAPTER_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(CHAPTER_STATUS)}")
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        self.ctx.update(chapter_id, {"status": status})
        return ToolResult.success(data={
            "chapter_id": chapter_id, "status": status,
        })

    @verb(role="effect")
    def rename_novel(self, novel_id: str, new_title: str) -> ToolResult:
        """Update a Novel's title (effect, graph-only).

        Inputs: novel_id, new_title.
        Returns: ``{novel_id, title}``.
        chain_next: continue authoring; the rename is auditable via the
                    graph's bi-temporal stamp.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        self.ctx.update(novel_id, {"title": new_title})
        return ToolResult.success(data={
            "novel_id": novel_id, "title": new_title,
        })

    @verb(role="transform")
    def novel_progress(self, novel_id: str) -> ToolResult:
        """Aggregate progress (word-count + per-status counts) for a novel (transform).

        Inputs: novel_id.
        Returns: ``{novel_id, chapter_count, word_count_total, by_status}``.
        chain_next: ``novel.render_manuscript`` once status counts say ready.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        word_count = sum(len((c.get("body") or "").split())
                         for c in chapters)
        by_status: dict[str, int] = {}
        for c in chapters:
            s = c.get("status", "outlined")
            by_status[s] = by_status.get(s, 0) + 1
        return ToolResult.success(data={
            "novel_id": novel_id,
            "chapter_count": len(chapters),
            "word_count_total": word_count,
            "by_status": by_status,
        })

    @verb(role="transform")
    def resume_session(self) -> ToolResult:
        """Return the most-recently-created Novel's id + title (transform).

        Inputs: none.
        Returns: ``{novel_id, title}`` — empty strings when no Novel exists.
        chain_next: typically ``novel.novel_progress(novel_id)`` to land in
                    the right state on session resume.
        """
        novels = list(self.ctx.find("Novel"))
        if not novels:
            return ToolResult.success(data={"novel_id": "", "title": ""})
        # Newest first by valid-from (graphqlite's bi-temporal stamp).
        last = max(novels, key=lambda r: r.get("vfrom", 0))
        return ToolResult.success(data={
            "novel_id": last.get("id", ""),
            "title": last.get("title", ""),
        })
