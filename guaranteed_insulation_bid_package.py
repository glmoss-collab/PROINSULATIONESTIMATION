"""
Guaranteed Insulation Inc. - Formal Bid Package Generator

Produces a formal bid package with:
- Company branding (Guaranteed Insulation Inc.)
- Executive summary of scope of work
- Financial breakdown
- Professional bid format
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from hvac_insulation_estimator import MaterialItem, ProjectQuote

from guaranteed_insulation_scope import COMPANY_NAME, SCOPE_DESCRIPTION


def _executive_summary_scope_of_work(quote: ProjectQuote, scope_exclusion_summary: Optional[str] = None) -> str:
    """Build executive summary / scope of work section."""
    lines = [
        "1. SCOPE OF WORK (EXECUTIVE SUMMARY)",
        "   " + "=" * 70,
        "",
        f"   {COMPANY_NAME} proposes to furnish and install external HVAC and mechanical",
        "   insulation as outlined in this bid. This proposal covers the following scope:",
        "",
        "   • External duct wrap and ductwork insulation (supply, return, exhaust, OA)",
        "   • HVAC piping insulation (chilled water, hot water, condenser water, steam,",
        "     condensate) with specified jacketing and vapor barrier",
        "   • Equipment insulation (AHUs, FCUs, boilers, chillers, tanks) where specified",
        "   • Kitchen exhaust / grease duct fireproofing and weatherproofing where specified",
        "   • Weatherproofing and jacketing for exterior systems (aluminum or PVC as specified)",
        "",
        "   Exclusions (not included in this bid):",
        "   • Duct liner and internal acoustic liner",
        "   • Waste, sanitary, or domestic plumbing insulation",
        "   • Fire sprinkler piping (non-mechanical)",
        "   • Any scope not explicitly listed above",
        "",
    ]
    if scope_exclusion_summary:
        lines.extend([
            "   Scope filter applied to project documents:",
            f"   {scope_exclusion_summary}",
            "",
        ])
    lines.extend([
        f"   Total bid reflects materials, labor, and {quote.contingency_percent:.0f}% contingency.",
        "",
    ])
    return "\n".join(lines)


def _financial_breakdown(quote: ProjectQuote) -> str:
    """Build detailed financial breakdown section."""
    material_total = sum(m.total_price for m in quote.materials)
    labor_total = quote.labor_hours * quote.labor_rate
    contingency = quote.subtotal * (quote.contingency_percent / 100)

    # By category
    by_cat = {}
    for m in quote.materials:
        by_cat[m.category] = by_cat.get(m.category, 0.0) + m.total_price

    lines = [
        "2. FINANCIAL BREAKDOWN",
        "   " + "=" * 70,
        "",
        "   MATERIALS BY CATEGORY",
        "   " + "-" * 70,
    ]
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        lines.append(f"   {cat.replace('_', ' ').title():<45} ${amt:>12,.2f}")
    lines.extend([
        "",
        f"   {'Materials Subtotal':<45} ${material_total:>12,.2f}",
        "",
        "   LABOR",
        "   " + "-" * 70,
        f"   Labor: {quote.labor_hours:.1f} hours @ ${quote.labor_rate:,.2f}/hr{'':<20} ${labor_total:>12,.2f}",
        "",
        "   SUMMARY",
        "   " + "-" * 70,
        f"   {'Materials':<45} ${material_total:>12,.2f}",
        f"   {'Labor':<45} ${labor_total:>12,.2f}",
        f"   {'Subtotal':<45} ${quote.subtotal:>12,.2f}",
        f"   Contingency ({quote.contingency_percent:.0f}%){'':<35} ${contingency:>12,.2f}",
        "   " + "-" * 70,
        f"   {'TOTAL BID':<45} ${quote.total:>12,.2f}",
        "",
    ])
    return "\n".join(lines)


def _material_schedule(quote: ProjectQuote) -> str:
    """Line-item material schedule."""
    lines = [
        "3. MATERIAL SCHEDULE (LINE ITEMS)",
        "   " + "=" * 70,
        "",
        f"   {'Description':<50} {'Qty':>10} {'Unit':<6} {'Total':>12}",
        "   " + "-" * 70,
    ]
    for m in quote.materials:
        lines.append(f"   {m.description[:50]:<50} {m.quantity:>10.2f} {m.unit:<6} ${m.total_price:>11,.2f}")
    lines.append("")
    return "\n".join(lines)


def _notes_section(quote: ProjectQuote) -> str:
    """Terms and notes."""
    lines = [
        "4. TERMS AND NOTES",
        "   " + "=" * 70,
        "",
    ]
    for i, note in enumerate(quote.notes, 1):
        lines.append(f"   {i}. {note}")
    lines.extend([
        "",
        "   This bid is valid for 30 days from the date of issue. Work shall be performed",
        "   in accordance with project specifications and applicable codes. Final quantities",
        "   subject to field verification.",
        "",
    ])
    return "\n".join(lines)


def generate_bid_package_text(
    quote: ProjectQuote,
    scope_exclusion_summary: Optional[str] = None,
) -> str:
    """
    Generate full formal bid package as plain text with:
    - Guaranteed Insulation Inc. branding
    - Executive summary (scope of work)
    - Financial breakdown
    - Material schedule
    - Terms and notes
    """
    sections = [
        "=" * 78,
        f"  {COMPANY_NAME.upper()}",
        "  FORMAL BID PACKAGE — EXTERNAL HVAC / MECHANICAL INSULATION",
        "=" * 78,
        "",
        f"  Project:        {quote.project_name}",
        f"  Bid/Quote No.:  {quote.quote_number}",
        f"  Date:           {quote.date}",
        "",
        "=" * 78,
        "",
        _executive_summary_scope_of_work(quote, scope_exclusion_summary),
        _financial_breakdown(quote),
        _material_schedule(quote),
        _notes_section(quote),
        "=" * 78,
        f"  {COMPANY_NAME}",
        "  " + SCOPE_DESCRIPTION,
        "=" * 78,
    ]
    return "\n".join(sections)


def export_bid_package_to_file(
    quote: ProjectQuote,
    output_path: str | Path,
    scope_exclusion_summary: Optional[str] = None,
) -> None:
    """Write the formal bid package to a text file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = generate_bid_package_text(quote, scope_exclusion_summary)
    output_path.write_text(text, encoding="utf-8")
