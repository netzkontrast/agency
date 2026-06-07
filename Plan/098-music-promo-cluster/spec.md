---
spec_id: "098"
slug: music-promo-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "095", "096", "097", "093"]
affects:
  - agency/capabilities/music/clusters/promo.py
  - agency/capabilities/music/drivers.py        # CloudDriver(boto3) extensions
  - agency/capabilities/music/ontology.py       # promo artefact schemas
  - agency/capabilities/music/data/templates/   # promo platform templates
  - tests/test_music_promo.py
domain: music / promo / publishing
wave: 7
parent_spec: "093"
---

# Spec 098 — Music Promo Cluster

## Why

The promo cluster is the **CloudDriver-boto3 + LLM-driver showcase**: promo
copy synthesis (currently rule-based in bitwize; optionally `llm`-driver-routed
in agency via Spec 092 G3), promo video render (delegated to AudioDriver), and
R2/S3 publishing (boto3).

bitwize ships ~10 promo tools: promo-writer (rule-based templating), promo-reviewer
(advisory), promo-director (orchestrator), cloud-uploader (R2/S3 publish),
generate_promo_videos (video render — already in 096 audio), publish_sheet_music
(R2 publish). 098 consolidates them.

This cluster's load-bearing piece is the **`publish_asset` verb**: a single,
uniform "ship an artefact to the cloud" boundary that all promo workflows
converge on. Sheet music, promo videos, master WAVs, album art — all go
through `publish_asset` via the boto3 half of CloudDriver. R2/S3 is the
backend; the test fake records the upload manifest.

## Done When

- [ ] **Verbs ship:** **10 user-facing + 1 composite gate verb = 11
  registered** (Codex P2 iteration 6 — `promo_review_gate` is required for
  the `promo-pass` skill walk), covering all bitwize promo + cloud tools.
- [ ] **CloudDriver(boto3) extended** with 4 new methods; in-memory dict-backed
  fake covers all of them; `r2_put` already exists from 007.
- [ ] **Artefact schemas added:** `promo-copy` (kept from 007),
  `published-asset`, `promo-album-package`, `social-post`.
- [ ] **Walkable skill: `promo-pass`** — 5-phase workflow per platform (draft
  → review → asset-attach → schedule → publish).
- [ ] **Walkable skill: `release-publish`** — 4-phase workflow (gather-assets
  → upload → catalogue-update → announce).
- [ ] **Platform templates** under `data/templates/`: X (280-char), Threads
  (500-char), Instagram (caption + media), TikTok (description + hashtags),
  Bluesky (300-char).
- [ ] **`scripts/test-cap music_promo`** Green; runs in < 8 seconds with ZERO
  network/boto3 binary required.
- [ ] **No regression on `promo_copy`, `publish_asset`** (preserved from 007).
- [ ] **`TODO.md` updated;** parent (093) row notes child shipped.

## Verb manifest

| # | Verb | Role | Driver | bitwize tool absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `promo_copy` | act | StateDriver (+optional LLMDriver) | promo-writer skill | kept from 007 |
| 2 | `promo_review` | transform | TextDriver | promo-reviewer skill | rule-based scoring |
| 3 | `publish_asset` | effect | CloudDriver | `r2_put` (general purpose) | kept from 007 |
| 4 | `publish_sheet_music` | effect | CloudDriver | `publish_sheet_music` | sheet-music-specific wrapper |
| 5 | `upload_promo_video` | effect | CloudDriver | (split from cloud-uploader) | promo-video-specific wrapper |
| 6 | `r2_delete` | effect | CloudDriver | (new — cleanup) | retracts a published asset |
| 7 | `r2_list` | transform | CloudDriver | (new — inventory) | lists by prefix |
| 8 | `generate_album_sampler` | effect | AudioDriver | `generate_album_sampler` | delegates to 096 audio |
| 9 | `prepare_singles` | effect | AudioDriver+StateDriver | `prepare_singles` | delegates to 096 audio |
| 10 | `release_package` | act | StateDriver | (composite — gathers all release artefacts) | kept-conceptual; act verb that records `release-package` artefact |

**Total: 10 verbs covering 10 bitwize tools (sampler/singles delegate to 096
audio but live conceptually with release).**

**Internal composite gate verb** (Codex P2 iteration 6 — registered, but
called only by walkable skill phase; counted in 093's gate-verb column for
098):

