"""Step 1: read every PDF in data/decks/ page by page.

For each page it keeps the text, the slide title and a PNG picture of the page,
and flags pages that are mostly visual (diagrams, screenshots, charts).

Run:  python ingest.py
Done when it prints a summary and data/slides.jsonl exists.
Fill in the 3 TODOs. Everything else already works.
"""
import pymupdf  # PyMuPDF: reads PDFs (pip install pymupdf)

import config
from jsonl import write_jsonl


def slide_title(page) -> str:
    """Return the slide title: the line of text with the biggest font on the page."""
    # TODO(1): find the line with the biggest font size.
    #   page.get_text("dict")["blocks"] is a list of blocks.
    #   A text block has block["lines"]; each line has line["spans"];
    #   each span has span["text"] and span["size"] (font size).
    #   Picture blocks have no "lines", so use block.get("lines", []).
    #   Join the spans' text to get the line's text. Keep the biggest one.
    #   Return "" if the page has no text. Cut it to 150 characters.
    raise NotImplementedError("TODO(1) in ingest.py: read the comment just above this line")


def image_share(page) -> float:
    """Return how much of the page (0.0 to 1.0) is covered by pictures."""
    # TODO(2): add up the area of every picture on the page, divided by the page area.
    #   page.get_image_info() gives one dict per picture, with info["bbox"] = (x0, y0, x1, y1).
    #   pymupdf.Rect(info["bbox"]) & page.rect  clips it to the page.
    #   A Rect has .width and .height. page.rect is the whole page.
    #   Pictures can overlap, so cap the result at 1.0 with min().
    raise NotImplementedError("TODO(2) in ingest.py: read the comment just above this line")


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
        # TODO(3): fill in these 4 things, then the dict below is complete.
        #   text   = the page's text: page.get_text(), with .strip()
        #   words  = how many words: len(text.split())
        #   save the page picture: page.get_pixmap(dpi=config.IMAGE_DPI).save(image_path)
        #          (only if image_path doesn't exist yet, so re-runs are fast)
        #   visual = True if words < config.VISUAL_WORDS
        #            or image_share(page) >= config.VISUAL_IMAGE_SHARE
        raise NotImplementedError("TODO(3) in ingest.py: read the comment just above this line")
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
