"""Command line: ``python -m local_estimator <demo|estimate|describe|bundle>``. Run from the repo root (parent of this folder)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .loaders import load_measurements, load_specs
from .pricebook import PriceBook
from .quote import EstimateResult, estimate
from .report import render_bid_text, render_json, render_material_csv
from .spec_text import extract_specs_from_text

PKG = Path(__file__).resolve().parent
DATA = PKG / "data"


def _run(args: argparse.Namespace) -> EstimateResult:
    measurements, warnings = load_measurements(args.measurements)
    if args.specs:
        specs = load_specs(args.specs)
    elif args.spec_text:
        specs = extract_specs_from_text(Path(args.spec_text).read_text(encoding="utf-8"))
        warnings.append(f"specs were parsed from free text ({len(specs)} found) - review them against the spec book")
    else:
        raise SystemExit("error: give --specs (CSV/JSON table) or --spec-text (plain-text spec)")
    if not specs:
        warnings.append("no specifications found - nothing can be priced")
    result = estimate(
        args.project,
        measurements,
        specs,
        pricebook=PriceBook.load(args.pricebook) if args.pricebook else None,
        markup_percent=args.markup_percent,
        labor_rate=args.labor_rate,
        contingency_percent=args.contingency_percent,
        apply_scope_filter=not args.no_scope_filter,
        extra_warnings=warnings,
    )
    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "bid.txt").write_text(render_bid_text(result), encoding="utf-8")
        (out / "estimate.json").write_text(render_json(result), encoding="utf-8")
        (out / "material_list.csv").write_text(render_material_csv(result), encoding="utf-8")
        print(f"wrote {out}/bid.txt, estimate.json, material_list.csv", file=sys.stderr)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m local_estimator", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_estimate_args(p: argparse.ArgumentParser, required: bool) -> None:
        p.add_argument("--measurements", required=required, help="takeoff CSV/JSON (see data/measurements_template.csv)")
        p.add_argument("--specs", help="spec table CSV/JSON (see data/specs_example.csv)")
        p.add_argument("--spec-text", help="plain-text spec to parse (best effort)")
        p.add_argument("--pricebook", help="price book JSON; default = built-in prices")
        p.add_argument("--project", default="Untitled Project")
        p.add_argument("--markup-percent", type=float, default=0.0, help="material markup, e.g. 15")
        p.add_argument("--labor-rate", type=float, default=65.0, help="$/hour")
        p.add_argument("--contingency-percent", type=float, default=10.0)
        p.add_argument("--no-scope-filter", action="store_true", help="price everything, skip company exclusions")
        p.add_argument("--out-dir", help="write bid.txt, estimate.json, material_list.csv here")
        p.add_argument("--json", action="store_true", help="print JSON instead of the text bid")

    add_estimate_args(sub.add_parser("estimate", help="price a takeoff"), required=True)
    sub.add_parser("demo", help="run on the bundled sample data (smoke test)")
    sub.add_parser("describe", help="print the machine-readable manifest (JSON)")
    sub.add_parser("bundle", help="print docs + manifest + all source as ONE text file to paste into an AI chat")
    args = parser.parse_args(argv)

    if args.cmd == "describe":
        from .manifest import render_manifest

        print(render_manifest())
        return 0
    if args.cmd == "bundle":
        from .manifest import render_bundle

        print(render_bundle())
        return 0
    if args.cmd == "demo":
        args = parser.parse_args(
            ["estimate", "--measurements", str(DATA / "measurements_template.csv"), "--specs", str(DATA / "specs_example.csv"),
             "--pricebook", str(DATA / "pricebook_sample.json"), "--project", "Demo Project", "--markup-percent", "15"]
        )
    result = _run(args)
    print(render_json(result) if args.json else render_bid_text(result))
    return 1 if result.is_draft else 0  # non-zero exit = needs review (lets scripts and bots detect a draft)