| # | Verb | Role | Composes | Called by skill |
|---|---|---|---|---|
| G1 | `promo_review_gate` | effect | `promo_review` scoring + platform-limit check + gate.check (BLOCKED_ON if review score below threshold) | `promo-pass` phase 2 |

**Done-When implication:** the cluster ships **10 user + 1 gate = 11
registered verbs**. Without it, the `promo-pass` review phase crashes at
"unknown verb".

## Design

### CloudDriver(boto3) method delta

```python
class CloudDriver(Boundary):
    # existing 007 methods preserved
    def url_head(self, url: str) -> int: ...      # stdlib half
    def r2_put(self, key: str, body: bytes,
               content_type: str = "") -> dict: ...  # boto3 half (kept from 007)

    # new methods (098)
    def r2_get(self, key: str) -> bytes | None: ...
    def r2_delete(self, key: str) -> None: ...
    def r2_list(self, prefix: str = "") -> list[dict]: ...
    def r2_presigned_url(self, key: str, expires_s: int = 3600) -> str: ...
```

The fake uses a dict-backed in-memory store keyed by R2 key; `r2_presigned_url`
returns a deterministic stub URL (`https://r2-fake/{key}?expires={...}`).

### LLMDriver wiring for promo copy (optional)

```python
# In clusters/promo.py:
@verb(role="act")
def promo_copy(self, album: str, platform: str = "x",
               variant: str = "default") -> ToolResult:
    """..."""
    state = self.ctx.get_driver("music_state")
    template = state.read_data("template", f"{platform}.yaml")
    album_data = state.find_album(album)[0]   # via 094

    # Path A (default — rule-based, no LLM dependency):
    body = template["pattern"].format(
        album=album_data["title"],
        theme=album_data["theme"],
        track_count=len(album_data["tracks"]),
    )

    # Path B (LLM-enhanced synthesis when usable — see Codex P2 below).
    # IMPORTANT (Codex P2 iteration 5): Engine ALWAYS registers an `llm`
    # driver per Spec 092 G3, so `DriverMissing` never fires. The default
    # `LLMClient.decide()` raises `RuntimeError` when `OPENROUTER_API_KEY`
    # is unset, and the API expects a non-empty `options` list (free-form
    # = ["free-form"] sentinel, not None). Catch the broad failure surface
    # so the rule-based body stays as the default-install behavior promised
    # in 093's deployment plan.
    try:
        llm = self.ctx.get_driver("llm")
        decision = llm.decide(
            prompt=f"Write a {platform} promo for {album_data['title']} "
                   f"(theme: {album_data['theme']}). Match this style: "
                   f"{template['style_examples']}",
            options=["free-form"],   # non-empty per LLMClient contract
        )
        body = decision.get("choice", body)        # falls through if no choice
    except (DriverMissing, RuntimeError, KeyError, ValueError,
            TimeoutError, OSError):
        # Codex P2 iteration 6: TimeoutError is a subclass of OSError, NOT
        # RuntimeError. The failure-mode table promises a fallback on LLM
        # timeout; include both to honor it. OSError also covers socket
        # errors and other I/O issues from the LLM transport.
        pass    # rule-based body stands; default install has no API key

    return ToolResult.success(data={"result": body, "artefact": {
        "kind": "promo-copy", "album": album, "platform": platform,
        "body": body}})
```

Tests pin Path A (no LLM driver bound); a separate test binds a fake `llm`
driver and verifies Path B.

### Primary actors (panel-added, iteration 1 / Cockburn)

- `promo-pass` — **Primary actor: agent** (drafts platform-specific copy);
  human-curator OR `promo_review_gate` (computed) acts as filter at phase 2.
- `release-publish` — **Primary actor: agent** (gathers + uploads); human-
  curator signs off on the announcement at phase 4.

### Failure modes (panel-added, iteration 1 / Nygard)

