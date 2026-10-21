"""Render an EstimateResult as a text bid, JSON, or a distributor CSV. No templating library - plain strings."""

from __future__ import annotations

import csv
import io
import json

from .quote import EstimateResult
from .scope import COMPANY_NAME, SCOPE_DESCRIPTION

RULE = "=" * 78


def render_bid_text(result: EstimateResult, company_name: str = COMPANY_NAME) -> str:
    q = result.quote
    materials_total = sum(m.total_price for m in q.materials)
    labor_total = q.labor_hours * q.labor_rate
    contingency = q.subtotal * q.contingency_percent / 100
    out = [RULE, f"  {company_name.upper()}", "  BID PACKAGE - EXTERNAL HVAC / MECHANICAL INSULATION", RULE]
    if result.is_draft:
        out += ["", f"  *** DRAFT - {len(result.warnings)} ISSUE(S) NEED REVIEW BEFORE THIS NUMBER IS USED ***"]
        out += [f"   ! {w}" for w in result.warnings]
    out += ["", f"  Project: {q.project_name}", f"  Quote #: {q.quote_number}", f"  Date:    {q.date}", "", "1. SCOPE", f"   {SCOPE_DESCRIPTION}"]
    if result.exclusions:
        out.append("   Excluded from this bid:")
        out += [f"    - {e['kind']} {e['id']}: {e['reason']}" for e in result.exclusions]
    out += ["", "2. MATERIAL SCHEDULE", f"   {'Description':<52}{'Qty':>10} {'Unit':<4}{'Total':>12}", "   " + "-" * 78]
    out += [f"   {m.description[:51]:<52}{m.quantity:>10.2f} {m.unit:<4}${m.total_price:>11,.2f}" for m in q.materials]
    out += [
        "",
        "3. FINANCIALS",
        f"   {'Materials':<50}${materials_total:>14,.2f}",
        f"   {f'Labor ({q.labor_hours:.1f} h @ ${q.labor_rate:,.2f}/h)':<50}${labor_total:>14,.2f}",
        f"   {'Subtotal':<50}${q.subtotal:>14,.2f}",
        f"   {f'Contingency ({q.contingency_percent:.0f}%)':<50}${contingency:>14,.2f}",
        f"   {'TOTAL':<50}${q.total:>14,.2f}",
    ]
    if result.alternatives:
        out += ["", "4. OPTIONAL UPGRADES"]
        out += [f"   {name.replace('_', ' '):<40} {a['difference']:>+13,.2f} USD" for name, a in result.alternatives.items()]
    out += ["", "NOTES"] + [f"   {i}. {n}" for i, n in enumerate(q.notes, 1)] + [RULE]
    return "\n".join(out) + "\n"


def render_json(result: EstimateResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def render_material_csv(result: EstimateResult) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, ["category", "description", "unit", "quantity", "total_price"], lineterminator="\n")
    writer.writeheader()
    for row in result.quote.material_list:
        writer.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items()})
    return buf.getvalue()
