# agency-scaffold: v1
"""loop — design + run a verified agent loop (the looper port; Specs 362–369, 387).

The **wired surface** of the looper port: thin verbs delegating to the
lifecycle-spine logic in ``agency/_loop.py`` so the loop is discoverable
(``search``), schema'd (``get_schema``), runnable (``execute``/CLI), and — the
point of Spec 387 W1 — records an ``Invocation`` on every call (the provenance
moat the bare spine functions bypassed). The loop's goal IS an Intent (363);
verification IS typed gate criteria (364); the council IS persona+panel (365); the
runtime IS a registered Lifecycle machine (366); emission IS Document render (368);
the runner is the out-of-session twin (369). See `docs/vision/reference/loop.md`.

Use when: designing, opening, advancing, or emitting a self-verifying agent loop —
an iterate-until-clean workflow with typed criteria, a cross-model review council,
and honest termination guards.
Triggers:
- "design / build / set up an agent loop" or a /goal-style iterate-until-verified task
- a loop needs typed verification criteria or a reviewer/judge gate
- emitting a portable loop workspace (loop.yaml / run-loop.py) or running it in-session
Red flags:
- a loop with NO termination guard → `open` refuses it (never a guard-free loop)
- a `revise_until_clean` gate with no judge member / human criterion → `recommend_council` flags it
- a model invoke / check that is a shell string → rejected (argv-only, Spec 192)
"""
from __future__ import annotations

from ... import _loop
from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


