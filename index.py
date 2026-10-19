"""Step 3: turn every slide into a vector (a list of numbers) so you can search by meaning.

Two modes:
  text   only the words a normal PDF reader sees. This is the baseline every tutorial builds.
  slide  slide title + text + the vision model's description of the visuals (needs step 4).

Build:   python index.py --set own --mode text
Search:  python index.py --set own --mode text --query "what is overfitting?"
Fill in the 3 TODOs.
"""
import argparse

import numpy as np

import config
from jsonl import read_jsonl, write_jsonl

_model = None


def embedder():
    """Load the embedding model once (the first run downloads about 130 MB)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def load_captions(set_name: str) -> dict:
    """Captions from step 4, as {slide_id: caption}. Empty until you run captions.py."""
    path = config.SETS[set_name]["captions"]
    return {c["id"]: c for c in read_jsonl(path)} if path.exists() else {}


def slide_document(slide: dict, mode: str, caption: dict | None) -> str:
    """The text that gets embedded for one slide."""
    caption = caption or {}
    # SlideVQA slides are pictures with no text layer, so fall back to the transcription.
    text = slide["text"] or caption.get("text", "")
    # TODO(1): build the document.
    #   mode "text":  return just `text`.
    #   mode "slide": return 3 labelled lines, skipping any that are empty:
    #       "Slide title: <title>"   (slide["title"], or caption.get("title", "") if that's empty)
    #       "Text: <text>"
    #       "Visuals: <caption.get('visual', '')>"
    #   joined with "\n".
    raise NotImplementedError("TODO(1) in index.py: read the comment just above this line")


def build(set_name: str, mode: str) -> None:
    slides = read_jsonl(config.SETS[set_name]["slides"])
    captions = load_captions(set_name)
    if mode == "slide" and not captions:
        raise SystemExit("No captions yet. Run captions.py first (step 4).")
    if set_name == "svqa" and not captions:
        raise SystemExit("SlideVQA slides are images with no text layer, so even the text baseline "
                         "needs the transcriptions from captions.py (step 4).")
    docs = [slide_document(s, mode, captions.get(s["id"])) for s in slides]

    # TODO(2): turn all docs into vectors with one call:
    #   embedder().encode(docs, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    #   normalize_embeddings=True makes every vector length 1, so a dot product = cosine similarity.
    #   Store the result in `vectors`.
    raise NotImplementedError("TODO(2) in index.py: read the comment just above this line")

    out = config.INDEX_DIR / f"{set_name}_{mode}"
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "vectors.npy", np.asarray(vectors, dtype=np.float32))
    write_jsonl(out / "slides.jsonl", [{**s, "doc": d} for s, d in zip(slides, docs)])
    empty = sum(1 for d in docs if not d.strip())
    print(f"Indexed {len(docs)} slides into {out.relative_to(config.ROOT)} ({empty} had no text at all).")


_loaded = {}


def load_index(set_name: str, mode: str):
    key = (set_name, mode)
    if key not in _loaded:
        folder = config.INDEX_DIR / f"{set_name}_{mode}"
        if not (folder / "vectors.npy").exists():
            raise SystemExit(f"No index yet. Run: python index.py --set {set_name} --mode {mode}")
        _loaded[key] = (np.load(folder / "vectors.npy"), read_jsonl(folder / "slides.jsonl"))
    return _loaded[key]


def search(query: str, set_name: str = "own", mode: str = "text", k: int = config.TOP_K) -> list[dict]:
    """Return the k slides most similar to the query, best first, each with a "score"."""
    vectors, slides = load_index(set_name, mode)
    # TODO(3): rank the slides.
    #   1. q = embedder().encode([config.EMBED_QUERY_PROMPT + query], normalize_embeddings=True)[0]
    #   2. scores = vectors @ q        (one similarity score per slide)
    #   3. top = np.argsort(-scores)[:k]   (positions of the k biggest scores)
    #   4. return [{**slides[i], "score": float(scores[i])} for i in top]
    raise NotImplementedError("TODO(3) in index.py: read the comment just above this line")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="own", choices=list(config.SETS))
    parser.add_argument("--mode", default="text", choices=["text", "slide"])
    parser.add_argument("--query", help="search instead of building")
    args = parser.parse_args()
    if args.query:
        for hit in search(args.query, args.set, args.mode):
            preview = hit["doc"].replace("\n", " ")[:90]
            print(f"{hit['score']:.3f}  {hit['deck']} p.{hit['page']}  {preview}")
    else:
        build(args.set, args.mode)


if __name__ == "__main__":
    main()
