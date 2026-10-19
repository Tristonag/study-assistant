"""All the settings in one place. Change a model, price or folder here and nowhere else."""
from pathlib import Path

# ---- Models ----------------------------------------------------------------
# Google renames models now and then. If you get a "model not found" error,
# check the current names at https://ai.google.dev/gemini-api/docs/models
CAPTION_MODEL = "gemini-3.1-flash-lite"   # reads slide images (the cheapest model that can see)
ANSWER_MODEL = "gemini-3.1-flash-lite"    # writes the answers
THINKING_LEVEL = None   # try "minimal" to save tokens; set it back to None if you get an error

EMBED_MODEL = "BAAI/bge-small-en-v1.5"    # turns text into vectors; runs free on your own PC
EMBED_QUERY_PROMPT = "Represent this sentence for searching relevant passages: "  # bge wants this before questions

# Paid-tier prices in US$ per 1 million tokens (https://ai.google.dev/gemini-api/docs/pricing).
# The free tier costs $0, but we track what it WOULD cost, so your README can say "$X per question".
PRICES = {
    "gemini-3.1-flash-lite": {"input": 0.25, "output": 1.50},
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
}
REQUESTS_PER_MINUTE = 10   # stays under the free-tier limit (see yours in AI Studio > Rate limit)

# ---- Folders ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"            # everything in here is gitignored
DECKS = DATA / "decks"          # put your lecture PDFs here
PAGES = DATA / "pages"          # page pictures get saved here
INDEX_DIR = DATA / "index"      # search indexes
RESULTS_DIR = ROOT / "results"  # eval tables: these DO get committed

# The two slide sets you test on: your own slides, and the public SlideVQA set.
SETS = {
    "own": {
        "slides": DATA / "slides.jsonl",
        "captions": DATA / "captions.jsonl",
        "questions": ROOT / "eval" / "own.csv",
    },
    "svqa": {
        "slides": DATA / "slidevqa" / "slides.jsonl",
        "captions": DATA / "slidevqa" / "captions.jsonl",
        "questions": DATA / "slidevqa" / "questions.csv",
    },
}

# ---- Reading slides and searching -------------------------------------------
IMAGE_DPI = 110            # page picture quality: sharp enough to read, small enough to be cheap
VISUAL_WORDS = 30          # a page with fewer words than this counts as "mostly visual"
VISUAL_IMAGE_SHARE = 0.3   # ...and so does a page where pictures cover 30% or more
TOP_K = 5                  # how many slides to retrieve per question
