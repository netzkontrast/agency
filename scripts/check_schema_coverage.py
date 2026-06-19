"""Spec 153 — schema-coverage CLI shim.

The audit core moved to :mod:`agency._schema_coverage` (Spec 153 Slice 3)
so the engine can import it without the dev-only ``scripts/`` tree. This shim
re-exports the public names and keeps the ``main()`` CLI unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from agency._schema_coverage import (  # noqa: F401  (re-export surface)
    CoverageReport, SchemaRegressionReport, schema_paths, schema_labels,
    audit_schemas, engine_loaded_schema_titles, truly_inline_schemas,
    load_schema_baseline, compare_uncovered_to_baseline,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="repo subdirectory holding `capabilities/` "
                             "(default: agency)")
    parser.add_argument("--baseline", default=None,
                        help="path to baseline file listing KNOWN-uncovered "
                             "labels; Slice 2 gate flags only NEW uncovered "
                             "labels (Spec 054 drift pattern)")
    parser.add_argument("--strict", action="store_true",
                        help="promote to gate: with --baseline, exit 1 on "
                             "new uncovered labels; without, exit 1 on any "
                             "uncovered label")
    args = parser.parse_args(argv)
    # Boot the engine just long enough to read the live ontology labels
    # AND the merged schema dict (which we then split into truly-
    # inline-only — see `truly_inline_schemas`).
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        merged = dict(e.ontology.schemas)
    finally:
        e.memory.close()
    root = Path(args.root)
    inline = truly_inline_schemas(root, merged)
    rep = audit_schemas(root, ontology_labels=ontology,
                        ontology_schemas=inline)
    print(f"schema coverage: {rep.coverage_fraction:.3f}  "
          f"({len(rep.covered)}/{rep.total_ontology_labels} labels covered; "
          f"{len(rep.uncovered)} uncovered; "
          f"{len(rep.non_node_schemas)} artefact/payload schemas)")
    if rep.uncovered:
        print(f"  uncovered ({len(rep.uncovered)}):")
        for label in sorted(rep.uncovered)[:20]:
            print(f"    {label}")
        if len(rep.uncovered) > 20:
            print(f"    ... and {len(rep.uncovered) - 20} more")
    if rep.non_node_schemas:
        print(f"  non-node schemas ({len(rep.non_node_schemas)}; "
              f"validate artefact/wire-payload shapes): "
              f"{', '.join(sorted(rep.non_node_schemas)[:10])}")
    if args.strict:
        if args.baseline is not None:
            baseline = load_schema_baseline(Path(args.baseline))
            res = compare_uncovered_to_baseline(rep, baseline)
            if res.new_uncovered:
                print(f"\nREGRESSION: {len(res.new_uncovered)} new "
                      f"uncovered labels not in baseline:")
                for label in sorted(res.new_uncovered):
                    print(f"  + {label}")
            if res.fixed_uncovered:
                print(f"\nFIXED: {len(res.fixed_uncovered)} baseline "
                      f"entries now covered — trim from {args.baseline}:")
                for label in sorted(res.fixed_uncovered):
                    print(f"  - {label}")
            return 0 if res.ok else 1
        return 0 if not rep.uncovered else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
