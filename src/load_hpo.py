"""Read the HPO file (hp.obo) into a simple list of terms.

Each term has: id, name, synonyms (list of (text, scope)), alt_ids.
Only active terms under 'Phenotypic abnormality' (HP:0000118) are kept,
because that branch holds the symptoms and signs. Other branches
(inheritance, frequency, clinical course) are not adverse events.
"""
import re
import sys
from pathlib import Path

HPO_PATH = Path("data/hp.obo")
ROOT_ID = "HP:0000118"  # Phenotypic abnormality

SYNONYM_RE = re.compile(
    r'^synonym:\s+"(.*)"\s+(EXACT|RELATED|NARROW|BROAD)(?:\s+([A-Za-z_]+))?\s*\[')
SYNONYM_FALLBACK_RE = re.compile(r'^synonym:\s+"(.*)"\s+(EXACT|RELATED|NARROW|BROAD)\b')


def read_stanzas(path):
    """Yield (version, term_dict) pairs; term_dict has raw fields for one [Term]."""
    version = None
    term = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("data-version:"):
                version = line.split(":", 1)[1].strip()
            if line.startswith("["):
                if term is not None:
                    yield term
                term = {"id": None, "name": None, "synonyms": [], "alt_ids": [],
                        "parents": [], "obsolete": False, "layperson": []} if line == "[Term]" else None
                continue
            if term is None or not line:
                continue
            if line.startswith("id: "):
                term["id"] = line[4:].strip()
            elif line.startswith("name: "):
                term["name"] = line[6:].strip()
            elif line.startswith("alt_id: "):
                term["alt_ids"].append(line[8:].strip())
            elif line.startswith("is_a: "):
                term["parents"].append(line[6:].split()[0])
            elif line.startswith("is_obsolete: true"):
                term["obsolete"] = True
            elif line.startswith("synonym: "):
                m = SYNONYM_RE.match(line)
                if m:
                    term["synonyms"].append((m.group(1), m.group(2)))
                    if m.group(3) == "layperson":
                        term["layperson"].append(m.group(1))
                else:
                    m = SYNONYM_FALLBACK_RE.match(line)
                    if m:
                        term["synonyms"].append((m.group(1), m.group(2)))
        if term is not None:
            yield term
    yield {"version": version}


def load_terms(path=HPO_PATH):
    """Return (version, terms, counts). terms = active terms under ROOT_ID."""
    all_terms = []
    version = None
    for item in read_stanzas(path):
        if "version" in item:
            version = item["version"]
        else:
            all_terms.append(item)
    active = [t for t in all_terms if t["id"] and not t["obsolete"]]
    children = {}
    for t in active:
        for p in t["parents"]:
            children.setdefault(p, []).append(t["id"])
    keep = {ROOT_ID}
    stack = [ROOT_ID]
    while stack:
        for c in children.get(stack.pop(), []):
            if c not in keep:
                keep.add(c)
                stack.append(c)
    terms = [t for t in active if t["id"] in keep and t["id"] != ROOT_ID]
    counts = {"stanzas": len(all_terms), "active": len(active), "kept": len(terms)}
    return version, terms, counts


def main():
    if not HPO_PATH.exists():
        sys.exit("Cannot find data/hp.obo - run this from the project folder.")
    version, terms, counts = load_terms()
    n_syn = sum(len(t["synonyms"]) for t in terms)
    print(f"HPO version:               {version}")
    print(f"Terms in file:             {counts['stanzas']}")
    print(f"Active (not obsolete):     {counts['active']}")
    print(f"Kept (symptoms and signs): {counts['kept']}")
    print(f"Synonyms on kept terms:    {n_syn}")
    n_lay = sum(len(t["layperson"]) for t in terms)
    print(f"  of which layperson:      {n_lay}")
    for want in ("Headache", "Nausea", "Dizziness", "Rash"):
        for t in terms:
            if t["name"] == want:
                syn = ", ".join(s for s, _ in t["synonyms"]) or "(none)"
                print(f"{t['id']}  {t['name']}  ->  {syn}")
                break
        else:
            print(f"(no term named exactly '{want}')")


if __name__ == "__main__":
    main()