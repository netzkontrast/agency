---
name: ponytail
description: Use when building or reviewing agency's frugal discipline (Spec 332) or multi-agent self-installer (Spec 333), or when you want the minimal-code "lazy senior dev" reflex as a reference. Ponytail is the upstream MIT skill agency redeveloped natively as `frugal`; this skill is the reference pointer — the engine implementation stays native (no vendored ponytail source).
---

# Ponytail — the lazy-senior-dev minimal-code reference

> *"He says nothing. He writes one line. It works."* Ponytail is the upstream
> open-source skill (MIT, [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail))
> that agency **redeveloped natively** as the `frugal` core discipline (Spec 332)
> and the multi-agent self-installer (Spec 333). This skill is the **reference**,
> not a re-vendoring: agency's core stays native (`agency/_frugal.py`), and
> ponytail's name/source was deliberately removed from the engine (commit
> `ec98a87`). Reach for the reference; never copy its source back into the engine.

## When to use

- Building or reviewing **Spec 332** (frugal core discipline — `agency/_frugal.py`)
  or **Spec 333** (multi-agent installer — `install.surface_card` + adapters).
- You want the minimal-code reflex itself: *write only what the task needs.*

## The discipline (the canon agency renders from `_frugal.py`)

**Lazy means efficient, not careless. The best code is the code never written.**
Before writing any code, stop at the **first rung that holds**:

1. Does this need to exist at all? (YAGNI)
2. Stdlib already does it? Use it.
3. Native platform feature covers it? Use it (`<input type="date">` over a picker lib).
4. Already-installed dependency solves it? Use it — never add one for a few lines.
5. Can it be one line? One line.
6. Only then: the minimum code that works.

**The safety floor — never simplified away** (the substrings the drift + gate
tests pin, `agency/_frugal.py:SAFETY_FLOOR_MARKERS`): input validation at trust
boundaries · error handling that prevents data loss · security · accessibility ·
anything explicitly requested. *Frugal code without its check is unfinished* —
non-trivial logic leaves ONE runnable check behind.

**Marker convention:** deliberate simplifications get a `# frugal:` comment naming
the ceiling + upgrade path (ponytail's `ponytail:` → agency's `# frugal:`).

## Where the reference lives (durable, in-repo)

- `Plan/done/332-frugal-core-discipline/reference/DISCIPLINE.md` — the discipline design.
- `Plan/done/333-multi-agent-installer/reference/INSTALLER.md` — the installer design
  (one source → many agents' native formats: `.cursor/rules/`, `.windsurf/rules/`,
  `.clinerules/`, `.kiro/steering/`, `AGENTS.md`, `.github/copilot-instructions.md`).
- Upstream (full source, 14-agent installer, benchmarks): the GitHub repo above —
  clone it as scratch reference; do not commit its source into agency.

## The rule (why this is a pointer, not a port)

Agency implements the discipline **from first principles** as a core feature with
agency-native mechanism — the M2 per-verb envelope stamp (`prefix.frugal`) and the
M1 hook injection have no upstream analogue; they exist because agency has a wire
envelope and a hook layer. Study ponytail for the *pattern*; ship agency's own.
