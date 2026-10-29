# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Validate the Kisiei lexicon (lexicon/entries/*.yaml) and export it.

Outputs:
  lexicon/kisiei.csv              one row per entry (UTF-8, comma-separated)
  lexicon/kisiei.lift             LIFT 0.13 XML, importable into FieldWorks / Lexique Pro
  docs/reference/word-lists.fr.md word lists by semantic domain (French)
  docs/reference/word-lists.en.md word lists by semantic domain (English)

Usage:  uv run tools/build_lexicon.py [--check] [--only lexicon/entries/FILE.yaml]
With --check, nothing is written; the exit code is 1 if validation fails.
With --only, only that file is validated (implies --check).
"""
import csv, io, re, sys, unicodedata, pathlib
from xml.sax.saxutils import escape, quoteattr
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEX = ROOT / "lexicon"
WORDLIST = ROOT / "references" / "bible-bkg-wordforms.tsv"
BIBLE_URL = "https://www.bible.com/bible/1394/{ref}.BKG"
WORD_RE = re.compile(r"(?:[^\W\d_]|[̀-ͯ])+(?:[-'’](?:[^\W\d_]|[̀-ͯ])+)*")

STATUSES = {"attested", "confirmed", "respelled", "check"}
POS = {"noun": ("nom", "noun"), "verb": ("verbe", "verb"), "adj": ("adjectif", "adjective"),
       "adv": ("adverbe", "adverb"), "pron": ("pronom", "pronoun"), "num": ("nombre", "numeral"),
       "det": ("déterminant", "determiner"), "prep": ("préposition", "preposition"),
       "postp": ("postposition", "postposition"), "conj": ("conjonction", "conjunction"),
       "part": ("particule", "particle"), "interj": ("interjection", "interjection"),
       "ideo": ("idéophone", "ideophone"), "name": ("nom propre", "proper name")}
LIFT_POS = {"noun": "Noun", "verb": "Verb", "adj": "Adjective", "adv": "Adverb", "pron": "Pronoun",
            "num": "Numeral", "det": "Determiner", "prep": "Preposition", "postp": "Postposition",
            "conj": "Connective", "part": "Particle", "interj": "Interjection", "ideo": "Ideophone",
            "name": "Proper Noun"}
FIELDS = {"lemma", "status", "pos", "class", "plural", "forms", "gloss", "domains", "keita",
          "childs", "note", "example"}


def key(w):
    d = unicodedata.normalize("NFD", w)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn")).lower()


def toned(w):
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", w))


def load_words():
    """key -> (count, first ref, set of lower-case spellings as written in the Bible)"""
    words = {}
    for line in WORDLIST.read_text(encoding="utf-8").splitlines()[1:]:
        k, n, spellings, ref = line.split("\t")
        forms = {unicodedata.normalize("NFC", s.rpartition(" ")[0]).lower() for s in spellings.split(", ")}
        words[k] = (int(n), ref, forms)
    return words


def attested(text, words):
    return all(key(w) in words or all(p in words for p in re.split(r"[-'’]", key(w)) if p)
               for w in WORD_RE.findall(text))


def load(only=None):
    domains = {d["code"]: d for d in yaml.safe_load((LEX / "domains.yaml").read_text(encoding="utf-8"))}
    entries = []
    paths = [pathlib.Path(only)] if only else sorted((LEX / "entries").glob("*.yaml"))
    for path in paths:
        for i, e in enumerate(yaml.safe_load(path.read_text(encoding="utf-8")) or [], 1):
            e["_file"], e["_n"] = path.name, i
            entries.append(e)
    return domains, entries


def validate(domains, entries, words):
    errors, warnings, seen = [], [], {}
    for e in entries:
        where = f"{e['_file']} #{e['_n']} ({e.get('lemma', '?')})"
        unknown = set(k for k in e if not k.startswith("_")) - FIELDS
        if unknown:
            errors.append(f"{where}: unknown field(s) {sorted(unknown)}")
        for f in ("lemma", "status", "pos", "gloss", "domains"):
            if not e.get(f):
                errors.append(f"{where}: missing '{f}'")
        if e.get("status") not in STATUSES:
            errors.append(f"{where}: status must be one of {sorted(STATUSES)}")
        if e.get("pos") not in POS:
            errors.append(f"{where}: pos must be one of {sorted(POS)}")
        g = e.get("gloss") or {}
        if not (isinstance(g, dict) and g.get("fr") and g.get("en")):
            errors.append(f"{where}: gloss needs 'fr' and 'en'")
        for d in e.get("domains") or []:
            if str(d) not in domains:
                errors.append(f"{where}: unknown semantic domain {d}")
        ch = e.get("childs")
        if ch is not None and (not isinstance(ch, dict) or set(ch) - {"page", "form", "sense"}):
            errors.append(f"{where}: 'childs' takes only page, form, sense")
        lemma = str(e.get("lemma", ""))
        if e.get("status") == "attested":
            for form in [lemma] + [str(x) for x in ([e["plural"]] if e.get("plural") else []) + (e.get("forms") or [])]:
                if not attested(form, words):
                    errors.append(f"{where}: '{form}' is marked attested but is not in the Bible word list")
                    continue
                # tone marks: the Bible always writes this word with accents, but the entry does not
                for w in WORD_RE.findall(form):
                    info = words.get(key(w))
                    if info and not toned(w) and all(toned(s) for s in info[2]):
                        warnings.append(f"{where}: the Bible always writes '{w}' with tone marks "
                                        f"({', '.join(sorted(info[2]))}); use the accented spelling")
        elif e.get("status") == "respelled" and " " not in lemma and lemma and attested(lemma, words):
            warnings.append(f"{where}: '{lemma}' is in the Bible word list; status could be 'attested'")
        k = (key(lemma), e.get("pos"), (g or {}).get("fr") if isinstance(g, dict) else None)
        if k in seen:
            warnings.append(f"{where}: duplicate of {seen[k]}")
        seen[k] = where
    return errors, warnings


def bible_info(e, words):
    k = key(str(e["lemma"]))
    return words.get(k) if e["status"] == "attested" and k in words else None


def sort_key(e):
    return key(str(e["lemma"]))


def export_csv(entries, words):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["lemma", "status", "pos", "class", "plural", "forms", "gloss_fr", "gloss_en",
                "domains", "bible_count", "bible_ref", "keita_form", "keita_page", "childs_page",
                "childs_form", "southern_sense_en", "note"])
    for e in sorted(entries, key=sort_key):
        b = bible_info(e, words)
        kt, ch = e.get("keita") or {}, e.get("childs") or {}
        w.writerow([e["lemma"], e["status"], e["pos"], e.get("class", ""), e.get("plural", ""),
                    "; ".join(map(str, e.get("forms") or [])), e["gloss"]["fr"], e["gloss"]["en"],
                    " ".join(map(str, e["domains"])), b[0] if b else "", b[1] if b else "",
                    kt.get("form", ""), kt.get("page", ""), ch.get("page", ""), ch.get("form", ""),
                    ch.get("sense", ""), e.get("note", "")])
    return out.getvalue()


def export_lift(entries, domains, words):
    def form(lang, text):
        return f'<form lang="{lang}"><text>{escape(str(text))}</text></form>'
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<lift version="0.13" producer="Kisie tools/build_lexicon.py">']
    for n, e in enumerate(sorted(entries, key=sort_key), 1):
        eid = f"{e['lemma']}_{n}"
        parts.append(f"  <entry id={quoteattr(eid)}>")
        parts.append(f"    <lexical-unit>{form('kqs', e['lemma'])}</lexical-unit>")
        if e.get("class"):
            parts.append(f"    <trait name=\"noun-class\" value={quoteattr(str(e['class']))}/>")
        parts.append(f"    <trait name=\"status\" value={quoteattr(e['status'])}/>")
        if e.get("plural"):
            parts.append(f"    <field type=\"plural\">{form('kqs', e['plural'])}</field>")
        for f in e.get("forms") or []:
            parts.append(f"    <variant>{form('kqs', f)}</variant>")
        parts.append(f"    <sense id={quoteattr(eid + '_s1')}>")
        parts.append(f"      <grammatical-info value={quoteattr(LIFT_POS[e['pos']])}/>")
        parts.append(f"      <gloss lang=\"fr\"><text>{escape(e['gloss']['fr'])}</text></gloss>")
        parts.append(f"      <gloss lang=\"en\"><text>{escape(e['gloss']['en'])}</text></gloss>")
        for d in e["domains"]:
            label = f"{d} {domains[str(d)]['en']}"
            parts.append(f"      <trait name=\"semantic-domain-ddp4\" value={quoteattr(label)}/>")
        parts.append("    </sense>")
        src = []
        b = bible_info(e, words)
        if b:
            src.append(f"BKG: {b[0]} occurrences, first {b[1]}")
        if e.get("keita"):
            src.append(f"Keita 1979, p. {e['keita'].get('page', '?')}: {e['keita'].get('form', '')}")
        if e.get("childs"):
            src.append(f"Childs 2000, p. {e['childs'].get('page', '?')}"
                       + (f": {e['childs']['form']}" if e["childs"].get("form") else ""))
            if e["childs"].get("sense"):
                parts.append(f"    <field type=\"southern-kissi-sense\">{form('en', e['childs']['sense'])}</field>")
        if src:
            parts.append(f"    <note type=\"source\">{form('en', '; '.join(src))}</note>")
        if e.get("note"):
            parts.append(f"    <note>{form('fr', e['note'])}</note>")
        parts.append("  </entry>")
    parts.append("</lift>")
    return "\n".join(parts) + "\n"


TEXT = {
    "fr": {"south": "kissi du Sud (Childs 2000, en anglais)", "title": "Listes de mots", "kis": "Kisiei", "pos": "Catégorie", "gloss": "Français",
           "src": "Source", "intro": (
               "Ces listes sont produites automatiquement à partir du [lexique](https://github.com/kebasaa/kisiei-language/tree/main/lexicon) "
               "du projet ({n} entrées). Les mots sont classés par **domaines sémantiques** selon la classification "
               "[SIL Semantic Domains](https://semdom.org/v4/) ; un mot peut figurer dans plusieurs domaines. "
               "Les mots attestés renvoient à leur première occurrence dans la Bible en kisiei ; les mots "
               "<span class=\"ks-badge ks-conf\">Confirmé</span> sont absents de la Bible mais confirmés par un locuteur ; les mots "
               "<span class=\"ks-badge ks-res\">Réécrit</span> viennent de la description de 1979 et doivent être "
               "confirmés. Le lexique est aussi disponible aux formats CSV et LIFT (pour FieldWorks).")},
    "en": {"south": "Southern Kissi (Childs 2000)", "title": "Word lists", "kis": "Kisiei", "pos": "Category", "gloss": "English",
           "src": "Source", "intro": (
               "These lists are generated automatically from the project's [lexicon](https://github.com/kebasaa/kisiei-language/tree/main/lexicon) "
               "({n} entries). Words are grouped by **semantic domain** following the "
               "[SIL Semantic Domains](https://semdom.org/v4/) classification; a word may appear in several domains. "
               "Attested words link to their first occurrence in the Kisiei Bible; "
               "<span class=\"ks-badge ks-conf\">Confirmed</span> words are not in the Bible but confirmed by a speaker; "
               "<span class=\"ks-badge ks-res\">Respelled</span> words come from the 1979 description and still need "
               "confirmation. The lexicon is also available as CSV and LIFT (for FieldWorks).")},
}
FLAG = {"attested": "", "confirmed": "\\|c", "respelled": "\\|r", "check": "\\|?"}


def bible_label(ref, lang):
    src = (ROOT / "tools" / "kisiei_hooks.py").read_text(encoding="utf-8")
    books = {}
    for m in re.finditer(r'"([1-3A-Z]{3})": \("([^"]+)", "([^"]+)"\)', src):
        books[m.group(1)] = (m.group(2), m.group(3))
    book, _, rest = ref.partition(".")
    ch, _, vs = rest.partition(".")
    name = books.get(book, (book, book))[0 if lang == "fr" else 1]
    return f"{name} {ch}" + ((("," if lang == "fr" else ":") + vs) if vs else "")


def export_page(lang, entries, domains, words):
    t = TEXT[lang]
    li = 0 if lang == "fr" else 1
    by_domain = {}
    for e in entries:
        for d in e["domains"]:
            by_domain.setdefault(str(d), []).append(e)
    lines = [f"# {t['title']}", "", "<!-- Generated by tools/build_lexicon.py from lexicon/entries/*.yaml; do not edit by hand. -->", "",
             t["intro"].format(n=len(entries)), ""]
    top_seen = set()
    for code in sorted(by_domain, key=lambda c: [int(x) for x in c.split(".")]):
        top = code.split(".")[0]
        if top not in top_seen:
            top_seen.add(top)
            lines += [f"## {top}. {domains[top][lang]}", ""]
        if code != top:
            lines += [f"### {code} {domains[code][lang]}", ""]
        lines += [f"| {t['kis']} | {t['pos']} | {t['gloss']} | {t['src']} |", "| --- | --- | --- | --- |"]
        for e in sorted(by_domain[code], key=sort_key):
            word = f"{{{{{e['lemma']}{FLAG[e['status']]}}}}}"
            if e.get("plural"):
                word += f", pl. {{{{{e['plural']}{FLAG[e['status']]}}}}}"
            pos = POS[e["pos"]][li] + (f" ({e['class']})" if e.get("class") else "")
            b = bible_info(e, words)
            if b:
                src = f"[{bible_label(b[1], lang)}]({BIBLE_URL.format(ref=b[1])})"
            elif e.get("keita"):
                src = f"Keita 1979, p. {e['keita'].get('page', '?')}"
            else:
                src = ""
            gloss = e["gloss"][lang].replace("|", "/")
            sense = (e.get("childs") or {}).get("sense")
            if sense:
                gloss += f" — *{t['south']} :* {sense.replace('|', '/')}"
            lines.append(f"| {word} | {pos} | {gloss} | {src} |")
        lines.append("")
    return "\n".join(lines)


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    check = "--check" in sys.argv or only is not None
    words = load_words()
    domains, entries = load(only)
    errors, warnings = validate(domains, entries, words)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(entries)} entries, {len(errors)} errors, {len(warnings)} warnings")
    if errors:
        sys.exit(1)
    if check:
        return
    (LEX / "kisiei.csv").write_text(export_csv(entries, words), encoding="utf-8")
    (LEX / "kisiei.lift").write_text(export_lift(entries, domains, words), encoding="utf-8")
    for lang in ("fr", "en"):
        (ROOT / "docs" / "reference" / f"word-lists.{lang}.md").write_text(
            export_page(lang, entries, domains, words), encoding="utf-8")
    print("wrote lexicon/kisiei.csv, lexicon/kisiei.lift, docs/reference/word-lists.{fr,en}.md")


if __name__ == "__main__":
    main()
