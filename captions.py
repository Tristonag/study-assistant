"""Step 4: let a vision model read every slide picture once.

For every slide it saves:
  title, text  what's written on the slide (SlideVQA slides are pictures, so this is their text)
  visual       a description of the diagrams, charts, tables, code and equations:
               the part that plain text extraction throws away
Results go into captions.jsonl right away, so you never pay twice for a slide,
and you can stop (Ctrl+C) and carry on later.

Run:  python captions.py --set own --limit 10     (try a few, check the cost)
      python captions.py --set own                (then the rest)
Fill in the 2 TODOs.
"""
import argparse
import json
import time

import config
import llm
from jsonl import append_jsonl, read_jsonl

PROMPT = """You are reading one lecture slide.
Return JSON with exactly these keys:
"title": the slide's title, or "" if it has none.
"text": all the text on the slide, in reading order.
"visual": a precise description of every diagram, chart, table, code block, equation or picture on the slide: what it shows, its labels, and the values or relationships it shows. Use "" if the slide is only text.
Return only the JSON."""


def parse_caption(raw: str) -> dict:
    """Turn the model's reply into {"title": ..., "text": ..., "visual": ...}."""
    start = raw.find("{")
    end = raw.rfind("}")

    try:
        if start == -1:
            raise ValueError("No JSON object found")

        data = json.loads(raw[start:end + 1])

    except ValueError:
        return {"title": "", "text": "", "visual": raw.strip()}

    return {
        key: str(data.get(key) or "").strip()
        for key in ("title", "text", "visual")
    }

def caption_slide(slide: dict) -> dict:
    raw, usage = llm.ask(PROMPT, model=config.CAPTION_MODEL, images=[config.ROOT / slide["image"]],
                         max_output_tokens=1500, json_output=True)
    return {"id": slide["id"], **parse_caption(raw), **usage}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="own", choices=list(config.SETS))
    parser.add_argument("--limit", type=int, default=0, help="only caption this many (0 = all)")
    args = parser.parse_args()

    slides = read_jsonl(config.SETS[args.set]["slides"])
    path = config.SETS[args.set]["captions"]
    done = {c["id"] for c in read_jsonl(path)} if path.exists() else set()

    # TODO(2): make `todo`: the slides whose id is NOT in done.
    #   If args.limit is more than 0, keep only the first args.limit of them.
    raise NotImplementedError("TODO(2) in captions.py: read the comment just above this line")

    print(f"{len(done)} slides already captioned, {len(todo)} to do now.")
    total = 0.0
    for n, slide in enumerate(todo, 1):
        caption = caption_slide(slide)
        append_jsonl(path, caption)          # saved straight away
        total += caption["cost_usd"]
        print(f"  [{n}/{len(todo)}] {slide['deck'][:30]} p.{slide['page']}: "
              f"{len(caption['visual'])} chars of visuals, ${caption['cost_usd']:.5f}")
        time.sleep(60 / config.REQUESTS_PER_MINUTE)   # stay under the free-tier rate limit
    if todo:
        print(f"\nDone. On the paid tier this run would cost ${total:.4f} "
              f"(${total / len(todo):.5f} per slide).")
        print(f"Next: python index.py --set {args.set} --mode slide, then evaluate.py with --mode slide")


if __name__ == "__main__":
    main()
