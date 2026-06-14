Feature: Novel capability — observable behaviour
  The novel capability drives book authoring from premise to publication.
  Every scenario asserts what the system DOES (returned values, graph state,
  provenance edges, gate verdicts, error codes) — never private methods,
  internal data shapes, or frozen counts.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ──────────────────────────────── MVN: create_novel ─────────────────────────

  Scenario: create_novel records a Novel node with concept status and serves the intent
    When I create a novel titled "Modem Daze" by "The Phreakers"
    Then the result contains a novel_id starting with "novel:"
    And the novel status is "concept"
    And a SERVES edge links the Novel to the intent

  # ──────────────────────────────── MVN: create_chapter ────────────────────────

  Scenario: create_chapter records a Chapter and links it to the novel
    Given a novel titled "Modem Daze" by "The Phreakers"
    When I create chapter 1 titled "Opening" for that novel
    Then the result contains a chapter_id starting with "chapter:"
    And the chapter status is "outlined"
    And a CHAPTER_OF edge links the chapter to the novel

  Scenario: create_chapter for an unknown novel returns a NOT_FOUND error
    When I create a chapter for novel_id "novel:does-not-exist"
    Then the result is None
    And the invocation error contains "NOT_FOUND"

  # ──────────────────────────────── MVN: chapter_report ────────────────────────

  Scenario: chapter_report aggregates chapter count and total word count
    Given a novel with chapters of 100 words and 200 words
    When I call chapter_report for that novel
    Then chapter_count is 2
    And word_count_total is at least 300
    And by_status shows 2 outlined chapters

  # ──────────────────────────────── MVN: render_manuscript ────────────────────

  Scenario: render_manuscript concatenates chapters in number order
    Given a novel titled "My Novel" by "An Author"
    And chapter 2 titled "Second" with body "second body"
    And chapter 1 titled "First" with body "first body"
    When I call render_manuscript
    Then the artefact kind is "manuscript"
    And the manuscript body contains the novel title and author
    And "First" appears before "Second" in the manuscript
    And "first body" appears before "second body" in the manuscript

  # ──────────────────────────────── conceptualize ──────────────────────────────

  Scenario: conceptualize produces a novel-concept artefact
    When I call conceptualize with title "Modem Daze" premise "A phreaker tale"
    Then the result artefact kind is "novel-concept"
    And the result text contains "Modem Daze"

  # ──────────────────────────────── lifecycle: ideas ───────────────────────────

  Scenario: capture_idea records an Idea with status new and serves the intent
    When I capture an idea with text "A novel about time-loops"
    Then the result contains an idea_id starting with "idea:"
    And the idea status is "new"
    And a SERVES edge links the Idea to the intent

  Scenario: list_ideas returns all ideas and filters by status
    Given three ideas have been captured
    When I list all ideas
    Then the idea count is 3
    When I list ideas with status "new"
    Then the idea count is 3
    When I list ideas with status "promoted"
    Then the idea count is 0

  Scenario: list_ideas rejects an invalid status with INVALID_ARGUMENT
    When I list ideas with status "bogus"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: promote_idea creates a Novel and records PROMOTED_TO edge
    Given a captured idea
    When I promote the idea to a novel titled "The Promoted Novel" by "An Author"
    Then the result contains a novel_id
    And the idea status becomes "promoted"
    And a PROMOTED_TO edge links the idea to the novel

  Scenario: promote_idea for an unknown idea returns a NOT_FOUND error
    When I promote idea_id "idea:does-not-exist" to a novel
    Then the result is None
    And the invocation error contains "NOT_FOUND"

  # ──────────────────────────────── find_novel ─────────────────────────────────

  Scenario: find_novel returns novels matching a substring query
    Given novels titled "The Great Modem" and "Quantum Dawn" and "Modem Mysteries"
    When I call find_novel with query "modem"
    Then the count is 2
    And the returned titles are "The Great Modem" and "Modem Mysteries"

  Scenario: find_novel with empty query returns all novels
    Given novels titled "The Great Modem" and "Quantum Dawn" and "Modem Mysteries"
    When I call find_novel with query ""
    Then the count is 3

  # ──────────────────────────────── set_novel_status ───────────────────────────

  Scenario: set_novel_status flips the status and persists it
    Given a novel titled "X" by "Y"
    When I set the novel status to "drafting"
    Then the returned status is "drafting"
    And the graph node status is "drafting"

  Scenario: set_novel_status rejects an invalid status with INVALID_ARGUMENT
    Given a novel titled "X" by "Y"
    When I set the novel status to "not-a-real-status"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: set_novel_status for an unknown novel returns NOT_FOUND
    When I set status "drafting" on novel_id "novel:nope"
    Then the result is None
    And the invocation error contains "NOT_FOUND"

  # ──────────────────────────────── lifecycle slice 2 ──────────────────────────

  Scenario: list_chapters returns chapters ordered by number
    Given a novel with chapters added in reverse order 3 2 1
    When I call list_chapters
    Then the chapter numbers are in ascending order 1 2 3

  Scenario: list_chapters on a novel with no chapters returns an empty list
    Given a novel titled "Empty" by "Author"
    When I call list_chapters
    Then chapter_count is 0 and chapters is an empty list

  Scenario: create_scene records a Scene node and a SCENE_OF edge to the chapter
    Given a novel with a chapter
    When I create a scene with slug "cold-open" and pov "third-limited"
    Then the result contains a scene_id starting with "scene:"
    And the scene pov is "third-limited"
    And a SCENE_OF edge links the scene to the chapter

  Scenario: create_scene rejects a pov with no POV signal with INVALID_ARGUMENT
    Given a novel with a chapter
    When I create a scene with pov "qwerty gibberish nonsense"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: create_scene projects a rich pov onto the canonical enum
    Given a novel with a chapter
    When I create a scene with a rich pov "omniscient-but-spelt-wrong"
    Then the scene pov is the canonical "third-omniscient"
    And the scene pov_detail preserves "omniscient-but-spelt-wrong"

  Scenario: set_chapter_status flips the chapter status and persists it
    Given a novel with a chapter
    When I set the chapter status to "drafted"
    Then the chapter node status is "drafted"

  Scenario: set_chapter_status rejects an invalid status with INVALID_ARGUMENT
    Given a novel with a chapter
    When I set the chapter status to "bogus"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: rename_novel updates the title in the graph
    Given a novel titled "Original Title" by "Author"
    When I rename the novel to "Renamed Title"
    Then the returned title is "Renamed Title"
    And the graph node title is "Renamed Title"

  Scenario: novel_progress aggregates word count and chapter status breakdown
    Given a novel with one 50-word chapter drafted and one 100-word chapter outlined
    When I call novel_progress
    Then word_count_total is at least 150
    And by_status shows 1 drafted and 1 outlined

  Scenario: resume_session returns the most recently created novel
    Given two novels have been created, the second titled "Last"
    When I call resume_session
    Then the returned novel_id matches the second novel
    And the returned title is "Last"

  Scenario: resume_session with no novels returns empty id and title
    When I call resume_session on a fresh engine with no novels
    Then the novel_id is "" and the title is ""

  # ──────────────────────────────── prose verbs (driver-free) ──────────────────

  Scenario: count_words returns word count and char count for simple prose
    When I call count_words with body "The quick brown fox jumps over the lazy dog."
    Then word_count is 9
    And char_count is 44

  Scenario: count_words on empty body returns zeros
    When I call count_words with body ""
    Then word_count is 0 and char_count is 0

  Scenario: analyze_readability returns a Flesch score for simple prose
    When I call analyze_readability with simple short-sentence prose
    Then the result contains a flesch score above 80
    And the sentence count is 4

  Scenario: analyze_readability on empty body returns INVALID_ARGUMENT
    When I call analyze_readability with body ""
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: check_filter_words detects high-density filter words
    When I call check_filter_words with filter-heavy prose
    Then the filter_count is at least 5
    And the density is above 0.1
    And the offenders include "really" "just" "very" "somehow" "actually"
    And the passed flag is False

  Scenario: check_filter_words passes on clean prose
    When I call check_filter_words with clean prose
    Then the filter_count is 0 and passed is True

  Scenario: scan_proper_nouns returns sorted unique proper nouns
    When I call scan_proper_nouns with body "Alice met Bob at the diner. Then Charlie arrived. Alice waved."
    Then proper_nouns is ["Alice", "Bob", "Charlie"]

  Scenario: scan_proper_nouns skips sentence-initial capitals
    When I call scan_proper_nouns with body "The morning was clear. She walked to the park. Then George arrived."
    Then proper_nouns contains only "George"

  Scenario: check_dialogue_attribution passes on plain said/asked attributions
    When I call check_dialogue_attribution with plain attribution prose
    Then the result passed is True and flowery_count is 0

  Scenario: check_dialogue_attribution flags flowery attributions
    When I call check_dialogue_attribution with flowery attribution prose
    Then the result passed is False
    And flowery_count is 3
    And flowery_hits contains "exclaimed"

  Scenario: check_show_dont_tell passes on action prose
    When I call check_show_dont_tell with action prose
    Then the result passed is True and tell_count is 0

  Scenario: check_show_dont_tell flags interior-monologue tells
    When I call check_show_dont_tell with telling-verb prose
    Then the result passed is False
    And tell_count is at least 4
    And tells contains "felt"

  Scenario: check_content_warnings returns no warnings for neutral prose
    When I call check_content_warnings with neutral prose
    Then warnings is an empty list

  Scenario: check_content_warnings detects violence and substance categories
    When I call check_content_warnings with violent substance prose
    Then warnings includes "violence"
    And warnings includes "substance"

  # ──────────────────────────────── manuscript verbs ───────────────────────────

  Scenario: render_blurb produces a blurb artefact containing hook and stakes
    Given a novel titled "Modem Daze" by "The Phreakers"
    When I call render_blurb with hook "A phreaker discovers a secret BBS" and stakes "The sysop is watching"
    Then the artefact kind is "blurb"
    And the result contains "Modem Daze"
    And the result contains "phreaker"
    And the result contains "sysop"

  Scenario: render_blurb for an unknown novel returns NOT_FOUND
    When I call render_blurb on novel_id "novel:nope"
    Then the result is None
    And the invocation error contains "NOT_FOUND"

  Scenario: render_query_letter produces a query-letter artefact
    Given a novel titled "Modem Daze" by "The Phreakers"
    When I call render_query_letter with agent "Jane Smith" and comp_titles "Neuromancer, Snow Crash"
    Then the artefact kind is "query-letter"
    And the result contains "Jane Smith" and "Modem Daze" and "The Phreakers"

  Scenario: render_synopsis aggregates chapter titles in order
    Given a novel with chapters "Connection" "Discovery" "Confrontation"
    When I call render_synopsis
    Then the artefact kind is "synopsis"
    And "Connection" appears before "Discovery" before "Confrontation" in the synopsis

  # ──────────────────────────────── research verbs ─────────────────────────────

  Scenario: capture_claim records a NovelClaim node serving the intent
    When I capture a claim with text "BBS peaked at 60K nodes" domain "historical"
    Then the result contains a claim_id starting with "novelclaim:"
    And the claim domain is "historical"
    And the claim verified status is "pending"
    And a SERVES edge links the claim to the intent

  Scenario: capture_claim rejects an invalid domain with INVALID_ARGUMENT
    When I capture a claim with invalid domain "not-a-domain"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: list_claims filters by verified status
    Given three claims have been captured
    When I list all claims
    Then the claim count is 3
    When I list claims with verified "pending"
    Then the claim count is 3
    When I list claims with verified "confirmed"
    Then the claim count is 0

  Scenario: list_claims rejects invalid verified value with INVALID_ARGUMENT
    When I list claims with verified "bogus"
    Then the result is None
    And the invocation error contains "INVALID_ARGUMENT"

  Scenario: pending_verifications aggregates pending claims by domain
    Given claims captured for domains "historical" and "scientific"
    When I call pending_verifications
    Then the total pending count is 2
    And the by_domain breakdown shows 1 for "historical" and 1 for "scientific"

  # ──────────────────────────────── storyform checks ───────────────────────────

  Scenario: check_throughline_partition passes the good_work fixture
    When I call check_throughline_partition with the good_work fixture
    Then the check result passed is True and violations is empty

  Scenario: check_throughline_partition fails the broken_throughline_partition fixture
    When I call check_throughline_partition with the broken_work_throughline_partition fixture
    Then the check result passed is False and violations is non-empty

  Scenario: check_slot_fill passes the good_work fixture
    When I call check_slot_fill with the good_work fixture
    Then the check result passed is True and violations is empty

  Scenario: check_slot_fill fails the broken_slot_fill fixture
    When I call check_slot_fill with the broken_work_slot_fill fixture
    Then the check result passed is False and violations is non-empty

  Scenario: check_storybeat_moment_refs passes the good_work fixture
    When I call check_storybeat_moment_refs with the good_work fixture
    Then the check result passed is True

  Scenario: check_storybeat_moment_refs fails the broken fixture
    When I call check_storybeat_moment_refs with the broken_work_storybeat_moment_refs fixture
    Then the check result passed is False and violations is non-empty

  Scenario: novel_coherence_check passes the good_work fixture
    When I call novel_coherence_check with the good_work fixture
    Then the composite result passed is True and violations is empty

  Scenario: novel_coherence_check fails each broken fixture at exactly its named check
    When I call novel_coherence_check with the broken_work_throughline_partition fixture
    Then the composite fails and "throughline_partition" is in the failed checks

  Scenario: novel_coherence_check approach_concern emits warnings not violations
    When I call novel_coherence_check with the broken_work_approach_concern fixture
    Then the composite warnings include "approach_concern"

  Scenario: validate_appreciations passes the good_work fixture
    When I call validate_appreciations with the good_work fixture
    Then the check result passed is True

  Scenario: validate_appreciations flags an invalid appreciation value
    When I call validate_appreciations with an NCP containing appreciation "NOT-A-REAL-APPRECIATION"
    Then the check result passed is False
    And the violations include the value "NOT-A-REAL-APPRECIATION"

  Scenario: validate_narrative_functions passes the good_work fixture
    When I call validate_narrative_functions with the good_work fixture
    Then the check result passed is True

  Scenario: validate_narrative_functions flags an invalid narrative_function value
    When I call validate_narrative_functions with an NCP containing narrative_function "BOGUS-FUNCTION-NAME"
    Then the check result passed is False
    And the violations include the value "BOGUS-FUNCTION-NAME"

  # ──────────────────────────────── worldbuilding ──────────────────────────────

  Scenario: create_world records a World node with the given slug and name
    When I create a world with slug "midgard" and name "Midgard"
    Then the result contains a world_id
    And the world slug is "midgard" and name is "Midgard"

  Scenario: world children link via PART_OF_WORLD
    Given a world "midgard"
    When I create culture "vikings" religion "asatru" language "old-norse" magic "seidr" under that world
    Then all four children return their id keys
    And four PART_OF_WORLD edges link to the world

  Scenario: create_culture for an unknown world returns None
    When I create a culture under world_id "world:does-not-exist"
    Then the result is None

  Scenario: create_world_axiom records axiom with hard severity
    Given a world "midgard"
    When I create a hard axiom "The dead never return."
    Then the result contains an axiom_id
    And the axiom severity is "hard"

  Scenario: create_world_axiom rejects unknown severity
    Given a world "midgard"
    When I create an axiom with severity "medium"
    Then the result is None

  Scenario: list_world groups children by label
    Given a world "midgard" with 2 cultures 1 religion 1 axiom
    When I call list_world
    Then cultures count is 2 and religions count is 1 and axioms count is 1

  Scenario: find_axiom_contradictions flags a negation pair
    Given a world with two contradicting axioms about the dead returning
    When I call find_axiom_contradictions
    Then passed is False
    And the contradiction pair is in the results

  Scenario: find_axiom_contradictions passes on independent axioms
    Given a world with two independent axioms
    When I call find_axiom_contradictions
    Then passed is True and contradictions is empty

  Scenario: link_character_to_world rejects an unknown edge kind
    Given a world with a religion
    When I link a character to the religion with edge_kind "SHOPS_AT"
    Then the result is None

  Scenario: link_character_to_world records a typed edge
    Given a world with a religion
    When I link a character to the religion with edge_kind "WORSHIPS"
    Then the returned edge_kind is "WORSHIPS"
    And a WORSHIPS edge exists between character and religion in the graph

  # ──────────────────────────────── codex ──────────────────────────────────────

  Scenario: create_codex_entry records a node and links to the novel
    Given a novel for codex tests
    When I create a codex entry slug "iron-mask" kind "artefact"
    Then the result contains an entry_id
    And a CODEX_OF edge links the entry to the novel

  Scenario: create_codex_entry rejects an unknown kind
    Given a novel for codex tests
    When I create a codex entry with kind "hyperbole"
    Then the result is None

  Scenario: list_codex_entries returns all entries
    Given a novel with codex entries "a" location and "b" artefact
    When I list all codex entries
    Then the entry slugs include "a" and "b"

  Scenario: list_codex_entries filters by kind
    Given a novel with codex entries "a" location and "b" artefact
    When I list codex entries with kind "location"
    Then the entry slugs include only "a"

  Scenario: match_codex_entries finds entries by trigger word
    Given a codex entry with triggers "Iron Mask, the mask"
    When I call match_codex_entries with text "She lifted the mask"
    Then the matches include slug "iron-mask"

  Scenario: match_codex_entries is case-insensitive
    Given a codex entry "raven" with trigger "Raven"
    When I call match_codex_entries with text "raven appeared in the rafters."
    Then the matches include slug "raven"

  Scenario: match_codex_entries returns empty list when no trigger fires
    Given a codex entry with trigger "X"
    When I call match_codex_entries with text "nothing relevant here."
    Then the matches list is empty

  Scenario: match_codex_entries skips archived entries
    Given a codex entry "cult" that has been archived
    When I call match_codex_entries with text "The cult gathered at dusk."
    Then the matches list is empty

  Scenario: update_codex_entry changes the body
    Given a codex entry with body "old body"
    When I update the codex entry body to "new body"
    Then the node body is "new body"

  Scenario: archive_codex_entry flags the entry as archived
    Given a codex entry
    When I archive the codex entry
    Then the node archived property is "yes"

  # ──────────────────────────────── character knowledge ────────────────────────

  Scenario: record_character_learns mints KNOWS and LEARNED_IN edges
    Given a mini-novel with scenes
    When I record that the character learned "The captain is bribed." in scene 2
    Then a KNOWS edge links the character to the KnownFact
    And a LEARNED_IN edge links the KnownFact to the scene

  Scenario: record_character_learns returns NOT_FOUND for an unknown scene
    Given a mini-novel with scenes
    When I record a fact for scene_id "scene:does-not-exist"
    Then the result is None

  Scenario: what_does_X_know_as_of returns facts learned at or before the scene
    Given a character with facts learned in scene 1 and scene 2
    When I call what_does_X_know_as_of as of scene 2
    Then "Fact A" and "Fact B" are in the facts list

  Scenario: what_does_X_know_as_of excludes facts learned after the scene
    Given a character with fact A learned in scene 1 and Future Fact learned in scene 3
    When I call what_does_X_know_as_of as of scene 2
    Then "Fact A" is in the facts list
    And "Future Fact" is not in the facts list

  Scenario: flag_anachronistic_reference passes when character has learned the fact
    Given a character who learned "The captain is bribed." in scene 1
    When I flag_anachronistic_reference for scene 2
    Then anachronism is False

  Scenario: flag_anachronistic_reference fires when fact only learned after the reference scene
    Given a character who learned "The captain is bribed." in scene 3
    When I flag_anachronistic_reference for scene 1
    Then anachronism is True

  Scenario: flag_anachronistic_reference returns no_record for an unrecorded fact
    Given a mini-novel with scenes
    When I check for fact "Never recorded." in scene 1
    Then anachronism is False and no_record is True

  # ──────────────────────────────── story time ─────────────────────────────────

  Scenario: record_story_event creates a StoryTimeEvent node
    Given a novel with scenes
    When I record a story event "King dies" at when_story "Y2391.04"
    Then the result contains an event_id
    And when_story is "Y2391.04"

  Scenario: record_story_event with scene_id creates HAPPENS_AT edge
    Given a novel with scenes
    When I record event "Coronation" anchored to scene 2
    Then a HAPPENS_AT edge links scene 2 to the event

  Scenario: reveal_in_scene adds a REVEALED_IN edge
    Given a story event and scenes
    When I call reveal_in_scene for the event and scene 3
    Then a REVEALED_IN edge links the event to scene 3

  Scenario: list_story_events_up_to includes events at or before the anchor scene
    Given events anchored Birth-A001-scene1 Marriage-A015-scene2 Death-A050-scene3
    When I call list_story_events_up_to for scene 2
    Then "Birth" and "Marriage" are in the events
    And "Death" is not in the events

  Scenario: list_story_events_up_to returns empty when scene has no anchor
    Given a novel with scenes and no anchored events
    When I call list_story_events_up_to for scene 1
    Then events is empty and anchor_when is None

  Scenario: list_reveals_in returns events disclosed in the scene
    Given an event revealed in scene 3
    When I call list_reveals_in for scene 3
    Then reveals contains 1 entry with label "Lost will"

  Scenario: mark_narrative_beat records a NarrativeBeat node
    Given a novel with scenes
    When I call mark_narrative_beat for scene 1 with beat "opening-image"
    Then the result contains a beat_id

  Scenario: mark_narrative_beat with predecessor_id creates a PRECEDES edge
    Given two beats recorded for scenes 1 and 2
    When beat 2 is marked with predecessor_id of beat 1
    Then a PRECEDES edge links beat 1 to beat 2

  Scenario: narrative_order returns beats in topological sort order
    Given three beats chained b1 precedes b2 precedes b3
    When I call narrative_order
    Then b1 appears before b2 and b2 appears before b3 in the returned list

  # ──────────────────────────────── editorial pipeline ─────────────────────────

  Scenario: check_voice_consistency passes when chapter bodies are similar
    When I call check_voice_consistency with three stylistically similar bodies
    Then the result passed is True and outliers is empty

  Scenario: check_voice_consistency flags a stylistic outlier chapter
    When I call check_voice_consistency with three tight bodies and one filter-heavy body
    Then the result passed is False and the outlier index is 3

  Scenario: check_pov_consistency passes on uniform single-scene chapters
    Given a novel with chapters each having one scene of same pov
    When I call check_pov_consistency
    Then the result passed is True

  Scenario: check_continuity passes when all proper nouns are consistent across chapters
    Given a novel whose chapters share the same proper noun "Elara"
    When I call check_continuity
    Then the result passed is True

  Scenario: check_sensitivity returns advisory warnings on sensitive content
    When I call check_sensitivity with a body containing sensitive themes
    Then the result contains a warnings field

  # ──────────────────────────────── gates ──────────────────────────────────────

  Scenario: pre_draft_gate blocks when novel has no chapters, no claims, no storyform
    Given a novel with no prerequisites
    When I call pre_draft_gate
    Then the result is None
    And the invocation error contains "GATE_FAILED"

  Scenario: pre_draft_gate passes when chapter, claim, and storyform are present
    Given a novel with one chapter, one claim, and a storyform node
    When I call pre_draft_gate
    Then the gate passed is True
    And checks shows chapter_outline, research_present, and storyform_present are all True

  Scenario: beta_ready_gate blocks when chapters are not yet drafted
    Given a novel with chapters still outlined
    When I call beta_ready_gate
    Then the result is None
    And the invocation error contains "GATE_FAILED"

  Scenario: beta_ready_gate passes when all chapters are drafted
    Given a novel with all chapters set to drafted
    When I call beta_ready_gate
    Then the gate passed is True
    And all_chapters_drafted is True

  Scenario: query_ready_gate blocks when novel status is not beta or later
    Given a novel still in concept status
    When I call query_ready_gate
    Then the result is None
    And the invocation error contains "GATE_FAILED"

  Scenario: query_ready_gate passes at beta with clean chapter content
    Given a novel at beta status with revised chapters
    When I call query_ready_gate
    Then the gate passed is True
    And status_beta_or_later is present in the checks

  Scenario: publish_ready_gate blocks on a chapter gap in the sequence
    Given a novel with chapters 1 and 3 but not 2 at querying status
    When I call publish_ready_gate
    Then the result is None
    And the invocation error contains "GATE_FAILED"

  Scenario: publish_ready_gate passes with contiguous chapters at querying
    Given a novel with 3 contiguous chapters all final at querying status
    When I call publish_ready_gate
    Then the gate passed is True
    And status_at_querying_or_later is True

  # ──────────────────────────────── E2E provenance ─────────────────────────────

  Scenario: full pipeline leaves a SERVES invocation for every verb fired
    When I run the full novel pipeline from idea to manuscript
    Then every pipeline verb is present in the provenance
    And the manuscript artefact kind is in the provenance
