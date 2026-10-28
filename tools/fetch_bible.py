# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Download the Kisiei Bible (BKG, bible.com version 1394) into a local text cache.

Each chapter is saved as ``.cache/bible/<BOOK>.<CH>.txt`` with one line per verse
(``GEN.1.3<TAB>text``) and one line per section heading (``GEN.1#h<TAB>text``).
Footnotes are left out. The cache is ignored by git: the Bible text is
(c) Alliance Biblique en Guinée and stays on the local machine.

Usage:  uv run tools/fetch_bible.py [--delay 1.0] [--books GEN,EXO]
Chapters already in the cache are skipped, so the script can be re-run to resume.
"""
import argparse
import html.parser
import pathlib
import sys
import time
import unicodedata
import urllib.error
import urllib.request

VERSION = 1394
URL = "https://www.bible.com/bible/{v}/{book}.{ch}.BKG"
CACHE = pathlib.Path(__file__).resolve().parent.parent / ".cache" / "bible"

# USFM book codes with their number of chapters (Protestant canon, 66 books).
BOOKS = [
    ("GEN", 50), ("EXO", 40), ("LEV", 27), ("NUM", 36), ("DEU", 34), ("JOS", 24), ("JDG", 21), ("RUT", 4),
    ("1SA", 31), ("2SA", 24), ("1KI", 22), ("2KI", 25), ("1CH", 29), ("2CH", 36), ("EZR", 10), ("NEH", 13),
    ("EST", 10), ("JOB", 42), ("PSA", 150), ("PRO", 31), ("ECC", 12), ("SNG", 8), ("ISA", 66), ("JER", 52),
    ("LAM", 5), ("EZK", 48), ("DAN", 12), ("HOS", 14), ("JOL", 3), ("AMO", 9), ("OBA", 1), ("JON", 4),
    ("MIC", 7), ("NAM", 3), ("HAB", 3), ("ZEP", 3), ("HAG", 2), ("ZEC", 14), ("MAL", 4),
    ("MAT", 28), ("MRK", 16), ("LUK", 24), ("JHN", 21), ("ACT", 28), ("ROM", 16), ("1CO", 16), ("2CO", 13),
    ("GAL", 6), ("EPH", 6), ("PHP", 4), ("COL", 4), ("1TH", 5), ("2TH", 3), ("1TI", 6), ("2TI", 4),
    ("TIT", 3), ("PHM", 1), ("HEB", 13), ("JAS", 5), ("1PE", 5), ("2PE", 3), ("1JN", 5), ("2JN", 1),
    ("3JN", 1), ("JUD", 1), ("REV", 22),
]


class ChapterParser(html.parser.HTMLParser):
    """Collect verse and heading text from the chapter markup.

    Verses are ``<span class="..._verse" data-usfm="GEN.1.3">`` containing ``..._content``
    spans; footnotes (``..._note``) and verse numbers (``..._label``) are skipped.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # one entry per open span/div: its role or None
        self.verse = None        # current verse reference
        self.chapter = None      # data-usfm of the chapter container
        self.verses = {}         # ref -> list of text pieces, in order
        self.order = []
        self.headings = []
        self._heading = None

    @staticmethod
    def _role(attrs):
        cls = dict(attrs).get("class") or ""
        for c in cls.split():
            for role in ("verse", "content", "note", "label", "heading", "chapter"):
                if c.endswith("_" + role):
                    return role
        return None

    def _inside(self, role):
        return role in self.stack

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "img", "hr", "input", "meta", "link"):
            return
        role = self._role(attrs)
        usfm = dict(attrs).get("data-usfm")
        if role == "chapter" and usfm:
            self.chapter = usfm
        if role == "verse" and usfm:
            self.verse = usfm.split("+")[0]
            if self.verse not in self.verses:
                self.verses[self.verse] = []
                self.order.append(self.verse)
        if role == "heading":
            self._heading = []
        self.stack.append(role)

    def handle_endtag(self, tag):
        if tag in ("br", "img", "hr", "input", "meta", "link") or not self.stack:
            return
        role = self.stack.pop()
        if role == "heading" and self._heading is not None:
            text = " ".join("".join(self._heading).split())
            if text:
                self.headings.append((self.verse, text))
            self._heading = None
        if role == "verse":
            self.verse = None

    def handle_data(self, data):
        if self._inside("note") or self._inside("label"):
            return
        if self._heading is not None:
            self._heading.append(data)
        elif self.verse and self._inside("content"):
            self.verses[self.verse].append(data)


def fetch(book, ch):
    req = urllib.request.Request(URL.format(v=VERSION, book=book, ch=ch),
                                 headers={"User-Agent": "Mozilla/5.0 (Kisiei guide research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def save(book, ch, page):
    p = ChapterParser()
    p.feed(page)
    if p.chapter != f"{book}.{ch}" or not p.order:
        return 0
    lines = []
    seen_headings = set()
    heads = {}
    for after, text in p.headings:
        heads.setdefault(after, []).append(text)
    for text in heads.get(None, []):
        lines.append(f"{book}.{ch}#h\t{text}")
    for ref in p.order:
        text = unicodedata.normalize("NFC", " ".join("".join(p.verses[ref]).split()))
        if text:
            lines.append(f"{ref}\t{text}")
        for h in heads.get(ref, []):
            if (ref, h) not in seen_headings:
                lines.append(f"{book}.{ch}#h\t{unicodedata.normalize('NFC', h)}")
                seen_headings.add((ref, h))
    (CACHE / f"{book}.{ch}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(p.order)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--books", default="")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    wanted = set(args.books.split(",")) if args.books else None
    done = missing = 0
    for book, n in BOOKS:
        if wanted and book not in wanted:
            continue
        for ch in range(1, n + 1):
            if (CACHE / f"{book}.{ch}.txt").exists():
                continue
            try:
                page = fetch(book, ch)
                verses = save(book, ch, page)
            except urllib.error.HTTPError as e:
                verses = 0
                print(f"{book}.{ch}: HTTP {e.code}", flush=True)
            except Exception as e:  # network hiccup: report and go on; a re-run resumes
                verses = 0
                print(f"{book}.{ch}: {e}", flush=True)
            if verses:
                done += 1
            else:
                missing += 1
                print(f"{book}.{ch}: not available", flush=True)
            if (done + missing) % 50 == 0:
                print(f"... {done} chapters saved, {missing} not available", flush=True)
            time.sleep(args.delay)
    print(f"Finished: {done} chapters saved, {missing} not available", flush=True)


if __name__ == "__main__":
    sys.exit(main())
