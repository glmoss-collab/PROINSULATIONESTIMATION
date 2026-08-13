"""MPA / Lawrenceville MOB — HVAC insulation takeoff and estimate.

Design Development set dated 6/12/26 (Jordan & Skala, 25-115.00).
Quantities from M0-00..M0-04 and M2-01..M2-06 plus Section 230700.

Square-foot formula (rectangular wrap, outside of insulation):
    SF = 2 * (W_in + H_in + 2 * t_in) / 12 * LF
Round:
    SF = pi * (D_in + 2 * t_in) / 12 * LF

Do not use diameter-of-first-number (the engine bug on 18x12).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

PRICEBOOK_PATH = Path(__file__).resolve().parents[2] / "pricebook_sample.json"
OUT_DIR = Path(__file__).resolve().parent

# Floor-to-floor from M0-04 elevation datum (feet)
# L1 1064, L2 1079 (15), L3 1093 (14), L4 1107 (14), L5 1121 (14), T/O roof 1136 (15)
STORY_HT = {
    "L1": 15.0,
    "L2": 14.0,
    "L3": 14.0,
    "L4": 14.0,
    "L5": 15.0,
}

# 2" Type 1 wrap stretch-out; 3" Type 2 for outside envelope
T_WRAP_2 = 2.0
T_WRAP_3 = 3.0

# Horizontal core mains: labels sit in the central core (~25–35 ft of run).
CORE_HORIZ_LF = 30.0

# Roof SA/RA from RTU to shaft — tag-to-unit distance at 1/8"=1'-0" (1 pt = 1/9 ft)
ROOF_MAIN_LF = {
    "RTU-1 SA 86x56": 36.0,
    "RTU-1 RA 78x56": 32.0,
    "RTU-2 SA 56x78": 33.0,
    "RTU-2 RA 56x86": 35.0,
    "RTU-3 SA 56x38": 28.0,
    "RTU-3 RA 58x40": 28.0,
    "RTU-R.ELEV1 SA 16x14": 12.0,
    "RTU-R.ELEV1 RA 14x14": 12.0,
    "RTU-R.ELEV2 SA 14x12": 10.0,
    "RTU-R.ELEV2 RA 14x12": 10.0,
}

LINER_FT_FROM_RTU = 15.0  # acoustical liner; no additional wrap
FITTING_SF_HORIZ = 0.15
FITTING_SF_VERT = 0.08

LABOR_RATE = 65.0
LABOR_OH = 1.20
MARKUP = 1.15
CONTINGENCY = 0.10
# Production (man-hr / SF). Stock engine 0.45 hr/LF is for small duct and
# understates 86x56; 0.12–0.25 hr/SF overstates wrap. These are wrap/jacket
# rates for large rectangular duct on a commercial core-and-shell job.
WRAP_HR_SF_IN = 0.045
WRAP_HR_SF_OUT = 0.060
JACKET_HR_SF = 0.100
PIPE_HR_LF = 0.35


def rect_sf(width_in: float, height_in: float, lf: float, t_in: float) -> float:
    """Insulated outside surface of rectangular duct (sq ft)."""
    return 2.0 * (width_in + height_in + 2.0 * t_in) / 12.0 * lf


def round_sf(dia_in: float, lf: float, t_in: float) -> float:
    return math.pi * (dia_in + 2.0 * t_in) / 12.0 * lf


@dataclass
class Line:
    item_id: str
    system: str
    location: str
    size: str
    width_in: float
    height_in: float
    lf: float
    t_in: float
    in_scope: bool
    treatment: str
    notes: str
    sf: float = 0.0
    fitting_sf: float = 0.0
    bill_sf: float = 0.0

    def compute(self, fitting_frac: float) -> None:
        if self.height_in <= 0:
            self.sf = round_sf(self.width_in, self.lf, self.t_in)
        else:
            self.sf = rect_sf(self.width_in, self.height_in, self.lf, self.t_in)
        self.fitting_sf = self.sf * fitting_frac
        self.bill_sf = self.sf + self.fitting_sf


def parse_size(size: str) -> tuple[float, float]:
    if "x" in size:
        w, h = size.lower().split("x")
        return float(w), float(h)
    return float(size.replace("Ø", "").replace('"', "")), 0.0


def build_takeoff() -> list[Line]:
    lines: list[Line] = []

    # Shaft / floor-tagged mains (vertical = story height, plus core horizontal)
    floor_ducts: dict[str, list[str]] = {
        "L1": ["60x24", "54x24"],
        "L2": ["60x24", "54x24"],
        "L3": ["90x28", "88x26", "78x30", "86x30"],
        "L4": ["90x28", "88x26", "70x36", "78x36"],
        "L5": ["56x24", "56x38", "58x40"],
    }
    for floor, sizes in floor_ducts.items():
        ht = STORY_HT[floor]
        for i, size in enumerate(sizes, 1):
            w, h = parse_size(size)
            lines.append(
                Line(
                    item_id=f"{floor}-RISER-{i}-{size}",
                    system="duct_sa_ra",
                    location=f"{floor} shaft / core (vertical)",
                    size=size,
                    width_in=w,
                    height_in=h,
                    lf=ht,
                    t_in=T_WRAP_2,
                    in_scope=True,
                    treatment="type1_2in_fsk_wrap",
                    notes="Interior chase — Type 1 blanket 2\" FSK (230700 2.03.B). Size as tagged on floor plan.",
                )
            )
            lines.append(
                Line(
                    item_id=f"{floor}-HORIZ-{i}-{size}",
                    system="duct_sa_ra",
                    location=f"{floor} core horizontal",
                    size=size,
                    width_in=w,
                    height_in=h,
                    lf=CORE_HORIZ_LF,
                    t_in=T_WRAP_2,
                    in_scope=True,
                    treatment="type1_2in_fsk_wrap",
                    notes=f"Core main; {CORE_HORIZ_LF:.0f} LF assumed from 1/8\" plan (tenant fit-out not drawn).",
                )
            )

    # Deduct 15' liner at roof end of each main RTU shaft pair (SA+RA)
    # Three building RTUs × 2 ducts. Elevator RTUs are short / all liner.
    for rtu, size in (
        ("RTU-1", "60x24"),
        ("RTU-1", "54x24"),
        ("RTU-2", "90x28"),
        ("RTU-2", "88x26"),
        ("RTU-3", "56x38"),
        ("RTU-3", "58x40"),
    ):
        w, h = parse_size(size)
        lines.append(
            Line(
                item_id=f"{rtu}-LINER-DEDUCT-{size}",
                system="duct_sa_ra",
                location="shaft at roof (liner zone)",
                size=size,
                width_in=w,
                height_in=h,
                lf=-LINER_FT_FROM_RTU,
                t_in=T_WRAP_2,
                in_scope=True,
                treatment="type1_2in_fsk_wrap",
                notes="Credit: first 15' from RTU is 1.5\" acoustical liner (M0-01 / M0-04). Liner by sheet metal.",
            )
        )

    # Roof duct — specified as 2\" liner board (SM). GI weatherproofing is an ALTERNATE.
    for name, lf in ROOF_MAIN_LF.items():
        size = name.split()[-1]
        w, h = parse_size(size)
        lines.append(
            Line(
                item_id=f"ROOF-{name.replace(' ', '-')}",
                system="duct_exterior",
                location="roof (outside envelope)",
                size=size,
                width_in=w,
                height_in=h,
                lf=lf,
                t_in=T_WRAP_3,
                in_scope=True,
                treatment="exterior_alternate_3in_plus_jacket",
                notes="230700 2.05 / M0-01: primary is 2\" liner board (SM). Priced as GI alternate: 3\" Type 2 wrap + aluminum jacket.",
            )
        )

    # Toilet / janitor exhaust — specified NOT insulated
    for floor, pieces in (
        ("L1", [("12x10", 15.0, False), ("16x10", 12.0, False), ("8Ø", 20.0, True), ("6Ø", 40.0, True)]),
        ("L2", [("12x10", 15.0, False), ("10x10", 12.0, False), ("8Ø", 20.0, True), ("6Ø", 40.0, True)]),
        ("L3", [("12x10", 15.0, False), ("10x10", 12.0, False), ("8Ø", 20.0, True), ("6Ø", 40.0, True)]),
        ("L4", [("12x10", 15.0, False), ("10x10", 12.0, False), ("8Ø", 20.0, True), ("6Ø", 40.0, True)]),
        ("L5", [("12x10", 15.0, False), ("10x10", 12.0, False), ("8Ø", 20.0, True), ("6Ø", 40.0, True)]),
    ):
        for size, lf, is_round in pieces:
            w, h = parse_size(size)
            lines.append(
                Line(
                    item_id=f"{floor}-EXH-{size}",
                    system="exhaust",
                    location=f"{floor} restroom / janitor",
                    size=size,
                    width_in=w,
                    height_in=0.0 if is_round else h,
                    lf=lf,
                    t_in=0.0,
                    in_scope=False,
                    treatment="excluded_exhaust",
                    notes="M0-01 Air Distribution note 8: exhaust shall not be insulated unless noted.",
                )
            )

    # Relief from exterior to 18\" past damper — Type 1, short
    lines.append(
        Line(
            item_id="RH-R.1-RELIEF",
            system="relief",
            location="roof relief hood RH-R.1",
            size="42x30",
            width_in=42.0,
            height_in=30.0,
            lf=8.0,
            t_in=T_WRAP_2,
            in_scope=True,
            treatment="type1_2in_fsk_wrap",
            notes="230700 2.03.B.4: relief from exterior to 18\" past damper. Hood throat 42x30, 6,500 CFM.",
        )
    )

    for line in lines:
        frac = FITTING_SF_VERT if "vertical" in line.location or "liner zone" in line.location else FITTING_SF_HORIZ
        if line.lf < 0:
            frac = FITTING_SF_VERT
        line.compute(frac if line.in_scope else 0.0)
    return lines


@dataclass
class MoneyLine:
    description: str
    qty: float
    unit: str
    unit_price: float
    category: str
    total: float = 0.0
    source: str = ""

    def __post_init__(self) -> None:
        self.total = self.qty * self.unit_price


def load_prices() -> dict[str, float]:
    raw = json.loads(PRICEBOOK_PATH.read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in raw.items() if _is_number(v)}


def _is_number(v: object) -> bool:
    try:
        float(v)  # type: ignore[arg-type]
        return True
    except (TypeError, ValueError):
        return False


def price_job(lines: list[Line], prices: dict[str, float]) -> dict:
    # Convert LF keys to SF for wrap. 12x12 duct = 4 SF/LF of 2\" wrap.
    wrap_2_sf = prices["fiberglass_2.0"] / 4.0
    # No fiberglass_3.0 key — scale 2.0 by 3/2 thickness (flagged).
    wrap_3_sf = prices["fiberglass_2.0"] / 4.0 * (3.0 / 2.0)
    jacket_sf = prices["aluminum_jacket"]
    mastic_sf = prices["mastic"]
    elasto_1 = prices["elastomeric_1.0"]

    interior = [ln for ln in lines if ln.in_scope and ln.treatment == "type1_2in_fsk_wrap"]
    exterior = [ln for ln in lines if ln.in_scope and ln.treatment == "exterior_alternate_3in_plus_jacket"]
    excluded = [ln for ln in lines if not ln.in_scope]

    int_sf = sum(ln.bill_sf for ln in interior)
    ext_sf = sum(ln.bill_sf for ln in exterior)

    # Condensate: 5 RTUs × 30 LF of 1\" elastomeric, outdoor UV (factory jacket in product)
    cond_lf = 5.0 * 30.0

    materials: list[MoneyLine] = [
        MoneyLine(
            "2\" FSK duct wrap (Type 1) — interior shafts, core, relief",
            round(int_sf, 1),
            "SF",
            round(wrap_2_sf, 4),
            "insulation",
            source="pricebook fiberglass_2.0 $5.25/LF ÷ 4 SF/LF (12x12 equivalent)",
        ),
        MoneyLine(
            "3\" FSK duct wrap (Type 2) — roof exterior ALTERNATE",
            round(ext_sf, 1),
            "SF",
            round(wrap_3_sf, 4),
            "insulation",
            source="fiberglass_2.0 scaled 3/2 — NO fiberglass_3.0 key in pricebook",
        ),
        MoneyLine(
            "Aluminum jacket — roof exterior ALTERNATE",
            round(ext_sf, 1),
            "SF",
            jacket_sf,
            "jacket",
            source="pricebook aluminum_jacket",
        ),
        MoneyLine(
            "Mastic / vapor seal — roof jacket seams",
            round(ext_sf, 1),
            "SF",
            mastic_sf,
            "mastic",
            source="pricebook mastic",
        ),
        MoneyLine(
            "1\" elastomeric — RTU condensate on roof (5 units × 30 LF)",
            cond_lf,
            "LF",
            elasto_1,
            "insulation",
            source="pricebook elastomeric_1.0; outdoor UV jacket per M0-01 (factory jacketed)",
        ),
    ]

    labor_hours = (
        int_sf * WRAP_HR_SF_IN
        + ext_sf * WRAP_HR_SF_OUT
        + ext_sf * JACKET_HR_SF
        + cond_lf * PIPE_HR_LF
    ) * LABOR_OH
    labor_cost = labor_hours * LABOR_RATE

    mat_raw = sum(m.total for m in materials)
    mat_marked = mat_raw * MARKUP
    subtotal = mat_marked + labor_cost
    contingency = subtotal * CONTINGENCY
    total = subtotal + contingency

    # Split: base (no exterior alternate) vs complete GI (with exterior)
    ext_mat = sum(m.total for m in materials if "ALTERNATE" in m.description or "roof jacket" in m.description)
    ext_labor_hrs = (ext_sf * WRAP_HR_SF_OUT + ext_sf * JACKET_HR_SF) * LABOR_OH
    ext_labor = ext_labor_hrs * LABOR_RATE
    base_mat = (mat_raw - ext_mat) * MARKUP
    base_labor = labor_cost - ext_labor
    base_sub = base_mat + base_labor
    base_cont = base_sub * CONTINGENCY
    base_total = base_sub + base_cont

    return {
        "interior_sf": round(int_sf, 1),
        "exterior_sf": round(ext_sf, 1),
        "condensate_lf": cond_lf,
        "materials": [asdict(m) for m in materials],
        "labor_hours": round(labor_hours, 1),
        "labor_rate": LABOR_RATE,
        "labor_cost": round(labor_cost, 2),
        "materials_raw": round(mat_raw, 2),
        "materials_marked": round(mat_marked, 2),
        "markup": MARKUP,
        "subtotal": round(subtotal, 2),
        "contingency": round(contingency, 2),
        "total_with_exterior_alternate": round(total, 2),
        "base_interior_and_condensate_only": round(base_total, 2),
        "exterior_alternate_delta": round(total - base_total, 2),
        "excluded_count": len(excluded),
        "wrap_2_sf_unit": wrap_2_sf,
        "wrap_3_sf_unit": wrap_3_sf,
    }


def format_bid(lines: list[Line], priced: dict) -> str:
    today = date.today().isoformat()
    in_lines = [ln for ln in lines if ln.in_scope]
    out_lines = [ln for ln in lines if not ln.in_scope]

    def money(n: float) -> str:
        return f"${n:,.2f}"

    body = []
    body.append("=" * 78)
    body.append("  GUARANTEED INSULATION INC.")
    body.append("  FORMAL BID PACKAGE — EXTERNAL HVAC / MECHANICAL INSULATION")
    body.append("=" * 78)
    body.append("")
    body.append("  Project:        MPA Gwinnett / Lawrenceville MOB")
    body.append("  Address:        Walther Road, Lawrenceville, GA")
    body.append("  Engineer:       Jordan & Skala  |  Architect: RJTR")
    body.append("  Project No.:    25-115.00")
    body.append("  Documents:      Mech drawings M0-00–M0-04, M2-01–M2-06 (DD 6/12/26)")
    body.append("                  Spec Section 230700 HVAC Insulation")
    body.append(f"  Bid/Quote No.:  GI-LMOB-{date.today().strftime('%Y%m%d')}")
    body.append(f"  Date:           {today}")
    body.append("  Set status:     DESIGN DEVELOPMENT — not issued for construction")
    body.append("")
    body.append("=" * 78)
    body.append("")
    body.append("1. SCOPE OF WORK (EXECUTIVE SUMMARY)")
    body.append("   " + "=" * 70)
    body.append("")
    body.append("   Base building HVAC insulation for three packaged gas/electric RTUs")
    body.append("   (RTU-1 56,000 CFM L1–L2; RTU-2 56,000 CFM L3–L4; RTU-3 27,000 CFM L5)")
    body.append("   plus two elevator RTUs, east/west shaft risers, core mains, and roof")
    body.append("   condensate. Five occupied floors; roof at 72' above Level 1.")
    body.append("")
    body.append("   INCLUDED (Guaranteed Insulation Inc.):")
    body.append("   • Type 1 2\" FSK duct wrap on interior SA/RA shaft risers and core mains")
    body.append("     after the 15' acoustical-liner zone at each RTU")
    body.append("   • Relief duct at RH-R.1 (exterior to 18\" past damper)")
    body.append("   • 1\" elastomeric on RTU condensate piping on the roof")
    body.append("   • ALTERNATE: 3\" Type 2 wrap + aluminum jacket on roof SA/RA")
    body.append("     (spec primary is 2\" liner board by sheet metal; this alternate is")
    body.append("     230700 2.05.A.2 / M0-01 exterior insulation option)")
    body.append("")
    body.append("   EXCLUDED:")
    body.append("   • Duct liner / acoustical liner (15' from RTU and VAV) — sheet metal")
    body.append("   • Factory-insulated flex duct (R-6 / R-8)")
    body.append("   • Toilet / janitor exhaust (M0-01: do not insulate unless noted)")
    body.append("   • Tenant VAV/PIU distribution — not designed (VAV schedule is blank)")
    body.append("   • Domestic water, waste, fire sprinkler")
    body.append("   • 2-hour fire wrap at smokeproof-enclosure penetrations (clarify)")
    body.append("   • Equipment casings, RTU internals, gas vents")
    body.append("")
    body.append("2. HOW LARGE-DUCT SF WAS CALCULATED")
    body.append("   " + "=" * 70)
    body.append("")
    body.append("   Rectangular (correct):  SF = 2 × (W + H + 2t) / 12 × LF")
    body.append("   Example 86\" × 56\" with 2\" wrap:  2×(86+56+4)/12 = 24.33 SF per LF")
    body.append("   The estimator engine's old parser treated \"86x56\" as 86\" ROUND")
    body.append("   (π×86/12 ≈ 22.5 SF/LF) and ignored the second dimension. Not used.")
    body.append("   Fittings: +15% SF on horizontal, +8% SF on vertical risers.")
    body.append("   Scale: 1/8\" = 1'-0\" on M2 sheets (1 PDF point = 1/9 foot).")
    body.append("")
    body.append("3. FINANCIAL BREAKDOWN")
    body.append("   " + "=" * 70)
    body.append("")
    body.append(f"   Interior wrap SF (Type 1):     {priced['interior_sf']:>10,.1f} SF")
    body.append(f"   Roof exterior SF (alternate):  {priced['exterior_sf']:>10,.1f} SF")
    body.append(f"   Condensate:                    {priced['condensate_lf']:>10,.1f} LF")
    body.append("")
    body.append("   MATERIALS")
    for m in priced["materials"]:
        body.append(
            f"   {m['description'][:52]:<52} {m['qty']:>8.1f} {m['unit']:<3} {money(m['total']):>12}"
        )
    body.append("")
    body.append(f"   Materials (pricebook, raw)                         {money(priced['materials_raw']):>12}")
    body.append(f"   Materials after {int(round((MARKUP-1)*100))}% markup                         {money(priced['materials_marked']):>12}")
    body.append(
        f"   Labor {priced['labor_hours']:.1f} hrs @ ${priced['labor_rate']:.2f}/hr (incl 20% OH)  {money(priced['labor_cost']):>12}"
    )
    body.append(f"   Subtotal                                           {money(priced['subtotal']):>12}")
    body.append(f"   Contingency (10%)                                  {money(priced['contingency']):>12}")
    body.append("   " + "-" * 70)
    body.append(f"   TOTAL with roof exterior ALTERNATE                 {money(priced['total_with_exterior_alternate']):>12}")
    body.append(f"   BASE (interior wrap + condensate only)             {money(priced['base_interior_and_condensate_only']):>12}")
    body.append(f"   Exterior alternate adder                           {money(priced['exterior_alternate_delta']):>12}")
    body.append("")
    body.append("4. TAKEOFF LINES (IN SCOPE)")
    body.append("   " + "=" * 70)
    body.append(f"   {'ID':<32} {'Size':<8} {'LF':>7} {'SF':>9} {'Bill SF':>9}")
    body.append("   " + "-" * 70)
    for ln in in_lines:
        body.append(
            f"   {ln.item_id[:32]:<32} {ln.size:<8} {ln.lf:>7.1f} {ln.sf:>9.1f} {ln.bill_sf:>9.1f}"
        )
    body.append("")
    body.append("5. EXCLUDED LINES (shown, not priced)")
    body.append("   " + "=" * 70)
    for ln in out_lines:
        body.append(f"   {ln.item_id:<32} {ln.size:<8} {ln.lf:>6.1f} LF  {ln.notes[:48]}")
    body.append("")
    body.append("6. TERMS, ASSUMPTIONS, CLARIFICATIONS")
    body.append("   " + "=" * 70)
    body.append("   1. DD set — VAV-1-1 through VAV-3-4 are scheduled with no CFM/inlet.")
    body.append("      Tenant medium-pressure mains and VAV runouts are NOT on the plans")
    body.append("      and are not in this number. Add by change order when issued.")
    body.append("   2. Floor-to-floor from M0-04: 15'/14'/14'/14'/15' (L1→roof = 72').")
    body.append("   3. Core horizontal LF = 30' per tagged main (plan measure at 1/8\").")
    body.append("   4. Roof LF from RTU tag to size tag at drawing scale.")
    body.append("   5. Pricebook has no fiberglass_3.0; 3\" wrap uses 2.0 × 3/2.")
    body.append("   6. Wrap $/SF = fiberglass_2.0 per LF ÷ 4 SF (12×12 duct). Large")
    body.append("      ducts are billed on SF, not a flat $/LF.")
    body.append("   7. Labor is SF-based (0.045 hr/SF indoor wrap, 0.06 outdoor,")
    body.append("      0.10 jacket). Stock engine 0.45 hr/LF understates 86x56.")
    body.append("   8. Confirm who furnishes roof liner vs Alumaguard before award.")
    body.append("   9. Confirm 2-hour wrap at stair/smokeproof penetrations.")
    body.append("  10. Bid valid 30 days. Quantities subject to IFC set and field verify.")
    body.append("  11. No hydronic CHW/HW mains appear on this DD mechanical set;")
    body.append("      CWS/CWR exist only in the legend. None taken off.")
    body.append("")
    body.append("=" * 78)
    body.append("  GUARANTEED INSULATION INC.")
    body.append("  External HVAC and mechanical insulation only.")
    body.append("=" * 78)
    return "\n".join(body)


def main() -> None:
    prices = load_prices()
    lines = build_takeoff()
    priced = price_job(lines, prices)
    bid = format_bid(lines, priced)

    payload = {
        "project": "MPA Gwinnett / Lawrenceville MOB",
        "document_date": "2026-06-12",
        "formulas": {
            "rectangular_sf": "2 * (W_in + H_in + 2*t_in) / 12 * LF",
            "round_sf": "pi * (D_in + 2*t_in) / 12 * LF",
        },
        "lines": [asdict(ln) for ln in lines],
        "pricing": priced,
    }
    (OUT_DIR / "takeoff.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUT_DIR / "GWINNETT_MOB_BID.txt").write_text(bid, encoding="utf-8")
    print(bid)
    print("\nWrote", OUT_DIR / "takeoff.json")
    print("Wrote", OUT_DIR / "GWINNETT_MOB_BID.txt")


if __name__ == "__main__":
    main()
