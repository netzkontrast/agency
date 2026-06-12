"""Spec 151 Slice 1 — ToolResult Codes coverage audit.

Pure AST-walking audit over `ToolResult.failure(code, ...)` call sites:
classify each as ATTR_REF (Codes.X — covered, when X is a real Codes
member), STRING_LITERAL (offender), EXPR (computed code — opaque but
counted against coverage), or UNKNOWN. Compose into a `CoverageReport`
with fraction + offenders + orphan-Codes detection.

The Slice 1 surface ships:
- `classify_failure_call(call_node) -> ClassifyResult` returning
  `(class, literal, code_name)` where `code_name` is the attribute
  name for ATTR_REF (e.g. `"NOT_FOUND"` for `Codes.NOT_FOUND`).
- `audit_source(src, path) -> list[CallSiteResult]` (per-file walk with
  alias detection for `from ... import ToolResult as TR`).
- `audit_tree(root) -> CoverageReport` (orphan check only counts the
  ATTR_REF code_names already classified — no re-walk that picks up
  unrelated `Codes.X` references).
- `codes_namespace_members() -> set[str]`
- CLI: `python -m scripts.check_codes_coverage [--root agency] [--floor 0.5]`

Slice 2+: WARN→error promotion, monotone floor invariant gate
(`live.codes_coverage.fraction >= last_floor`), shared `Codes` namespace
audit for cross-capability drift, backfill of literal-string call sites.

Per CLAUDE.md rule 8: the report shape carries RELATIONSHIPS (fraction,
subset checks), not pinned counts.

Codex review (PR #126):
- EXPR sites are now in the fraction denominator so an EXPR-only tree
  reports 0.0 (not the misleading 1.0 the original "trivially covered"
  shortcut produced). The empty-tree convention `total_failure_sites == 0
  → 1.0` stands.
- `Codes.NOT_FOND` (a typo) is no longer classified as covered: ATTR_REF
  is gated on the attribute name being a real `Codes` member; typo'd
  attribute references fall through to STRING_LITERAL with
  `literal = "Codes.<typo>"`.
- `from agency.toolresult import ToolResult as TR; TR.failure(...)`
  is now detected via a per-file ImportFrom-alias scan; the audit no
  longer silently drops aliased call sites.
- Orphan detection counts ONLY code_names already classified as
  ATTR_REF — a `Codes.X == "y"` comparison or constant reference
  elsewhere in the same file no longer rescues a dead Codes member
  from the orphan list.
"""
from __future__ import annotations

import argparse
import ast
import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path


class CallSiteClass(str, enum.Enum):
    ATTR_REF = "attr_ref"            # Codes.X (where X is a real Codes member) — covered
    STRING_LITERAL = "string_literal"  # 'literal' or Codes.<typo> — offender
    EXPR = "expr"                    # computed — counted against coverage (not opaque-OK)
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FileLoc:
    path: str
    line: int                                                     # 1-indexed


@dataclass(frozen=True)
class CallSiteResult:
    loc: FileLoc
    classification: CallSiteClass
    literal: str = ""                                             # filled when classification == STRING_LITERAL
    code_name: str = ""                                           # attribute name for ATTR_REF (e.g. "NOT_FOUND")


@dataclass
class CoverageReport:
    """The Slice 1 audit payload. Slice 2 adds `floor`, `monotone_ok`."""

    total_failure_sites: int = 0
    covered_sites: int = 0
    offenders: list[CallSiteResult] = field(default_factory=list)
    orphan_codes: set[str] = field(default_factory=set)
    expr_sites: int = 0                                           # opaque — IN the denominator (Codex review)
    unknown_sites: int = 0                                        # **payload / no code arg — IN the denominator

    @property
    def fraction(self) -> float:
        """Coverage fraction = covered_sites / (covered + offenders + expr + unknown).

        Empty tree (`total_failure_sites == 0`) is `1.0` by convention —
        trivially covered. An EXPR-only or UNKNOWN-only tree is **0.0**,
        not the misleading `1.0` the previous "trivially covered"
        shortcut produced — `Codes.X` typed paths must be proven, not
        inferred from the absence of literal strings.

        UNKNOWN sites are e.g. `ToolResult.failure(**payload)` where the
        code argument is unpacked — the runtime code value is opaque to
        the lint, so the site is counted against coverage just like an
        EXPR site (Codex review).
        """
        denom = (self.covered_sites + len(self.offenders)
                 + self.expr_sites + self.unknown_sites)
        if denom == 0:
            return 1.0
        return self.covered_sites / denom