class LoopCapability(CapabilityBase):
    name = "loop"
    home = "lifecycle"                 # the loop runtime IS a Lifecycle machine (366)
    # Interim: criteria/council/control are JSON on the loop node (parity with the
    # spine). Typed-node promotion (VerificationCriterion/CouncilMember/LoopControl)
    # is a later Spec 387 slice; W1 ships the wired surface + provenance.
    ontology = OntologyExtension()

    @property
    def _host(self):
        """The Engine handle the `_loop` functions need (.intent/.memory/.lifecycle)."""
        eng = self.ctx.engine
        if eng is None:
            raise RuntimeError("loop verbs require an engine-backed context")
        return eng

    # ── Spec 363 — goal ──────────────────────────────────────────────────────
    @verb(role="effect")
    def frame_goal(self, statement: str, definition_of_done: str,
                   deliverable: str = "", context_sources: list | None = None) -> dict:
        """Frame a loop goal as a root Intent (the goal IS an Intent, 363).

        Inputs: statement (str), definition_of_done (str), deliverable (str),
                context_sources (list of {file}|{cmd:[argv]} — argv-safe).
        Returns: ``{goal_id, context_sources}``.
        chain_next: loop.critique_goal(goal_id) then loop.open(goal_id).
        """
        return _loop.frame_goal(self._host, statement, definition_of_done,
                                deliverable=deliverable, context_sources=context_sources)

    @verb(role="transform")
    def critique_goal(self, goal_id: str) -> dict:
        """Coach a loop goal against goal-rubric.md — advisory, never blocks (363).

        Inputs: goal_id (str — the goal Intent id).
        Returns: ``{findings, clarity, ok, rubric_source}``.
        chain_next: re-frame on a failing dimension, or loop.open.
        """
        return _loop.critique_goal(self._host, goal_id)

    # ── Spec 364 — verification ──────────────────────────────────────────────
    @verb(role="effect")
    def add_criterion(self, loop_id: str, kind: str, check: list | None = None,
                      expect: str = "exit_zero", contains: str = "", rubric: str = "",
                      prompt: str = "", cid: str = "") -> dict:
        """Add a typed verification criterion (programmatic|judge|human) to a loop (364).

        Inputs: loop_id (str), kind (str), check (argv list — programmatic),
                expect (exit_zero|exit_nonzero|stdout_contains), contains (str),
                rubric (str — judge), prompt (str — human), cid (str — optional id).
        Returns: ``{criterion_id, kind}``.
        chain_next: loop.verify_report(loop_id) to audit the set.
        """
        return _loop.add_criterion(self._host, loop_id, kind, check=check, expect=expect,
                                   contains=contains, rubric=rubric, prompt=prompt, cid=cid)

    @verb(role="transform")
    def verify_report(self, loop_id: str) -> dict:
        """Audit a loop's verification SET against verification-rubric.md (364).

        Inputs: loop_id (str).
        Returns: ``{criteria, programmatic_ratio, warnings, rubric_source}``.
        chain_next: convert a judge/human criterion to programmatic where possible.
        """
        return _loop.verify_report(self._host, loop_id)

    # ── Spec 365 — council ───────────────────────────────────────────────────
    @verb(role="effect")
    def add_member(self, loop_id: str, role: str, scope: str = "both", family: str = "",
                   local: bool = False, driver: str = "", mid: str = "") -> dict:
        """Add a council member (reviewer|judge) bound to a model family to a loop (365).

        Inputs: loop_id (str), role (reviewer|judge), scope (plan|delivery|both),
                family (str), local (bool), driver (str), mid (str — optional id).
        Returns: ``{member_id, role, family}``.
        chain_next: loop.recommend_council(loop_id) to check the verdict-source rule.
        """
        return _loop.add_member(self._host, loop_id, role, scope=scope, family=family,
                                local=local, driver=driver, mid=mid)

    @verb(role="transform")
    def recommend_council(self, loop_id: str, host_family: str = "") -> dict:
        """Report verdict-source coverage + a cross-family recommendation (365).

        Inputs: loop_id (str), host_family (str — the host's model family).
        Returns: ``{members, verdict_sources_ok, missing, recommended, ...}``.
        chain_next: add a judge member for any gate missing a verdict source.
        """
        return _loop.recommend_council(self._host, loop_id, host_family=host_family)

    # ── Spec 366 — the machine ───────────────────────────────────────────────
    @verb(role="effect")
    def open(self, goal_id: str, max_iterations: int = 12, max_revisions: int = 3,
             budget: dict | None = None, no_progress_stall: int = 2) -> dict:
        """Open a loop Lifecycle SERVING the goal Intent; refuses a guard-free loop (366).

        Inputs: goal_id (str — the goal Intent), max_iterations (int),
                max_revisions (int), budget (dict|None), no_progress_stall (int).
        Returns: ``{loop_id, state, control}``.
        chain_next: loop.advance(loop_id) to walk it.
        """
        return _loop.open_loop(self._host, goal_id, max_iterations=max_iterations,
                               max_revisions=max_revisions, budget=budget,
                               no_progress_stall=no_progress_stall)

    @verb(role="effect")
    def advance(self, loop_id: str, artefact: str = "", judge_output: str = "",
                criteria_cwd: str = "") -> dict:
        """Advance the loop ONE transition — the in-session walk step (366).

        Inputs: loop_id (str), artefact (str — the drafted plan/delivery),
                judge_output (str — a judge member's verdict), criteria_cwd (str).
        Returns: ``{state, decision, stop_reason?, review?}``.
        chain_next: loop.advance again, or loop.compile when completed.
        """
        return _loop.advance(self._host, loop_id, artefact=artefact,
                             judge_output=judge_output, criteria_cwd=criteria_cwd or None)

    @verb(role="act")
    def preview(self, loop_id: str) -> dict:
        """Render the graph-derived ASCII flow preview of a loop (367 phase 6).

        Inputs: loop_id (str).
        Returns: ``{ascii, states, criteria, council, control}``.
        chain_next: loop.emit(loop_id, target) to write the workspace.
        """
        return _loop.preview(self._host, loop_id)

    # ── Spec 368 — emit ──────────────────────────────────────────────────────
    @verb(role="transform")
    def compile(self, loop_id: str) -> dict:
        """Resolve a loop into looper's loop.resolved.json shape, validated (368).

        Inputs: loop_id (str).
        Returns: ``{resolved, valid, findings}``.
        chain_next: loop.emit(loop_id, target) to render the files.
        """
        return _loop.compile(self._host, loop_id)

    @verb(role="effect")
    def emit(self, loop_id: str, target: str) -> dict:
        """Project the loop to its portable workspace (loop.yaml/resolved/LOOP.md…) (368).

        Inputs: loop_id (str), target (str — output directory).
        Returns: ``{files, valid, findings}``.
        chain_next: loop.emit_runner(loop_id, target) for the external runner.
        """
        return _loop.emit(self._host, loop_id, target)

    # ── Spec 369 — runner + egress ───────────────────────────────────────────
    @verb(role="effect")
    def emit_runner(self, loop_id: str, target: str) -> dict:
        """Write the stdlib run-loop.py (reads only loop.resolved.json) (369).

        Inputs: loop_id (str), target (str — output directory).
        Returns: ``{file}``.
        chain_next: run `python run-loop.py loop.resolved.json` externally.
        """
        return _loop.emit_runner(self._host, loop_id, target)

    @verb(role="act")
    def detect_models(self, store_path: str = "") -> dict:
        """Probe the model allowlist by PATH — metadata only, never secrets (369).

        Inputs: store_path (str — optional config path to persist the available set).
        Returns: ``{models, available}``.
        chain_next: loop.register_model(...) to add a custom model.
        """
        return _loop.detect_models(store_path=store_path or None)

    @verb(role="effect")
    def register_model(self, cli: str, family: str, invoke: list,
                       local: bool = False, store_path: str = "") -> dict:
        """Register a model invocation — argv-only, rejects secret-shaped material (369).

        Inputs: cli (str), family (str), invoke (argv list), local (bool),
                store_path (str — optional config path).
        Returns: ``{registered, ...}`` or ``{error}``.
        chain_next: loop.add_member(loop_id, ...) referencing the family.
        """
        return _loop.register_model(cli, family, invoke, local=local,
                                    store_path=store_path or None)

    @verb(role="transform")
    def egress_consent(self, member: dict, consent_given: bool = False,
                       policy: str = "required", redact_globs: list | None = None,
                       context_paths: list | None = None) -> dict:
        """Decide the cross-vendor egress gate (consent + redaction) — pure (369).

        Inputs: member (dict — the council member), consent_given (bool),
                policy (str), redact_globs (list), context_paths (list).
        Returns: ``{permit, requires_consent, redacted, reason}``.
        chain_next: record the consent as provenance, then send (or redact).
        """
        return _loop.egress_consent(member, consent_given=consent_given, policy=policy,
                                    redact_globs=redact_globs, context_paths=context_paths)
