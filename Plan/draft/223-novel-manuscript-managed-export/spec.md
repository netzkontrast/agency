---
spec_id: "223"
slug: novel-manuscript-managed-export
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "107"
depends_on: ["107", "124", "147", "209", "146", "154", "217", "218"]
vision_goals: [8, 7]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_manuscript_managed.py
---

# Spec 223 — novel manuscript Managed-Agent export

## Why

Spec 107 (novel-manuscript) ships the FormatDriver; Spec 124 added the
FakeFormatDriver + 3 export verbs, deferring the production
PandocFormatDriver (weasyprint) to Slice 2. Like the music audio driver
(Spec 209), heavy export (pandoc/weasyprint → EPUB/PDF) can run on a
Managed-Agent sandbox for users without local binaries (Goal 8) — the
zero-install publication path. The FormatDriver boundary already exists.

## Done When

- [ ] **A Managed-Agent FormatDriver** behind the Spec 107 boundary —
      dispatches pandoc/weasyprint export to a session (Spec 147),
      output files return via the session-outputs Files API.
- [ ] **Typed return shape**:
      ```python
      ManuscriptExportResult = {
        "intent_id":      str,
        "work_id":        str,
        "format":         Literal["epub","pdf","docx"],
        "artefact_id":    str,           # FormatArtefact PRODUCES Novel
        "file_handle":    str,           # Spec 154 recall handle for the file bytes
        "size_bytes":     int,
        "backend":        Literal["pandoc-managed","weasyprint-managed",
                                  "pandoc-local","weasyprint-local","fake"],
        "session_id":     str | None,    # Spec 147 managed-agent session
        "duration_ms":    int,
        "refusal":        dict | None,
      }
      ```
- [ ] **Backend selection** is decidable: local binary present → local;
      else `[anthropic]` present + Managed-Agents capable → managed;
      else FakeFormatDriver (CI default).
- [ ] **The FakeFormatDriver stays the CI default** (zero binaries,
      Spec 124).
- [ ] **The export Artefact (Goal 7: files render from the graph)**
      records identically across backends — `artefact_id` resolves to
      the same shape regardless of which backend produced the bytes.
- [ ] **Invariant — backend equivalence.** For a fixture work, exporting
      via Fake vs. managed (mocked) vs. local (mocked) MUST produce
      Artefacts whose `kind`, `format`, `work_id`, and `PRODUCES Novel`
      edges are identical; only `size_bytes` and `backend` differ.
- [ ] **Invariant — file bytes via handle, not inline.** Assert the
      return shape carries `file_handle` AND the bytes are reachable
      via `recall_overflow(file_handle)`; never inline (a 20MB EPUB
      inline would blow the LLM context budget — Spec 146 / 154).
- [ ] **Invariant — session lifecycle.** When `backend` starts with
      `*-managed`, `session_id` is non-null AND a
      `MonitorEvent("session_terminated")` SERVES intent within the
      duration window (no orphaned sessions).
- [ ] **Invariant — duration bound RELATIONAL.** Assert
      `duration_ms <= MAX_EXPORT_MS` (configured tunable per backend,
      not a pinned snapshot).
- [ ] **Failure modes**:
      - `Codes.EXPORT_BACKEND_REFUSAL` from the Managed-Agent
        (pandoc errored inside the sandbox) — error log captured as
        Artefact(kind="export-stderr");
      - `Codes.EXPORT_TIMEOUT` after `MAX_EXPORT_MS` — session
        terminated, partial output discarded;
      - `Codes.EXPORT_FORMAT_UNSUPPORTED` when caller requests a format
        the selected backend can't produce (e.g. weasyprint asked for
        EPUB);
      - `Codes.SESSION_DISPATCH_FAILED` from Spec 147 — falls back to
        local if available, else FakeFormatDriver with a typed warning.
- [ ] Test: the Managed-Agent driver exports an EPUB (mocked session);
      backend equivalence asserted across all 3 paths; session
      lifecycle event chain validated; timeout terminates session;
      Fake fallback unchanged.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a 41-chapter novel ready for export, no local pandoc binary
        installed, ANTHROPIC_API_KEY set, Managed-Agents capable
When:   export_manuscript(work_id=X, format="epub") is called
Then:   backend selection picks "pandoc-managed"
        AND a Spec 147 session is dispatched with the assembled
            manuscript as input
        AND the session runs pandoc inside its sandbox
        AND the EPUB returns via the Files API
        AND result.artefact_id resolves to a FormatArtefact PRODUCES
            Novel{id:X}
        AND result.file_handle reaches the 4.2MB EPUB bytes via
            recall_overflow
        AND a MonitorEvent("session_terminated") SERVES intent fires

Given:  the managed pandoc session fails with a markdown parse error
        on chapter 19
When:   export_manuscript collects the result
Then:   returns Codes.EXPORT_BACKEND_REFUSAL naming chapter 19
        AND an Artefact(kind="export-stderr") captures the pandoc log
        AND the session is terminated cleanly (no orphan)

Given:  caller requests format="epub" on a weasyprint-only backend
When:   the verb validates the request
Then:   returns Codes.EXPORT_FORMAT_UNSUPPORTED naming the mismatch
        AND does NOT dispatch a session (cheap rejection)
```

## Failure modes

External tooling surface: pandoc/weasyprint refusals propagate as
`EXPORT_BACKEND_REFUSAL` with the stderr captured as an Artefact (so
the author can hand-fix the source). Managed-Agent session dispatch
failures propagate as `SESSION_DISPATCH_FAILED` and degrade gracefully
to local (if present) or Fake. Session termination is guaranteed —
even on timeout, the session_terminated MonitorEvent fires so the
graph stays consistent. File bytes NEVER cross back inline; the Spec
154 handle is the contract.

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge.
- Spec 209 (music audio MA driver) is the parallel pattern (Goal 8
  zero-install).
- Spec 124 (format-driver) is the parent boundary.
- Spec 146 (output-prefix) + Spec 154 (overflow capture) — file bytes
  always via handle.
- Spec 217 (build walkable) — calls this verb at the manuscript phase.
- Spec 218 (lifecycle output-budget) — the manuscript assembly that
  feeds this export shares the same overflow envelope.

## Open questions

1. Managed-Agent or document a local-pandoc install? **Recommend**:
   both — local when present (faster, no token cost), Managed-Agent
   as the zero-install fallback; backend selection is decidable.
2. Session reuse across formats (one session, both EPUB and PDF)?
   **Recommend**: yes — Spec 147 session bridge supports multi-tool
   sessions; reuse halves the dispatch latency for "publish all".
3. Per-format MAX_EXPORT_MS? **Recommend**: yes — PDF (weasyprint)
   takes longer than EPUB (pandoc); separate tunables per backend.
4. Should partial exports be retained on timeout? **Recommend**:
   no — partial EPUB/PDF is worse than no output (a half-EPUB confuses
   readers); discard and surface the timeout typed code cleanly.