# ── AST walker ──────────────────────────────────────────────────────────────
# The audit only treats a `<name>.failure(...)` call as a ToolResult
# failure when `<name>` was IMPORTED FROM `agency.toolresult` in the same
# file — that way a third-party / fixture class also named `ToolResult`
# doesn't trip the audit. Same rule for `Codes` aliases so the classifier
# honors `from agency.toolresult import Codes as C; ToolResult.failure(
# C.NOT_FOUND, ...)`.
_AGENCY_TOOLRESULT_MODULES = frozenset({
    "agency.toolresult",                                          # absolute import
    ".toolresult",                                                # relative from agency/
    "..toolresult",                                               # nested module relative
})


def _module_matches_toolresult(node: ast.ImportFrom) -> bool:
    """Recognize an ImportFrom whose source is the agency.toolresult module
    in any of the relative / absolute forms the codebase uses."""
    name = node.module or ""
    if name in _AGENCY_TOOLRESULT_MODULES:
        return True
    # Relative imports show up with level > 0 and `module` set to the
    # tail. `from ..toolresult import ...` → level=2, module="toolresult".
    if node.level and name == "toolresult":
        return True
    return False


def _agency_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Return `(toolresult_names, codes_names)` — the per-module names
    that resolve to `agency.toolresult.ToolResult` and `Codes` respectively.

    Only ImportFrom statements that target `agency.toolresult` count —
    a third-party `ToolResult` (e.g. a vendored helper, an unrelated lib)
    is no longer auto-aliased.
    """
    toolresult: set[str] = set()
    codes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and _module_matches_toolresult(node):
            for alias in node.names:
                if alias.name == "ToolResult":
                    toolresult.add(alias.asname or alias.name)
                elif alias.name == "Codes":
                    codes.add(alias.asname or alias.name)
    return toolresult, codes


def _is_toolresult_failure(call: ast.Call, *, aliases: set[str]) -> bool:
    """Recognize `<alias>.failure(...)` where `<alias>` resolves to
    `ToolResult` in this module (via direct import or `as` alias)."""
    fn = call.func
    if not isinstance(fn, ast.Attribute) or fn.attr != "failure":
        return False
    parent = fn.value
    if isinstance(parent, ast.Name) and parent.id in aliases:
        return True
    return False


def classify_failure_call(
    call: ast.Call, *, codes_members: set[str] | None = None,
    codes_aliases: set[str] | None = None,
) -> tuple[CallSiteClass, str, str]:
    """Classify the FIRST positional / `code` kwarg of a failure call.

    Returns `(classification, literal, code_name)`. `literal` is the
    source text for STRING_LITERAL (or `"Codes.<typo>"` for an
    attribute that doesn't name a real `Codes` member); `code_name` is
    the attribute name for ATTR_REF (e.g. `"NOT_FOUND"`).

    When `codes_members` is given, an ATTR_REF whose attr name is NOT
    in that set is reclassified as STRING_LITERAL — a typo like
    `Codes.NOT_FOND` raises AttributeError at runtime and must be
    surfaced as an offender, not silently counted as covered.

    `codes_aliases` enumerates the per-module names that resolve to
    `agency.toolresult.Codes` — `Codes` itself plus any
    `from agency.toolresult import Codes as <X>` alias. When None, the
    default `{"Codes"}` is used (the common case).
    """
    # An explicit empty `codes_aliases` set means the audited file did not
    # import `Codes`. Codex review on PR #126: do NOT fall back to the
    # bare `{"Codes"}` because that hides NameErrors at runtime — surface
    # the broken path as a STRING_LITERAL offender (see the
    # `code_arg.value.id == "Codes"` branch below).
    if codes_aliases is None:
        codes_aliases = {"Codes"}
    code_arg: ast.AST | None = None
    if call.args:
        code_arg = call.args[0]
    else:
        for kw in call.keywords:
            if kw.arg == "code":
                code_arg = kw.value
                break
    if code_arg is None:
        return CallSiteClass.UNKNOWN, "", ""
    if isinstance(code_arg, ast.Constant) and isinstance(code_arg.value, str):
        return CallSiteClass.STRING_LITERAL, code_arg.value, ""
    if isinstance(code_arg, ast.Attribute) and isinstance(code_arg.value, ast.Name):
        receiver = code_arg.value.id
        attr_name = code_arg.attr
        if receiver in codes_aliases:
            if codes_members is not None and attr_name not in codes_members:
                # Typo — surface as an offender so the AttributeError doesn't
                # hide behind an inflated "covered" count.
                return CallSiteClass.STRING_LITERAL, f"Codes.{attr_name}", ""
            return CallSiteClass.ATTR_REF, "", attr_name
        # Receiver looks like the user intended `Codes.X` (literally
        # named `Codes`) but the file did NOT import it. At runtime this
        # raises NameError. Surface as an offender so the broken failure
        # path is visible in the audit, not silently mis-classified as
        # EXPR (which would understate the severity).
        if receiver == "Codes":
            return CallSiteClass.STRING_LITERAL, f"Codes.{attr_name} (not imported)", ""
    # Anything else (Name, BinOp, Call, conditional expr, …) is computed.
    return CallSiteClass.EXPR, "", ""


def audit_source(
    src: str, path: str, *, codes_members: set[str] | None = None,
) -> list[CallSiteResult]:
    """Walk a single source file's AST; return every failure call site.

    `codes_members` defaults to the live `Codes` namespace; pass a fixed
    set in tests to keep them hermetic against namespace evolution.

    Files that do not import `ToolResult` from `agency.toolresult` are
    skipped entirely — a third-party `ToolResult.failure(...)` call site
    no longer trips the audit and no longer inflates the offender count.
    """
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    if codes_members is None:
        codes_members = codes_namespace_members()
    tr_aliases, codes_aliases = _agency_aliases(tree)
    if not tr_aliases:
        # File never imports agency.toolresult.ToolResult — skip.
        return []
    out: list[CallSiteResult] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_toolresult_failure(node, aliases=tr_aliases):
            # Pass the per-file `codes_aliases` set verbatim — if the
            # file did NOT import `Codes`, the set is EMPTY and any
            # `Codes.X` literal is reclassified as STRING_LITERAL
            # because `Codes` is an undefined name at runtime
            # (NameError). Codex review: do NOT replace empty with
            # `{"Codes"}` here — that fallback hid broken failure paths.
            cls, lit, code_name = classify_failure_call(
                node, codes_members=codes_members,
                codes_aliases=codes_aliases)
            out.append(CallSiteResult(
                loc=FileLoc(path=path, line=node.lineno),
                classification=cls,
                literal=lit,
                code_name=code_name,
            ))
    return out


def audit_tree(root: Path) -> CoverageReport:
    """Walk every `*.py` under `root`; compose the CoverageReport."""
    root = Path(root)
    members = codes_namespace_members()
    rep = CoverageReport()
    all_sites: list[CallSiteResult] = []
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        try:
            src = py.read_text(encoding="utf-8")
        except OSError:
            continue
        all_sites.extend(audit_source(src, path=str(py), codes_members=members))
    for site in all_sites:
        if site.classification == CallSiteClass.ATTR_REF:
            rep.covered_sites += 1
        elif site.classification == CallSiteClass.STRING_LITERAL:
            rep.offenders.append(site)
        elif site.classification == CallSiteClass.EXPR:
            rep.expr_sites += 1
        elif site.classification == CallSiteClass.UNKNOWN:
            rep.unknown_sites += 1
    rep.total_failure_sites = len(all_sites)
    # Orphan check (invariant c): a documented Codes member is an
    # orphan iff NO ATTR_REF call site in the audited tree carries that
    # exact attribute name. The previous pass re-walked every file and
    # picked up unrelated `Codes.X` references (e.g. `if x == Codes.Y`
    # comparisons), so a dead member could escape detection by appearing
    # near another covered failure path. Counting only the ATTR_REF
    # code_names already classified above closes that hole.
    used: set[str] = {s.code_name for s in all_sites
                      if s.classification == CallSiteClass.ATTR_REF
                      and s.code_name}
    rep.orphan_codes = members - used
    return rep


# ── Codes namespace introspection ──────────────────────────────────────────
def codes_namespace_members() -> set[str]:
    """Read the live `Codes` class members (uppercase constants only)."""
    from agency.toolresult import Codes
    return {n for n in dir(Codes)
            if n.isupper() and not n.startswith("_")
            and isinstance(getattr(Codes, n), str)}


# ── Slice 2: offender baseline + WARN→error gate ──────────────────────────
@dataclass(frozen=True)
class OffenderBaselineEntry:
    """One known-historical STRING_LITERAL offender. The Slice 2 gate
    flags REGRESSIONS only (Spec 054 drift pattern; mirrors Spec 146
    Slice 2.2 baseline structure)."""

    path: str
    line: int
    literal: str


@dataclass
class OffenderRegressionReport:
    """Slice 2 gate payload — `ok` flips False on ANY new offender;
    fixed offenders surfaced so the baseline can be trimmed."""

    new_offenders: list[CallSiteResult] = field(default_factory=list)
    fixed_offenders: list[OffenderBaselineEntry] = field(default_factory=list)
    ok: bool = True


def load_codes_baseline(path: Path) -> set[OffenderBaselineEntry]:
    """Parse `<path>:<line>:<literal>` lines into a set. Blank +
    `#`-comment lines are skipped. Malformed line → ValueError so a
    typo can't silently bypass the gate."""
    path = Path(path)
    if not path.exists():
        return set()
    out: set[OffenderBaselineEntry] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 2)
        if len(parts) != 3:
            raise ValueError(
                f"baseline line must be `<path>:<line>:<literal>`; got {raw!r}")
        p, ln, lit = parts
        try:
            ln_i = int(ln)
        except ValueError as e:
            raise ValueError(
                f"baseline line number must be int; got {raw!r}") from e
        out.add(OffenderBaselineEntry(path=p, line=ln_i, literal=lit))
    return out


