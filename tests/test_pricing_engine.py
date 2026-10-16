"""Regression tests for PricingEngine takeoff math and the calculate_pricing agent tool."""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hvac_insulation_estimator import InsulationSpec, MeasurementItem, PricingEngine  # noqa: E402
from claude_agent_tools import calculate_pricing  # noqa: E402


def duct_spec(**kw):
    base = dict(system_type="duct", size_range="all", thickness=1.5, material="fiberglass", facing="FSK")
    base.update(kw)
    return InsulationSpec(**base)


def duct(size="18x12", length=100.0, **kw):
    return MeasurementItem("D-1", "duct", size, length, kw.pop("location", "indoor"), **kw)


def test_fittings_are_additive_not_multiplicative():
    engine = PricingEngine(fitting_allowance_lf={"elbow": 2.0})
    mats = engine.calculate_materials([duct(fittings={"elbow": 2})], [duct_spec()])
    insulation = next(m for m in mats if m.category == "insulation")
    assert insulation.quantity == pytest.approx(104.0)  # was 200.0


def test_rectangular_duct_uses_perimeter():
    engine = PricingEngine()
    mats = engine.calculate_materials([duct("18x12")], [duct_spec()])
    jacket = next(m for m in mats if m.category == "jacket")
    assert jacket.quantity == pytest.approx(2 * (18 + 12 + 4 * 1.5) / 12 * 100)  # 300 SF, was 549.8


def test_round_duct_and_pipe_use_circumference():
    engine = PricingEngine()
    spec = InsulationSpec("pipe", "all", 1.0, "elastomeric", facing="ASJ")
    pipe = MeasurementItem("P-1", "pipe", '4"', 50.0, "indoor")
    jacket = next(m for m in engine.calculate_materials([pipe], [spec]) if m.category == "jacket")
    assert jacket.quantity == pytest.approx(math.pi * (4 + 2) / 12 * 50)


def test_missing_price_key_is_flagged_not_invented():
    engine = PricingEngine()
    spec = duct_spec(material="unobtainium", facing=None)
    mats = engine.calculate_materials([duct()], [spec])
    assert mats[0].total_price == 0.0  # was 5.0 x quantity
    assert mats[0].description.startswith("[UNPRICED")
    assert any("unobtainium" in w for w in engine.warnings)


def test_unmatched_measurement_is_reported():
    engine = PricingEngine()
    pipe = MeasurementItem("P-9", "pipe", '2"', 10.0, "indoor")
    assert engine.calculate_materials([pipe], [duct_spec()]) == []
    assert any("P-9" in w for w in engine.warnings)


def test_spec_selected_by_size_band_then_location():
    engine = PricingEngine()
    small = InsulationSpec("pipe", "1/2-2 inch", 1.0, "elastomeric")
    large = InsulationSpec("pipe", "2.5-6 inch", 2.0, "mineral_wool")
    assert engine._find_applicable_spec(MeasurementItem("a", "pipe", '1-1/2"', 1, "indoor"), [small, large]) is small
    assert engine._find_applicable_spec(MeasurementItem("b", "pipe", '4"', 1, "indoor"), [small, large]) is large
    assert engine._find_applicable_spec(MeasurementItem("c", "pipe", '12"', 1, "indoor"), [small, large]) is None

    indoor = duct_spec(location="indoor")
    outdoor = duct_spec(location="outdoor")
    assert engine._find_applicable_spec(duct(location="outdoor"), [indoor, outdoor]) is outdoor


def test_duct_labor_uses_duct_rate():
    engine = PricingEngine()
    mats = engine.calculate_materials([duct("12x12", 100.0)], [duct_spec(facing=None)])
    hours, cost = engine.calculate_labor(mats)
    assert hours == pytest.approx(100 * engine.labor_rates["duct_insulation"] * 1.2)  # was pipe rate
    assert cost == pytest.approx(hours * engine.labor_rate)


def test_labor_rate_is_configurable():
    engine = PricingEngine(labor_rate=100.0)
    hours, cost = engine.calculate_labor(engine.calculate_materials([duct()], [duct_spec()]))
    assert cost == pytest.approx(hours * 100.0)


def test_calculate_pricing_tool_runs_end_to_end():
    """Previously raised TypeError (PricingEngine had no pricebook/markup_percent/calculate_item)."""
    result = calculate_pricing(
        specifications=[{"system_type": "duct", "size_range": "all", "thickness": 1.5, "material": "fiberglass",
                         "facing": "FSK", "special_requirements": [], "location": "indoor"}],
        measurements=[{"item_id": "D-1", "system_type": "duct", "size": "18x12", "length": 100, "location": "indoor",
                       "fittings": {}}],
        markup_percent=15.0,
    )
    assert result["success"], result.get("error")
    assert result["total"] > 0
    assert result["warnings"] == []
    # fiberglass_1.5 = $4.50/LF x 1.15 markup x 100 LF
    insulation = next(m for m in result["materials"] if m["category"] == "insulation")
    assert insulation["total_price"] == pytest.approx(4.50 * 1.15 * 100, abs=0.01)
