"""Spec 158 Slice 1 — capability scaffold-marker presence audit.

Walks `agency/capabilities/*` and reports which capabilities carry the
`# agency-scaffold: v1` marker on their main file. The Spec 024 block-mode
lint applies uniformly only when every capability declares the marker;
a NEW capability without it is a doctrine drift (the marker is the
trigger for the lint pass).

Pattern matches the Spec 146 Slice 2.2 + Spec 151 Slice 2 baseline gates:
typed shapes, pure functions, CLI exit code 0/1, line-shift robust by
keying on capability name not file line.

Slice 2+ — `scripts/check-drift` integration so a new capability without
the marker fails CI immediately; today the audit is informational.
"""
from __future__ import annotations

import argparse
import enum
from dataclasses import dataclass, field
from pathlib import Path


MARKER = "# agency-scaffold: v1"


class MarkerStatus(str, enum.Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNKNOWN = "unknown"   # e.g. capability folder with no _main.py


@dataclass(frozen=True)
class CapabilityMarker:
    """One capability's marker status."""

    name: str
    path: str
    status: MarkerStatus


@dataclass
class ScaffoldReport:
    """The audit payload. `fraction` = present / (present + missing);
    `unknown` not counted in denominator."""

    markers: list[CapabilityMarker] = field(default_factory=list)

    @property
    def present(self) -> list[CapabilityMarker]:
        return [m for m in self.markers if m.status == MarkerStatus.PRESENT]

    @property
    def missing(self) -> list[CapabilityMarker]:
        return [m for m in self.markers if m.status == MarkerStatus.MISSING]

    @property
    def unknown(self) -> list[CapabilityMarker]:
        return [m for m in self.markers if m.status == MarkerStatus.UNKNOWN]

    @property
    def fraction(self) -> float:
        denom = len(self.present) + len(self.missing)
        if denom == 0:
            return 1.0
        return len(self.present) / denom


def audit_tree(root: Path) -> ScaffoldReport:
    """Walk `<root>/capabilities/*`; classify each capability's main file."""
    rep = ScaffoldReport()
    caps_dir = Path(root) / "capabilities"
    if not caps_dir.exists():
        return rep
    for entry in sorted(caps_dir.iterdir()):
        if entry.name.startswith("_"):
            continue
        if entry.is_file() and entry.suffix == ".py":
            text = _safe_read(entry)
            status = MarkerStatus.PRESENT if MARKER in text else MarkerStatus.MISSING
            rep.markers.append(CapabilityMarker(
                name=entry.stem, path=str(entry), status=status))
        elif entry.is_dir():
            main = entry / "_main.py"
            if not main.exists():
                rep.markers.append(CapabilityMarker(
                    name=entry.name, path=str(main),
                    status=MarkerStatus.UNKNOWN))
                continue
            text = _safe_read(main)
            status = MarkerStatus.PRESENT if MARKER in text else MarkerStatus.MISSING
            rep.markers.append(CapabilityMarker(
                name=entry.name, path=str(main), status=status))
    return rep


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency",
                        help="agency package root (default: agency)")
    parser.add_argument("--strict", action="store_true",
                        help="promote to gate: exit 1 if any capability lacks the marker")
    args = parser.parse_args(argv)
    rep = audit_tree(Path(args.root))
    print(f"scaffold-marker coverage: {rep.fraction:.3f}  "
          f"({len(rep.present)}/{len(rep.present) + len(rep.missing)} "
          f"capabilities marked; {len(rep.unknown)} unknown)")
    if rep.missing:
        print(f"  missing ({len(rep.missing)}):")
        for m in rep.missing:
            print(f"    {m.name}  ({m.path})")
    if rep.unknown:
        print(f"  unknown ({len(rep.unknown)} — capability folder lacks _main.py):")
        for m in rep.unknown:
            print(f"    {m.name}  ({m.path})")
    if args.strict and rep.missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
