"""Look up words in HPO: python src/search_hpo.py dizziness rash cough"""
import sys

from load_hpo import load_terms

version, terms, _ = load_terms()
for word in sys.argv[1:]:
    w = word.lower()
    print(f"\n== {word} ==")
    exact = []
    partial = []
    for t in terms:
        if t["name"].lower() == w:
            exact.append((t, "official name"))
            continue
        hit = [s for s, _ in t["synonyms"] if s.lower() == w]
        if hit:
            exact.append((t, "synonym"))
        elif w in t["name"].lower():
            partial.append(t)
    for t, how in exact:
        print(f"  EXACT ({how}): {t['id']}  {t['name']}")
    for t in partial[:8]:
        print(f"  contains:      {t['id']}  {t['name']}")
    if len(partial) > 8:
        print(f"  ... and {len(partial) - 8} more terms containing '{word}'")
    if not exact and not partial:
        print("  nothing found")