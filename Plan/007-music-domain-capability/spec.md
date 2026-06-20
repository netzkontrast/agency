---
spec_id: 007
slug: music-domain-capability
status: draft
owner: "@agency"
depends_on: [001, 002]
affects:
  - examples/music.py
  - examples/music_drivers.py
  - examples/test_music_capability.py
source-repos:
  - "https://github.com/bitwize-music-studio/claude-ai-music-skills.git @ v0.91.0 (SHA b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf)"
estimated_jules_sessions: 3
domain: music
wave: 2
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting.** Run gates 1→4 in order:
> (1) Confidence ≥ 0.90, (2) TDD Red-Green-Refactor, (3) Evidence pasted under `## Evidence`, (4) Self-Review answered.
> Branch: `claude/extract-agency-plugin-o4JRc`. Only modify paths under `affects:` below.
> Source repos under `source-repos:` are clone-and-read-only into `~/work/vendor/`; never commit them.
> If anything is ambiguous, open a draft PR labelled `[BLOCKED: clarification]` and stop — do not guess.

> **BLOCKED ON SPEC 002.** This spec makes **zero edits to `agency/`** (see
> Done-When and Open Q #2). All driver injection routes through Spec 002's
> `DriverRegistry` (`ctx.get_driver(name)`). Spec 002 is `status: draft` and has
> not shipped. **Until 002's `DriverRegistry` lands, 007 is BLOCKED — it is NOT
> licensed to edit `agency/engine.py` to add injectors.** Confirm 002 is `done`
> before coding any driver-backed verb.

# Spec 007 — Music Domain Capability (a clustered-contract example extension)

## Why

`examples/music.py` is the canon's designated **example extension** for the
`music` domain (CAPABILITY-CLUSTERS.md:16 — disposition verbatim "example
extension (`examples/music.py`, loaded via `extra_capabilities`)"). Its job per
the canon is to **prove the contract**, not to mirror a legacy tool count. Music
was already surveyed and **absorbed** — "the four concepts + the engine absorb
it all … the only net-new specs were `delegate` and `reflect`" (CORE.md:137-141).
So 007's deliverable is a *proof of absorption*: it must demonstrate that a hard,
messy, real-world domain **fits** the clustered Capability + Boundary/Driver +
gated-skill contract, with the **provenance moat** (Memory) as the headline thing
the legacy surface cannot do.

[`bitwize-music`](https://github.com/bitwize-music-studio/claude-ai-music-skills)
(v0.91.0) is the real domain we draw from. It ships **89 distinct MCP tools** plus
slash-command skills, across one FastMCP server (`servers/bitwize-music-server/
handlers/`) organised into **nineteen** handler modules — 15 top-level + 4 under
`processing/`, each wired by a `register(mcp)` call in `server.py:338-353`:
`core` (18 tools — the single largest module), `content`, `text_analysis`,
`lyrics_analysis`, `album_ops`, `gates`, `streaming`, `skills`, `status`,
`promo`, `health`, `ideas`, `rename`, `database`, `maintenance`, and the four
`processing/{audio,mixing,video,sheet_music}` modules. It is a **flat, hand-wired
tool surface**: every tool is programmatically registered via `mcp.tool()(fn)`
inside its module's `register()` (e.g. `skills.py:117-118`); every workflow
guard-rail lives in skill prose; and there is **no provenance** — a mastering run,
a plagiarism scan, and a tweet insert leave no shared trace.

That flat 89-tool surface is exactly the bloat the canon warns against
(CAPABILITY-CLUSTERS.md:31 — "**Multiplying concepts would re-introduce
bloat**"). **Porting all 89 as 1:1 auto-wired MCP verbs would re-import that
bloat into `examples/`**, merely relocated. The canon's growth unit is *one file
that owns one ontology fragment* (CAPABILITY-CLUSTERS.md:6-8), proven by a
**representative slice**, not an exhaustive clone. So 007 ships a small,
representative verb set and demotes the full 89-tool inventory to a documentation
appendix.

**What 007 proves (the clustered contract on a real domain):**

- **The clustered Capability shape.** bitwize's tools fall into **eight clusters**
  spanning the four concepts. 007 ships **one representative verb per cluster**
  (~12-16 verbs total) — each proving its cluster's role (`act` / `transform` /
  `effect`) and its driver boundary fires. Code-mode IS the contract (CORE.md:9-18):
  the agent discovers a verb via `search`, reads it via `get_schema`, runs it in
  `execute` which records an `Invocation` that `SERVES` the intent. The example
  publishes a *lean* surface, not a 89-tool menu.
- **The Boundary/Driver contract (Spec 002, Option B).** Side-effecting clusters
  reach their work through injected drivers — `StateDriver`, `TextDriver`,
  `AudioDriver`, `DBDriver`, `CloudDriver` — each a marker `Boundary` exposing its
  **own typed, named methods** (`AudioDriver.read_loudness(...)`, `DBDriver.cursor()`,
  `CloudDriver.url_head(url)` — the `jules.py` `create/get/list` shape, NOT a
  stringly-typed `dispatch(op, **kw)`). The verb stays pure and testable; production
  binds the real driver, tests bind a deterministic fake. **All injection routes
  through Spec 002's `DriverRegistry` (`ctx.get_driver(name)`) — 007 edits no
  core file.** This is why 007 depends on **001** (ToolResult / Boundary / Driver
  / TypedError) and **002** (the Option-B typed-named-method Driver taxonomy +
  `DriverRegistry` + OntologyExtension contract).
- **The uniform `ToolResult` envelope (Spec 001).** Every verb returns a Spec-001
  `ToolResult` (`ok / data / warnings / next_suggested_tools / error`), so a failed
  master or a blocked gate is typed (`GATE_FAILED`, `DEPENDENCY_MISSING`) rather
  than a stringly-typed raise.
- **Gated, walkable skills with the right human-in-loop mechanism.** Workflow
  guard-rails become real skills, not prose — and the canon's distinction is
  honored (CORE.md:57-62): **machine-checkable predicates** use `gate.check`
  (PASSED / BLOCKED_ON), while the **terminal human "is this ready / ship it?"
  confirmation** is an `elicit` step (the engine `lifecycle_gate`), exactly like
  the existing `album-concept` Phase-7 hard gate. The `pre-generation` and
  `release-qa` skills are `OntologyExtension.skills` phase-graphs the engine's
  skill-walker advances one phase at a time.
- **The provenance moat (the headline proof — net-new vs bitwize).** Every verb
  records an `Invocation` that `SERVES` the intent; `act` verbs that emit a
  document record a `PRODUCES` edge. A release audit — "show me every master, QC
  pass, and tweet for this album" — is one `memory_graph_provenance(intent_id)`
  traversal. **bitwize cannot do this** (no graph/provenance layer in handlers).
  This is the one thing the example exists to demonstrate.

The deliverable lives in `examples/` (not core `agency/capabilities/`) per the
canon (CAPABILITY-CLUSTERS.md:16, CLAUDE.md standing rule) — loaded via
`Engine(..., extra_capabilities=[…])`, keeping the bootstrap harness minimal while
proving the contract end-to-end.

> **Out of scope (downstream consequence, not a goal).** Whether bitwize's product
> surface is eventually *retired* is a downstream product-migration question, not
> the concern of an example file (CORE.md:131-133 — the stakeholder is a plugin
> author learning the contract). 007 proves the *shape* on a real domain;
> feature-parity with bitwize is illustrative (the appendix shows nothing is
> unmodelable), not contractual.

## Done When

- [ ] **007 modifies no file under `agency/`.** Drivers inject via Spec 002's
      `DriverRegistry` (`ctx.get_driver(name)`). If 002's registry has not landed,
      007 is **BLOCKED, not licensed to edit `agency/engine.py`** (no new
      injectors, no core edit). `affects:` lists only `examples/` paths.
- [ ] `examples/music.py` defines a `MusicCapability(CapabilityBase)` carrying
      **one representative verb per cluster** (the eight clusters of the design
      table), **~12-16 verbs total** — enough to prove each role
      (`act`/`transform`/`effect`) and each driver boundary fires. This is the
      build contract; the full 89-tool inventory is a documentation **appendix**
      (see Appendix A), not a list of verbs to implement. The long tail is marked
      "covered-by-pattern, port-on-demand."
- [ ] Verbs are role-tagged `act` / `transform` / `effect` and each is documented
      against the cluster it represents.
- [ ] Side-effecting representative verbs reach their work through injected drivers
      (`StateDriver`, `TextDriver`, `AudioDriver`, `DBDriver`, `CloudDriver`) typed
      as Spec-001 `Boundary`/`Driver` protocols (Spec-002 Option B, typed named
      methods) in `examples/music_drivers.py`, resolved via `self.ctx.get_driver(name)`.
      No verb shells out to `ffmpeg`/AnthemScore/R2/Postgres directly.
- [ ] Every verb returns a Spec-001 `ToolResult`. `act` verbs that produce a
      document set `data["artefact"]` so the Registry records a `PRODUCES` edge
      (matching `examples/music.py:conceptualize` today).
- [ ] `MusicCapability.ontology` is a **single** `OntologyExtension` carrying: the
      `Album` and `Track` nodes (extended with the fields the representative verbs
      read/write — `status`, `genre`, `slug`, `target_lufs`, …), the closed enums
      (`(Album,status)`, `(Album,type)` reusing today's `ALBUM_TYPES`,
      `(Track,status)`), a `Tweet`/`Idea`/`SheetMusic` node, the `pre-generation`
      and `release-qa` gated skill phase-graphs, and the artefact schemas
      (`album-concept` (kept), `promo-copy`, `mastering-report`, `lyric-report`).
      Merged STRICTLY onto core (`Ontology.extend`).
- [ ] The existing `conceptualize` act verb and the `album-concept` skill are
      **preserved** (007 extends, does not regress the demo).
- [ ] **Gate split honored (CORE.md:57-62).** Machine-checkable predicates use
      `gate.check`; the terminal human "ready / ship it?" confirmation uses an
      `elicit` step (`lifecycle_gate`), exactly like `album-concept` Phase 7. The
      gated-skill table names which gates are computed and which are human.
- [ ] `examples/test_music_capability.py` proves, with fake drivers: (a)
      `MusicCapability.as_capability()` discovers the representative verbs; (b) each
      cluster's representative verb returns a well-formed `ToolResult`; (c) the
      transform verb (`count_syllables`) is deterministic and driver-free; (d) the
      effect verb (`master_album`) routes through the injected `AudioDriver` fake
      (whose typed `read_loudness()`/`run_ffmpeg()` methods stand in for
      pyloudnorm/ffmpeg) and records an `Invocation`; (e) a failed `pre-generation`
      computed gate, run against a `lifecycle_id` that `SERVES` the intent, returns
      `ToolResult(ok=False, error=GATE_FAILED)` and pauses the lifecycle via
      `gate.check`, while the terminal confirmation pauses via `elicit`/
      `lifecycle_gate`; (f) the ontology merges cleanly onto core with no
      strict-schema collision; (g) the `DBDriver` fake models a psycopg2-shaped
      cursor (no Postgres host) and the `CloudDriver` fake's `url_head` (stdlib
      urllib) is testable while `r2_put` (boto3) returns `DEPENDENCY_MISSING` when
      unconfigured.
- [ ] Loading `Engine(path, extra_capabilities=[MusicCapability.as_capability()])`
      registers the capability and merges its ontology without error (same path
      `examples/music.py` already exercises), and **without any prior edit to
      `agency/`**.

## Design

### Driver clusters (the Boundary/Driver layer — Spec 001/002)

bitwize's tools split cleanly along the axis of *what external surface they touch*.
Each surface is one `Driver` — a marker `Boundary` exposing typed named methods
(Spec 002, Option B) — resolved inside a verb via `self.ctx.get_driver(name)`
(Spec 002's `DriverRegistry`; **no engine edit**). The verb is pure; the driver is
the only thing that knows about `ffmpeg`, `pyloudnorm`, AnthemScore, the PostgreSQL
promo DB, the markdown state tree, or Cloudflare R2 — so tests bind fakes. CI needs
no audio binaries and **no Postgres host**: the `DBDriver` fake models a
psycopg2-shaped cursor, not a local file.

| Driver | Boundary it owns | Real backend | bitwize handler modules |
|---|---|---|---|
| `StateDriver` | the album/track markdown state tree + cache + path resolution + config + session | filesystem + state cache | `core`, `content`, `album_ops`, `rename`, `status`, `ideas`, `promo`, `skills`, `health`, `maintenance` (session/config/health/idea/rename helpers) |
| `TextDriver` | pure text/lyric analysis (no I/O) | stdlib only (`re`, `statistics`, `threading`) + module-level pattern tables; **no `pronouncing`/`textstat`** | `text_analysis`, `lyrics_analysis` |
| `AudioDriver` | WAV analysis, mix/master/QC, video render, sheet-music transcription | `pyloudnorm` (+`numpy`/`scipy`/`soundfile`) for loudness; **`ffmpeg` via `subprocess`** for encode/render; **AnthemScore** shelled out for transcription. **No `librosa`** (imported nowhere in handlers). | `processing/audio`, `processing/mixing`, `processing/video`, `processing/sheet_music` |
| `DBDriver` | the tweet/promo **PostgreSQL** database | **PostgreSQL via `psycopg2`** — `tools/database/connection.py` `get_connection()` calls `psycopg2.connect(host/port/dbname/user/password, connect_timeout=5)` reading creds from `~/.bitwize-music/config.yaml`; `db_init` runs `tools/database/schema.sql` + a migrations dir. **Needs a Postgres host + creds (or a stubbed driver in CI).** | `database` |
| `CloudDriver` | **split:** (a) streaming-URL reachability checks (stdlib, no creds) and (b) R2 publishing (network + creds) | (a) `url_head()` over **stdlib `urllib.request`** (`streaming.py:247-301`, HEAD→GET fallback, SSRF scheme guard) — `httpx` is imported nowhere; (b) `r2_put()` over **boto3/R2** (`processing/sheet_music.py:435`) | `streaming` (urllib half), `processing/sheet_music` `publish_sheet_music` (boto3 half) |

All five drivers are reached via `self.ctx.get_driver(name)` (`state`, `text`,
`audio`, `db`, `cloud`) — Spec 002's `DriverRegistry`, populated by the engine at
startup. **007 does not add injectors to `engine.py`**; if 002's registry is
unlanded, 007 is blocked (Open Q #2).

### The eight verb clusters (representative slice)

Roles per the model: **act** = craft write that produces an artefact;
**transform** = stateless pure compute; **effect** = external side-effect.

007 ships **one representative verb per cluster** (the picks below), proving each
role + driver fires. The remaining tools in each cluster are documented in
Appendix A as "covered-by-pattern, port-on-demand."

| # | Cluster | Representative verb (the one 007 ships) | Role | Driver | Proves |
|---|---|---|---|---|---|
| 1 | **concept** (kept demo) | `conceptualize` (already shipped) | act | — (pure render) | act + artefact `PRODUCES` + hard `elicit` gate |
| 2 | **catalog** (album/track/idea CRUD + read) | `create_album` (+ read `find_album`) | act / transform | StateDriver | act write + transform read over a state boundary |
| 3 | **state** (session/cache/config/path/health) | `get_album_progress` | transform | StateDriver | a read-projection over state |
| 4 | **lyric** (text analysis, all pure) | `count_syllables` | transform | TextDriver (stdlib-pure) | a deterministic, driver-free transform |
| 5 | **audio** (analyze/mix/master/QC) | `master_album` (pipeline) | effect | AudioDriver | effect through a heavy-binary driver + `DEPENDENCY_MISSING` |
| 6 | **media** (video + sheet music) | `transcribe_audio` | effect | AudioDriver | effect via shelled-out backend (AnthemScore) + stub |
| 7 | **promo** (tweet DB + promo copy + cloud) | `db_create_tweet` (+ `verify_streaming_urls`) | effect | DBDriver (Postgres), CloudDriver (urllib) | effect over a psycopg2-shaped fake + a stdlib-urllib check that runs in CI |
| 8 | **gates** (validation → gate/skill) | `run_pre_generation_gates` + the `pre-generation` skill | act | StateDriver + `gate` + `elicit` | computed `gate.check` AND a terminal human `elicit` confirmation |

That is **~12-16 auto-wired verbs** once the parenthetical read/check companions
are counted. Each proves a distinct point on the contract; none is there for
parity. The full inventory (all 89, every legacy tool given a taxonomic home) is
**Appendix A**.

### Verbs vs internal driver methods vs gated skills

- **Verbs (auto-wired MCP tools):** the representative picks above. One agency
  verb per representative bitwize tool. Pipeline picks (`master_album`) wrap a
  bitwize multi-step chain (analyze→QC→master→verify→update-status) as a single
  `effect` verb the AudioDriver executes step-wise and the verb records as one
  Invocation.
- **Internal driver methods (NOT verbs, no MCP tool):** the *primitive steps*
  bitwize never exposed as separate tools but that the drivers need — typed named
  methods per Spec 002 Option B, named for the **real** backends:
  `AudioDriver.read_loudness()` (pyloudnorm) / `AudioDriver.run_ffmpeg()`
  (subprocess) / `AudioDriver.run_anthemscore()` (shell-out),
  `StateDriver.read_markdown()` / `StateDriver.write_field()`,
  `DBDriver.cursor()` (a psycopg2 connection/cursor, NOT a sqlite file),
  `CloudDriver.url_head(url)` (stdlib urllib) and `CloudDriver.r2_put()` (boto3).
  These are driver-internal; the verb orchestrates them. This is where the
  `pyloudnorm`/`ffmpeg`/AnthemScore/psycopg2/boto3 calls live so they are mockable.
- **Gated skills (walkable phase-graphs in the OntologyExtension, NOT one tool):**
  bitwize's *workflow chains* (the pre-generation chain and the pre-release chain)
  become `OntologyExtension.skills` entries the engine's skill-walker advances one
  phase at a time, with gated phases — exactly like the existing `album-concept`
  skill. The individual computed checks remain callable transform verbs that the
  skill phases `invoke:` (the `plugin.py` skill→verb `invoke` binding pattern).

### Gated-skill mapping (bitwize chains → agency gates) — the `gate.check` / `elicit` split

The canon (CORE.md:57-62) distinguishes **computed predicates** (`gate.check` —
machine-checkable, records PASSED / BLOCKED_ON) from **human confirmation**
(`elicit` / the engine `lifecycle_gate` — pauses the Lifecycle at `input-required`,
the answer resumes it). 007 maps each gate to the correct mechanism:

| bitwize workflow | agency mechanism | gate kind |
|---|---|---|
| `run_pre_generation_gates` — **exactly 8 checks** (`gates.py:_check_pre_gen_gates_for_track`, lines 42-189): (1) Sources Verified, (2) Lyrics Reviewed, (3) Pronunciation Resolved, (4) Explicit Flag Set, (5) Style Prompt Complete, (6) Artist Names Cleared, (7) Homograph Check, (8) Lyric Length | `pre-generation` skill: only **3 of the 8** checks exist as standalone transform verbs the phases can `invoke:` (`check_pronunciation_enforcement`, `check_explicit_content`, `scan_artist_names`); the other 5 (Sources/Lyrics/Style/Homograph/Length) are computed **inline inside `run_pre_generation_gates`**, not separate tools. The aggregate machine outcome → one **`gate.check`** (`computed`). | **computed** (`gate.check`) |
| The terminal "OK to generate?" confirmation at the end of pre-generation | an **`elicit`** step (`lifecycle_gate`) — the human "ready?" pause, identical in shape to `album-concept` Phase 7 | **human** (`elicit`) |
| pre-release QA (the **release-director prose chain**; there is **no single `run_release_gates` tool** — the QA is `validate_album_structure` + `check_streaming_lyrics` + manual checks) | `release-qa` skill: phases `invoke:` `validate_album_structure`, `qc_audio`, `check_streaming_lyrics` as computed `gate.check`s | **computed** (`gate.check`) per phase |
| The terminal "ship it?" release confirmation | an **`elicit`** step (`lifecycle_gate`) — the human release sign-off | **human** (`elicit`) |
| album-conceptualizer Phase 7 confirmation | already the `album-concept` skill's hard `elicit` gate (kept) | **human** (`elicit`, kept) |

`gate.check` requires a `lifecycle_id` that `SERVES` the current intent
(`gate.py:23-27` rejects cross-intent gates), so both the `pre-generation` and
`release-qa` skills must thread a lifecycle id. The pattern matches `plugin.py`'s
`SKILL_CREATION_SKILL` (phases bound to `invoke: {capability, verb}`) and
`examples/music.py`'s `ALBUM_CONCEPT_SKILL` (terminal human gate).

### Provenance (the headline proof — no bitwize equivalent)

Every representative verb records an `Invocation` `SERVES`→intent; `act` verbs that
emit a document (`promo-copy`, `mastering-report`, `lyric-report`, `album-concept`)
also record a `PRODUCES` edge. A release audit — "show me every master, QC pass,
and tweet for this album" — is one `memory_graph_provenance(intent_id)` traversal,
which bitwize cannot do (verified: no graph/provenance layer in handlers). This is
the load-bearing proof of the example and should be foregrounded in the tests.

## Files

- **Create**:
  - `examples/music_drivers.py` — the five `Boundary`/`Driver` protocols
    (`StateDriver`, `TextDriver`, `AudioDriver`, `DBDriver`, `CloudDriver`), each
    exposing typed named methods (Spec 002 Option B) + their default real backends
    (lazy-importing `pyloudnorm`/`ffmpeg`(subprocess)/AnthemScore/`psycopg2`/`boto3`
    only when called, so import never fails in CI; TextDriver and the urllib half of
    CloudDriver are stdlib-only with no lazy deps) + deterministic fakes for tests.
    Models the `jules.py` `JulesBackend`/`JulesClient` split.
  - `examples/test_music_capability.py` — the Done-When tests, using fake drivers;
    no audio binaries required.
- **Modify**:
  - `examples/music.py` — keep `conceptualize` + `ALBUM_CONCEPT_SKILL`; add the
    eight clusters' **representative** verbs (role-tagged), the expanded
    `OntologyExtension` (nodes/enums/skills/schemas), and the driver-accessor
    plumbing (`self.ctx.get_driver(name)`).
- **Out of this spec (explicitly NOT edited):**
  - `agency/engine.py` — **007 makes zero edits here.** Driver injection routes
    through Spec 002's `DriverRegistry`; if 002 has not shipped, 007 is BLOCKED
    (Open Q #2), not licensed to edit core.

## Open Questions / Needs Research

1. **Core vs. example — RESOLVED to `examples/` (canon + spec-panel).** The
   catalogue row (`agency/capabilities/music.py`) conflicts with CAPABILITY-CLUSTERS.md:16
   ("example extension (`examples/music.py`, …)") and CLAUDE.md's standing rule.
   Keep `examples/`; demote the catalogue row. Not a blocker.

2. **Driver injection point — BLOCKER until Spec 002 ships.** 007 routes all
   driver injection through Spec 002's `DriverRegistry` (`ctx.get_driver(name)`)
   and **edits no core file**. Spec 002 is `status: draft`. **If 002's registry
   has not landed, 007 is BLOCKED — it is NOT licensed to add injectors to
   `engine.py`.** This is a hard dependency (per VISION-REVIEW M4), not an
   editorial choice. Confirm 002 is `done` before coding any driver-backed verb.

3. **External dependencies — the real per-driver matrix (stubs where creds/binaries
   needed).** The representative verbs surface the full dep range:
   - **AudioDriver** (`master_album`, `transcribe_audio`) — `pyloudnorm`
     (+numpy/scipy/soundfile), **`ffmpeg` via subprocess**, **AnthemScore** (paid
     GUI/CLI) shelled out. Heavy binaries → ship the real backend as a stub
     returning `ToolResult(ok=False, error=DEPENDENCY_MISSING)` with install
     guidance.
   - **DBDriver** (`db_create_tweet`) — **PostgreSQL via `psycopg2`** + a Postgres
     host & creds from `~/.bitwize-music/config.yaml`. No local-sqlite fallback →
     stub the real backend; the fake is psycopg2-cursor-shaped.
   - **CloudDriver (split)** — `url_head` (`verify_streaming_urls`) is **stdlib
     `urllib`, needs NO stub and runs in CI today**; only `r2_put` (boto3/R2 creds)
     needs a stub.
   Recommendation: stub AudioDriver, DBDriver, and the boto3 half of CloudDriver;
   implement TextDriver and the urllib half of CloudDriver now. Tests use fakes
   regardless.

4. **Gate granularity — RESOLVED: one aggregate computed `gate.check` + a terminal
   `elicit` (CORE.md:57-62).** Only 3 of the 8 pre-generation checks are standalone
   verbs; the other 5 are internal to `run_pre_generation_gates`. So the machine
   outcome is one aggregate `gate.check` after the 8 internal checks (matches the
   real tool's single per-track pass/fail), and the human "ready?" confirmation is
   a separate `elicit`/`lifecycle_gate` step. Per-gate provenance later = a refactor
   of the gate function, out of scope.

5. **Overlap with existing core capabilities — RESOLVED.** `list_skills`/`get_skill`
   overlap `plugin.help` + `develop.reference`; bitwize `search` overlaps the engine's
   public `search`. Per VISION-REVIEW M5, **prefer dropping** `search`/`list_skills`/
   `get_skill` in favor of the core surface (the canon wants the menu lean); they are
   NOT among 007's representative picks. Drop `check_venv_health`/`cleanup_legacy_venvs`
   as obsolete-once-one-engine (no per-tool venvs under Agency). All four are
   appendix-only.

6. **`StateDriver` storage model — interim (b), end-state (a) (spec-panel).** For
   *this* spec, adopt **(b) filesystem markdown, 1:1 with bitwize** so 007 is
   shippable without a graph-native rewrite; flag **(a) mirror albums/tracks into
   Memory nodes** (graph-native, provenance for free) as the desirable end-state,
   deferred to the named `019-state-migration-from-bitwize` spec. No blocker for 007
   under (b).

## Evidence

- `/home/user/agency/docs/vision/CAPABILITY-CLUSTERS.md:16` — `music` disposition
  "example extension (`examples/music.py`, …)"; `:6-8` — growth unit is "a file
  that owns an ontology fragment"; `:31` — "Multiplying concepts would re-introduce
  bloat" (the re-scope's load-bearing line).
- `/home/user/agency/docs/vision/CORE.md:9-18` — code-mode IS the contract / lean
  surface; `:28-29` — role tags; `:47-62` — skills are gated step-graphs and
  human-in-loop gates are `elicit` steps; `:131-133` — capability-owned ontology;
  `:137-141` — music was surveyed and absorbed, no net-new primitive.
- `/home/user/agency/examples/music.py` — the demo this spec extends: `conceptualize`
  act verb, `ALBUM_TYPES` enum, `ALBUM_CONCEPT_SKILL` 7-phase hard-gated (`elicit`)
  skill, `music_ontology` `OntologyExtension`.
- `/home/user/agency/Plan/002-boundary-driver-protocol/spec.md:99-109, :244-288` —
  Spec 002's `DriverRegistry` reached via `ctx.get_driver(name)`; `status: draft`
  (the blocking dependency for Open Q #2).
- `/home/user/agency/research/capability-specs/specs/music.md` — the 89-tool
  inventory (source for Appendix A). Authoritative module layout is
  `server.py:338-353` (**19 modules**).
- Backend ground truth (spec-panel-verified against bitwize v0.91.0):
  `handlers/database.py:19` + `tools/database/connection.py` —
  `psycopg2.connect(..., connect_timeout=5)`, creds from `~/.bitwize-music/config.yaml`,
  `db_init` runs `tools/database/schema.sql` (**PostgreSQL, not SQLite**);
  `handlers/streaming.py:247-301` — `urllib.request.urlopen` HEAD→GET (**no `httpx`**);
  `handlers/processing/audio.py:258` `import pyloudnorm`,
  `handlers/processing/_helpers.py:161` `_check_anthemscore`, ffmpeg via subprocess
  in `processing/_album_stages.py` (**no `librosa`** in any handler);
  `handlers/processing/sheet_music.py:435` + boto3 for R2;
  `handlers/text_analysis.py:530` owns `extract_links`;
  `handlers/processing/audio.py:1379` owns `prune_archival`.
- `/home/user/agency/agency/capability.py:84-123` — `@verb` decorator + role tags +
  `CapabilityBase.as_capability()` reflection compile; `:36-81` — `CapabilityContext`.
- `/home/user/agency/agency/capabilities/plugin.py:134-180` — a real multi-verb
  capability with skill→verb `invoke` bindings and an `OntologyExtension` (the
  structural template).
- `/home/user/agency/agency/capabilities/jules.py:25-77` — the Boundary/Driver
  injection pattern (`JulesBackend` Protocol + `JulesClient` default).
- `/home/user/agency/agency/capabilities/gate.py:20-32` — `gate.check`:
  PASSED / BLOCKED_ON + `input-required` pause — the **computed** gate target.
- `/home/user/agency/agency/engine.py:40-56` — boundary injection +
  `extra_capabilities` extension point; `:61-89` — `_wire` auto-wiring one MCP tool
  per verb. (007 does NOT edit this file.)
- `/home/user/agency/research/oo-architecture/spec.md` (Spec 001, status done) +
  `PROPOSAL.md:5-83` — the `ToolResult` envelope, `Boundary`/`Driver` protocols,
  `TypedError`/`ErrorType` (depends_on=001).
- `/home/user/agency/agency/ontology.py:60-111` — `OntologyExtension`
  (nodes/edges/enums/skills/schemas/templates) + strict `extend()` merge.

---

# Appendix A — Full bitwize-tool → agency-taxonomy map (documentation, NOT the build contract)

> **This appendix is documentation, not a build list.** It proves the canon's
> claim that **every legacy bitwize tool has a taxonomic home** in the clustered
> Capability + Driver model — i.e. nothing in the 89-tool surface is unmodelable.
> It is **NOT** a list of verbs 007 must implement. 007 ships only the
> representative verb per cluster (Design table); the rows below marked anything
> other than a representative pick are **"covered-by-pattern, port-on-demand."**
> The representative picks 007 actually builds are flagged **[SHIP]**.

### Driver clusters (full module assignment)

| # | Cluster | bitwize tools (the full set) | Role(s) | Driver |
|---|---|---|---|---|
| 1 | **concept** (kept demo) | `conceptualize` **[SHIP]** | act | — (pure render) |
| 2 | **catalog** | `create_album` **[SHIP]**, `create_track`, `create_idea`, `promote_idea`, `update_idea`, `rename_album`, `rename_track`, `update_album_status`, `update_track_field`, `list_albums`, `list_tracks`, `list_track_files`, `find_album` **[SHIP]**, `get_track`, `get_album_full`, `get_album_progress`, `get_ideas`, `resolve_track_file`, `extract_section`, `format_for_clipboard` | act (writes) / transform (reads) | StateDriver |
| 3 | **state** | `get_session`, `update_session`, `rebuild_state`, `get_config`, `get_python_command`, `resolve_path`, `load_override`, `get_reference`, `get_plugin_version`, `health_check`, `diagnose`, `migrate_audio_layout`, `search`, `get_pending_verifications`, `list_skills`, `get_skill`, `get_album_progress` **[SHIP]** | transform / effect | StateDriver |
| 4 | **lyric** (all pure text) | `count_syllables` **[SHIP]**, `analyze_readability`, `analyze_rhyme_scheme`, `validate_section_structure`, `check_homographs`, `scan_artist_names`, `check_explicit_content`, `extract_distinctive_phrases`, `extract_links`, `get_lyrics_stats`, `check_cross_track_repetition`, `check_pronunciation_enforcement`, `check_streaming_lyrics` | transform | TextDriver (mostly stdlib-pure) |
| 5 | **audio** | `analyze_audio`, `analyze_mix_issues`, `qc_audio`, `mono_fold_check`, `polish_audio`, `polish_album`, `master_audio`, `master_album` **[SHIP]**, `master_with_reference`, `polish_and_master_album`, `fix_dynamic_track`, `reset_mastering`, `render_codec_preview`, `measure_album_signature`, `album_coherence_check`, `album_coherence_correct`, `prune_archival` | effect / transform | AudioDriver |
| 6 | **media** | `generate_promo_videos`, `generate_album_sampler`, `transcribe_audio` **[SHIP]**, `prepare_singles`, `create_songbook` | effect | AudioDriver |
| 7 | **promo** | `db_init`, `db_sync_album`, `db_create_tweet` **[SHIP]**, `db_update_tweet`, `db_delete_tweet`, `db_list_tweets`, `db_search_tweets`, `db_get_tweet_stats`, `get_promo_status`, `get_promo_content`, `get_streaming_urls`, `update_streaming_url`, `verify_streaming_urls` **[SHIP]**, `publish_sheet_music` | effect / transform | DBDriver (Postgres/psycopg2), CloudDriver (urllib + boto3) |
| 8 | **gates** | `run_pre_generation_gates` **[SHIP]**, `validate_album_structure`, `validate_section_structure`, `create_album_structure` | act | StateDriver + `gate` + `elicit` |

### All 89, nothing dropped — every legacy tool has a home

| # | bitwize tool | agency taxonomy home | driver | role | disposition |
|---|---|---|---|---|---|
| 1 | `create_album_structure` | catalog/gates | StateDriver | act | port-on-demand |
| 2 | `create_track` | catalog | StateDriver | act | port-on-demand |
| 3 | `create_idea` | catalog | StateDriver | act | port-on-demand |
| 4 | `update_idea` | catalog | StateDriver | act | port-on-demand |
| 5 | `promote_idea` | catalog | StateDriver | act | port-on-demand |
| 6 | `get_ideas` | catalog | StateDriver | transform | port-on-demand |
| 7 | `rename_album` | catalog | StateDriver | act | port-on-demand |
| 8 | `rename_track` | catalog | StateDriver | act | port-on-demand |
| 9 | `update_album_status` | catalog | StateDriver | act | port-on-demand |
| 10 | `update_track_field` | catalog | StateDriver | act | port-on-demand |
| 11 | `list_albums` | catalog | StateDriver | transform | port-on-demand |
| 12 | `list_tracks` | catalog | StateDriver | transform | port-on-demand |
| 13 | `list_track_files` | catalog | StateDriver | transform | port-on-demand |
| 14 | `find_album` | catalog | StateDriver | transform | **[SHIP]** (catalog read companion) |
| 15 | `get_track` | catalog | StateDriver | transform | port-on-demand |
| 16 | `get_album_full` | catalog | StateDriver | transform | port-on-demand |
| 17 | `get_album_progress` | state | StateDriver | transform | **[SHIP]** (cluster-3 representative) |
| 18 | `resolve_track_file` | catalog | StateDriver | transform | port-on-demand |
| 19 | `extract_section` | catalog | StateDriver | transform | port-on-demand |
| 20 | `format_for_clipboard` | catalog | StateDriver | transform | port-on-demand |
| 21 | `get_session` | state | StateDriver | transform | port-on-demand |
| 22 | `update_session` | state | StateDriver | effect | port-on-demand |
| 23 | `rebuild_state` | state | StateDriver | effect | port-on-demand |
| 24 | `get_config` | state | StateDriver | transform | port-on-demand |
| 25 | `get_python_command` | state | StateDriver | transform | port-on-demand |
| 26 | `resolve_path` | state | StateDriver | transform | port-on-demand |
| 27 | `load_override` | state | StateDriver | transform | port-on-demand |
| 28 | `get_reference` | state | StateDriver | transform | port-on-demand |
| 29 | `get_plugin_version` | state | StateDriver | transform | port-on-demand |
| 30 | `check_venv_health` | state | StateDriver | transform | DROP (obsolete: no per-tool venvs under Agency) |
| 31 | `health_check` | state | StateDriver | transform | port-on-demand |
| 32 | `diagnose` | state | StateDriver | transform | port-on-demand |
| 33 | `cleanup_legacy_venvs` | state | StateDriver | effect | DROP (obsolete: no per-tool venvs) |
| 34 | `migrate_audio_layout` | state | StateDriver | effect | port-on-demand |
| 35 | `prune_archival` | audio | AudioDriver | effect | port-on-demand (lives in `processing/audio.py:1379`) |
| 36 | `search` | state | StateDriver | transform | DROP (use core `search`) |
| 37 | `get_pending_verifications` | state | StateDriver | transform | port-on-demand |
| 38 | `extract_links` | lyric | TextDriver | transform | port-on-demand (lives in `text_analysis.py:530` — pure text) |
| 39 | `list_skills` | state | StateDriver | transform | DROP (use core `plugin.help`) |
| 40 | `get_skill` | state | StateDriver | transform | DROP (use core `develop.reference`) |
| 41 | `count_syllables` | lyric | TextDriver | transform | **[SHIP]** (cluster-4 representative, driver-free) |
| 42 | `analyze_readability` | lyric | TextDriver | transform | port-on-demand |
| 43 | `analyze_rhyme_scheme` | lyric | TextDriver | transform | port-on-demand |
| 44 | `validate_section_structure` | lyric/gates | TextDriver | transform | port-on-demand (also a gate-skill step) |
| 45 | `check_homographs` | lyric | TextDriver | transform | port-on-demand |
| 46 | `scan_artist_names` | lyric | TextDriver | transform | port-on-demand (pre-gen `invoke:` verb) |
| 47 | `check_explicit_content` | lyric | TextDriver | transform | port-on-demand (pre-gen `invoke:` verb) |
| 48 | `extract_distinctive_phrases` | lyric | TextDriver | transform | port-on-demand |
| 49 | `get_lyrics_stats` | lyric | TextDriver | transform | port-on-demand |
| 50 | `check_cross_track_repetition` | lyric | TextDriver+StateDriver | transform | port-on-demand |
| 51 | `check_pronunciation_enforcement` | lyric | TextDriver+StateDriver | transform | port-on-demand (pre-gen `invoke:` verb) |
| 52 | `check_streaming_lyrics` | lyric | TextDriver+StateDriver | transform | port-on-demand (release-qa `invoke:` verb) |
| 53 | `analyze_audio` | audio | AudioDriver | transform | port-on-demand |
| 54 | `analyze_mix_issues` | audio | AudioDriver | transform | port-on-demand |
| 55 | `qc_audio` | audio | AudioDriver | transform | port-on-demand (release-qa `invoke:` verb) |
| 56 | `mono_fold_check` | audio | AudioDriver | effect | port-on-demand |
| 57 | `polish_audio` | audio | AudioDriver | effect | port-on-demand |
| 58 | `polish_album` | audio | AudioDriver | effect | port-on-demand (pipeline) |
| 59 | `master_audio` | audio | AudioDriver | effect | port-on-demand |
| 60 | `master_album` | audio | AudioDriver | effect | **[SHIP]** (cluster-5 representative, pipeline) |
| 61 | `master_with_reference` | audio | AudioDriver | effect | port-on-demand |
| 62 | `polish_and_master_album` | audio | AudioDriver | effect | port-on-demand (pipeline) |
| 63 | `fix_dynamic_track` | audio | AudioDriver | effect | port-on-demand |
| 64 | `reset_mastering` | audio | AudioDriver/StateDriver | effect | port-on-demand |
| 65 | `render_codec_preview` | audio | AudioDriver | effect | port-on-demand |
| 66 | `measure_album_signature` | audio | AudioDriver | transform | port-on-demand |
| 67 | `album_coherence_check` | audio | AudioDriver | transform | port-on-demand |
| 68 | `album_coherence_correct` | audio | AudioDriver | effect | port-on-demand |
| 69 | `generate_promo_videos` | media | AudioDriver | effect | port-on-demand |
| 70 | `generate_album_sampler` | media | AudioDriver | effect | port-on-demand |
| 71 | `transcribe_audio` | media | AudioDriver | effect | **[SHIP]** (cluster-6 representative; `processing/sheet_music.py`; AnthemScore shell-out) |
| 72 | `prepare_singles` | media | AudioDriver | effect | port-on-demand (`processing/sheet_music.py`) |
| 73 | `create_songbook` | media | AudioDriver | effect | port-on-demand (`processing/sheet_music.py`) |
| 74 | `db_init` | promo | DBDriver | effect | port-on-demand |
| 75 | `db_sync_album` | promo | DBDriver+StateDriver | effect | port-on-demand |
| 76 | `db_create_tweet` | promo | DBDriver | effect | **[SHIP]** (cluster-7 representative; psycopg2-shaped fake) |
| 77 | `db_update_tweet` | promo | DBDriver | effect | port-on-demand |
| 78 | `db_delete_tweet` | promo | DBDriver | effect | port-on-demand |
| 79 | `db_list_tweets` | promo | DBDriver | transform | port-on-demand |
| 80 | `db_search_tweets` | promo | DBDriver | transform | port-on-demand |
| 81 | `db_get_tweet_stats` | promo | DBDriver | transform | port-on-demand |
| 82 | `get_promo_status` | promo | StateDriver | transform | port-on-demand |
| 83 | `get_promo_content` | promo | StateDriver | transform | port-on-demand |
| 84 | `get_streaming_urls` | promo | StateDriver | transform | port-on-demand |
| 85 | `update_streaming_url` | promo | StateDriver | effect | port-on-demand (writes URL into markdown state) |
| 86 | `verify_streaming_urls` | promo | CloudDriver | effect | **[SHIP]** (cluster-7 cloud companion; stdlib `urllib`, runs in CI) |
| 87 | `publish_sheet_music` | promo | CloudDriver | effect | port-on-demand (`processing/sheet_music.py:435`, boto3/R2 — stub) |
| 88 | `run_pre_generation_gates` | gates | StateDriver+`gate`+`elicit` | act | **[SHIP]** (cluster-8 representative: computed `gate.check` + terminal `elicit`) |
| 89 | `validate_album_structure` | gates | StateDriver | act | port-on-demand (feeds `release-qa` skill) |

**Coverage proof:** all 89 rows have a taxonomic home (cluster + driver + role);
zero are unmodelable. 14 rows are flagged **[SHIP]** (the representative slice);
5 are **DROP** (obsolete or shadow a core capability — Open Q #5); the remaining
70 are **port-on-demand** (the pattern is proven, the verb is mechanical to add).

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Partially implemented (kept as example — single verb only)

### Done
- `examples/music.py` exists with `MusicCapability(CapabilityBase)`, the `conceptualize` act verb, `ALBUM_CONCEPT_SKILL` (7-phase hard-gated skill), `ALBUM_TYPES` enum, and `music_ontology` (`OntologyExtension`). `examples/music.py:5,22,46,58,65`
- The `extra_capabilities` loading path works: `Engine(..., extra_capabilities=[MusicCapability.as_capability()])` registers the capability and merges the ontology. Confirmed by `tests/test_agency.py:1116-1153`.
- The `album-concept` skill walks to a hard gate (Phase 7 `elicit`). `tests/test_agency.py:1116`.
- The `Album` node type and closed `type` enum reject unknown values (polka test). `tests/test_agency.py:1150`.

### Still to implement
- `examples/music_drivers.py` — the five `Boundary`/`Driver` protocols (`StateDriver`, `TextDriver`, `AudioDriver`, `DBDriver`, `CloudDriver`) do not exist; no file at that path.
- `examples/test_music_capability.py` — does not exist; no dedicated music-capability test file.
- All 13 additional representative verbs (cluster 2-8): `create_album`, `find_album`, `get_album_progress`, `count_syllables`, `master_album`, `transcribe_audio`, `db_create_tweet`, `verify_streaming_urls`, `run_pre_generation_gates`, etc. — none implemented.
- The expanded `OntologyExtension` (Track/Tweet/Idea/SheetMusic nodes, closed enums, `pre-generation` and `release-qa` gated skill phase-graphs, artefact schemas for `promo-copy`/`mastering-report`/`lyric-report`).
- Hard blocker: Spec 002 (`DriverRegistry`) is still `status: draft` and never shipped (`agency/capabilities/` has no registry mechanism beyond `extra_capabilities`). Per the spec's own Done-When #1, 007 is BLOCKED on 002 for any driver-backed verb.

### Refinement needed (given later specs)
- Spec 016 (`capability-authoring-doctrine`) introduced `develop.scaffold_capability` and `plugin.lint_capability` in block mode (`develop.py:249`, `plugin.py:279`). Any implementation of 007 should use the scaffold-first workflow and carry `# agency-scaffold: v1` markers.
- Spec 020 (central `.agency/session.db`) changes where the graph is stored; the `StateDriver` storage-model question (Open Q #6 — filesystem vs graph) is now more squarely resolved in favor of graph-canonical with `apply=True` export (the pattern Spec 010 adopted).
- The overview (`Plan/000-overview.md`) classifies 007 as "Wave-1 backlog — revisit when canon needs new ground," not in-flight. No active push is planned.

### Evidence
- code: `examples/music.py` (single verb + skill + ontology); no `examples/music_drivers.py` or `examples/test_music_capability.py`
- tests: `tests/test_agency.py:1116-1153` (music capability smoke test — conceptualize + album-concept skill walk + type enum rejection)
- commits/notes: `5a4263b` "move the music domain demo out of core into examples/" (the original extraction); Spec 002 (`Plan/002-boundary-driver-protocol/spec.md`) remains `status: draft`, confirming the driver injection blocker is unresolved.

## Followup — Implementation Status (2026-06-07)

**Verdict:** Partially implemented — the clustered Driver contract + provenance moat
are proven; computed-gate wiring + the long-tail remain.

### Done (PR — first slice)
- **`examples/music_drivers.py`** — the five Spec-002 `Driver` protocols (Option B,
  typed named methods): `StateDriver` · `TextDriver` · `AudioDriver` · `DBDriver` ·
  `CloudDriver`, each with a deterministic FAKE (no ffmpeg / Postgres / R2 / network).
  `fake_drivers()` is the test bundle.
- **`examples/music.py`** — `MusicCapability` grows from 1 → **9 representative verbs**
  across 8 clusters, each role-tagged + reaching external work via
  `self.ctx.get_driver(name)` (NO direct ffmpeg/Postgres/R2): `conceptualize` (act,
  kept) · `count_syllables` (transform, driver-free) · `lyric_report` (act, TextDriver)
  · `master_album` (effect, AudioDriver) · `catalogue_status` (transform, DBDriver) ·
  `promo_copy` (act) · `set_album_status` (effect, StateDriver) · `publish_asset`
  (effect, CloudDriver → typed `DEPENDENCY_MISSING` when unconfigured). Every verb
  returns a Spec-001 `ToolResult`; act verbs set `data['artefact']` → PRODUCES edge.
- **Ontology** extended in a single `OntologyExtension`: Album (status/genre/slug/
  target_lufs) + Track (status/slug) + Tweet/Idea/SheetMusic nodes, the closed
  `(Album,status)`/`(Track,status)` enums, the `pre-generation` + `release-qa` gated
  skill phase-graphs, and the `promo-copy`/`mastering-report`/`lyric-report` artefact
  schemas. Merges strictly onto core; `conceptualize` + `album-concept` preserved.
- **007 modifies NO file under `agency/`** — drivers inject via the Spec-002
  `DriverRegistry` (`Engine(..., drivers=fake_drivers())`), proving the drop-in claim.
- **The provenance moat** (the headline, net-new vs bitwize): every verb records an
  `Invocation` that SERVES the intent; `master_album`/`lyric_report`/`promo_copy`
  record a PRODUCES artefact — a release audit is one traversal.
- **Tests** — `tests/test_music_capability.py` (9, CI-collected): discovery + ontology
  merge, deterministic driver-free transform, AudioDriver routing + provenance, DBDriver
  cursor, TextDriver lyric-report, state/promo clusters, typed INVALID_ARGUMENT +
  DEPENDENCY_MISSING failures, and missing-driver degradation. Full suite 913 passed.

### Done — computed gates (2026-06-07, Done-When (e))
- `music.pregen_check(lifecycle_id, concept_ready, rights_clear)` + `music.release_check
  (lifecycle_id, album)` [effect] compute the predicate (release_check reads track
  statuses via the DBDriver) and call `gate.check` — a fail records BLOCKED_ON, flips
  the lifecycle to `input-required`, and returns a typed `GATE_FAILED`; a pass records
  PASSED. The terminal human "ship it?" stays an `elicit`/`lifecycle_gate` (the gated
  skills' hard final phase). `tests/test_music_capability.py` (+3). Music is now 11
  verbs / 9 clusters.

### Done — long-tail clusters (2026-06-07)
- 5 more representative verbs reach the 12–16 target — now **15 verbs / 11 clusters**:
  `transcribe_sheet` (sheet-music, act via AudioDriver → `sheet-music` artefact) ·
  `analyze_mix` (mixing, transform via AudioDriver, decidable loudness findings) ·
  `verify_streaming` (streaming, transform via CloudDriver `url_head`) · `capture_idea`
  (ideas, effect — records an `Idea` graph node + StateDriver persist) · `music_health`
  (health, transform, driver-free). `tests/test_music_capability.py` (+3).

### Still
- The remaining bitwize tools (video sampler, promo videos, maintenance, …) stay
  "covered-by-pattern, port-on-demand" — each is a verb in one of the proven clusters,
  not a new contract.
