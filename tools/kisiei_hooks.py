"""MkDocs hooks for the Kisiei guide-book: Kisiei examples, Bible references and citations.

* ``{{pɔmbɔɔ}}`` marks Kisiei text. Every word must be in the Bible word list
  (``references/bible-bkg-wordforms.tsv``, compared without tone marks and case), otherwise
  the build fails. ``{{word|r}}`` marks a form respelled from the 1979 source that the Bible
  does not contain; ``{{word|?}}`` marks a form still to check. They render as
  ``<span class="ks ks-att|ks-conf|ks-res|ks-chk">``.
* ``[[GEN.1.3]]`` (USFM book, chapter, verse or range) becomes a link to the verse on
  bible.com, written with the French or English book abbreviation of the page.
* ``[[Key]]`` or ``[[Key|text]]`` cites ``docs/references.bib``; the bibliography page gets the
  full list appended. An unknown key is a build error.
"""
import logging
import os
import re
import unicodedata

from mkdocs.exceptions import PluginError

log = logging.getLogger("mkdocs.hooks.kisiei")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIB = os.path.join(ROOT, "docs", "references.bib")
WORDS = os.path.join(ROOT, "references", "bible-bkg-wordforms.tsv")
BIBLE_URL = "https://www.bible.com/bible/1394/{ref}.BKG"
BIBLIO_PAGE = {"fr": "sources/bibliography/", "en": "en/sources/bibliography/"}

BOOKS = {  # USFM: (French, English)
    "GEN": ("Gn", "Gen"), "EXO": ("Ex", "Exod"), "LEV": ("Lv", "Lev"), "NUM": ("Nb", "Num"),
    "DEU": ("Dt", "Deut"), "JOS": ("Jos", "Josh"), "JDG": ("Jg", "Judg"), "RUT": ("Rt", "Ruth"),
    "1SA": ("1 S", "1 Sam"), "2SA": ("2 S", "2 Sam"), "1KI": ("1 R", "1 Kgs"), "2KI": ("2 R", "2 Kgs"),
    "1CH": ("1 Ch", "1 Chr"), "2CH": ("2 Ch", "2 Chr"), "EZR": ("Esd", "Ezra"), "NEH": ("Ne", "Neh"),
    "EST": ("Est", "Esth"), "JOB": ("Jb", "Job"), "PSA": ("Ps", "Ps"), "PRO": ("Pr", "Prov"),
    "ECC": ("Qo", "Eccl"), "SNG": ("Ct", "Song"), "ISA": ("Es", "Isa"), "JER": ("Jr", "Jer"),
    "LAM": ("Lm", "Lam"), "EZK": ("Ez", "Ezek"), "DAN": ("Dn", "Dan"), "HOS": ("Os", "Hos"),
    "JOL": ("Jl", "Joel"), "AMO": ("Am", "Amos"), "OBA": ("Ab", "Obad"), "JON": ("Jon", "Jonah"),
    "MIC": ("Mi", "Mic"), "NAM": ("Na", "Nah"), "HAB": ("Ha", "Hab"), "ZEP": ("So", "Zeph"),
    "HAG": ("Ag", "Hag"), "ZEC": ("Za", "Zech"), "MAL": ("Ml", "Mal"), "MAT": ("Mt", "Matt"),
    "MRK": ("Mc", "Mark"), "LUK": ("Lc", "Luke"), "JHN": ("Jn", "John"), "ACT": ("Ac", "Acts"),
    "ROM": ("Rm", "Rom"), "1CO": ("1 Co", "1 Cor"), "2CO": ("2 Co", "2 Cor"), "GAL": ("Ga", "Gal"),
    "EPH": ("Ep", "Eph"), "PHP": ("Ph", "Phil"), "COL": ("Col", "Col"), "1TH": ("1 Th", "1 Thess"),
    "2TH": ("2 Th", "2 Thess"), "1TI": ("1 Tm", "1 Tim"), "2TI": ("2 Tm", "2 Tim"), "TIT": ("Tt", "Titus"),
    "PHM": ("Phm", "Phlm"), "HEB": ("He", "Heb"), "JAS": ("Jc", "Jas"), "1PE": ("1 P", "1 Pet"),
    "2PE": ("2 P", "2 Pet"), "1JN": ("1 Jn", "1 John"), "2JN": ("2 Jn", "2 John"), "3JN": ("3 Jn", "3 John"),
    "JUD": ("Jude", "Jude"), "REV": ("Ap", "Rev"),
}
STATUS = {"": "att", "c": "conf", "r": "res", "?": "chk", "s": "south"}
TITLES = {
    "fr": {"att": "Attesté dans la Bible (BKG)", "conf": "Confirmé par un locuteur du kisiei, absent de la Bible",
           "res": "Réécrit d'après Keita 1979, absent de la Bible",
           "chk": "À vérifier", "south": "Kissi du Sud uniquement (Childs 2000), non attesté au Nord"},
    "en": {"att": "Attested in the Bible (BKG)", "conf": "Confirmed by a Kisiei speaker, not in the Bible",
           "res": "Respelled from Keita 1979, not in the Bible",
           "chk": "To check", "south": "Southern Kissi only (Childs 2000), not attested in the North"},
}
WORD_RE = re.compile(r"(?:[^\W\d_]|[\u0300-\u036f])+(?:[-'’](?:[^\W\d_]|[\u0300-\u036f])+)*")

