"""Spec 151 — Codes-coverage CLI shim.

The audit core moved to :mod:`agency._codes_coverage` (Spec 151 Slice 3) so
the engine can import it without the dev-only ``scripts/`` tree. This shim
re-exports every public name and keeps the ``main()`` CLI so
``python -m scripts.check_codes_coverage`` / ``python scripts/check_codes_coverage.py``
behave exactly as before.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from agency._codes_coverage import (  # noqa: F401  (re-export surface)
    CallSiteClass, FileLoc, CallSiteResult, CoverageReport,
    OffenderBaselineEntry, OffenderRegressionReport,
    classify_failure_call, audit_source, audit_tree,
    codes_namespace_members, load_codes_baseline,
    compare_offenders_to_baseline,
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
