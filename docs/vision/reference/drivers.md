# Drivers & Boundaries — external I/O (Spec 002)

<!-- doc-source: agency/capability.py agency/engine.py examples/music_drivers.py Plan/002-boundary-driver-protocol/spec.md -->
<!-- doc-hash: c1824bdfeb79c188 -->

Every external side-effect (git, Jules, audio, a DB, object storage, the token counter,
the Skills API) is isolated behind a **Driver** so it can be stubbed deterministically in
tests and swapped in production. Spec 002 unifies what used to be six ad-hoc injector
seams into one named table.

## The contract (`agency/capability.py`)

- **`Boundary`** — a marker `Protocol` for any injected external dependency. Memberless
  + `runtime_checkable` → a no-op `isinstance`, so concrete clients need **no** base-class
  change.
- **`Driver`** — a `Boundary` reached **by name**. **Option B**: there is no uniform
  `dispatch(op)`. Each driver keeps its own typed, named methods (`AudioDriver
  .read_loudness(path)`, `GitClient.branch(...)`); the uniform contract is the RETURN
  TYPE (`ToolResult`), produced by the *wrapping verb*.
- **`DriverRegistry`** — `register(name, driver)` · `register_factory(name, factory)`
  (Spec 286-A2 — a lazy default, materialized on first `get`) · `get(name)` (raises
  `DriverMissing`, a `LookupError`) · `has(name)` · `names()` · `backend(name)` /
  `readiness(name)` (health probes).

## How the engine wires it

`Engine.__init__` builds one `DriverRegistry` registering the **nine** core boundaries —
`runner` · `jules` · `vcs` · `embedder` · `web_search` · `token_counter` ·
`skills_client` · `llm` (the LLM-decider, Spec 092 G3) · `anthropic` (the AnthropicDriver,
Spec 147) — as **lazy factories** (explicit injection wins; an unused boundary is never
constructed) and derives
`Registry.injectors` from it (one source of truth, so `inject=[…]` + `ctx.client` keep
working). A `drivers={…}` kwarg lets a host register **a domain cluster with no new
Engine kwarg and no new injectors key**.

## A verb reaching a driver

```python
@verb(role="effect")
def master_album(self, album, path, target_lufs=-14.0) -> ToolResult:
    try:
        audio = self.ctx.get_driver("music_audio")
    except DriverMissing:
        return ToolResult.failure("DEPENDENCY_MISSING", "no audio driver")
    loud = audio.read_loudness(path)          # typed, named method
    audio.run_ffmpeg([...])                    # no direct ffmpeg in the verb
    return ToolResult.success(data={"result": …, "artefact": {…}})
```

## The worked example: `agency/capabilities/music/drivers.py`

The music capability ships five Driver protocols — `State` · `Text` · `Audio` · `DB` ·
`Cloud` — each with a deterministic **fake** (`fake_drivers()`), so the whole music
domain runs with no ffmpeg / Postgres / R2 / network. The host passes real drivers via
`Engine(..., drivers={"music_audio": RealAudioDriver(), …})`. This proves the drop-in
claim: the music capability edits **no** file under `agency/`. See
[../../guide/capabilities.md](../../guide/capabilities.md) (`music`) + Spec 007.