def compare_offenders_to_baseline(
    rep: CoverageReport,
    baseline: set[OffenderBaselineEntry],
) -> OffenderRegressionReport:
    """Set difference: live offenders not in baseline = REGRESSION;
    baseline entries with no matching live offender = FIXED."""
    live: set[tuple[str, int, str]] = {
        (o.loc.path, o.loc.line, o.literal) for o in rep.offenders}
    base: set[tuple[str, int, str]] = {
        (b.path, b.line, b.literal) for b in baseline}
    new_keys = live - base
    fixed_keys = base - live
    new_offenders = sorted(
        (o for o in rep.offenders
         if (o.loc.path, o.loc.line, o.literal) in new_keys),
        key=lambda o: (o.loc.path, o.loc.line, o.literal))
    fixed_offenders = sorted(
        (b for b in baseline
         if (b.path, b.line, b.literal) in fixed_keys),
        key=lambda b: (b.path, b.line, b.literal))
    return OffenderRegressionReport(
        new_offenders=new_offenders,
        fixed_offenders=fixed_offenders,
        ok=(len(new_offenders) == 0),
    )


# ── CLI entry ──────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="root directory to walk for *.py (default: agency)")
    parser.add_argument("--floor", type=float, default=0.0,
                        help="minimum coverage fraction (informational; "
                             "Slice 2 uses --baseline + --strict for the gate)")
    parser.add_argument("--baseline", default=None,
                        help="path to baseline file enumerating known "
                             "historical STRING_LITERAL offenders (Spec 151 "
                             "Slice 2 drift gate); only regressions exit 1")
    parser.add_argument("--strict", action="store_true",
                        help="promote to gate: with --baseline, exit 1 on "
                             "new offenders; without, exit 1 on any offender")
    args = parser.parse_args(argv)
    rep = audit_tree(Path(args.root))
    # CLI denominator and breakdown MUST match CoverageReport.fraction's
    # math: covered + offenders + expr + unknown. Codex review on PR #126:
    # an UNKNOWN-only tree previously printed "0/0 covered" hiding the
    # call sites entirely; now `unknown` appears in the breakdown.
    denom = (rep.covered_sites + len(rep.offenders)
             + rep.expr_sites + rep.unknown_sites)
    print(f"codes coverage: {rep.fraction:.3f}  "
          f"({rep.covered_sites}/{denom} covered; "
          f"{len(rep.offenders)} offenders; {rep.expr_sites} computed; "
          f"{rep.unknown_sites} unknown)")
    if rep.offenders:
        print(f"  offenders ({len(rep.offenders)}):")
        for o in rep.offenders[:20]:
            print(f"    {o.loc.path}:{o.loc.line}  {o.literal!r}")
        if len(rep.offenders) > 20:
            print(f"    ... and {len(rep.offenders) - 20} more")
    if rep.orphan_codes:
        print(f"  orphan Codes ({len(rep.orphan_codes)}): "
              f"{', '.join(sorted(rep.orphan_codes))}")
    if args.strict:
        if args.baseline is not None:
            baseline = load_codes_baseline(Path(args.baseline))
            res = compare_offenders_to_baseline(rep, baseline)
            if res.new_offenders:
                print(f"\nREGRESSION: {len(res.new_offenders)} new "
                      f"offenders not in baseline:")
                for o in res.new_offenders:
                    print(f"  + {o.loc.path}:{o.loc.line}  {o.literal!r}")
            if res.fixed_offenders:
                print(f"\nFIXED: {len(res.fixed_offenders)} baseline "
                      f"entries no longer present — trim from "
                      f"{args.baseline}:")
                for b in res.fixed_offenders:
                    print(f"  - {b.path}:{b.line}  {b.literal!r}")
            return 0 if res.ok else 1
        return 0 if not rep.offenders else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
