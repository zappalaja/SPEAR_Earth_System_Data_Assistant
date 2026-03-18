#!/usr/bin/env python3
"""Merge Nougat outputs into cleaned Markdown.

- Finds Nougat-produced markdown-like files under NOUGAT_OUT_DIR.
- For each source PDF, chooses the best matching markdown file (largest).
- Applies boilerplate filtering ONCE (so RAG stage stays clean).
- Writes cleaned .md files into MERGED_MD_DIR.
- Writes pdf_sha256.json and manifest.json for provenance.

Usage:
  python merge_nougat_md.py --pdf_dir INPUT_PDF_DIR --nougat_out NOUGAT_OUT_DIR --merged_out MERGED_MD_DIR
"""

import argparse, hashlib, json, re
from pathlib import Path

import pypdf

BOILERPLATE_PATTERNS = [
    r"^references\s*$",
    r"^acknowledg(e)?ments\s*$",
    r"copyright\s*©",
    r"all\s+rights\s+reserved",
    r"published\s+by",
    r"\bdoi:\s*",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

MISSING_PAGE_RE = re.compile(r"\[MISSING_PAGE_(?:FAIL|EMPTY|POST)(?::(\d+))?\]")


def extract_page_text(pdf_path: Path, page_num: int) -> str:
    """Extract text from a single PDF page using pypdf (0-indexed)."""
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if page_num < 0 or page_num >= len(reader.pages):
            return ""
        text = reader.pages[page_num].extract_text() or ""
        return text.strip()
    except Exception as e:
        print(f"  pypdf fallback failed for page {page_num + 1}: {e}")
        return ""


def fill_missing_pages(text: str, pdf_path: Path) -> tuple[str, int]:
    """
    Replace [MISSING_PAGE_FAIL:N] / [MISSING_PAGE_EMPTY:N] markers with
    pypdf-extracted text from the corresponding page. Returns the patched
    text and the count of pages recovered.
    """
    recovered = 0

    def _replace(match):
        nonlocal recovered
        page_str = match.group(1)
        if page_str is None:
            # [MISSING_PAGE_POST] — no page number, can't recover
            return match.group(0)
        page_num = int(page_str) - 1  # Nougat uses 1-indexed pages
        page_text = extract_page_text(pdf_path, page_num)
        if page_text:
            recovered += 1
            return f"\n\n<!-- pypdf fallback: page {page_num + 1} -->\n{page_text}\n"
        return match.group(0)  # keep marker if pypdf also fails

    patched = MISSING_PAGE_RE.sub(_replace, text)
    return patched, recovered


def clean_text(text: str) -> str:
    out_lines = []
    for line in text.splitlines():
        if any(re.search(pat, line, flags=re.IGNORECASE) for pat in BOILERPLATE_PATTERNS):
            continue
        out_lines.append(line.rstrip())
    cleaned = "\n".join(out_lines)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned.strip() + "\n"

def safe_name(stem: str) -> str:
    stem = re.sub(r"[\\/:*?\"<>|]", "_", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem[:180] if len(stem) > 180 else stem

def find_best_md(nougat_out: Path, pdf_stem: str) -> Path | None:
    candidates = []
    for ext in ("*.mmd", "*.md", "*.markdown", "*.txt"):
        for p in nougat_out.rglob(ext):
            if pdf_stem.lower() in p.stem.lower():
                candidates.append(p)
    if not candidates:
        for d in nougat_out.rglob("*"):
            if d.is_dir() and pdf_stem.lower() in d.name.lower():
                for ext in ("*.mmd", "*.md", "*.markdown", "*.txt"):
                    candidates.extend(list(d.rglob(ext)))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True)
    ap.add_argument("--nougat_out", required=True)
    ap.add_argument("--merged_out", required=True)
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    nougat_out = Path(args.nougat_out).expanduser().resolve()
    merged_out = Path(args.merged_out).expanduser().resolve()
    merged_out.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    pdf_hashes = {}
    manifest = []

    for pdf in pdfs:
        pdf_hash = sha256_file(pdf)
        pdf_hashes[pdf.name] = pdf_hash

        best_md = find_best_md(nougat_out, pdf.stem)
        if best_md is None:
            manifest.append({
                "pdf": pdf.name,
                "pdf_sha256": pdf_hash,
                "status": "missing_md",
                "nougat_md": None,
                "merged_md": None
            })
            continue

        text = best_md.read_text(errors="ignore")

        # Fill in pages that Nougat skipped/failed using pypdf
        text, pages_recovered = fill_missing_pages(text, pdf)
        if pages_recovered:
            print(f"  pypdf recovered {pages_recovered} missing page(s) for: {pdf.name}")

        cleaned = clean_text(text)

        out_name = safe_name(pdf.stem) + ".md"
        out_path = merged_out / out_name
        out_path.write_text(cleaned, encoding="utf-8")

        manifest.append({
            "pdf": pdf.name,
            "pdf_sha256": pdf_hash,
            "status": "ok",
            "nougat_md": str(best_md),
            "merged_md": str(out_path),
        })

    (merged_out / "pdf_sha256.json").write_text(json.dumps(pdf_hashes, indent=2), encoding="utf-8")
    (merged_out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    ok = sum(1 for m in manifest if m["status"] == "ok")
    missing = len(manifest) - ok
    print(f"Merged+cleaned markdown: ok={ok}, missing={missing}")
    print(f"Wrote: {merged_out/'pdf_sha256.json'}")
    print(f"Wrote: {merged_out/'manifest.json'}")

if __name__ == "__main__":
    main()
