"""Run the coder on data/verbatims.csv and compare with the answer key.

Writes outputs/predictions.csv and outputs/accuracy_by_category.csv.
Run: python src/evaluate.py
"""
import csv
import sys
from pathlib import Path

from coder import load_coder

if len(sys.argv) > 1 and sys.argv[1] == "heldout":
    VERBATIMS = Path("data/verbatims_heldout.csv")
    PRED_OUT = Path("outputs/heldout_predictions.csv")
    CAT_OUT = Path("outputs/heldout_accuracy_by_category.csv")
else:
    VERBATIMS = Path("data/verbatims.csv")
    PRED_OUT = Path("outputs/predictions.csv")
    CAT_OUT = Path("outputs/accuracy_by_category.csv")


def split_ids(cell):
    return set() if cell == "NONE" else set(cell.split(";"))


def run():
    """Return (version, rows). Each row has the phrase, key, prediction and verdict."""
    version, terms, coder = load_coder()
    name = {t["id"]: t["name"] for t in terms}
    rows = []
    with open(VERBATIMS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            expected = split_ids(r["expected_ids"])
            ids, how = coder.code(r["verbatim"])
            predicted = set(ids)
            rows.append({
                "id": r["id"], "verbatim": r["verbatim"], "category": r["category"],
                "expected": ";".join(sorted(expected)) or "NONE",
                "predicted": ";".join(sorted(predicted)) or "NONE",
                "predicted_names": "; ".join(name.get(i, i) for i in sorted(predicted)),
                "how": how,
                "correct": "yes" if predicted == expected else "no",
                "tp": len(predicted & expected), "fp": len(predicted - expected),
                "fn": len(expected - predicted),
            })
    return version, rows


def summarise(rows):
    """Return {category: (n, n_correct)} plus an 'ALL' entry, and TP/FP/FN totals."""
    cats = {}
    for r in rows:
        n, ok = cats.get(r["category"], (0, 0))
        cats[r["category"]] = (n + 1, ok + (r["correct"] == "yes"))
    cats["ALL"] = (len(rows), sum(r["correct"] == "yes" for r in rows))
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    return cats, tp, fp, fn


def main():
    version, rows = run()
    PRED_OUT.parent.mkdir(exist_ok=True)
    cols = ["id", "verbatim", "category", "expected", "predicted", "predicted_names",
            "how", "correct"]
    with open(PRED_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    cats, tp, fp, fn = summarise(rows)
    with open(CAT_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "phrases", "correct", "percent_correct"])
        for c, (n, ok) in cats.items():
            w.writerow([c, n, ok, f"{100 * ok / n:.1f}"])

    print(f"HPO version: {version}")
    print(f"{'category':12s} {'phrases':>7s} {'correct':>7s} {'percent':>8s}")
    for c, (n, ok) in cats.items():
        print(f"{c:12s} {n:7d} {ok:7d} {100 * ok / n:7.1f}%")
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    print(f"\nTerm level: TP={tp} FP={fp} FN={fn}  "
          f"precision={100 * precision:.1f}%  recall={100 * recall:.1f}%")
    print("\nPhrases coded wrongly:")
    for r in rows:
        if r["correct"] == "no":
            print(f"  {r['id']} [{r['category']}] '{r['verbatim']}'  "
                  f"expected {r['expected']}  got {r['predicted']}  ({r['how']})")
    print(f"\nWrote {PRED_OUT} and {CAT_OUT}")


if __name__ == "__main__":
    main()