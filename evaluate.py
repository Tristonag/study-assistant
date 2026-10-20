"""Step 2 onwards: measure how good the search (and the answers) are.

For each question it searches the index and checks:
  hit@5   is a correct slide in the top 5?          (1 or 0, averaged = "hit rate")
  MRR@10  how high is the first correct slide?      (1/rank: 1st = 1.0, 2nd = 0.5 ... not found = 0)
Results are split by question type (the "where" column), printed, and saved to results/.

Run:  python evaluate.py --set own --mode text
      python evaluate.py --set svqa --mode slide --answers 50    (also scores 50 answers)
Fill in the 2 TODOs (the metrics). Everything else already works.
"""
import argparse
import csv
import datetime
import re
from collections import defaultdict

import config
import index


def load_questions(set_name: str) -> list[dict]:
    """Read the question CSV. Every question gets a set of correct slide ids ("gold")."""
    path = config.SETS[set_name]["questions"]
    if not path.exists():
        raise SystemExit(f"No questions at {path}. "
                         + ("Copy eval/own_template.csv to eval/own.csv and write your questions."
                            if set_name == "own" else "Run: python slidevqa_download.py"))
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    questions = []
    for row in rows:
        if not row.get("question", "").strip():
            continue
        if set_name == "own":   # deck + page(s), e.g. page "12" or "12|13"
            gold = {f"{row['deck'].strip()}#p{int(p)}" for p in str(row["page"]).split("|")}
        else:
            gold = set(row["gold"].split("|"))
        questions.append({"question": row["question"].strip(), "gold": gold,
                          "answer": row.get("answer", "").strip(),
                          "where": (row.get("where") or "all").strip().lower()})
    return questions


def hit_at_k(ranked_ids: list[str], gold: set[str], k: int) -> int:
    """1 if any correct id is in the first k results, else 0."""
    return int(any(slide_id in gold for slide_id in ranked_ids[:k]))

def reciprocal_rank(ranked_ids: list[str], gold: set[str], k: int) -> float:
    """1 / (position of the first correct id), looking only at the first k. 0 if none."""
    for position, slide_id in enumerate(ranked_ids[:k], start=1):
        if slide_id in gold:
            return 1 / position
    return 0.0

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9.%]+", " ", s.lower()).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="own", choices=list(config.SETS))
    parser.add_argument("--mode", default="text", choices=["text", "slide"])
    parser.add_argument("--k", type=int, default=config.TOP_K)
    parser.add_argument("--answers", type=int, default=0, help="also generate and score this many answers (costs API calls)")
    parser.add_argument("--note", default="", help="what you changed, e.g. 'added reranker'")
    args = parser.parse_args()

    questions = load_questions(args.set)
    groups = defaultdict(lambda: {"n": 0, "hit": 0, "rr": 0.0})
    misses = []
    for q in questions:
        hits = index.search(q["question"], args.set, args.mode, k=10)
        ranked = [h["id"] for h in hits]
        hit = hit_at_k(ranked, q["gold"], args.k)
        rr = reciprocal_rank(ranked, q["gold"], 10)
        for group in (q["where"], "ALL"):
            groups[group]["n"] += 1
            groups[group]["hit"] += hit
            groups[group]["rr"] += rr
        if not hit:
            misses.append([q["question"], "|".join(sorted(q["gold"])), "|".join(ranked[:3]), q["where"]])

    answer_line = ""
    if args.answers:
        import answer
        correct, cost = 0, 0.0
        sample = [q for q in questions if q["answer"]][:args.answers]
        for q in sample:
            text, _, usage = answer.answer(q["question"], args.set, args.mode, short=True)
            correct += int(normalize(q["answer"]) in normalize(text))
            cost += usage["cost_usd"]
        answer_line = f"Answer accuracy: {correct}/{len(sample)} = {correct / max(1, len(sample)):.0%} (${cost / max(1, len(sample)):.5f} per answer)"

    print(f"\n{args.set} / {args.mode}  ({len(questions)} questions)")
    print(f"{'type':<12}{'n':>5}{f'hit@{args.k}':>9}{'MRR@10':>9}")
    rows = []
    for group in sorted(groups, key=lambda g: (g == "ALL", g)):
        g = groups[group]
        hit_rate, mrr = g["hit"] / g["n"], g["rr"] / g["n"]
        print(f"{group:<12}{g['n']:>5}{hit_rate:>9.1%}{mrr:>9.3f}")
        rows.append([group, g["n"], round(hit_rate, 4), round(mrr, 4)])
    if answer_line:
        print(answer_line)

    config.RESULTS_DIR.mkdir(exist_ok=True)
    with open(config.RESULTS_DIR / f"{args.set}_{args.mode}.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["type", "n", f"hit@{args.k}", "mrr@10"], *rows])
    history = config.RESULTS_DIR / "history.csv"
    is_new = not history.exists()
    total = groups["ALL"]
    with open(history, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["date", "set", "mode", "n", f"hit@{args.k}", "mrr@10", "note"])
        w.writerow([datetime.date.today().isoformat(), args.set, args.mode, total["n"],
                    round(total["hit"] / total["n"], 4), round(total["rr"] / total["n"], 4), args.note])
    misses_file = config.DATA / f"misses_{args.set}_{args.mode}.csv"   # in data/, so it stays private
    with open(misses_file, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["question", "gold", "top3", "where"], *misses])
    print(f"\nSaved results/{args.set}_{args.mode}.csv and added a line to results/history.csv.")
    print(f"{len(misses)} misses listed in {misses_file.relative_to(config.ROOT)}: read 5 of them and write down why each failed.")


if __name__ == "__main__":
    main()
