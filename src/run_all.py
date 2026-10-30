"""Rebuild everything twice, confirm the two runs are identical, then verify.

Run: python src/run_all.py
"""
import hashlib
import subprocess
import sys
from pathlib import Path

STEPS = [
    ["src/make_verbatims.py"],
    ["src/make_heldout.py"],
    ["src/evaluate.py"],
    ["src/evaluate.py", "heldout"],
]
FILES = [
    "data/verbatims.csv",
    "data/verbatims_heldout.csv",
    "outputs/predictions.csv",
    "outputs/accuracy_by_category.csv",
    "outputs/heldout_predictions.csv",
    "outputs/heldout_accuracy_by_category.csv",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_once():
    for step in STEPS:
        done = subprocess.run([sys.executable] + step, capture_output=True, text=True)
        if done.returncode != 0:
            print(done.stdout)
            print(done.stderr)
            sys.exit(f"FAILED while running: {' '.join(step)}")
    return {f: sha(f) for f in FILES}


def main():
    print("Run 1 of 2 ...")
    first = run_once()
    print("Run 2 of 2 ...")
    second = run_once()
    print()
    same = True
    for f in FILES:
        ok = first[f] == second[f]
        same = same and ok
        print(f"{'identical' if ok else 'DIFFERENT':10s} {first[f][:12]}  {second[f][:12]}  {f}")
    if not same:
        sys.exit("\nThe two runs gave different files.")
    print(f"\nAll {len(FILES)} files identical across both runs.\n")
    check = subprocess.run([sys.executable, "src/verify_coder.py"])
    sys.exit(check.returncode)


if __name__ == "__main__":
    main()