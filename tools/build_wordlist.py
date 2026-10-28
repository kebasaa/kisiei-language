# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build references/bible-bkg-wordforms.tsv from the local Bible cache (.cache/bible).

One row per comparison form (no tone marks, lower case), with:
key, count, spellings (the written forms with their counts, most frequent first), first reference.
Only word forms and counts are written; no verse text leaves the cache.

Usage:  uv run tools/build_wordlist.py
"""
import collections
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "bible"
OUT = ROOT / "references" / "bible-bkg-wordforms.tsv"
WORD_RE = re.compile(r"(?:[^\W\d_]|[\u0300-\u036f])+(?:[-'’](?:[^\W\d_]|[\u0300-\u036f])+)*")
sys.path.insert(0, str(ROOT / "tools"))
from fetch_bible import BOOKS  # noqa: E402


def key(word):
    d = unicodedata.normalize("NFD", word)
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", d).lower().replace("’", "'")


def chapters():
    for book, n in BOOKS:
        for ch in range(1, n + 1):
            p = CACHE / f"{book}.{ch}.txt"
            if p.exists():
                yield p


def main():
    counts = collections.Counter()
    spell = collections.defaultdict(collections.Counter)
    first = {}
    n_files = 0
    for p in chapters():
        n_files += 1
        for line in p.read_text(encoding="utf-8").splitlines():
            ref, _, text = line.partition("\t")
            if ref.endswith("#h"):
                ref = ref[:-2]
            for w in WORD_RE.findall(text):
                w = unicodedata.normalize("NFC", w).replace("’", "'")
                parts = [w] + (re.split(r"[-']", w) if re.search(r"[-']", w) else [])
                for part in parts:
                    if not part:
                        continue
                    k = key(part)
                    counts[k] += 1
                    spell[k][part.lower() if part[0].isupper() and not part.isupper() else part] += 1
                    first.setdefault(k, ref)
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as f:
        f.write("key\tcount\tspellings\tfirst_ref\n")
        for k in sorted(counts):
            forms = ", ".join(f"{s} {c}" for s, c in spell[k].most_common())
            f.write(f"{k}\t{counts[k]}\t{forms}\t{first[k]}\n")
    print(f"{n_files} chapters, {sum(counts.values())} word tokens, {len(counts)} distinct forms -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
