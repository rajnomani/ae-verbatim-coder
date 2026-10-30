"""Build the HELD-OUT test set: new phrases the matcher was never tuned on.

Rule: after this file is created, nobody changes coder.py because of how it
scores here. It is run once, and whatever it scores is reported.
Phrases are SYNTHETIC. The answer key uses the same 20 terms as make_verbatims.py.
Run: python src/make_heldout.py
"""
import csv
import random
import sys
from pathlib import Path

from load_hpo import load_terms
from make_verbatims import TERMS

ROWS = [
    # clean: medical wording or synonyms not used in the development set
    ("tachycardia", ["tachycardia"], "clean"), ("sleep disturbance", ["sleepdist"], "clean"),
    ("body ache", ["bodyache"], "clean"), ("pyrexia", ["fever"], "clean"),
    ("emesis", ["vomiting"], "clean"), ("cephalalgia", ["headache"], "clean"),
    ("palpitation", ["palpitations"], "clean"), ("sleeplessness", ["insomnia"], "clean"),
    ("tiredness", ["fatigue"], "clean"),
    # misspelt
    ("diarreah", ["diarrhea"], "misspelt"), ("headake", ["headache"], "misspelt"),
    ("fatique", ["fatigue"], "misspelt"), ("vomitng", ["vomiting"], "misspelt"),
    ("constipatoin", ["constipation"], "misspelt"), ("insomnnia", ["insomnia"], "misspelt"),
    ("palpitaions", ["palpitations"], "misspelt"), ("feaver", ["fever"], "misspelt"),
    ("nausa", ["nausea"], "misspelt"),
    # everyday / patient wording
    ("sore tummy", ["abdpain"], "lay"), ("cant sleep", ["insomnia"], "lay"),
    ("feeling sick", ["nausea"], "lay"), ("runny tummy", ["diarrhea"], "lay"),
    ("itchy all over", ["pruritus"], "lay"), ("throwing up", ["vomiting"], "lay"),
    ("tired all the time", ["fatigue"], "lay"), ("dizzy spells", ["dizziness"], "lay"),
    ("hacking cough", ["cough"], "lay"), ("sore muscles", ["myalgia"], "lay"),
    ("pain in my back", ["backpain"], "lay"), ("mouth very dry", ["drymouth"], "lay"),
    ("skin rashes", ["rash"], "lay"), ("bowels not opening", ["constipation"], "lay"),
    ("running a temperature", ["fever"], "lay"),
    # the term sits inside a longer note
    ("headache since yesterday", ["headache"], "context"),
    ("vomiting after meals", ["vomiting"], "context"),
    ("slight fever in the evening", ["fever"], "context"),
    ("ongoing cough for two weeks", ["cough"], "context"),
    ("complains of abdominal pain", ["abdpain"], "context"),
    ("palpitations at night", ["palpitations"], "context"),
    ("constipation x 3 days", ["constipation"], "context"),
    ("back pain on lifting", ["backpain"], "context"),
    # two or three events in one phrase
    ("nausea and headache", ["nausea", "headache"], "multi"),
    ("vomiting, fever", ["vomiting", "fever"], "multi"),
    ("rash, itching", ["rash", "pruritus"], "multi"),
    ("insomnia and fatigue", ["insomnia", "fatigue"], "multi"),
    ("diarrhoea, vomiting", ["diarrhea", "vomiting"], "multi"),
    ("dry mouth, constipation", ["drymouth", "constipation"], "multi"),
    ("headache, dizziness and nausea", ["headache", "dizziness", "nausea"], "multi"),
    ("fever and body ache", ["fever", "bodyache"], "multi"),
    # negated
    ("no vomiting", [], "negated"), ("denies fever", [], "negated"),
    ("no headache reported", [], "negated"), ("without nausea", [], "negated"),
    ("no cough or fever", [], "negated"), ("denied dizziness", [], "negated"),
    ("no abdominal pain, no diarrhoea", [], "negated"), ("nausea absent", [], "negated"),
    ("no rash but itching", ["pruritus"], "negated"),
    ("denies headache but reports nausea", ["nausea"], "negated"),
    # nothing codable
    ("all fine", [], "unmappable"), ("nil", [], "unmappable"),
    ("as per previous visit", [], "unmappable"), ("patient comfortable", [], "unmappable"),
    ("check-up", [], "unmappable"), ("refused to answer", [], "unmappable"),
]

OUT = Path("data/verbatims_heldout.csv")


def main():
    version, hpo_terms, _ = load_terms()
    hpo_name = {t["id"]: t["name"] for t in hpo_terms}
    bad = [(k, i, n) for k, (i, n) in TERMS.items() if hpo_name.get(i) != n]
    if bad:
        sys.exit(f"Answer key does not match HPO: {bad}")
    rows = list(ROWS)
    random.Random(11).shuffle(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "verbatim", "expected_ids", "category"])
        for n, (text, keys, cat) in enumerate(rows, start=1):
            ids = ";".join(TERMS[k][0] for k in keys) if keys else "NONE"
            w.writerow([f"H{n:03d}", text, ids, cat])
    cats = {}
    for _, _, cat in rows:
        cats[cat] = cats.get(cat, 0) + 1
    print(f"Wrote {len(rows)} held-out phrases to {OUT}")
    for cat, n in cats.items():
        print(f"  {cat:11s} {n}")


if __name__ == "__main__":
    main()