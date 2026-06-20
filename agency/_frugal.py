"""Frugal core discipline — Spec 332 Slice 1 (level + render).

Agency's own minimal-code reflex (a redevelopment, not a port): a ladder + a
non-negotiable safety floor. The active **level** resolves via Spec 334 config
(``frugal.level``: env ``AGENCY_FRUGAL_LEVEL`` → ``.agency/config.yaml`` →
``full``). ``render()`` emits the discipline at a level (the FULL projection for
the M1 session injection; the COMPACT projection for the M2 per-verb envelope
stamp). ``off`` emits nothing.

M1 (session injection) + M2 (envelope stamp) are later slices; this slice is the
content + level state they both consume.
"""
from __future__ import annotations

from . import _config

LEVELS = ("off", "lite", "full", "ultra")
DEFAULT_LEVEL = "full"
SESSION_INJECT = ("off", "discipline", "full")   # SessionStart inject detail (Spec 348)

# The safety-floor invariants — pinned verbatim so no level (bar off) and no
# Spec 333 adapter copy can silently drop one (the Slice-4 gate asserts these).
SAFETY_FLOOR_MARKERS = (
    "input validation at trust boundaries",
    "prevents data loss",
    "security",
    "accessibility",
)

_LADDER = (
    "1. Does this need to exist at all? (YAGNI) — speculative need = skip it.\n"
    "2. Stdlib does it? Use it.\n"
    "3. Native platform feature covers it? Use it.\n"
    "4. Already-installed dependency solves it? Use it; never add one for a few lines.\n"
    "5. Can it be one line? One line.\n"
    "6. Only then: the minimum code that works."
)

_FLOOR = (
    "Never simplify away: input validation at trust boundaries, error handling "
    "that prevents data loss, security measures, accessibility basics, and "
    "anything explicitly requested. Frugal code without its check is unfinished "
    "— non-trivial logic leaves ONE runnable check behind."
)

_LEVEL_NOTE = {
    "lite": "Build what's asked; name the leaner alternative in one line.",
    "full": "The ladder enforced; stdlib + native first; shortest diff.",
    "ultra": "Deletion before addition; ship the one-liner and challenge the rest.",
}


def _norm(level: str | None) -> str:
    """Coerce to a known level; an invalid/empty value falls back to the default."""
    lvl = str(level or "").strip().lower()
    return lvl if lvl in LEVELS else DEFAULT_LEVEL


def normalized(level: str | None) -> str:
    """Public: coerce a level string to a known level (invalid/empty → default).
    The one public normalizer so callers don't import the private ``_norm``."""
    return _norm(level)


def frugal_level(*, path: str | None = None) -> str:
    """The active level (env > config.yaml > full), validated."""
    return _norm(_config.config_get("frugal.level", path=path))


def set_frugal_level(level: str, *, path: str | None = None) -> str:
    """Persist the level to the config (durable across processes); returns it."""
    norm = _norm(level)
    _config.config_set("frugal.level", norm, path=path)
    return norm


def render(level: str | None = None, *, mode: str = "full") -> str:
    """The discipline text at ``level`` (defaults to the active level). ``off`` →
    empty. ``mode="full"`` = the whole ladder + floor (M1 session inject);
    ``mode="compact"`` = a one-line, token-bounded stamp that still names the
    floor (M2 per-verb envelope prefix)."""
    lvl = _norm(level) if level is not None else frugal_level()
    if lvl == "off":
        return ""
    if mode == "compact":
        return (f"frugal[{lvl}]: YAGNI→stdlib→native→dep→1-line · "
                "floor: validate/secure/a11y never cut")
    return (
        f"FRUGAL DISCIPLINE — level: {lvl}\n"
        "Write only what the task needs; frugal means efficient, not careless.\n\n"
        "The ladder — stop at the first rung that holds:\n"
        f"{_LADDER}\n\n"
        f"{_LEVEL_NOTE.get(lvl, '')}\n\n"
        f"Safety floor: {_FLOOR}"
    )


