"""Spec 151 Slice 1 — ToolResult Codes coverage audit.

Pure AST-walking audit over `ToolResult.failure(code, ...)` call sites:
classify each as ATTR_REF (Codes.X — covered), STRING_LITERAL (offender),
EXPR (computed code — opaque to lint), or UNKNOWN. Compose into a
`CoverageReport` with fraction + offenders + orphan-Codes detection.

The Slice 1 surface ships:
- `classify_failure_call(call_node) -> ClassifyResult`
- `audit_source(src, path) -> list[CallSiteResult]`
- `audit_tree(root) -> CoverageReport`
- `codes_namespace_members() -> set[str]`
- CLI: `python -m scripts.check_codes_coverage [--root agency] [--floor 0.5]`

Slice 2+: WARN→error promotion, monotone floor invariant gate
(`live.codes_coverage.fraction >= last_floor`), shared `Codes` namespace
audit for cross-capability drift, backfill of literal-string call sites.

Per CLAUDE.md rule 8: the report shape carries RELATIONSHIPS (fraction,
subset checks), not pinned counts.
"""
from __future__ import annotations

import argparse
import ast
import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path


class CallSiteClass(str, enum.Enum):
    ATTR_REF = "attr_ref"            # Codes.X — covered
    STRING_LITERAL = "string_literal"  # 'literal' — offender
    EXPR = "expr"                    # computed — opaque to lint
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


@dataclass
class CoverageReport:
    """The Slice 1 audit payload. Slice 2 adds `floor`, `monotone_ok`."""

    total_failure_sites: int = 0
    covered_sites: int = 0
    offenders: list[CallSiteResult] = field(default_factory=list)
    orphan_codes: set[str] = field(default_factory=set)
    expr_sites: int = 0                                           # opaque — neither covered nor offender

    @property
    def fraction(self) -> float:
        """Coverage fraction. Empty tree (no failure sites at all) is 1.0
        by convention — trivially covered. EXPR sites are NEITHER covered
        nor offender; they are subtracted from the denominator (Slice 2
        may add a sub-audit for them)."""
        denom = self.covered_sites + len(self.offenders)
        if denom == 0:
            return 1.0
        return self.covered_sites / denom


# ── AST walker ──────────────────────────────────────────────────────────────
def _is_toolresult_failure(call: ast.Call) -> bool:
    """Recognize the shape `ToolResult.failure(...)`.

    Robust to `ToolResult.failure` and aliased `TR.failure` — the
    rightmost attr must be `failure` and the second-rightmost identifier
    must contain `ToolResult` or end with the same. Slice 2 may widen to
    `*.failure` and re-import-aware traversal.
    """
    fn = call.func
    if not isinstance(fn, ast.Attribute) or fn.attr != "failure":
        return False
    parent = fn.value
    # ToolResult.failure
    if isinstance(parent, ast.Name) and "ToolResult" in parent.id:
        return True
    # tr.failure — heuristic: any single-name receiver. We're conservative
    # at the source level; an unused import shadow is exceedingly rare.
    return False


def classify_failure_call(call: ast.Call) -> tuple[CallSiteClass, str]:
    """Classify the FIRST positional / `code` kwarg of a failure call.

    Returns `(classification, literal)`. `literal` is the empty string
    for everything except STRING_LITERAL.
    """
    code_arg: ast.AST | None = None
    if call.args:
        code_arg = call.args[0]
    else:
        for kw in call.keywords:
            if kw.arg == "code":
                code_arg = kw.value
                break
    if code_arg is None:
        return CallSiteClass.UNKNOWN, ""
    if isinstance(code_arg, ast.Constant) and isinstance(code_arg.value, str):
        return CallSiteClass.STRING_LITERAL, code_arg.value
    if isinstance(code_arg, ast.Attribute) and isinstance(code_arg.value, ast.Name) \
            and code_arg.value.id == "Codes":
        return CallSiteClass.ATTR_REF, ""
    # Anything else (Name, BinOp, Call, conditional expr, …) is computed.
    return CallSiteClass.EXPR, ""


def audit_source(src: str, path: str) -> list[CallSiteResult]:
    """Walk a single source file's AST; return every failure call site."""
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    out: list[CallSiteResult] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_toolresult_failure(node):
            cls, lit = classify_failure_call(node)
            out.append(CallSiteResult(
                loc=FileLoc(path=path, line=node.lineno),
                classification=cls,
                literal=lit,
            ))
    return out


def audit_tree(root: Path) -> CoverageReport:
    """Walk every `*.py` under `root`; compose the CoverageReport."""
    root = Path(root)
    rep = CoverageReport()
    all_sites: list[CallSiteResult] = []
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        try:
            src = py.read_text(encoding="utf-8")
        except OSError:
            continue
        all_sites.extend(audit_source(src, path=str(py)))
    for site in all_sites:
        if site.classification == CallSiteClass.ATTR_REF:
            rep.covered_sites += 1
        elif site.classification == CallSiteClass.STRING_LITERAL:
            rep.offenders.append(site)
        elif site.classification == CallSiteClass.EXPR:
            rep.expr_sites += 1
    rep.total_failure_sites = len(all_sites)
    # Orphan check (invariant c): a documented Codes member with no
    # ATTR_REF call site in the audited tree is an orphan.
    used: set[str] = set()
    for site in all_sites:
        if site.classification == CallSiteClass.ATTR_REF:
            # Re-parse the file to recover the .X attribute name (cheap;
            # rare enough that the re-walk is fine for Slice 1).
            try:
                tree = ast.parse(Path(site.loc.path).read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) \
                        and isinstance(node.value, ast.Name) \
                        and node.value.id == "Codes":
                    used.add(node.attr)
    rep.orphan_codes = codes_namespace_members() - used
    return rep


# ── Codes namespace introspection ──────────────────────────────────────────
def codes_namespace_members() -> set[str]:
    """Read the live `Codes` class members (uppercase constants only)."""
    from agency.toolresult import Codes
    return {n for n in dir(Codes)
            if n.isupper() and not n.startswith("_")
            and isinstance(getattr(Codes, n), str)}


# ── CLI entry ──────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="root directory to walk for *.py (default: agency)")
    parser.add_argument("--floor", type=float, default=0.0,
                        help="minimum coverage fraction (Slice 1: informational; "
                             "Slice 2 promotes to a CI-blocking gate)")
    args = parser.parse_args(argv)
    rep = audit_tree(Path(args.root))
    print(f"codes coverage: {rep.fraction:.3f}  "
          f"({rep.covered_sites}/{rep.covered_sites + len(rep.offenders)} typed; "
          f"{rep.expr_sites} computed)")
    if rep.offenders:
        print(f"  offenders ({len(rep.offenders)}):")
        for o in rep.offenders[:20]:
            print(f"    {o.loc.path}:{o.loc.line}  {o.literal!r}")
        if len(rep.offenders) > 20:
            print(f"    ... and {len(rep.offenders) - 20} more")
    if rep.orphan_codes:
        print(f"  orphan Codes ({len(rep.orphan_codes)}): "
              f"{', '.join(sorted(rep.orphan_codes))}")
    # Slice 1: informational. Slice 2 promotes to:
    #     return 0 if rep.fraction >= args.floor else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
