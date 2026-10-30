"""Build the test set: messy adverse-event phrases + the correct HPO term(s).

The phrases are SYNTHETIC (written by hand, no real patients). The answer key
(expected_ids) is written here, separately from the matching code, so the
matcher cannot mark its own homework.
Run: python src/make_verbatims.py
"""
import csv
import random
import sys
from pathlib import Path

from load_hpo import load_terms

# The 17 terms the answer key covers. Names are exactly as HPO spells them.
TERMS = {
    "rash": ("HP:0000988", "Skin rash"),
    "nausea": ("HP:0002018", "Nausea"),
    "diarrhea": ("HP:0002014", "Diarrhea"),
    "headache": ("HP:0002315", "Headache"),
    "fatigue": ("HP:0012378", "Fatigue"),
    "dizziness": ("HP:0002321", "Vertigo"),
    "cough": ("HP:0012735", "Cough"),
    "vomiting": ("HP:0002013", "Vomiting"),
    "abdpain": ("HP:0002027", "Abdominal pain"),
    "constipation": ("HP:0002019", "Constipation"),
    "insomnia": ("HP:0100785", "Insomnia"),
    "pruritus": ("HP:0000989", "Pruritus"),
    "palpitations": ("HP:0001962", "Palpitations"),
    "backpain": ("HP:0003418", "Back pain"),
    "myalgia": ("HP:0003326", "Myalgia"),
    "fever": ("HP:0001945", "Fever"),
    "drymouth": ("HP:0000217", "Xerostomia"),
    "tachycardia": ("HP:0001649", "Tachycardia"),
    "sleepdist": ("HP:0002360", "Sleep disturbance"),
    "bodyache": ("HP:0033047", "Body ache"),
}