_bib = {}
_words = set()


def key(word):
    """Comparison form: no tone marks, lower case, NFC."""
    d = unicodedata.normalize("NFD", word)
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", d).lower().replace("’", "'")


def load_words():
    words = set()
    if not os.path.exists(WORDS):
        raise PluginError(f"missing {WORDS}: run `uv run tools/build_wordlist.py` first")
    with open(WORDS, encoding="utf-8") as f:
        next(f)
        for line in f:
            words.add(line.split("\t", 1)[0])
    return words


def attested(word):
    k = key(word)
    return k in _words or all(p in _words for p in re.split(r"[-'’]", k) if p)


def load_bib():
    if not os.path.exists(BIB):
        return {}
    text = open(BIB, encoding="utf-8").read()
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", text, re.S):
        fields = {"type": m.group(1).lower()}
        for f in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*(?=\n\s*\w+\s*=|\n*$)", m.group(3), re.S):
            fields[f.group(1).lower()] = " ".join(f.group(2).split())
        if m.group(2) in entries:
            raise PluginError(f"duplicate bibliography key {m.group(2)}")
        entries[m.group(2)] = fields
    return entries


def _short(e):
    authors = [a.strip() for a in e.get("author", "").split(" and ") if a.strip()]
    last = [a.split(",")[0].strip("{}") for a in authors]
    name = (last[0] if len(last) == 1 else f"{last[0]} & {last[1]}" if len(last) == 2
            else f"{last[0]} et al." if last else e.get("title", "?"))
    return f"{name} ({e.get('year', 's.d.')})"


def _format(k, e):
    authors = " ; ".join(a.strip().strip("{}") for a in e.get("author", "").split(" and ") if a.strip())
    parts = [f"{authors + ' ' if authors else ''}({e.get('year', 's.d.')}). *{e.get('title', '')}*."]
    venue = ", ".join(x for x in (e.get("publisher") or e.get("institution") or e.get("school"),
                                  e.get("address"), e.get("note")) if x)
    if venue:
        parts.append(venue + ".")
    if e.get("url"):
        parts.append(f"<{e['url']}>")
    return f'<li id="{k}" markdown="1">' + " ".join(parts) + "</li>"


def _locale(page):
    return "en" if page.url.startswith("en/") else "fr"


def _rel(page, target):
    here = page.url if page.url.endswith("/") or page.url == "" else os.path.dirname(page.url) + "/"
    return os.path.relpath(target or ".", here or ".").replace(os.sep, "/") + "/"


