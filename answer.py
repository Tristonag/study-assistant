"""Step 3: answer a question from the slides, citing the slides it used.

Run:  python answer.py "What is the difference between bagging and boosting?"
      python answer.py --mode slide "..."      (after step 4)
Fill in the TODO.
"""
import argparse

import config
import index
import llm

SYSTEM = ("You are a study assistant. Answer ONLY from the slides you are given. "
          "After each fact, cite the slide it came from, like [deck p.12]. "
          "If the slides don't contain the answer, say \"I couldn't find that in your slides.\" "
          "Never guess.")


def cite(slide: dict) -> str:
    return f"[{slide['deck']} p.{slide['page']}]"


def build_prompt(question: str, hits: list[dict]) -> str:
    """Put the retrieved slides and the question into one prompt."""
    # TODO(1): build a prompt that looks like this:
    #
    #   Slides:
    #
    #   [ML_L06 p.12]
    #   <the slide's "doc" text>
    #
    #   ---
    #
    #   [ML_L06 p.13]
    #   <doc>
    #
    #   Question: <question>
    #
    #   Use cite(hit) for each label and hit["doc"] for the text.
    #   Hint: make a list of blocks, then "\n\n---\n\n".join(blocks).
    raise NotImplementedError("TODO(1) in answer.py: read the comment just above this line")


def answer(question: str, set_name: str = "own", mode: str = "text", k: int = config.TOP_K,
           short: bool = False) -> tuple[str, list[dict], dict]:
    """Returns (answer_text, slides_used, usage)."""
    hits = index.search(question, set_name, mode, k)
    prompt = build_prompt(question, hits)
    if short:   # used by evaluate.py to score answers against SlideVQA's short gold answers
        prompt += "\n\nReply with only the answer, in as few words as possible, with no citation."
    text, usage = llm.ask(prompt, system=SYSTEM, max_output_tokens=120 if short else 600)
    return text, hits, usage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--set", default="own", choices=list(config.SETS))
    parser.add_argument("--mode", default="text", choices=["text", "slide"])
    args = parser.parse_args()
    text, hits, usage = answer(args.question, args.set, args.mode)
    print(f"\n{text}\n\nSlides searched:")
    for hit in hits:
        print(f"  {hit['score']:.3f}  {cite(hit)}  {hit['image']}")
    print(f"\n{usage['input_tokens']} tokens in, {usage['output_tokens']} out, "
          f"${usage['cost_usd']:.5f} on the paid tier")


if __name__ == "__main__":
    main()
