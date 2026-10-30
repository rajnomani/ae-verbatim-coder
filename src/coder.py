"""Map free-text adverse event phrases to HPO terms.

Steps for each phrase:
  1. Clean it (lower case, punctuation removed).
  2. If the whole phrase is an HPO name or synonym, use that.
  3. Otherwise split it into clauses at commas, semicolons, 'and', 'but', 'with'.
  4. A clause containing a negation word (no, denies, without...) is skipped.
  5. For each other clause, try in order:
       a) the clause is an HPO name/synonym                    -> 'exact'
       b) a close spelling of one (rapidfuzz, with safety rule) -> 'fuzzy'
       c) the longest HPO name/synonym inside the clause        -> 'contained'
Text sources: HPO names, EXACT synonyms, and synonyms HPO tags 'layperson'.
Nothing is learned from the test set.

Changes after run 1 (see README): spelling match now comes before 'contained';
the spelling safety rule was added; layperson synonyms were added.
"""
import re

from rapidfuzz import fuzz, process

from load_hpo import load_terms

FUZZY_CUTOFF = 80        # whole-phrase similarity (0-100) needed for a spelling match
WORD_CUTOFF = 70         # every single word must also be at least this similar
MIN_FUZZY_LENGTH = 4     # do not spell-match very short text
MIN_CONTAINED_LENGTH = 3
SYNONYM_SCOPES = ("EXACT",)
USE_LAYPERSON = True     # also use synonyms HPO tags 'layperson', whatever their scope

NEGATION = re.compile(r"\b(no|not|denies|denied|without|absence of|negative for|nil)\b")
SPLIT = re.compile(r",|;|/|\band\b|\bbut\b|\bwith\b|\bplus\b")


def clean(text):
    """Lower case; every character that is not a letter or digit becomes a space."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def build_lexicon(terms):
    """Return {cleaned text: set of HPO ids}."""
    lex = {}
    for t in terms:
        texts = [t["name"]] + [s for s, scope in t["synonyms"] if scope in SYNONYM_SCOPES]
        if USE_LAYPERSON:
            texts += t.get("layperson", [])
        for s in texts:
            key = clean(s)
            if key:
                lex.setdefault(key, set()).add(t["id"])
    return lex


def words_close(a, b):
    """Same number of words, and each word pair is equal or at least WORD_CUTOFF similar.

    This stops 'stomach ache' being accepted as 'stomach cancer': the whole phrase
    looks similar, but 'ache' and 'cancer' are not close.
    """
    wa, wb = a.split(), b.split()
    if len(wa) != len(wb):
        return False
    return all(x == y or fuzz.ratio(x, y) >= WORD_CUTOFF for x, y in zip(wa, wb))


class Coder:
    def __init__(self, terms):
        self.lex = build_lexicon(terms)
        self.keys = list(self.lex)
        self.max_words = max(len(k.split()) for k in self.keys)

    def _result(self, key, how):
        ids = self.lex[key]
        return ids, how + ("+ambiguous" if len(ids) > 1 else "")

    def match_clause(self, clause):
        """Return (set of ids, how) for one cleaned clause, or (empty set, 'none')."""
        if clause in self.lex:
            return self._result(clause, "exact")
        if len(clause) >= MIN_FUZZY_LENGTH:
            hits = process.extract(clause, self.keys, scorer=fuzz.ratio,
                                   limit=10, score_cutoff=FUZZY_CUTOFF)
            for key, score, _ in hits:
                if words_close(clause, key):
                    return self._result(key, f"fuzzy:{score:.0f}")
        words = clause.split()
        for size in range(min(len(words), self.max_words), 0, -1):
            for start in range(len(words) - size + 1):
                piece = " ".join(words[start:start + size])
                if len(piece) >= MIN_CONTAINED_LENGTH and piece in self.lex:
                    return self._result(piece, "contained")
        return set(), "none"

    def code(self, text):
        """Return (sorted list of ids, short note on how each clause was handled)."""
        whole = clean(text)
        if whole in self.lex and not NEGATION.search(whole):
            ids, how = self._result(whole, "exact")
            return sorted(ids), how
        found = set()
        notes = []
        for raw in SPLIT.split(text.lower()):
            clause = clean(raw)
            if not clause:
                continue
            if NEGATION.search(clause):
                notes.append("negated")
                continue
            ids, how = self.match_clause(clause)
            found |= ids
            notes.append(how)
        return sorted(found), "|".join(notes) if notes else "empty"


def load_coder():
    version, terms, _ = load_terms()
    return version, terms, Coder(terms)