def on_startup(command, dirty, **kwargs):
    global _bib, _words
    _bib = load_bib()
    _words = load_words()


def on_pre_build(config, **kwargs):
    on_startup(None, False)


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    lang = _locale(page)
    missing = []

    def checked(m):
        """Return (text, status) of a {{...}} example, recording words missing from the Bible list."""
        # inside Markdown tables the separator is written "\|"
        text, _, flag = m.group(1).replace("\\|", "|").partition("|")
        flag = flag.strip()
        if flag not in STATUS:
            raise PluginError(f"{src}: unknown Kisiei flag '|{flag}' in {m.group(0)}")
        status = STATUS[flag]
        if status == "att":
            bad = [w for w in WORD_RE.findall(text) if not attested(w)]
            if bad:
                missing.append(f"{text} ({', '.join(bad)})")
        return text, status

    def kisiei(m):
        text, status = checked(m)
        title = TITLES[lang][status]
        return f'<span class="ks ks-{status}" title="{title}">{text}</span>'

    # Mermaid diagrams: the words are checked the same way but written as plain italics,
    # since the diagram source is not Markdown (Mermaid's own {{hexagon}} shape is therefore not usable)
    def mermaid(m):
        return re.sub(r"\{\{([^{}\n]+?)\}\}", lambda w: f"<i>{checked(w)[0]}</i>", m.group(0))

    markdown = re.sub(r"^```mermaid\n.*?^```", mermaid, markdown, flags=re.S | re.M)
    markdown = re.sub(r"\{\{([^{}\n]+?)\}\}", kisiei, markdown)
    if missing:
        raise PluginError(f"{src}: not in the Bible word list (mark with |r or |?): " + "; ".join(missing))

    def bible(m):
        ref = m.group(1)
        book, rest = ref.split(".", 1)
        name = BOOKS[book][0 if lang == "fr" else 1]
        sep = "," if lang == "fr" else ":"
        ch, _, vs = rest.partition(".")
        label = f"{name} {ch}{sep}{vs}" if vs else f"{name} {ch}"
        first = ref.split("-")[0]
        return f'<a class="bref" href="{BIBLE_URL.format(ref=first)}">{label}</a>'

    markdown = re.sub(r"\[\[((?:" + "|".join(BOOKS) + r")\.\d+(?:\.\d+(?:-\d+)?)?)\]\]", bible, markdown)

    # [[Key]] -> Keita (1979); [[Key, p. 57]] -> Keita (1979, p. 57);
    # [[(Key, p. 57)]] -> (Keita 1979, p. 57); [[Key|text]] -> custom link text
    def cite(m):
        paren, body = m.group(1), m.group(2)
        body, _, text = body.partition("|")
        k, _, loc = body.partition(",")
        k, loc = k.strip(), loc.strip()
        if k not in _bib:
            raise PluginError(f"{src}: unknown citation key [[{k}]]")
        e = _bib[k]
        if e.get("shorthand"):
            short = e["shorthand"] + (f", {loc}" if loc else "")
            label = text.strip() or (f"({short})" if paren else short)
        else:
            name, year = _short(e).rsplit(" (", 1)
            year = year.rstrip(")") + (f", {loc}" if loc else "")
            label = text.strip() or (f"({name} {year})" if paren else f"{name} ({year})")
        return f'<a class="cite" href="{_rel(page, BIBLIO_PAGE[lang])}#{k}">{label}</a>'

    markdown = re.sub(r"\[\[(\(?)([A-Za-z][A-Za-z0-9_:\-]*(?:,[^\]|)]+)?(?:\|[^\]]+)?)\)?\]\]", cite, markdown)

    if src.startswith("sources/bibliography."):
        items = "\n".join(_format(k, _bib[k]) for k in sorted(_bib, key=lambda k: _short(_bib[k]).lower()))
        markdown += f'\n\n<ol class="biblio" markdown="1">\n{items}\n</ol>\n'
    return markdown
