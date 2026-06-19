Feature: Music capability — observable behaviour across all clusters
  The music capability exposes a wire surface for album lifecycle, lyrics
  analysis, catalogue management, promo, research, and gate verdicts.
  All scenarios use fake drivers so no binaries or network are required.

  Background:
    Given a music engine with fake drivers
    And a confirmed music intent

  # ───────────────────────────── Lifecycle cluster (094) ─────────────────────

  Scenario: capture_idea returns a new idea node
    When I capture the idea "A documentary about modems"
    Then the result carries an idea_id
    And the idea status is "new"
    And the idea text matches the input

  Scenario: promote_idea creates an album and records a PROMOTED_TO edge
    Given an idea "The phreaker tale" has been captured
    When I promote that idea with artist "Phreak" and title "The Phreaker Tale"
    Then the result status is "promoted"
    And an album_slug is returned
    And the idea status in the graph is "promoted"
    And a PROMOTED_TO edge links the idea to the album

  Scenario: promote_idea on a ghost id returns NOT_FOUND
    When I promote a non-existent idea id
    Then the invocation outcome is "failed"
    And the error contains "not_found"

  Scenario: list_ideas filters by status
    Given ideas "alpha" and "beta" have been captured
    And "alpha" has been promoted
    When I list all ideas
    Then the count is 2
    When I list ideas with status "new"
    Then the count is 1
    When I list ideas with status "promoted"
    Then the count is 1

  Scenario: create_album returns an album_slug and seeds an artist page
    When I create album "Origin" by artist "Studio One" in genre "ambient"
    Then the album_slug is "origin"
    And artist_seeded is True
    And the album node has type "thematic"

  Scenario: create_album with unknown type returns INVALID_ARGUMENT
    When I create album "Bad" by artist "A" in genre "g" with type "polka"
    Then the invocation outcome is "failed"
    And the error contains "invalid_argument"

  Scenario: find_album returns exact and fuzzy matches
    Given albums "Origin" and "Echoes" exist for artist "A"
    When I search for album "origin"
    Then exactly 1 album is found
    And the first album slug is "origin"
    When I search for album "echo"
    Then exactly 1 album is found

  Scenario: create_track returns a slug and a RECORDED_FOR edge lands
    Given album "Loop" by artist "A" exists
    When I create track "Intro" number 1 on album "loop"
    And I create track "Beat" number 2 on album "loop"
    Then the track slugs begin with the track number prefix
    And 2 RECORDED_FOR edges link tracks to the album

  Scenario: list_tracks and set_track_status round-trip
    Given album "Loop" by artist "A" exists
    And 2 tracks exist on album "loop"
    When I set the first track status to "mastered"
    And I list tracks for album "loop"
    Then at least one track has status "mastered"

  Scenario: set_track_status with invalid status returns INVALID_ARGUMENT
    Given album "Loop" by artist "A" exists
    And 1 track exists on album "loop"
    When I set that track status to "bogus"
    Then the invocation outcome is "failed"
    And the error contains "invalid_argument"

  Scenario: album_progress reports completion percentage
    Given album "Long Player" by artist "A" exists
    And 2 tracks exist on album "long-player"
    And the first track has status "mastered"
    When I request album progress for "long-player"
    Then track_count is 2
    And tracks_completed is 1
    And completion_percentage is 50

  Scenario: rename_album moves state and tracks remain accessible
    Given album "Old Name" by artist "A" exists with 1 track
    When I rename album "old-name" to "new-name"
    Then the rename succeeds
    And the track is still listed under "new-name"

  Scenario: rename_album on unknown slug returns NOT_FOUND
    When I rename album "ghost" to "phantom"
    Then the invocation outcome is "failed"
    And the error contains "NOT_FOUND"

  Scenario: set_album_status with invalid status returns INVALID_ARGUMENT
    When I set album "X" status to "bogus"
    Then the invocation outcome is "failed"
    And the error contains "invalid_argument"

  Scenario: conceptualize returns an album-concept artefact
    When I conceptualize album "Nightfall" by "Artist" of type "narrative"
    Then the result contains a rendered concept
    And an album-concept artefact is recorded against the intent

  Scenario: resume_session returns stored session state
    Given session state is set to last_album "origin" last_phase "drafting"
    When I call resume_session
    Then session last_album is "origin"
    And session last_phase is "drafting"

  # ───────────────────────────── Lyrics cluster (095) ─────────────────────────

  Scenario: analyze_rhyme_scheme returns scheme and group count
    When I analyze the rhyme scheme of "The cat sat\nOn the mat\nThe dog ran"
    Then the result contains a "scheme"
    And groups is at least 1

  Scenario: analyze_readability returns grade level
    When I analyze readability of multi-verse lyrics
    Then the result contains a "grade_level"
    And avg_words_per_sentence is positive

  Scenario: check_pronunciation flags non-standard words
    When I check pronunciation of "The phreaker dialed a modem at night"
    Then at least 1 finding is returned
    And "phreaker" appears in the flagged words

  Scenario: check_homographs flags ambiguous words
    When I check homographs of "She read the lead carefully"
    Then the flagged words include "lead" or "read"

  Scenario: check_explicit_content classifies clean lyrics as clean
    When I check explicit content of "Sunshine and good vibes"
    Then the rating is "clean"

  Scenario: check_explicit_content classifies profanity as explicit
    When I check explicit content of "What the fuck is happening"
    Then the rating is "explicit"

  Scenario: check_cross_track_repetition flags a repeated line
    When I check cross-track repetition of two tracks sharing a line
    Then repeated_lines is at least 1

  Scenario: extract_section returns the named block body
    When I extract section "Chorus" from the test lyrics block
    Then the body contains "stronger than the tide"

  Scenario: validate_section_structure rejects lowercase section tags
    When I validate section structure of a lowercase-tagged lyric block
    Then ok is False
    And a finding has issue "title-case required"

  Scenario: scan_artist_names flags blocklisted names
    When I scan artist names in "Like Drake said, the city's mine"
    Then at least 1 hit is returned
    And "drake" appears in the hit names

  Scenario: check_voice_tells flags cliche escalation
    When I check voice tells for escalating cliche lyrics
    Then "cliche_escalation" appears in the finding heuristics

  Scenario: prosody_gate fails when rhyme groups are too few
    When I run prosody_gate on lyrics with an all-A rhyme scheme
    Then the gate fails
    And the lifecycle state is "input-required"

  Scenario: pronunciation_gate passes on clean lyrics
    When I run pronunciation_gate on "Sunshine warms the morning fields\nBirds wheel above the bay"
    Then passed is True

  Scenario: explicit_gate blocks explicit lyrics by default
    When I run explicit_gate on "we yelled fuck and ran"
    Then the gate fails

  Scenario: explicit_gate passes explicit lyrics when allow_explicit is True
    When I run explicit_gate on "we yelled fuck and ran" with allow_explicit
    Then passed is True
    And rating is "explicit"

  Scenario: repetition_gate passes on unique tracks
    When I run repetition_gate on two tracks with no shared lines
    Then passed is True

  Scenario: check_name_exposure finds a rostered name
    When I check name exposure of "Lex stood there in the rain" against roster ["Lex"]
    Then count is 1
    And hits contain name "Lex"

  Scenario: check_name_exposure respects word boundary
    When I check name exposure of "it is in my lexicon" against roster ["Lex"]
    Then count is 0

  Scenario: check_name_exposure is case-insensitive
    When I check name exposure of "lex walked home alone" against roster ["Lex"]
    Then count is 1

  Scenario: name_exposure_gate blocks when a rostered name is found
    When I run name_exposure_gate on "and then Lex spoke softly" with roster ["Lex"]
    Then the gate fails
    And the lifecycle state is "input-required"

  Scenario: name_exposure_gate passes when no rostered names appear
    When I run name_exposure_gate on "the host watched the witness leave" with roster ["Zephyr"]
    Then passed is True
    And hits is empty

  Scenario: extract_distinctive_phrases returns novel trigrams
    When I extract distinctive phrases from "The blue box echoes through the night"
    Then at least 1 phrase is returned

  Scenario: check_streaming_lyrics flags bracket tags
    When I check streaming lyrics of "[Verse 1]\nbody here"
    Then safe is False
    And bracket_tags is at least 1

  # ───────────────────────────── Audio cluster (096) ──────────────────────────

  Scenario: master_audio produces a mastering-report artefact
    When I master audio "/tmp/track1.wav" with target_lufs -14.0 and preset "streaming"
    Then the artefact kind is "mastering-report"
    And target_lufs in the artefact is -14.0
    And a mastering-report artefact is recorded against the intent

  Scenario: master_with_reference uses reference loudness for target
    When I master audio "/tmp/track1.wav" with reference "/tmp/reference.wav"
    Then the artefact contains a target_lufs
    And the preset starts with "ref:"

  Scenario: polish_audio returns a polished output path
    When I polish audio "/tmp/t1.wav"
    Then the output path ends with ".polished"

  Scenario: polish_album polishes every track in the list
    When I polish album "A" with 3 paths
    Then count is 3
    And every polished path ends with ".polished"

  Scenario: analyze_audio returns loudness and spectral signature
    When I analyze audio "/tmp/t1.wav"
    Then loudness_lufs is present
    And signature contains centroid_hz

  Scenario: qc_audio returns 7 QC rows with a summary verdict
    When I run qc_audio on "/tmp/t1.wav"
    Then 7 QC rows are returned
    And summary is one of "pass", "warn", "fail"
    And all expected QC categories are present

  Scenario: mono_fold_check reports phase safety
    When I run mono_fold_check on "/tmp/t1.wav"
    Then cancellation_db is present
    And phase_safe is present

  Scenario: measure_album_signature returns per-track signatures
    When I measure album signature for 2 paths
    Then count is 2
    And each signature has centroid_hz and rms_db

  Scenario: album_coherence_check reports outliers
    When I run album_coherence_check on 4 paths
    Then coherent is present
    And outliers is present
    And track_count is 4

  Scenario: fix_dynamic_track returns DR metrics
    When I fix dynamic track "/tmp/t1.wav" with target_dr 8.0
    Then measured_dr is present
    And target_dr is 8.0
    And applied is present

  Scenario: render_codec_preview returns a preview path
    When I render codec preview of "/tmp/t1.wav" with codec "aac"
    Then the codec in result is "aac"
    And bitrate_kbps is 256
    And the output ends with ".aac.preview"

  Scenario: reset_mastering flips mastered tracks back to non-mastered
    Given album "Origin" by artist "A" has 1 mastered track
    When I reset mastering for album "origin"
    Then reset is True
    And no tracks are in "mastered" status

  Scenario: generate_promo_videos produces a promo-video artefact
    When I generate promo videos for album "A" with template "reels-15s"
    Then the artefact kind is "promo-video"
    And the output path contains "reels-15s"

  Scenario: create_songbook produces a sheet-music artefact
    When I create a songbook for album "A" with 3 tracks
    Then the artefact kind is "sheet-music"
    And the output path contains "3-tracks"

  Scenario: measure_gate fails when loudness is outside the target window
    When I run measure_gate on "/tmp/t1.wav" with window min -9.0 max -8.0
    Then the gate fails
    And the lifecycle state is "input-required"

  Scenario: measure_gate passes when window includes the measured loudness
    When I run measure_gate on "/tmp/t1.wav" with window min -25.0 max -5.0
    Then passed is True
    And measured_lufs is present

  # ───────────────────────────── Catalogue cluster (097) ──────────────────────

  Scenario: db_create_tweet returns a tweet-record artefact with a tweet_id
    When I create a tweet for album "Origin" with body "New album out now!"
    Then the artefact kind is "tweet-record"
    And tweet_id is present in the artefact
    And a tweet-record artefact is recorded against the intent

  Scenario: db_update and db_delete tweet round-trip
    Given a tweet exists for album "A" with body "initial"
    When I update that tweet status to "scheduled"
    And I list tweets for album "A" filtered by "scheduled"
    Then the count is 1
    When I delete that tweet
    And I list tweets for album "A"
    Then the count is 0

  Scenario: db_search_tweets finds a substring match
    Given 2 tweets exist for album "A"
    When I search tweets for "phreaker"
    Then count is 1
    And the returned tweet body contains "phreaker"

  Scenario: db_get_tweet_stats aggregates by status
    Given 2 tweets exist for album "A" with one scheduled
    When I get tweet stats for album "A"
    Then total is 2
    And draft count is 1
    And scheduled count is 1

  Scenario: db_sync_album replaces existing tweets
    Given 1 tweet exists for album "A"
    When I sync album "A" with 3 new tweets
    Then removed is 1
    And created is 3
    And listing tweets for "A" returns 3

  Scenario: update and get streaming URLs round-trip
    When I update streaming url for album "A" platform "spotify"
    And I update streaming url for album "A" platform "apple"
    And I get streaming urls for album "A"
    Then the returned platforms include "spotify" and "apple"

  Scenario: get_promo_status combines tweets and streaming counts
    Given 1 tweet and 1 streaming url exist for album "A"
    When I get promo status for album "A"
    Then tweets total is 1
    And streaming_urls count is 1

  Scenario: get_promo_content splits drafts and scheduled
    Given 2 tweets exist for album "A" with one scheduled
    When I get promo content for album "A"
    Then total is 2
    And drafts count is 1
    And scheduled count is 1

  Scenario: extract_links finds URLs in text
    When I extract links from text containing 2 URLs
    Then count is 2
    And one url contains "spotify"
    And one url contains "apple"

  Scenario: tweet_schedule_gate passes a valid body with scheduled_at
    When I run tweet_schedule_gate with a valid body and scheduled_at
    Then passed is True
    And length is positive

  Scenario: tweet_schedule_gate fails on empty body
    When I run tweet_schedule_gate with an empty body
    Then the gate fails
    And the error contains "body is empty"

  Scenario: tweet_schedule_gate fails when over max_length
    When I run tweet_schedule_gate with a body of 281 characters
    Then the gate fails
    And the error contains "length 281 > 280"

  Scenario: tweet_schedule_gate fails when scheduled_at is missing
    When I run tweet_schedule_gate with a valid body and no scheduled_at
    Then the gate fails
    And the error contains "scheduled_at is required"

  # ───────────────────────────── Promo cluster (098) ──────────────────────────

  Scenario: promo_review scores clean CTA copy highly
    When I review promo body "New album out now! Stream everywhere." for platform "x"
    Then score is at least 80
    And max_length is 280

  Scenario: promo_review flags over-length copy
    When I review a promo body over 280 characters for platform "x"
    Then an over_length finding is present
    And score is below 70

  Scenario: promo_review flags missing call-to-action
    When I review promo body "Just words, no call to action." for platform "x"
    Then a no_cta finding is present

  Scenario: promo_review flags explicit content
    When I review promo body "This shit is fire! Stream now." for platform "x"
    Then an explicit finding is present

  Scenario: upload_promo_video produces a published-asset artefact
    Given the cloud driver is configured
    When I upload promo video for album "Origin" with key "origin/promo.mp4"
    Then the artefact kind is "published-asset"
    And the asset_kind is "promo-video"

  Scenario: publish_sheet_music produces a published-asset artefact
    Given the cloud driver is configured
    When I publish sheet music for album "Origin" with key "origin/songbook.pdf"
    Then the artefact kind is "published-asset"
    And the asset_kind is "sheet-music"

  Scenario: publish_sheet_music fails when cloud is unconfigured
    When I publish sheet music without a configured cloud driver
    Then the invocation outcome is "failed"
    And the error contains "DEPENDENCY_MISSING"

  Scenario: r2_delete and r2_list round-trip
    Given the cloud driver is configured
    And 3 assets are uploaded under prefix "a/"
    When I list assets under prefix "a/"
    Then count is 3
    When I delete asset "a/promo1.mp4"
    And I list assets under prefix "a/"
    Then count is 2

  Scenario: release_package records a promo-album-package artefact
    Given the cloud driver is configured
    When I create a release package for album "Origin" with 3 assets
    Then the artefact kind is "promo-album-package"
    And the artefact has 3 assets
    And a promo-album-package artefact is recorded against the intent

  Scenario: promo_review_gate passes quality copy
    Given the cloud driver is configured
    When I run promo_review_gate on "New album out now! Stream everywhere." for "x"
    Then passed is True
    And score is at least 70

  Scenario: promo_review_gate blocks low-quality copy
    Given the cloud driver is configured
    When I run promo_review_gate on "   " for "x"
    Then the gate fails
    And the lifecycle state is "input-required"

  Scenario: verify_streaming produces a streaming-verify artefact
    Given the cloud driver is configured
    When I verify streaming urls for album "A"
    Then the artefact kind is "streaming-verify"
    And a streaming-verify artefact is recorded against the intent

  # ───────────────────────────── Research cluster (099) ───────────────────────

  Scenario: capture_claim records an AlbumClaim node and SERVES the intent
    When I capture claim "The defendant pled guilty" from "https://courtlistener.com/x" domain "legal" album "case-files"
    Then the claim_id starts with "albumclaim:"
    And domain is "legal"
    And verified is "pending"
    And a SERVES edge links the claim to the intent

  Scenario: capture_claim rejects an unknown domain
    When I capture claim with domain "polka"
    Then the invocation outcome is "failed"
    And the error contains "invalid_argument"

  Scenario: list_claims filters by verified status
    Given 2 claims exist for album "A" with status "pending"
    When I list all claims
    Then count is 2
    When I list claims with status "pending"
    Then count is 2
    When I list claims with status "human-confirmed"
    Then count is 0

  Scenario: pending_verifications aggregates by domain
    Given 2 legal claims and 1 financial claim for album "A"
    When I get pending verifications for album "A"
    Then pending_count is 3
    And legal count is 2
    And financial count is 1

  Scenario: verify_sources clears pending claims
    Given 3 claims exist for album "A"
    When I verify sources for album "A"
    Then verified_count is 3
    And no pending claims remain

  Scenario: verify_gate passes when there are no pending claims
    When I run verify_gate on album "A" with no claims
    Then passed is True
    And pending_count is 0

  Scenario: verify_gate blocks when pending claims exist
    Given 1 pending claim exists for album "A"
    When I run verify_gate on album "A"
    Then the gate fails
    And the error contains "1 pending"
    And the lifecycle state is "input-required"

  Scenario: human_signoff records an AlbumVerification node
    When I call human_signoff for album "Origin" reviewer "alice"
    Then album in result is "Origin"
    And reviewer in result is "alice"
    And signoff_id starts with "albumverification:"

  Scenario: document_hunt delegates to a research lead
    When I call document_hunt with query "SEC enforcement actions 2023"
    Then research_id is present
    And domain is "document_hunter"

  Scenario: research_scope delegates to a research lead
    When I call research_scope question "What happened in 2008?" album "A"
    Then research_id is present
    And specialists is present
    And album is "A"

  # ───────────────────────────── Gates cluster (100) ──────────────────────────

  Scenario: validate_album flags missing album
    When I validate album "nonexistent"
    Then files_present is False
    And track_count is 0
    And at least 1 issue is reported

  Scenario: validate_album passes for an existing album with a track
    Given album "Origin" by artist "A" exists with 1 track
    When I validate album "origin"
    Then files_present is True
    And track_count is 1
    And mirror_paths_ok is True

  Scenario: diagnose returns driver inventory and surface counts
    Given the cloud driver is configured
    When I call diagnose
    Then ok is True
    And all 5 music drivers are wired
    And verbs_count is the live verb count
    And skills_count is at least 10

  Scenario: concept_gate passes when album exists
    Given album "Origin" by artist "A" exists
    Given the cloud driver is configured
    When I run concept_gate on album "origin"
    Then passed is True

  Scenario: concept_gate blocks when album is missing
    Given the cloud driver is configured
    When I run concept_gate on album "ghost"
    Then the gate fails
    And the lifecycle state is "input-required"

  Scenario: audio_release_gate passes when all tracks are mastered
    Given the cloud driver is configured
    Given album "Origin" by artist "A" exists with 1 mastered track
    When I run audio_release_gate on album "origin"
    Then passed is True

  Scenario: audio_release_gate blocks when tracks are not mastered
    Given the cloud driver is configured
    Given album "Origin" by artist "A" exists with 1 unmastered track
    When I run audio_release_gate on album "origin"
    Then the gate fails

  Scenario: catalogue_gate passes with urls and scheduled tweets
    Given the cloud driver is configured
    And a streaming url and a scheduled tweet exist for album "A"
    When I run catalogue_gate on album "A"
    Then passed is True

  Scenario: catalogue_gate blocks on empty state
    Given the cloud driver is configured
    When I run catalogue_gate on album "A" with no state
    Then the gate fails

  Scenario: promo_gate passes with a published asset
    Given the cloud driver is configured
    And a promo video is uploaded for album "A"
    When I run promo_gate on album "A"
    Then passed is True

  Scenario: promo_gate blocks with no assets
    Given the cloud driver is configured
    When I run promo_gate on album "A" with no assets
    Then the gate fails

  # ─────────────────────────── Provenance (cross-cluster) ─────────────────────

  Scenario: full release pipeline records provenance across all clusters
    Given the cloud driver is configured
    When I run the full release pipeline for album "Modem Daze"
    Then the provenance chain includes artefact kind "published-asset"
    And the provenance chain includes artefact kind "tweet-record"
    And the gate names include "audio-release"
    And the gate names include "catalogue"
    And the gate names include "promo"

  Scenario: driver-backed verbs return DEPENDENCY_MISSING when no driver is wired
    When I run driver-backed verbs with no music drivers registered
    Then each verb returns DEPENDENCY_MISSING

  # ─────────────────────────── Capability health (007 baseline) ───────────────

  Scenario: music_health reports all drivers wired
    When I call music_health
    Then ok is True
    And all 5 drivers are in drivers_wired

  Scenario: count_syllables is deterministic and driver-free
    When I count syllables of "mastering"
    Then syllable count is 3
    And calling again returns the same result

  Scenario: lyric_report uses the text driver and produces a lyric-report artefact
    When I call lyric_report for album "X" with lyrics "hello darkness\nmy old friend"
    Then the artefact kind is "lyric-report"
    And lines is 2
    And a lyric-report artefact exists in the graph
