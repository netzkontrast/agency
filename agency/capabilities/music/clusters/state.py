# agency-scaffold: v1
"""music state cluster — album-status persistence + Spec-115 production binding.

``set_album_status`` (the StateDriver banner verb from 007) plus the Spec 115
production-binding verbs (get_config · load_override · get_reference ·
format_clipboard) that read config / reference / clipboard state. Relocated
VERBATIM from ``_main.py`` per Spec 094 design §"Module layout" (Spec 286
Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult, Codes

from ..ontology import ALBUM_STATUS
from ._base import _MusicBase


class StateCluster(_MusicBase):
    # ───────── state cluster (effect via StateDriver) ─────────
    @verb(role="effect")
    def set_album_status(self, album: str, status: str) -> ToolResult:
        """Persist an album's production status via the StateDriver (effect).

        Inputs: album, status (one of the Album.status enum).
        Returns: ``{album, status}`` echoing the persisted record.
        chain_next: ``release-qa``.
        """
        if status not in ALBUM_STATUS:
            return ToolResult.failure(Codes.INVALID_ARGUMENT,
                                      f"status {status!r} not in {sorted(ALBUM_STATUS)}")
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
        state.put(f"album:{album}", {"album": album, "status": status})
        return ToolResult.success(data={"album": album, "status": status})

    # Spec 115 — production binding: 4 NEW verbs covering bitwize's config /
    # override / reference / clipboard MCP functions.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def get_config(self) -> ToolResult:
        """Read the music capability's loaded config (transform).

        Resolves from `.agency/music-config.yaml`, `~/.agency-music/config.yaml`,
        or `$AGENCY_MUSIC_HOME/config.yaml` per Spec 115 resolution order.

        Inputs: none.
        Returns: ``{config: dict}`` in the bitwize-compatible config shape.
        chain_next: ``music.create_album`` once artist + paths are confirmed.
        """
        from ..config import MusicConfig
        cfg = MusicConfig.load()
        return ToolResult.success(data={"config": cfg.as_dict()})

    @verb(role="transform")
    def load_override(self, name: str) -> ToolResult:
        """Load a user-authored override file from the configured overrides dir (transform).

        Bitwize lets users author `{overrides}/<name>.md` (e.g. a custom
        pronunciation guide or genre tweak); this verb reads it. Empty/missing
        returns ``found=False``.

        Inputs: name (override file stem).
        Returns: ``{name, found, body}``.
        chain_next: pass ``body`` into a verb that takes the override as input.
        """
        from pathlib import Path
        from ..config import MusicConfig
        cfg = MusicConfig.load()
        overrides_dir = Path(cfg.overrides).expanduser()
        candidate = overrides_dir / f"{name}.md"
        if not candidate.is_file():
            return ToolResult.success(data={"name": name, "found": False,
                                            "body": ""})
        return ToolResult.success(data={"name": name, "found": True,
                                        "body": candidate.read_text(encoding="utf-8")})

    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def get_reference(self, slug: str,
                       kind: str = "reference", *, state) -> ToolResult:
        """Read a bundled reference / data file by slug (transform).

        Resolves from ``agency/capabilities/music/data/<kind>/<slug>``.
        ``kind`` defaults to ``reference`` (the 50 bitwize docs ported in
        Spec 094). Pass ``kind="genres"`` to read a genre file.

        Inputs: slug (path or filename under data/<kind>/), kind (default ``reference``).
        Returns: ``{kind, slug, body}``.
        chain_next: feed the body into a verb that needs the doctrine context.
        """
        # `_require_drv` is on CapabilityBase — the prior `hasattr` guard was
        # unreachable. Always route via StateDriver.read_data (both
        # FakeStateDriver and FileStateDriver implement it).
        return ToolResult.success(data=state.read_data(kind=kind, slug=slug))

    @verb(role="transform")
    def format_clipboard(self, text: str,
                          format: str = "lyrics") -> ToolResult:
        """Format text for clipboard paste into Suno / other generation services (transform).

        Bitwize ports ``format_for_clipboard`` from the content handler. Two
        shapes:

        - ``lyrics``: strips bracketed section tags + trailing whitespace
          (Suno-safe).
        - ``style-prompt``: collapses multi-line prompts to single-line + cap
          at 200 chars (Suno style-prompt limit).

        Inputs: text, format (one of ``lyrics`` / ``style-prompt``; default ``lyrics``).
        Returns: ``{text, format, char_count}``.
        chain_next: paste into Suno / external generation service.
        """
        if format == "style-prompt":
            single = " ".join(text.split())
            if len(single) > 200:
                single = single[:200].rsplit(" ", 1)[0] + "…"
            return ToolResult.success(data={"text": single,
                                            "format": "style-prompt",
                                            "char_count": len(single)})
        # Default = lyrics: strip [Verse 1]-style tags + collapse blank runs
        out_lines = []
        prev_blank = False
        for ln in text.splitlines():
            s = ln.strip()
            if s.startswith("[") and s.endswith("]"):
                continue
            if not s:
                if prev_blank:
                    continue
                prev_blank = True
            else:
                prev_blank = False
            out_lines.append(ln)
        cleaned = "\n".join(out_lines).strip()
        return ToolResult.success(data={"text": cleaned, "format": "lyrics",
                                        "char_count": len(cleaned)})
