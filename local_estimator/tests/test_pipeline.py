import ast
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from local_estimator import (PriceBook, estimate, extract_specs_from_text, load_measurements, load_specs, render_bid_text,
                             render_json, render_material_csv)
from local_estimator.cli import DATA, main
from local_estimator.manifest import render_manifest

PKG = Path(__file__).resolve().parents[1]


class Pipeline(unittest.TestCase):
    def sample(self):
        ms, warns = load_measurements(DATA / "measurements_template.csv")
        return ms, warns, load_specs(DATA / "specs_example.csv"), PriceBook.load(DATA / "pricebook_sample.json")

    def test_sample_prices_cleanly(self):
        ms, warns, specs, pb = self.sample()
        r = estimate("T", ms, specs, pricebook=pb, markup_percent=15, extra_warnings=warns, quote_date="2026-01-01")
        self.assertFalse(r.is_draft, r.warnings)
        self.assertGreater(r.quote.total, 0)
        self.assertAlmostEqual(r.quote.total, r.quote.subtotal * 1.10)
        self.assertEqual(json.loads(render_json(r))["quote"]["quote_number"], "Q20260101")
        self.assertIn("TOTAL", render_bid_text(r))
        self.assertTrue(render_material_csv(r).startswith("category,"))

    def test_draft_banner_when_unpriced(self):
        ms, warns, specs, _ = self.sample()
        r = estimate("T", ms, specs, pricebook=PriceBook({"fiberglass_1.5": 4.0}))
        self.assertTrue(r.is_draft)
        self.assertIn("DRAFT", render_bid_text(r))

    def test_scope_filter_excludes_with_reason(self):
        ms, warns = load_measurements(DATA / "measurements_template.csv")
        ms[0].notes.append("sanitary waste line")
        r = estimate("T", ms, load_specs(DATA / "specs_example.csv"))
        self.assertEqual([e["id"] for e in r.exclusions], [ms[0].item_id])
        self.assertRegex(r.exclusions[0]["reason"], "waste|sanitary")

    def test_bluebeam_style_export(self):
        ms, warns = load_measurements(DATA / "bluebeam_export_example.csv")
        self.assertEqual(warns, [])
        sa, chws, ra = ms
        self.assertEqual((sa.system_type, sa.size, round(sa.length, 2)), ("duct", "24x16", 125.5))
        self.assertEqual((chws.system_type, chws.size), ("pipe", '2"'))
        self.assertEqual(ra.length, 1250.0)

    def test_bad_rows_are_reported_not_dropped_silently(self):
        from local_estimator import measurements_from_rows

        ms, warns = measurements_from_rows([{"id": "A", "type": "duct", "size": "12x12", "length": "lots"},
                                            {"id": "B", "size": "4", "length": "10"}])
        self.assertEqual([m.item_id for m in ms], ["B"])
        self.assertEqual(len(warns), 2)  # bad length + unknown system

    def test_text_spec_extraction(self):
        specs = extract_specs_from_text((DATA / "spec_text_example.txt").read_text())
        self.assertEqual([(s.system_type, s.thickness, s.material, s.location) for s in specs],
                         [("duct", 1.5, "fiberglass", "indoor"), ("pipe", 1.0, "elastomeric", "indoor"),
                          ("pipe", 1.0, "elastomeric", "outdoor")])
        self.assertEqual(specs[1].size_range, "1/2 to 2 inch")

    def test_cli_demo_and_estimate_write_files(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["demo"]), 0)
        with tempfile.TemporaryDirectory() as out, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            main(["estimate", "--measurements", str(DATA / "measurements_template.csv"), "--specs", str(DATA / "specs_example.csv"),
                  "--out-dir", out])
            self.assertTrue({"bid.txt", "estimate.json", "material_list.csv"} <= {p.name for p in Path(out).iterdir()})


class Hygiene(unittest.TestCase):
    def test_imports_are_stdlib_or_package_only(self):
        allowed = getattr(sys, "stdlib_module_names", None)
        if allowed is None:
            self.skipTest("needs Python 3.10+ for sys.stdlib_module_names")
        for path in PKG.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    self.assertTrue(name in allowed or name == "local_estimator", f"{path.name} imports third-party '{name}'")

    def test_committed_manifest_is_current(self):
        self.assertEqual((PKG / "MANIFEST.json").read_text().strip(), render_manifest().strip(),
                         "run: python -m local_estimator describe > local_estimator/MANIFEST.json")


if __name__ == "__main__":
    unittest.main()
