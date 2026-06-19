Feature: document capability — render, index_repo, explain, and scope guards (Spec 043, Spec 056)
  The document capability renders graph state as markdown (render), produces a
  compact repo briefing (index_repo), and emits structured code explanations
  (explain). Behaviour is observable through returned content, graph state,
  and file system effects.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── document.render — install-artefacts scope ──────────────────────────────

  Scenario: render install-artefacts returns content with the correct H1
    Given two install-artefact Reflection nodes exist
    When I call document.render with scope "install-artefacts"
    Then the content starts with "# Install artefacts"
    And the node_count is 2
    And each artefact name appears as an H2 heading
    And the artefact bodies are fenced in code blocks
    And the token count is positive

  Scenario: render install-artefacts with no nodes returns empty content with the H1
    When I call document.render with scope "install-artefacts"
    Then the content starts with "# Install artefacts"
    And the node_count is 0

  # ── document.render — reflections scope ────────────────────────────────────

  Scenario: render reflections lists nodes newest-first
    Given three technical reflections are recorded in order first, second, third
    When I call document.render with scope "reflections"
    Then the node_count is 3
    And the content heading mentions "Reflections"
    And "third thing" appears before "first thing" in the content

  Scenario: render reflections filtered by intent only shows that intent's nodes
    Given a reflection under this intent and another under a separate intent
    When I call document.render with scope "reflections" filtered to this intent
    Then the content includes the node under this intent
    And the content does not include the node under the other intent

  Scenario: render reflections truncates very long text
    Given a reflection with text 1000 characters long
    When I call document.render with scope "reflections"
    Then the content does not contain 600 consecutive identical characters

  # ── document.render — provenance scope ─────────────────────────────────────

  Scenario: render provenance returns the intent header and required sections
    When I call document.render with scope "provenance" for this intent
    Then the content includes a heading with the intent id
    And the content includes sections "Acceptance", "Invocations", and "Artefacts"

  Scenario: render provenance with no intent id produces a none-placeholder heading
    When I call document.render with scope "provenance" and no intent id
    Then the render content includes "# Intent (none) provenance"

  Scenario: render provenance includes sub-intents under a Sub-intents section
    Given a child intent exists under this intent
    When I call document.render with scope "provenance" for this intent
    Then the content includes a "Sub-intents" section
    And the child intent id appears in the content

  # ── document.render — capability-catalogue scope ───────────────────────────

  Scenario: render capability-catalogue lists known capabilities
    When I call document.render with scope "capability-catalogue"
    Then the content starts with "# Capability catalogue"
    And the catalogue includes entries for "reflect", "delegate", and "document"
    And the content footer mentions capabilities and verbs

  # ── document.render — edge cases ───────────────────────────────────────────

  Scenario: render with an unknown scope returns an error
    When I call document.render with scope "no-such-scope"
    Then the render result carries an error
    And the content is empty

  Scenario: render with an unsupported format returns an error
    When I call document.render with scope "reflections" and format "html"
    Then the render result carries an error

  Scenario: render does not write any graph nodes
    When I call document.render with scope "capability-catalogue"
    Then the Reflection node count is unchanged

  # ── document.render — scope guard: research-report ─────────────────────────

  Scenario: render research-report accepts a Research node id
    Given a Research node exists from a research.lead call
    When I call document.render with scope "research-report" using the Research id
    Then the result does not contain "is not an Intent id"
    And the result does not carry a Research-id error

  Scenario: render research-report rejects an Intent id
    When I call document.render with scope "research-report" using this intent's id
    Then the result carries "not a Research id" in the error

  Scenario: render provenance rejects a non-Intent id
    Given an Artefact node exists
    When I call document.render with scope "provenance" using the Artefact id
    Then the result carries "not an Intent id" in the error

  Scenario: render provenance accepts the intent id
    When I call document.render with scope "provenance" for this intent
    Then the result does not contain "not an Intent id"

  # ── document.index_repo ─────────────────────────────────────────────────────

  Scenario: index_repo briefing fits within the token budget
    When I call document.index_repo on the agency repo with apply False
    Then the briefing token count is at most 3500

  Scenario: index_repo briefing names every top-level capability
    When I call document.index_repo on the agency repo with apply False
    Then the briefing content includes "reflect", "delegate", "analyze", and "document"

  Scenario: index_repo briefing includes the required structural sections
    When I call document.index_repo on the agency repo with apply False
    Then the briefing includes "## Substrate"
    And the briefing includes "## Macro-structure"
    And the briefing includes "## Entry points"
    And the briefing includes "## Notable patterns"

  Scenario: index_repo records a RepoIndex node in the graph
    When I call document.index_repo on the agency repo with apply False
    Then a RepoIndex node is added to the graph
    And the RepoIndex node carries the path, token_count, and a content_sha of 16 characters

  Scenario: index_repo with apply False does not write a file
    When I call document.index_repo on a temp directory with apply False
    Then no PROJECT_INDEX.md file is written

  Scenario: index_repo with apply True writes the briefing file
    Given a minimal project directory with a pyproject.toml and a Python module
    When I call document.index_repo on that directory with apply True
    Then a PROJECT_INDEX.md file is written
    And the file content matches the returned content

  Scenario: index_repo respects max_tokens truncation
    When I call document.index_repo on the agency repo with max_tokens 500
    Then the briefing token count is at most 600
    And the content signals truncation

  # Mandatory rule: a SAVED project index never deletes content to fit a budget.
  Scenario: saving the index never omits content to fit a token budget
    Given a project directory with several modules and a pyproject.toml
    When I call document.index_repo on that directory with apply True and max_tokens 20
    Then a PROJECT_INDEX.md file is written
    And the written index omits no content
    And the written index lists every seeded module

  Scenario: index_repo reports files_scanned greater than zero
    When I call document.index_repo on the agency repo with apply False
    Then the files_scanned count is positive

  # ── document.explain ────────────────────────────────────────────────────────

  Scenario: explain a module returns content mentioning the module
    When I call document.explain for target "agency.capabilities.reflect"
    Then the content mentions "reflect"
    And the result carries a reflection_id

  Scenario: explain a symbol returns content mentioning the symbol
    When I call document.explain for target "agency.capabilities.reflect.ReflectCapability"
    Then the content mentions "ReflectCapability"

  Scenario: explain a file path returns content mentioning the file and its functions
    Given a fixture Python file with a function named "greet"
    When I call document.explain for that file path
    Then the content mentions "fixture.py"
    And the content mentions "greet"

  Scenario: explain an unknown target returns an error
    When I call document.explain for target "no.such.module.xyz"
    Then the explain result carries an error

  Scenario: explain at depth brief stays under 220 tokens
    When I call document.explain for target "agency.capabilities.reflect" at depth "brief"
    Then the explain token count is at most 220

  Scenario: explain at depth standard stays under 700 tokens
    When I call document.explain for target "agency.capabilities.reflect" at depth "standard"
    Then the explain token count is at most 700

  Scenario: explain at depth deep stays under 2700 tokens
    When I call document.explain for target "agency.capabilities.reflect" at depth "deep"
    Then the explain token count is at most 2700

  Scenario: explain at an invalid depth falls back to standard budget
    When I call document.explain for target "agency.capabilities.reflect" at depth "enormous"
    Then the explain token count is at most 700

  Scenario: explain records a Reflection node with kind "explanation"
    When I call document.explain for target "agency.capabilities.reflect"
    Then a new Reflection node is added to the graph
    And that Reflection node has kind "explanation"
    And that Reflection node targets "agency.capabilities.reflect"

  # ── graph↔markdown interconnect — ingest, sync, revisions (Spec 290) ─────────

  Scenario: ingesting an un-anchored markdown file mints a Document and stamps the anchor
    Given an un-anchored markdown file "note.md" with body "# Title\nSome body."
    When I call document.ingest on that file
    Then the ingest action is "created"
    And the ingest result carries a document_id
    And the file now begins with an agency-node anchor for that document_id
    And a DocRevision with source "file" is linked to the Document

  Scenario: re-ingesting an unchanged file is idempotent
    Given an un-anchored markdown file "stable.md" with body "unchanged content"
    When I call document.ingest on that file
    And I call document.ingest on that file again
    Then the second ingest action is "unchanged"
    And the Document has exactly one revision

  Scenario: ingesting a changed file keeps both versions bi-temporally
    Given a Document seeded with a graph-authored revision and an anchored file
    When I call document.ingest on that anchored file
    Then the ingest action is "revised"
    And the Document has exactly two revisions
    And the latest revision has source "file"
    And the earliest revision has source "graph"

  Scenario: every ingested file is audited as a prompt
    Given an un-anchored markdown file "prompt.md" with body "Write a haiku about the sea."
    When I call document.ingest on that file
    Then the ingest result carries a clarity_score
    And the latest revision carries that clarity_score

  Scenario: sync ingests every changed markdown file under a directory
    Given a directory with two un-anchored markdown files
    When I call document.sync on that directory
    Then the sync result reports two ingested files
    And a second sync on that directory reports zero ingested files

  Scenario: a session renders as a Document gathering the four concepts
    When I render the current session as a Document
    Then the session document covers Intent, Capability, Lifecycle, and Memory
    And the session result carries a document_id
    And the session Document has a graph-authored revision

  Scenario: a session is archived into the dedicated past-sessions directory
    When I render the current session as a Document
    Then the session is written under a "sessions" directory
    And the archived session file carries the document anchor

  # ── C3: convergence proof + schema-conformance gate (Spec 292) ──────────────

  Scenario: ingesting against a bound schema fails when required fields are missing
    Given an un-anchored markdown file "nofm.md" with body "no frontmatter here"
    When I call document.ingest on that file bound to schema "repo-index"
    Then the ingest result carries an error naming the missing fields

  Scenario: ingesting against a bound schema passes when frontmatter satisfies it
    Given a markdown file "withfm.md" whose frontmatter satisfies schema "repo-index"
    When I call document.ingest on that file bound to schema "repo-index"
    Then the ingest action is "created"
    And the Document conforms to schema "repo-index"

  Scenario: the convergence audit flags a Document carrying no convergence facets
    Given a bare Document node with no revisions
    When I audit that Document's convergence
    Then the convergence audit marks it a defect

  Scenario: an ingested file is not a convergence defect
    Given an un-anchored markdown file "conv.md" with body "Summarise the quarter."
    When I call document.ingest on that file
    When I audit the ingested Document's convergence
    Then the convergence audit does not mark it a defect
    And the convergence audit reports a clarity facet

  # ── C4: a session Document reopens and reconstructs the four concepts ────────

  Scenario: reopening an archived session reconstructs the four concepts
    Given a session has been archived to disk
    When I reopen that archived session file
    Then the reopened session restores the Document into the graph
    And the reopened session reconstructs Intent, Capability, Lifecycle, and Memory

  # ── render→file mirror closes the bi-directional loop (Spec 292) ────────────

  Scenario: mirror event-sources the graph→file direction
    Given three technical reflections are recorded in order first, second, third
    When I mirror the "reflections" scope to a file
    Then the mirror action is "created"
    And the mirrored file begins with an agency-node anchor
    And the mirrored Document has a graph-authored revision

  Scenario: a mirrored file edited on disk keeps both directions bi-temporally
    Given three technical reflections are recorded in order first, second, third
    When I mirror the "reflections" scope to a file
    And a human edits that mirrored file and I ingest it
    Then the Document has both a graph-authored and a file-authored revision
