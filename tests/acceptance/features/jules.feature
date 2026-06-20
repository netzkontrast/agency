Feature: jules capability — dispatch, provenance, and in-process contracts
  jules drives remote agent sessions end-to-end. Because real Jules work
  requires JULES_API_KEY + network, these scenarios test ONLY the observable
  in-process contract: envelope shapes, graph provenance, state logic, and
  skill registration. Network / API behaviours are listed as GAPS below.

  Background:
    Given a confirmed intent

  # ── dispatch — envelope + provenance ─────────────────────────────────────────

  Scenario: dispatch returns the documented envelope
    Given a stub Jules backend
    When I dispatch a Jules session with source "netzkontrast/agency" and branch "main"
    Then the result carries status, session, url, alias, and artefact fields

  Scenario: dispatch records provenance in the graph
    Given a stub Jules backend
    When I dispatch a Jules session with source "netzkontrast/agency" and branch "main"
    Then an Invocation SERVES the intent in the graph

  Scenario: dispatch records a JulesSession node in the graph
    Given a stub Jules backend
    When I dispatch a Jules session with source "netzkontrast/agency" and branch "main"
    Then a JulesSession node is recorded in the graph

  Scenario: dispatch default flag matrix — plan-gated, no automation
    Given a recording stub Jules backend
    When I dispatch a Jules session with source "netzkontrast/agency" and branch "main"
    Then the backend receives require_plan_approval=True and automation_mode=""

  Scenario: dispatch with automation_mode AUTO_CREATE_PR
    Given a recording stub Jules backend
    When I dispatch with automation_mode "AUTO_CREATE_PR"
    Then the backend receives require_plan_approval=True and automation_mode="AUTO_CREATE_PR"

  Scenario: dispatch with zero-touch flags
    Given a recording stub Jules backend
    When I dispatch with require_plan_approval=False and automation_mode="AUTO_CREATE_PR"
    Then the backend receives require_plan_approval=False and automation_mode="AUTO_CREATE_PR"

  Scenario: dispatch forwards protocol_preset to the backend
    Given a recording stub Jules backend
    When I dispatch with protocol_preset "agency-default"
    Then the backend receives protocol_preset="agency-default"

  # ── activities — trimmed preview vs full retrieval (no silent truncation) ─────

  Scenario: activities defaults to the trimmed summary preview
    Given a stub Jules backend that captures the activities call
    When I fetch activities without full
    Then the activities backend received summary_only=True

  Scenario: activities full=True requests the untrimmed bodies (recovers a long message)
    Given a stub Jules backend that captures the activities call
    When I fetch activities with full=True
    Then the activities backend received summary_only=False

  # ── verify — COMPLETED ≠ done logic ──────────────────────────────────────────

  Scenario: verify returns silent_fail when COMPLETED but branch not on remote
    Given a vcs backend that reports the branch does NOT exist on origin
    When I invoke verify with state "COMPLETED" and branch "feat-missing"
    Then the result contains ok=False and reason mentions the branch

  Scenario: verify returns ok when branch exists on remote
    Given a vcs backend that reports the branch EXISTS on origin
    When I invoke verify with state "COMPLETED" and branch "feat-present"
    Then the result contains ok=True

  Scenario: verify does not flag silent_fail for in-progress sessions
    Given a vcs backend that reports the branch does NOT exist on origin
    When I invoke verify with state "IN_PROGRESS" and branch "feat-wip"
    Then the result does not flag silent_fail

  # ── lint_prompt — observable output contract ──────────────────────────────────

  Scenario: lint_prompt returns ok=True for a canonical prompt
    When I lint a prompt that names all canonical Jules tools
    Then the lint result is ok with no missing tools

  Scenario: lint_prompt flags missing tools in a bad prompt
    When I lint a prompt that says "open a PR when done"
    Then the lint result is not ok and missing includes "submit" and "pre_commit_instructions"

  Scenario: lint_prompt reports extras for tools outside the caller override
    When I lint a prompt naming publish pair plus "replace_with_git_merge_diff" with must_name "pre_commit_instructions,submit"
    Then the lint result is ok and extras includes "replace_with_git_merge_diff"

  Scenario: lint_prompt empty must_name falls back to the canonical set
    When I lint the same prompt with empty must_name and with default must_name
    Then both results are identical

  # ── review_comment — PR review-cycle handshake ────────────────────────────────

  Scenario: review_comment appends the handshake tail
    When I invoke review_comment with body "Verdict: changes-requested."
    Then the result carries tail_appended=True
    And the text contains "reply_to_pr_comments"
    And the original body is preserved in the text

  Scenario: review_comment is idempotent — tail does not duplicate
    When I invoke review_comment twice with the same body
    Then the reply_to_pr_comments text appears exactly once in the final text

  # ── detect_mode — dogfood vs delegate distinction ────────────────────────────

  Scenario: detect_mode returns dogfood for the self source
    When I invoke detect_mode with source "netzkontrast/agency"
    Then the mode is "dogfood"
    And the reason mentions lexical scoping

  Scenario: detect_mode returns delegate for an external source
    When I invoke detect_mode with source "someone-else/their-project"
    Then the mode is "delegate"
    And the reason mentions clone block

  # ── preamble assembly — observable text contracts ────────────────────────────

  Scenario: Mode A preamble omits clone block
    When I assemble the preamble for source "netzkontrast/agency" with prompt "do the thing"
    Then the assembled text does not contain "git clone"
    And the assembled text contains "AGENCY_PROTOCOL.md"
    And the assembled text contains the original prompt

  Scenario: Mode B preamble includes clone block
    When I assemble the preamble for source "someone-else/project" with prompt "do the thing"
    Then the assembled text contains "git clone --depth=1"
    And the assembled text contains the original prompt

  Scenario: Mode B preamble includes read-only instruction
    When I assemble the preamble for source "someone-else/project" with prompt "do the thing"
    Then the assembled text contains a read-only instruction for the agency clone

  Scenario: unknown preset raises an error
    When I assemble the preamble with an unknown preset name
    Then a ValueError is raised mentioning "unknown protocol_preset"

  Scenario: default preset equals explicit "agency-default" preset
    When I assemble the preamble for source "netzkontrast/agency" with prompt "x" twice
    Then both assembled texts are identical

  # ── watch — queue drain + heartbeat ──────────────────────────────────────────

  Scenario: watch returns error when called without session or for_intent
    When I invoke watch with no arguments
    Then the result action is "error"
    And the instruction mentions "session or for_intent"

  Scenario: watch returns noop when the watcher has not been started
    When I invoke watch with for_intent set but no watcher started
    Then the result action is "noop"
    And the evidence reason mentions "not started"

  Scenario: watch drains a queued event and returns it
    Given a watcher attached to the engine with a queued verify_pr event
    When I invoke watch with for_intent set
    Then the result action is "verify_pr"

  Scenario: watch returns heartbeat noop on empty queue with zero timeout
    Given a watcher attached to the engine with no queued events
    When I invoke watch with for_intent set and timeout=0
    Then the result action is "noop"
    And the instruction is "Working."

  # ── recover — in-flight tracking ─────────────────────────────────────────────

  Scenario: recover errors when the watcher has not been started
    When I invoke recover with session "sess-x" but no watcher started
    Then the result status is "error"
    And the reason mentions "not started"

  Scenario: recover promotes a session into recovery tracking
    Given a watcher attached to the engine with no queued events
    When I invoke recover with session "s-1" owner "netzkontrast" repo "agency" branch "feat-x" base "main"
    Then the result status is "probing"
    And the session is tracked in recovery_in_flight

  Scenario: recover defaults base to main when omitted
    Given a watcher attached to the engine with no queued events
    When I invoke recover with session "s-2" with no base provided
    Then the recovery entry has base "main"

  # ── watcher event classifier — state routing ──────────────────────────────────

  Scenario: COMPLETED with unapproved plan routes to review_and_approve_plan
    When I classify a COMPLETED session with unapproved plan and no branch on remote
    Then the classified action is "review_and_approve_plan"

  Scenario: COMPLETED with branch on remote and no unapproved plan routes to verify_pr
    When I classify a COMPLETED session with branch on remote and no unapproved plan
    Then the classified action is "verify_pr"

  Scenario: COMPLETED with patch outputs and no branch routes to recover_silent_fail
    When I classify a COMPLETED session with patch outputs but no branch on remote
    Then the classified action is "recover_silent_fail"

  Scenario: COMPLETED with no patch and no plan routes to dispatch_fresh
    When I classify a COMPLETED session with no outputs and no plan
    Then the classified action is "dispatch_fresh"

  Scenario: IN_PROGRESS to AWAITING_PLAN_APPROVAL routes to review_and_approve_plan
    When I classify a session transitioning to "AWAITING_PLAN_APPROVAL"
    Then the classified action is "review_and_approve_plan"

  Scenario: IN_PROGRESS to PAUSED routes to inspect_and_resume
    When I classify a session transitioning to "PAUSED"
    Then the classified action is "inspect_and_resume"

  Scenario: IN_PROGRESS to CANCELLED routes to terminal
    When I classify a session transitioning to "CANCELLED"
    Then the classified action is "terminal"

  # ── INSTRUCTIONS templates — observable tool-name contracts ──────────────────

  Scenario: recover_silent_fail instruction names the canonical publish pair
    Then the recover_silent_fail instruction names "pre_commit_instructions"
    And the recover_silent_fail instruction names "submit"

  Scenario: verify_pr instruction references git ls-remote
    Then the verify_pr instruction references "git ls-remote"

  Scenario: review_and_approve_plan instruction names jules verbs
    Then the review_and_approve_plan instruction names "jules.plan"
    And the review_and_approve_plan instruction names "jules.approve_plan"

  Scenario: dispatch_fresh instruction names all canonical Jules tools
    Then the dispatch_fresh instruction names "submit"
    And the dispatch_fresh instruction names "pre_commit_instructions"
    And the dispatch_fresh instruction names "request_user_input"
    And the dispatch_fresh instruction names "replace_with_git_merge_diff"
    And the dispatch_fresh instruction names "request_code_review"

  Scenario: every INSTRUCTIONS template fits within the token budget
    Then every INSTRUCTIONS template is under 480 characters

  # ── skill registration ────────────────────────────────────────────────────────

  Scenario: jules-protocol-preamble is registered on the jules ontology
    Given a fresh agency engine in code-mode
    Then the skill "jules-protocol-preamble" is registered on the jules ontology

  Scenario: jules-protocol-preamble has five phases
    Given a fresh agency engine in code-mode
    Then the skill "jules-protocol-preamble" has exactly 5 phases in order

  Scenario: jules-tool-discipline is registered and has one phase
    Given a fresh agency engine in code-mode
    Then the skill "jules-tool-discipline" is registered on the jules ontology
    And the skill "jules-tool-discipline" has exactly 1 phase

  Scenario: jules-recovery-when-stuck is registered and has four phases
    Given a fresh agency engine in code-mode
    Then the skill "jules-recovery-when-stuck" is registered on the jules ontology
    And the skill "jules-recovery-when-stuck" has exactly 4 phases in order

  Scenario: jules-pr-review-cycle is registered and has three phases
    Given a fresh agency engine in code-mode
    Then the skill "jules-pr-review-cycle" is registered on the jules ontology
    And the skill "jules-pr-review-cycle" has exactly 3 phases

  Scenario: jules-fanout is registered and has three phases
    Given a fresh agency engine in code-mode
    Then the skill "jules-fanout" is registered on the jules ontology
    And the skill "jules-fanout" has exactly 3 phases

  Scenario: jules-self-improvement is registered and has two phases
    Given a fresh agency engine in code-mode
    Then the skill "jules-self-improvement" is registered on the jules ontology
    And the skill "jules-self-improvement" has exactly 2 phases

  # ── skill walk — hard gate + provenance ──────────────────────────────────────

  Scenario: jules-tool-discipline walk completes on a canonical prompt
    When I walk "jules-tool-discipline" with a canonical prompt
    Then the walk status is "completed"

  Scenario: jules-tool-discipline walk completes even when tools are missing
    When I walk "jules-tool-discipline" with a bad prompt
    Then the walk status is "completed"

  Scenario: jules-tool-discipline walk records a Phase node
    When I walk "jules-tool-discipline" with a canonical prompt
    Then a Phase node is recorded for the skill "jules-tool-discipline"

  Scenario: jules-recovery-when-stuck walk hard-gates at recovered
    Given a stub Jules backend for skill walk
    When I walk "jules-recovery-when-stuck" through all phases
    Then the walk pauses at "recovered" with status "input-required"
    And confirming completes the walk

  Scenario: jules-recovery-when-stuck walk records provenance for all phases
    Given a stub Jules backend for skill walk
    When I walk "jules-recovery-when-stuck" through all phases and confirm
    Then 4 Phase nodes are recorded for the skill "jules-recovery-when-stuck"

  Scenario: jules-pr-review-cycle walk completes when all phases supply outputs
    When I walk "jules-pr-review-cycle" through all phases
    Then the walk status is "completed"

  Scenario: jules-pr-review-cycle draft-replies phase appends handshake tail
    When I invoke review_comment with body "Verdict: changes-requested. Fix the test."
    Then the result carries tail_appended=True
    And the text contains "reply_to_pr_comments"

  Scenario: jules-fanout walk fan-out phase spawns delegations then hard-gates
    Given a stub Jules backend for fanout
    When I walk "jules-fanout" through plan and fan-out phases
    Then the walk pauses at "join" with status "input-required"
    And a Delegation node is recorded serving the intent

  Scenario: jules-fanout confirming join completes the walk
    Given a stub Jules backend for fanout
    When I walk "jules-fanout" through all phases and confirm join
    Then the walk status is "completed"
