# Study Assistant: ask your lecture slides anything, diagrams included

Ask a question about your lecture slides and get an answer that cites the exact slide, including what's only in the diagrams, tables, charts and code screenshots.

> Rewrite the next section in your own words before you commit. Recruiters can tell.

## The problem

Most of the tools nowadays that help students study with their lecture slides only read the text layer of a PDF. Usually, in real
courses, lecture slides put a lot of their meaning or details into diagrams, tables, charts, screenshots or equations, and the tools that only extracts plain text throws it all away. If you asked the tools about a diagram, the tools either cant find the right slide or would make something up.

## Who it's for

Any student with lecture slides, at any university. My classmates are the first users.

## What it does (v1)

1. Upload your slides (PDF).
2. Ask a question.
3. Get an answer that cites the slides it used, with the slide picture shown right under the answer.

**Out of scope for v1:** accounts, a mobile app, anything that isn't slides.

## How I measure it

- **My own eval set:** 50 questions from real lecture slides, each tagged by where the answer lives (text, table, diagram, code, equation).
- **A public benchmark:** the SlideVQA retrieval test set used in the VisRAG paper (556 questions over 1,284 slides), so anyone can compare.
- **Metrics:** hit@5 (is a correct slide in the top 5?), MRR@10, answer accuracy, cost per question, response time.

## Results

Filled in as I go. Full history in `results/history.csv`.

| Version | Own set hit@5: text questions | Own set hit@5: visual questions | SlideVQA hit@5 | SlideVQA MRR@10 |
|---|---|---|---|---|
| Text-only baseline | | | | |
| + vision captions | | | | |

## Plan

- [ ] Step 0: repo, API key, cost plan
- [ ] Step 1: read slides (text, titles, page pictures)
- [ ] Step 2: eval set (my 50 questions + SlideVQA)
- [ ] Step 3: text-only baseline, measured
- [ ] Step 4: slide-aware version: a vision model reads the visuals
- [ ] Step 5: improvements, one change at a time
- [ ] Step 6: web app, deployed
- [ ] Step 7: launch to students
- [ ] Step 8: case study

## Run it yourself

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash). macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # then paste your Gemini API key into .env
python check_setup.py
```

## Cost and privacy

- Development uses the Gemini API free tier, with my own slides and the public SlideVQA set only.
- The public app uses a separate paid key with a small prepaid balance and auto-reload off, so it can never cost more than what's loaded.
- Course slides and benchmark data are never committed (`data/` is gitignored).
- The app logs counts (questions per day, cost, response time), never what people ask.

## Built with

Python, PyMuPDF, sentence-transformers (bge-small-en-v1.5), NumPy, Gemini API (gemini-3.1-flash-lite), Streamlit.