# (phrase, [term keys that are correct], category). [] means "no term applies".
ROWS = [
    # clean: official names or HPO synonyms, with ordinary case/spacing changes
    ("rash", ["rash"], "clean"), ("Skin rash", ["rash"], "clean"),
    ("nausea", ["nausea"], "clean"), ("  NAUSEA.", ["nausea"], "clean"),
    ("diarrhoea", ["diarrhea"], "clean"), ("Diarrhea", ["diarrhea"], "clean"),
    ("headache", ["headache"], "clean"), ("Headaches", ["headache"], "clean"),
    ("fatigue", ["fatigue"], "clean"), ("FATIGUE", ["fatigue"], "clean"),
    ("dizziness", ["dizziness"], "clean"), ("vertigo", ["dizziness"], "clean"),
    ("cough", ["cough"], "clean"), ("COUGH", ["cough"], "clean"),
    ("vomiting", ["vomiting"], "clean"), ("Vomiting.", ["vomiting"], "clean"),
    ("abdominal pain", ["abdpain"], "clean"), ("ABDOMINAL PAIN", ["abdpain"], "clean"),
    ("constipation", ["constipation"], "clean"), ("Constipation", ["constipation"], "clean"),
    ("insomnia", ["insomnia"], "clean"), ("INSOMNIA", ["insomnia"], "clean"),
    ("pruritus", ["pruritus"], "clean"), ("Pruritus", ["pruritus"], "clean"),
    ("palpitations", ["palpitations"], "clean"), ("PALPITATIONS", ["palpitations"], "clean"),
    ("back pain", ["backpain"], "clean"), ("BACK PAIN", ["backpain"], "clean"),
    ("myalgia", ["myalgia"], "clean"), ("Myalgia.", ["myalgia"], "clean"),
    ("fever", ["fever"], "clean"), ("FEVER", ["fever"], "clean"),
    ("xerostomia", ["drymouth"], "clean"), ("dry mouth", ["drymouth"], "clean"),
    # misspelt
    ("skin rahs", ["rash"], "misspelt"), ("nausia", ["nausea"], "misspelt"),
    ("nauseaa", ["nausea"], "misspelt"), ("diarhoea", ["diarrhea"], "misspelt"),
    ("hedache", ["headache"], "misspelt"), ("headach", ["headache"], "misspelt"),
    ("fatgue", ["fatigue"], "misspelt"), ("dizzyness", ["dizziness"], "misspelt"),
    ("couhg", ["cough"], "misspelt"), ("vomitting", ["vomiting"], "misspelt"),
    ("abdomnal pain", ["abdpain"], "misspelt"), ("constipaton", ["constipation"], "misspelt"),
    ("insomia", ["insomnia"], "misspelt"), ("pruritis", ["pruritus"], "misspelt"),
    ("palpatations", ["palpitations"], "misspelt"), ("bakc pain", ["backpain"], "misspelt"),
    ("myalgea", ["myalgia"], "misspelt"), ("fevr", ["fever"], "misspelt"),
    ("dry mouht", ["drymouth"], "misspelt"),
    # everyday / patient wording
    ("red spots on arms and chest", ["rash"], "lay"), ("skin broke out", ["rash"], "lay"),
    ("felt sick to my stomach", ["nausea"], "lay"), ("queasy", ["nausea"], "lay"),
    ("loose motions", ["diarrhea"], "lay"), ("watery stools", ["diarrhea"], "lay"),
    ("head was pounding", ["headache"], "lay"), ("pain in head", ["headache"], "lay"),
    ("felt very tired", ["fatigue"], "lay"), ("no energy", ["fatigue"], "lay"),
    ("felt dizzy", ["dizziness"], "lay"), ("room was spinning", ["dizziness"], "lay"),
    ("coughing a lot", ["cough"], "lay"), ("kept coughing at night", ["cough"], "lay"),
    ("threw up", ["vomiting"], "lay"), ("vomited twice", ["vomiting"], "lay"),
    ("stomach ache", ["abdpain"], "lay"), ("tummy pain", ["abdpain"], "lay"),
    ("constipated", ["constipation"], "lay"), ("could not pass stool", ["constipation"], "lay"),
    ("unable to sleep", ["insomnia"], "lay"), ("trouble sleeping", ["sleepdist"], "lay"),
    ("itching", ["pruritus"], "lay"), ("itchy skin", ["pruritus"], "lay"),
    ("heart racing", ["tachycardia"], "lay"), ("felt heart pounding", ["palpitations"], "lay"),
    ("backache", ["backpain"], "lay"), ("back hurts", ["backpain"], "lay"),
    ("muscle pain", ["myalgia"], "lay"), ("body aches", ["bodyache"], "lay"),
    ("high temperature", ["fever"], "lay"), ("feverish", ["fever"], "lay"),
    ("mouth felt dry", ["drymouth"], "lay"),
    # the term sits inside a longer note
    ("mild headache after dose", ["headache"], "context"),
    ("patient reports nausea", ["nausea"], "context"),
    ("nausea since morning", ["nausea"], "context"),
    ("severe fatigue for 3 days", ["fatigue"], "context"),
    ("rash on both arms", ["rash"], "context"),
    ("diarrhoea x2 days", ["diarrhea"], "context"),
    ("c/o cough", ["cough"], "context"),
    ("pt had vomiting", ["vomiting"], "context"),
    ("moderate abdominal pain", ["abdpain"], "context"),
    ("dizziness on standing", ["dizziness"], "context"),
    ("fever 38.5 C", ["fever"], "context"),
    ("insomnia for one week", ["insomnia"], "context"),
    # two or three events in one phrase
    ("headache and nausea", ["headache", "nausea"], "multi"),
    ("nausea, vomiting", ["nausea", "vomiting"], "multi"),
    ("fever with cough", ["fever", "cough"], "multi"),
    ("diarrhoea and abdominal pain", ["diarrhea", "abdpain"], "multi"),
    ("fatigue and insomnia", ["fatigue", "insomnia"], "multi"),
    ("rash and pruritus", ["rash", "pruritus"], "multi"),
    ("dizziness, headache", ["dizziness", "headache"], "multi"),
    ("constipation and back pain", ["constipation", "backpain"], "multi"),
    ("myalgia and fever", ["myalgia", "fever"], "multi"),
    ("dry mouth and palpitations", ["drymouth", "palpitations"], "multi"),
    ("vomiting and diarrhoea", ["vomiting", "diarrhea"], "multi"),
    ("cough, fatigue and fever", ["cough", "fatigue", "fever"], "multi"),
    # negated: the event did NOT happen, so it must not be coded
    ("no nausea", [], "negated"), ("denies headache", [], "negated"),
    ("no fever", [], "negated"), ("without vomiting", [], "negated"),
    ("no rash noted", [], "negated"), ("no complaints of dizziness", [], "negated"),
    ("absence of cough", [], "negated"), ("denies abdominal pain", [], "negated"),
    ("no diarrhoea", [], "negated"), ("negative for palpitations", [], "negated"),
    ("no fever but headache", ["headache"], "negated"),
    ("no vomiting, but nausea", ["nausea"], "negated"),
    ("denies cough; reports fatigue", ["fatigue"], "negated"),
    # nothing codable
    ("felt off", [], "unmappable"), ("same as before", [], "unmappable"),
    ("see notes", [], "unmappable"), ("N/A", [], "unmappable"),
    ("no complaints", [], "unmappable"), ("patient well", [], "unmappable"),
    ("unknown", [], "unmappable"), ("?", [], "unmappable"),
    ("none", [], "unmappable"), ("routine visit", [], "unmappable"),
]

OUT = Path("data/verbatims.csv")


def main():
    # 1. Every ID in the answer key must exist in HPO with the name written above.
    version, hpo_terms, _ = load_terms()
    hpo_name = {t["id"]: t["name"] for t in hpo_terms}
    bad = [(k, i, n, hpo_name.get(i)) for k, (i, n) in TERMS.items() if hpo_name.get(i) != n]
    if bad:
        for k, i, n, found in bad:
            print(f"PROBLEM {k}: {i} should be '{n}' but HPO says '{found}'")
        sys.exit("Answer key does not match HPO - fix before continuing.")
    print(f"Answer key check: all {len(TERMS)} terms found in HPO {version} with the right names")

    # 2. Mix the order (fixed seed, so the file is the same every time) and write it.
    rows = list(ROWS)
    random.Random(7).shuffle(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "verbatim", "expected_ids", "category"])
        for n, (text, keys, cat) in enumerate(rows, start=1):
            ids = ";".join(TERMS[k][0] for k in keys) if keys else "NONE"
            w.writerow([f"V{n:03d}", text, ids, cat])

    cats = {}
    for _, _, cat in rows:
        cats[cat] = cats.get(cat, 0) + 1
    print(f"Wrote {len(rows)} phrases to {OUT}")
    for cat, n in cats.items():
        print(f"  {cat:11s} {n}")


if __name__ == "__main__":
    main()