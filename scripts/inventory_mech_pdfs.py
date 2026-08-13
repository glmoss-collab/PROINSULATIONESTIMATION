"""Inventory a mechanical drawing PDF and a spec PDF for a GI takeoff.

This is the first step of every job. It does not invent linear feet.
It writes page lists, insulation-section text, and size/tag callouts
so the next step (manual or agent takeoff) starts from the same facts.

Usage:
    python3 scripts/inventory_mech_pdfs.py \\
        --drawings path/to/drawings.pdf \\
        --specs path/to/specs.pdf \\
        --out estimates/my-job/inventory
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pymupdf

SIZE_RE = re.compile(
    r"^\d{1,3}x\d{1,3}$|^\d{1,3}Ø$|^\d{1,2}\"$",
    re.IGNORECASE,
)
TAG_RE = re.compile(
    r"^(RTU|VAV|PIU|EF|AHU|FCU|WSHP|HP|RH|SA|RA|OA|EA)[-.]?\S*$",
    re.IGNORECASE,
)
INSULATION_SECTION_RE = re.compile(
    r"230700|23\s*07\s*00|HVAC INSULATION",
    re.IGNORECASE,
)


def page_preview(page: pymupdf.Page) -> dict[str, Any]:
    text = page.get_text("text") or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rect = page.rect
    return {
        "width_pt": round(rect.width, 1),
        "height_pt": round(rect.height, 1),
        "chars": len(text),
        "heading": " | ".join(lines[:6])[:240],
    }


def inventory_pdf(path: Path) -> dict[str, Any]:
    doc = pymupdf.open(path)
    pages = []
    for i in range(doc.page_count):
        info = page_preview(doc[i])
        info["page"] = i + 1
        pages.append(info)
    meta = doc.metadata or {}
    result = {
        "file": str(path),
        "page_count": doc.page_count,
        "title": meta.get("title") or "",
        "producer": meta.get("producer") or "",
        "pages": pages,
    }
    doc.close()
    return result


def extract_insulation_spec(spec_path: Path, out_dir: Path) -> list[int]:
    doc = pymupdf.open(spec_path)
    hit_pages: list[int] = []
    chunks: list[str] = []
    for i in range(doc.page_count):
        text = doc[i].get_text("text") or ""
        if INSULATION_SECTION_RE.search(text):
            hit_pages.append(i + 1)
            chunks.append(f"\n\n===== SPEC PAGE {i + 1} =====\n{text}")
    doc.close()
    (out_dir / "spec_insulation.txt").write_text("".join(chunks), encoding="utf-8")
    return hit_pages


def extract_drawing_callouts(drawings_path: Path, out_dir: Path) -> dict[str, Any]:
    doc = pymupdf.open(drawings_path)
    by_page: list[dict[str, Any]] = []
    for i in range(doc.page_count):
        page = doc[i]
        words = page.get_text("words")
        sizes = Counter()
        tags = Counter()
        scale_hits: list[str] = []
        for w in words:
            token = w[4]
            if SIZE_RE.match(token):
                sizes[token] += 1
            if TAG_RE.match(token):
                tags[token] += 1
            if re.search(r"1/8\"|1/4\"|1/16\"|SCALE", token, re.I):
                scale_hits.append(token)
        by_page.append(
            {
                "page": i + 1,
                "word_count": len(words),
                "sizes": sizes.most_common(40),
                "tags": tags.most_common(40),
                "scale_tokens": scale_hits[:20],
            }
        )
        (out_dir / f"drawing_p{i + 1:02d}.txt").write_text(
            page.get_text("text") or "",
            encoding="utf-8",
        )
    doc.close()
    return {"pages": by_page}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory mech drawings + specs")
    parser.add_argument("--drawings", required=True, type=Path)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if not args.drawings.is_file() or not args.specs.is_file():
        print("Drawings and specs PDFs must exist.", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    drawings = inventory_pdf(args.drawings)
    specs = inventory_pdf(args.specs)
    insulation_pages = extract_insulation_spec(args.specs, args.out)
    callouts = extract_drawing_callouts(args.drawings, args.out)

    summary = {
        "drawings": {k: drawings[k] for k in ("file", "page_count", "title", "producer")},
        "specs": {k: specs[k] for k in ("file", "page_count", "title", "producer")},
        "insulation_spec_pages": insulation_pages,
        "drawing_pages": drawings["pages"],
        "spec_pages": [
            {"page": p["page"], "heading": p["heading"], "chars": p["chars"]}
            for p in specs["pages"]
        ],
        "callouts": callouts,
    }
    (args.out / "inventory.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(f"Drawings: {drawings['page_count']} pages  ({args.drawings.name})")
    print(f"Specs:    {specs['page_count']} pages  ({args.specs.name})")
    print(f"230700 / HVAC Insulation pages: {insulation_pages or 'NONE FOUND'}")
    print(f"Wrote {args.out / 'inventory.json'}")
    print(f"Wrote {args.out / 'spec_insulation.txt'}")
    print("Next: take off sizes from inventory + plans; price with SF = 2*(W+H+2t)/12*LF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
