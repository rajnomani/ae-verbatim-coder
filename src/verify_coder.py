"""Independent checks on the results.

This script does NOT use the coder, rapidfuzz or the HPO parser. It reads the
answer keys and the prediction files with the plain csv module, recounts every
number itself, and fails loudly if anything disagrees.
Run: python src/verify_coder.py
"""
import csv
import re
import sys
from pathlib import Path

SETS = [
    # name, answer key, predictions, accuracy table, expected number of phrases
    ("dev", "data/verbatims.csv", "outputs/predictions.csv",
     "outputs/accuracy_by_category.csv", 133),
    ("heldout", "data/verbatims_heldout.csv", "outputs/heldout_predictions.csv",
     "outputs/heldout_accuracy_by_category.csv", 65),
]
HPO_FILE = Path("data/hp.obo")
ID_PATTERN = re.compile(r"^HP:\d{7}$")

results = []


def check(label, ok):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + label)


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ids(cell):
    return set() if cell == "NONE" else set(cell.split(";"))


def hpo_ids():
    """Every 'id: HP:...' line in the HPO file (plain text scan)."""
    found = set()
    with open(HPO_FILE, encoding="utf-8") as f:
        for line in f:
            if line.startswith("id: HP:"):
                found.add(line[4:].strip())
    return found


def main():
    known = hpo_ids() if HPO_FILE.exists() else None
    phrases = {}
    for name, key_path, pred_path, cat_path, n_expected in SETS:
        key, pred, cats = read(key_path), read(pred_path), read(cat_path)
        print(f"\n--- {name} set ---")
        check(f"[{name}] {n_expected} phrases in the answer key", len(key) == n_expected)
        check(f"[{name}] predictions cover exactly the same phrases, in the same order",
              [(r["id"], r["verbatim"]) for r in key] == [(r["id"], r["verbatim"]) for r in pred])
        check(f"[{name}] answer key was copied into the predictions unchanged",
              all(ids(k["expected_ids"]) == ids(p["expected"]) for k, p in zip(key, pred)))
        every_id = [i for r in key for i in ids(r["expected_ids"])] + \
                   [i for r in pred for i in ids(r["predicted"])]
        check(f"[{name}] every code looks like HP:0000000", all(ID_PATTERN.match(i) for i in every_id))
        if known is not None:
            missing = sorted({i for r in pred for i in ids(r["predicted"])} - known)
            check(f"[{name}] every predicted code exists in the HPO file {missing[:3] or ''}", not missing)

        # Recount from scratch: a phrase is right only if the two sets of codes are identical.
        recount = {}
        tp = fp = fn = 0
        verdict_ok = True
        for k, p in zip(key, pred):
            want, got = ids(k["expected_ids"]), ids(p["predicted"])
            right = want == got
            verdict_ok = verdict_ok and (p["correct"] == ("yes" if right else "no"))
            n, ok = recount.get(k["category"], (0, 0))
            recount[k["category"]] = (n + 1, ok + right)
            tp, fp, fn = tp + len(want & got), fp + len(got - want), fn + len(want - got)
        check(f"[{name}] each 'correct' verdict in the predictions file matches my recount", verdict_ok)
        table = {r["category"]: (int(r["phrases"]), int(r["correct"])) for r in cats}
        total = (sum(n for n, _ in recount.values()), sum(ok for _, ok in recount.values()))
        mine = dict(recount, ALL=total)
        check(f"[{name}] accuracy table matches my recount for every category", table == mine)
        shown = {r["category"]: r["percent_correct"] for r in cats}
        check(f"[{name}] percentages in the table are right",
              all(abs(float(shown[c]) - 100 * ok / n) < 0.06 for c, (n, ok) in mine.items()))
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        print(f"      my recount: {total[1]} of {total[0]} correct "
              f"({100 * total[1] / total[0]:.1f}%), TP={tp} FP={fp} FN={fn}, "
              f"precision {100 * precision:.1f}%, recall {100 * recall:.1f}%")
        phrases[name] = {re.sub(r"\W+", " ", r["verbatim"].lower()).strip() for r in key}

    print("\n--- both sets ---")
    overlap = phrases["dev"] & phrases["heldout"]
    check(f"no phrase appears in both sets {sorted(overlap)[:3] or ''}", not overlap)

    failed = results.count(False)
    print()
    if failed:
        print(f"{failed} of {len(results)} CHECKS FAILED")
        sys.exit(1)
    print(f"ALL {len(results)} CHECKS PASS")


if __name__ == "__main__":
    main()