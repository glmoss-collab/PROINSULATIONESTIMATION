import math
import unittest

from local_estimator import InsulationSpec, MeasurementItem, PriceBook, PricingEngine
from local_estimator.sizes import parse_length_ft, parse_size, parse_size_range


def duct_spec(**kw):
    base = dict(system_type="duct", size_range="all", thickness=1.5, material="fiberglass", facing="FSK")
    base.update(kw)
    return InsulationSpec(**base)


def duct(size="18x12", length=100.0, **kw):
    return MeasurementItem("D-1", "duct", size, length, kw.pop("location", "indoor"), **kw)


class SizeParsing(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(parse_size("18x12").kind, "rect")
        self.assertEqual(parse_size('1-1/2"').dims, (1.5,))
        self.assertEqual(parse_size("4 inch").dims, (4.0,))
        self.assertIsNone(parse_size("TBD"))

    def test_ranges(self):
        self.assertEqual(parse_size_range("1/2-2 inch"), (0.5, 2.0))
        self.assertEqual(parse_size_range('up to 6"'), (0.0, 6.0))
        self.assertEqual(parse_size_range("over 12 inch")[0], 12.0)
        self.assertIsNone(parse_size_range("all"))

    def test_lengths(self):
        self.assertEqual(parse_length_ft("125.5"), 125.5)
        self.assertEqual(parse_length_ft("1,250 ft"), 1250.0)
        self.assertAlmostEqual(parse_length_ft("125' 6\""), 125.5)
        self.assertAlmostEqual(parse_length_ft("18 in"), 1.5)
        with self.assertRaises(ValueError):
            parse_length_ft("a lot")


class EngineRules(unittest.TestCase):
    def test_fittings_add_length_not_multiply(self):
        e = PricingEngine(fitting_allowance_lf={"elbow": 2.0})
        ins = next(m for m in e.calculate_materials([duct(fittings={"elbow": 2})], [duct_spec()]) if m.category == "insulation")
        self.assertAlmostEqual(ins.quantity, 104.0)

    def test_unconfigured_fitting_warns(self):
        e = PricingEngine()
        e.calculate_materials([duct(fittings={"valve": 2})], [duct_spec()])
        self.assertTrue(any("valve" in w for w in e.warnings))

    def test_rectangular_uses_perimeter(self):
        jacket = next(m for m in PricingEngine().calculate_materials([duct("18x12")], [duct_spec()]) if m.category == "facing")
        self.assertAlmostEqual(jacket.quantity, 2 * (18 + 12 + 6) / 12 * 100)

    def test_pipe_uses_circumference(self):
        spec = InsulationSpec("pipe", "all", 1.0, "elastomeric", facing="ASJ")
        pipe = MeasurementItem("P-1", "pipe", '4"', 50.0)
        jacket = next(m for m in PricingEngine().calculate_materials([pipe], [spec]) if m.category == "facing")
        self.assertAlmostEqual(jacket.quantity, math.pi * 6 / 12 * 50)

    def test_missing_price_is_flagged_not_invented(self):
        e = PricingEngine()
        mats = e.calculate_materials([duct()], [duct_spec(material="unobtainium", facing=None)])
        self.assertEqual(mats[0].total_price, 0.0)
        self.assertTrue(mats[0].description.startswith("[UNPRICED]"))
        self.assertTrue(any("unobtainium" in w for w in e.warnings))

    def test_unmatched_unsupported_and_zero_length_are_reported(self):
        e = PricingEngine()
        runs = [MeasurementItem("P-9", "pipe", '2"', 10), MeasurementItem("E-1", "equipment", "AHU", 5),
                duct(length=0.0), MeasurementItem("U-1", "", "4", 5)]
        self.assertEqual(e.calculate_materials(runs, [duct_spec()]), [])
        self.assertEqual(len(e.warnings), 4)

    def test_spec_chosen_by_size_band_then_location(self):
        e = PricingEngine()
        small = InsulationSpec("pipe", "1/2-2 inch", 1.0, "elastomeric")
        large = InsulationSpec("pipe", "2.5-6 inch", 2.0, "mineral_wool")
        find = lambda size: e.find_spec(MeasurementItem("x", "pipe", size, 1), [small, large])  # noqa: E731
        self.assertIs(find('1-1/2"'), small)
        self.assertIs(find('4"'), large)
        self.assertIsNone(find('12"'))
        indoor, outdoor = duct_spec(location="indoor"), duct_spec(location="outdoor")
        self.assertIs(e.find_spec(duct(location="Roof - RTU-1"), [indoor, outdoor]), outdoor)

    def test_jacket_requirement_beats_facing(self):
        spec = InsulationSpec("pipe", "all", 1.0, "elastomeric", facing="ASJ", special_requirements=["pvc_jacket_20mil"])
        mats = PricingEngine().calculate_materials([MeasurementItem("P", "pipe", '2"', 10)], [spec])
        self.assertIn("Pvc Jacket 20Mil", [m.description.split(" - ")[0] for m in mats])

    def test_unknown_facing_is_flagged(self):
        e = PricingEngine()
        e.calculate_materials([duct()], [duct_spec(facing="Zebra")])
        self.assertTrue(any("zebra_facing" in w for w in e.warnings))

    def test_duct_labor_uses_duct_rate_and_configurable_rate(self):
        e = PricingEngine(labor_rate=100.0)
        hours, cost = e.calculate_labor(e.calculate_materials([duct("12x12")], [duct_spec(facing=None)]))
        self.assertAlmostEqual(hours, 100 * 0.45 * 1.2)
        self.assertAlmostEqual(cost, hours * 100.0)

    def test_factory_facing_adds_no_labor(self):
        """FSK/ASJ comes on the insulation product; charging it jacketing hours was the double count."""
        e = PricingEngine()
        bare, _ = e.calculate_labor(e.calculate_materials([duct()], [duct_spec(facing=None)]))
        faced = e.calculate_materials([duct()], [duct_spec(facing="FSK")])
        self.assertTrue(any(m.category == "facing" and m.total_price > 0 for m in faced))  # material still priced
        self.assertAlmostEqual(e.calculate_labor(faced)[0], bare)

    def test_field_jacket_still_adds_labor(self):
        e = PricingEngine()
        pipe = MeasurementItem("P", "pipe", '2"', 50, "Roof")
        plain = InsulationSpec("pipe", "all", 1.0, "elastomeric", location="outdoor")
        jacketed = InsulationSpec("pipe", "all", 1.0, "elastomeric", special_requirements=["aluminum_jacket"], location="outdoor")
        base, _ = e.calculate_labor(e.calculate_materials([pipe], [plain]))
        mats = e.calculate_materials([pipe], [jacketed])
        area = next(m.quantity for m in mats if m.category == "jacket")
        self.assertAlmostEqual(e.calculate_labor(mats)[0], base + area * 0.25 * 1.2)

    def test_markup_and_pricebook_override(self):
        pb = PriceBook().with_overrides({"fiberglass_1.5": 10.0})
        e = PricingEngine(pb, markup=1.5)
        ins = next(m for m in e.calculate_materials([duct()], [duct_spec(facing=None)]) if m.category == "insulation")
        self.assertAlmostEqual(ins.total_price, 10.0 * 1.5 * 100)


if __name__ == "__main__":
    unittest.main()
