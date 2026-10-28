# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Search the local Bible cache (.cache/bible) and print hits in context with their reference.

Patterns are Python regular expressions matched against words or whole verses.
Tone marks are ignored unless --exact is given, so ``nan`` also finds ``náŋ``... only if the
letters match: ŋ and n stay distinct.

Examples:
  uv run tools/bible_concordance.py -w "pɔmbɔɔ"              # a word (tone-insensitive)
  uv run tools/bible_concordance.py -w ".*lan$" --forms       # words ending in -lan, with counts
  uv run tools/bible_concordance.py -v "\\bte\\b.*\\bpɛ\\b" -n 20  # verses with te ... pɛ
  uv run tools/bible_concordance.py -w "nhoo" --books MAT,MRK
"""
import argparse
import collections
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "bible"
WORD_RE = re.compile(r"(?:[^\W\d_]|[\u0300-\u036f])+(?:[-'’](?:[^\W\d_]|[\u0300-\u036f])+)*")
sys.path.insert(0, str(ROOT / "tools"))
from fetch_bible import BOOKS  # noqa: E402


def strip(s):
    d = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn"))


def verses(books=None):
    for book, n in BOOKS:
        if books and book not in books:
            continue
        for ch in range(1, n + 1):
            p = CACHE / f"{book}.{ch}.txt"
            if p.exists():
                for line in p.read_text(encoding="utf-8").splitlines():
                    ref, _, text = line.partition("\t")
                    if not ref.endswith("#h"):
                        yield ref, text


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-w", "--word", help="regex for a whole word")
    g.add_argument("-v", "--verse", help="regex searched in the verse text")
    ap.add_argument("-n", type=int, default=15, help="max hits shown (default 15)")
    ap.add_argument("--forms", action="store_true", help="only list the matching word forms with counts")
    ap.add_argument("--exact", action="store_true", help="do not ignore tone marks")
    ap.add_argument("--books", default="", help="comma-separated USFM codes")
    ap.add_argument("--width", type=int, default=70, help="context width for word hits")
    a = ap.parse_args()
    norm = (lambda s: s) if a.exact else strip
    books = set(a.books.split(",")) if a.books else None
    pat = re.compile(a.word or a.verse, re.I)
    forms = collections.Counter()
    shown = total = 0
    for ref, text in verses(books):
        if a.verse:
            if pat.search(norm(text)):
                total += 1
                if shown < a.n:
                    print(f"{ref:12} {text}")
                    shown += 1
            continue
        for m in WORD_RE.finditer(text):
            w = m.group(0)
            if pat.fullmatch(norm(w)):
                total += 1
                forms[w] += 1
                if not a.forms and shown < a.n:
                    s, e = max(0, m.start() - a.width), min(len(text), m.end() + a.width)
                    print(f"{ref:12} …{text[s:m.start()]}[{w}]{text[m.end():e]}…")
                    shown += 1
    if a.forms or a.word:
        print(f"\n{total} hits, {len(forms)} forms:")
        print(", ".join(f"{w} {c}" for w, c in forms.most_common(60)))
    else:
        print(f"\n{total} verses")


if __name__ == "__main__":
    sys.exit(main())
