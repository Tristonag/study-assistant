"""Step 1: read every PDF in data/decks/ page by page.

For each page it keeps the text, the slide title and a PNG picture of the page,
and flags pages that are mostly visual (diagrams, screenshots, charts).

Run:  python ingest.py
Done when it prints a summary and data/slides.jsonl exists.
"""
import pymupdf  # PyMuPDF: reads PDFs (pip install pymupdf)

import config
from jsonl import write_jsonl


def slide_title(page) -> str:
    """Return the slide title: the line of text with the biggest font on the page."""
    biggest_size = 0
    title = ""
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"]).strip()
            size = max((span["size"] for span in line["spans"]), default=0)

            if text and size > biggest_size:
                biggest_size = size
                title = text
    return title[:150]


def image_share(page) -> float:
    """Return how much of the page (0.0 to 1.0) is covered by pictures."""
    page_area = page.rect.width * page.rect.height
    total_area = 0
    for info in page.get_image_info():
        rect = pymupdf.Rect(info["bbox"]) & page.rect
        area = rect.width * rect.height
        if area >= 0.9 * page_area:
            continue  # full-page picture = slide background, not a diagram
        total_area += area

    return min(total_area / page_area, 1.0)


def ingest_pdf(pdf_path) -> list[dict]:
    """Read one PDF and return one dict per page."""
    doc = pymupdf.open(pdf_path)
    deck = pdf_path.stem                      # the file name without ".pdf"
    out_dir = config.PAGES / deck
    out_dir.mkdir(parents=True, exist_ok=True)

    slides = []
    for i, page in enumerate(doc):
        n = i + 1                             # people count pages from 1
        image_path = out_dir / f"p{n:03d}.png"
        text = page.get_text().strip()
        words = len(text.split())

        if not image_path.exists():
            page.get_pixmap(dpi=config.IMAGE_DPI).save(image_path)

        visual = (
            words < config.VISUAL_WORDS
            or (image_share(page) >= config.VISUAL_IMAGE_SHARE
                and words < config.VISUAL_MAX_WORDS)
        )

        slides.append({
            "id": f"{deck}#p{n}",
            "deck": deck,
            "page": n,
            "title": slide_title(page),
            "text": text,
            "words": words,
            "visual": visual,
            "image": image_path.relative_to(config.ROOT).as_posix(),
        })
    return slides


def main():
    config.DECKS.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(config.DECKS.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {config.DECKS}\n"
                         "Put your lecture slides there first (save PowerPoint files as PDF).")
    slides = []
    for pdf in pdfs:
        pages = ingest_pdf(pdf)
        slides += pages
        print(f"  {pdf.name}: {len(pages)} pages, {sum(p['visual'] for p in pages)} mostly visual")

    out = config.SETS["own"]["slides"]
    write_jsonl(out, slides)
    n_visual = sum(s["visual"] for s in slides)
    print(f"\n{len(pdfs)} decks, {len(slides)} pages. "
          f"{n_visual} pages ({n_visual / len(slides):.0%}) are mostly visual.")
    print(f"Saved to {out.relative_to(config.ROOT)}")
    print("Put that % in your README. It's the first number that shows why this project exists.")


if __name__ == "__main__":
    main()