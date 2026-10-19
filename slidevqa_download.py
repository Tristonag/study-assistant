"""Step 2: download the public SlideVQA test set (the retrieval version used in the VisRAG paper).

1,284 slide images, 556 questions, and which slide answers each question. About 100 MB.
Everything goes into data/slidevqa/, which is gitignored.

License: SlideVQA may only be used for evaluation. Never commit these files or put them
online. Just report your scores.

Run:  python slidevqa_download.py
This file is complete: you don't need to change anything.
"""
import csv
import re
from collections import defaultdict

from datasets import load_dataset

import config
from jsonl import write_jsonl

REPO = "openbmb/VisRAG-Ret-Test-SlideVQA"
OUT = config.DATA / "slidevqa"


def deck_and_page(corpus_id: str) -> tuple[str, int]:
    """'some-deck-name-7-1024.jpg' -> ('some-deck-name', 7)"""
    m = re.match(r"^(.*)-(\d+)-\d+\.jpg$", corpus_id)
    return (m.group(1), int(m.group(2))) if m else (corpus_id, 0)


def main():
    img_dir = OUT / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    try:
        print("Downloading slides (about 100 MB, takes a few minutes)...")
        corpus = load_dataset(REPO, "corpus", split="train")
        queries = load_dataset(REPO, "queries", split="train")
        qrels = load_dataset(REPO, "qrels", split="train")
    except Exception as error:
        raise SystemExit(f"Download failed: {error}\n\nIf it mentions logging in or access: make a free account at "
                         "huggingface.co, open the dataset page and accept its terms, create a Read token "
                         "(Settings > Access Tokens), run `hf auth login`, paste the token, and try again.")

    slides = []
    for n, row in enumerate(corpus):
        cid = row["corpus-id"]
        path = img_dir / f"{n:04d}.jpg"    # short file names: Windows dislikes very long paths
        if not path.exists():
            image = row["image"]
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(path, quality=92)
        deck, page = deck_and_page(cid)
        slides.append({"id": cid, "deck": deck[:40], "page": page, "title": "", "text": "",
                       "words": 0, "visual": None, "image": path.relative_to(config.ROOT).as_posix()})
    write_jsonl(config.SETS["svqa"]["slides"], slides)

    gold = defaultdict(list)
    for row in qrels:
        if row["score"] > 0:
            gold[row["query-id"]].append(row["corpus-id"])

    kept = 0
    with open(config.SETS["svqa"]["questions"], "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "gold", "answer", "where"])
        for q in queries:
            if gold[q["query-id"]]:
                writer.writerow([q["query"], "|".join(gold[q["query-id"]]), q["answer"], "slidevqa"])
                kept += 1

    print(f"Saved {len(slides)} slide images and {kept} questions to {OUT.relative_to(config.ROOT)}")
    print("These slides are pictures with no text layer, so SlideVQA scores come after step 4 (captions.py).")


if __name__ == "__main__":
    main()