def help_text(level: str | None = None) -> str:
    """The COMPLETE frugal help (the ponytail-help info): the discipline (ladder +
    floor) + the levels table + how to switch + what's configurable. This is the
    SessionStart inject when ``frugal.session_inject=full`` (the default, Spec 348)
    — the agent's full initial briefing, not just the one-line stamp."""
    lvl = _norm(level) if level is not None else frugal_level()
    if lvl == "off":
        return ""
    rows = list(_LEVEL_NOTE.items()) + [("off", "disable the discipline injection.")]
    levels = "\n".join(f"  {k:<5} — {v}" for k, v in rows)
    return (
        f"{render(lvl, mode='full')}\n\n"
        f"Levels (active: {lvl}):\n{levels}\n"
        "Switch the level — set AGENCY_FRUGAL_LEVEL (env) or frugal.level in "
        ".agency/config.yaml; resolution env > config > full.\n"
        "Inject detail — frugal.session_inject = off | discipline | full (this card)."
    )


def session_inject_text(level: str | None = None, *, path: str | None = None) -> str:
    """The SessionStart inject content (Spec 348 mandatory wiring), configurable via
    ``frugal.session_inject``: ``off`` → nothing · ``discipline`` → the ladder +
    floor (the M1 render) · ``full`` → the complete help card (default). Never
    raises — a bad/missing config degrades to the full help."""
    lvl = _norm(level) if level is not None else frugal_level()
    if lvl == "off":
        return ""
    try:
        what = _config.config_get("frugal.session_inject", path=path)
        what = str(what).strip().lower() if what else "full"
    except Exception:
        what = "full"
    if what == "off":
        return ""
    if what == "discipline":
        return render(lvl, mode="full")
    return help_text(lvl)


def safety_floor_intact(render_fn=None) -> dict:
    """Spec 332 Slice 4 — the safety-floor gate predicate. The floor is a
    first-class clause no level (bar ``off``) can strip: at every non-off level
    the FULL render must carry every ``SAFETY_FLOOR_MARKER`` and the COMPACT
    render must name the floor. Returns ``{ok, checked, findings}`` —
    gate-recordable via ``gate.check(passed=result['ok'])``. ``render_fn`` is the
    render under test (defaults to the live one; injectable so a stripped render
    is detectable)."""
    r = render_fn or render
    checked = [lvl for lvl in LEVELS if lvl != "off"]
    findings: list[dict] = []
    for level in checked:
        full = r(level, mode="full")
        for marker in SAFETY_FLOOR_MARKERS:
            if marker not in full:
                findings.append({"level": level, "mode": "full", "missing": marker})
        if "floor" not in r(level, mode="compact"):
            findings.append({"level": level, "mode": "compact", "missing": "floor"})
    return {"ok": not findings, "checked": checked, "findings": findings}


def frugal_prefix(level: str | None = None, *, path: str | None = None) -> dict:
    """Spec 332 M2 — the per-verb stamp as a prefix fragment:
    ``{"frugal": <compact render>}`` when stamping is active, else ``{}``.

    ``off`` level OR ``frugal.stamp_every_verb=false`` → empty. The value is
    byte-stable at a fixed level (the wrapping driver's prefix cache stays warm;
    a level change is an intentional one-time bust). Never raises — a stamp must
    never break a verb (the assumption-guard / M1 degrade precedent)."""
    try:
        stamp = _config.config_get("frugal.stamp_every_verb", path=path)
        if isinstance(stamp, str):
            stamp = stamp.strip().lower() not in ("false", "0", "no", "off", "")
        if not stamp:
            return {}
        text = render(level, mode="compact")
    except Exception:
        return {}
    return {"frugal": text} if text else {}


# The frugal config section (Spec 334 registry) — default level full.
_config.register_config_section("frugal", [
    _config.ConfigKey("level", "AGENCY_FRUGAL_LEVEL", DEFAULT_LEVEL,
                      "minimal-code discipline level", enum=LEVELS),
    _config.ConfigKey("stamp_every_verb", "AGENCY_FRUGAL_STAMP", True,
                      "M2: stamp the discipline on every verb's envelope prefix"),
    _config.ConfigKey("session_inject", "AGENCY_FRUGAL_SESSION_INJECT", "full",
                      "SessionStart inject detail: off|discipline|full (Spec 348)",
                      enum=SESSION_INJECT),
])
