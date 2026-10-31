"""Spec layer, step 1: pull the text out of manufacturer datasheets and point at the lines that carry
MPPT count, rated AC power, max AC current and phases.

    python -I tools/specs/extract.py cache/specs/<brand>          # every PDF in the directory
    python -I tools/specs/extract.py cache/specs/<brand>/x.pdf    # one file

Runs isolated (-I): the directory holds downloaded files, never code. Writes <file>.txt (pdfplumber text,
page by page) and <file>.hits.txt (the candidate lines with page numbers) next to each PDF. Nothing is
written to data/: the YAML in data/specs/ is written by hand from the hits, with the source URL, the
datasheet's own version/date and the day it was read — the same rule as the register rows.
"""
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None
from pypdf import PdfReader

KEYS = [
    ("mppt", r"\b(no\.?|number)\s*of\s*(independent\s+)?mpp(t|\s*trackers?)|\bmppt?\s*trackers?\b|\bmpp\s*trackers?\b|mppt\s*(count|inputs?)|anzahl\s*(der\s*)?mpp"),
    ("ac_power", r"(rated|nominal|nom\.?)\s*(ac\s*)?(output\s*)?(active\s*)?power|ac\s*nominal\s*power|rated\s*power\b|nennleistung|ausgangsleistung"),
    ("ac_current", r"max(imum|\.)?\s*(ac\s*)?(output\s*)?current|max\.?\s*continuous\s*(ac\s*)?current|ausgangsstrom"),
    ("phases", r"\bphase(s)?\b|\bphasig\b|grid\s*connection\s*type|ac\s*connection"),
    ("dc_power", r"max(imum|\.)?\s*(pv|dc)\s*(input\s*)?power|max\.?\s*recommended\s*pv|dc\s*eingangsleistung"),
    ("model", r"\bmodel\b|\btype\b|typenbezeichnung"),
]


def text_of(pdf: Path) -> list[str]:
    pages = []
    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(pdf)) as doc:
                for p in doc.pages:
                    pages.append(p.extract_text(layout=True) or "")
            if any(t.strip() for t in pages):
                return pages
        except Exception as e:  # noqa: BLE001
            print(f"  pdfplumber failed ({e}); falling back to pypdf", file=sys.stderr)
    r = PdfReader(str(pdf))
    return [(p.extract_text(extraction_mode="layout") or "") for p in r.pages]


def main(target: str):
    t = Path(target)
    pdfs = sorted(t.glob("*.pdf")) if t.is_dir() else [t]
    for pdf in pdfs:
        pages = text_of(pdf)
        pdf.with_suffix(".txt").write_text("\n\f\n".join(pages), encoding="utf-8")
        hits = []
        for i, page in enumerate(pages, 1):
            for line in page.splitlines():
                s = re.sub(r"\s+", " ", line).strip()
                if not s:
                    continue
                for key, pat in KEYS:
                    if re.search(pat, s, re.I):
                        hits.append(f"p{i} [{key}] {s}")
                        break
        pdf.with_suffix(".hits.txt").write_text("\n".join(hits), encoding="utf-8")
        print(f"{pdf.name}: {len(pages)} pages, {len(hits)} candidate lines -> {pdf.with_suffix('.hits.txt').name}")


if __name__ == "__main__":
    main(sys.argv[1])
