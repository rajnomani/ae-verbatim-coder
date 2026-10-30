# ae-verbatim-coder

Suggests standard terms for messy adverse-event (AE) verbatim text, and measures how often it is right.

A "verbatim" is the words a patient or investigator wrote down, such as "felt sick to my stomach". Coding means mapping that text to a standard term. This tool maps verbatims to terms in the **Human Phenotype Ontology (HPO)**, an open terminology. It does **not** use MedDRA, which is licensed.

It suggests codes for a human to review. It is not a replacement for a trained coder and must not be used on real safety data.

## Results

All phrases are synthetic (written for this project, no patient data). The answer key was reviewed by a clinician (MBBS). The coder was frozen before the held-out set was scored.

| Set | Phrases | Exactly right | Precision | Recall |
|---|---|---|---|---|
| Development set (used to build the coder) | 133 | 110 (82.7%) | 97.2% | 81.7% |
| **Held-out set (scored once, coder frozen)** | 65 | **50 (76.9%)** | 92.2% | 78.3% |

"Exactly right" means the set of terms returned equals the answer key for that phrase. Precision and recall are counted per term.

Held-out accuracy by category: clean 7/9, misspelt 9/9, context 8/8, multi-symptom 8/8, negated 9/10, unmappable 5/6, **lay wording 4/15 (26.7%)**.

**The held-out figure is the honest one.** The development figure is higher because I looked at its mistakes while improving the coder.

## How it works
1. Text is cleaned (lower case, punctuation removed) and split into clauses at commas, "and", "with" and similar words.
2. Each clause is looked up in the HPO term names plus their EXACT synonyms, including HPO's own layperson-tagged synonyms.
3. If there is no exact match, a fuzzy match (rapidfuzz) is tried. It is only accepted if the word count matches and each word is close.
4. If that fails, the longest known term inside the clause is used.
5. A clause with a negation word before the symptom ("no", "denies", "without") is skipped.
6. If a phrase maps to more than one term, it is flagged "ambiguous".

## What changed between run 1 and run 2
| Run | Coder | Answer key | Correct |
|---|---|---|---|
| Run 1 | version 1 | original | 98/133 (73.7%) |
| Run 1, key fixed | version 1 | corrected after clinician review | 101/133 (75.9%) |
| Run 2 | version 2 | corrected | 110/133 (82.7%) |

Four answer-key decisions were made by the clinician: heart racing = Tachycardia, trouble sleeping = Sleep disturbance, body aches = Body ache, room spinning = Vertigo. Matcher version 2 added a word-level check for fuzzy matches. This stopped "stomach ache" matching "Stomach cancer". The old and new outputs are kept in `docs/`.

## Limits (read before trusting the numbers)
- All phrases are synthetic and only cover 20 common AE terms. Real verbatims are messier.
- The sets are small (133 and 65), so each percentage moves a lot if a few phrases change.
- One clinician reviewed the answer key.
- HPO describes phenotypes (mostly rare disease), not drug adverse events. Its coverage of everyday lay wording is poor, which is why lay-wording accuracy is only 26.7% held-out.
- Negation is only detected when the cue comes **before** the symptom. "nausea absent" was wrongly coded as Nausea.
- Known wrong matches: "hacking cough" gave Barking cough; "pain in my back" gave the general term Pain; "all fine" gave Small finger (HP:0030033) through fuzzy matching.
- Words with no HPO synonym (for example "cephalalgia", "sleeplessness") are not found.

## Run it
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
curl -L -o data/hp.obo http://purl.obolibrary.org/obo/hp.obo
python src/run_all.py
```
`run_all.py` builds both test sets, scores them twice, checks the two runs are byte-identical, then runs 17 independent checks (a separate recount of every result without using the coder). Note: `hp.obo` is downloaded fresh, so a newer HPO release may change the numbers slightly. This work used `hp/releases/2026-09-01`.

## Files
- `src/load_hpo.py` reads the HPO file
- `src/coder.py` the matcher
- `src/make_verbatims.py`, `src/make_heldout.py` build the two test sets and answer keys
- `src/evaluate.py` scores a set
- `src/verify_coder.py`, `src/run_all.py` checks and one-command re-run
- `data/` test sets and answer keys; `outputs/` latest results; `docs/` earlier runs

## Ideas for next
- Detect negation that comes after the symptom ("nausea absent").
- Add a hand-made lay-term table and test it on a new held-out set.
- Handle general terms such as Pain and Spinning more carefully.

## Acknowledgements and licence
This project uses the Human Phenotype Ontology (version hp/releases/2026-09-01), http://www.human-phenotype-ontology.org. The HPO file is downloaded, not stored here, and its content is not altered.

Köhler S, Doelken SC, Mungall CJ, et al. The Human Phenotype Ontology project: linking molecular biology and disease through phenotype data. *Nucleic Acids Res.* 2014;42(D1):D966-D974. doi:10.1093/nar/gkt1026

Code: MIT licence (see `LICENSE`).