| Boundary call | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| R2 unreachable | `botocore.exceptions.EndpointConnectionError` | raises `BoundaryFailed` | `ToolResult.failure(BOUNDARY_FAILED, "R2 unreachable")` |
| R2 auth failed | `botocore.exceptions.ClientError` (403/401) | raises | `ToolResult.failure(DEPENDENCY_MISSING, "R2 auth failed — check `[music-cloud]` config")` |
| R2 bucket missing | `ClientError` (NoSuchBucket) | raises | `ToolResult.failure(BOUNDARY_FAILED, "bucket missing")` |
| Quota exceeded | `ClientError` (QuotaExceeded) | raises | `ToolResult.failure(BOUNDARY_FAILED, "R2 quota exceeded")` |
| `boto3` not installed (default install, no `[music-cloud]` extra) | deferred import — CloudDriver `__init__` (the boto3 half) does NOT touch boto3; `r2_put`/`r2_get`/`r2_delete`/`r2_list` lazy-import on first call. The stdlib half (`url_head`) stays available regardless. | first R2 method call raises `DependencyMissing("[music-cloud]")` | per-verb `ToolResult.failure(DEPENDENCY_MISSING, "boto3 not installed — install agency[music-cloud]")`. Lifecycle/lyrics/research/gates/streaming-verify (stdlib half) stay usable; only R2 upload verbs degrade. |
| LLM driver decide() times out | `TimeoutError` | raises | promo_copy falls back to Path A (rule-based) silently, records warning |

### Walkable skill: `promo-pass`

```python
PROMO_PASS_SKILL = {
    "name": "promo-pass",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft",
         "produces": ["promo_body", "promo_platform"]},
        {"index": 2, "name": "review",
         "produces": ["review_score"],
         "gate": "computed", "gate_verb": "music.promo_review_gate"},
        {"index": 3, "name": "asset-attach",
         "produces": ["asset_url"]},
        {"index": 4, "name": "schedule",
         "produces": ["scheduled_at_set"]},
        {"index": 5, "name": "publish",
         "produces": ["posted"]},
    ],
}
```

### Walkable skill: `release-publish`

```python
RELEASE_PUBLISH_SKILL = {
    "name": "release-publish",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "gather",
         "produces": ["all_release_assets_listed"]},
        {"index": 2, "name": "upload",
         "produces": ["all_assets_published"]},
        {"index": 3, "name": "catalogue",
         "produces": ["streaming_urls_recorded"]},
        {"index": 4, "name": "announce",
         "produces": ["announcement_drafted"],
         "gate": "hard"},   # elicit — human approves the announcement
    ],
}
```

### Artefact schemas added

```python
PROMO_ARTEFACTS = [
    "promo-copy",            # kept from 007
    "published-asset",       # new — one per R2 upload
    "promo-album-package",   # new — composite of release assets
    "social-post",           # new — record of a scheduled/posted social post
]
```

### Platform templates

```
agency/capabilities/music/data/templates/
├── x.yaml              # 280-char Twitter/X
├── threads.yaml        # 500-char Threads
├── instagram.yaml      # caption + media
├── tiktok.yaml         # description + hashtags
└── bluesky.yaml        # 300-char Bluesky
```

Each carries: `pattern` (template string), `style_examples` (LLM hint),
`max_chars` (validation), `media_required` (bool).

## Test plan

```python
# tests/test_music_promo.py — ~14 tests
def test_promo_cluster_discovers_all_verbs(): ...
def test_promo_copy_renders_template_without_llm_driver(): ...
def test_promo_copy_uses_llm_driver_when_bound(): ...
def test_promo_review_scores_against_platform_limits(): ...
def test_publish_asset_records_published_asset_artefact(): ...
def test_publish_sheet_music_routes_to_r2_put_with_sheet_metadata(): ...
def test_upload_promo_video_routes_to_r2_put_with_video_metadata(): ...
def test_r2_delete_removes_from_fake_store(): ...
def test_r2_list_returns_keys_by_prefix(): ...
def test_release_package_act_verb_records_artefact_with_all_assets(): ...
def test_generate_album_sampler_delegates_to_audio_cluster(): ...
def test_promo_pass_skill_walks_through_review_gate(): ...
def test_release_publish_skill_pauses_on_announce_hard_gate(): ...
def test_promo_verb_fails_typed_when_cloud_driver_missing_for_publish(): ...
```

## Open questions

1. **LLM driver for promo copy: default on or off?** Off (Path A, rule-based) —
   matches bitwize behaviour; LLM is opt-in via driver registration. Followup
   spec may flip the default after 092 G3's `llm_select` Matcher ships.
2. **R2 vs S3 — single CloudDriver or split?** Single. R2's S3-API compatibility
   means one driver covers both; the production binding decides the endpoint.
3. **Asset retraction (`r2_delete`) — verb or admin-only?** Verb — the agent
   needs a way to un-publish a bad asset before re-publishing. Provenance
   records both the publish and the delete.
4. **`release_package` as a verb or a skill phase?** Verb (act) — it produces
   a record-of-truth artefact that the release skill's final phase consumes.
   The skill orchestrates; the verb produces.

## Followup

(Populated when the PR ships.)
