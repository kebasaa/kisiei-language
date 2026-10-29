# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Validate the Kisiei lexicon (lexicon/entries/*.yaml) and export it.

Outputs:
  lexicon/kisiei.csv              one row per entry, headword first (UTF-8, comma-separated)
  lexicon/kisiei.tsv              the same table, tab-separated
  lexicon/cldf/                   CLDF Dictionary module (entries, senses, languages, sources)
  lexicon/kisiei.lift             LIFT 0.13 XML, importable into FieldWorks / Lexique Pro
  docs/reference/dictionary.{fr,en}.md     alphabetical dictionary, Kisiei-French / Kisiei-English
  docs/reference/reverse-index.{fr,en}.md  French-Kisiei / English-Kisiei index
  docs/reference/word-lists.{fr,en}.md     word lists by semantic domain

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

STATUSES = {"attested", "confirmed", "respelled", "check", "southern"}
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
    # Bible forms already accounted for by an attested entry (words of compounds included): a respelled
    # entry with the same letters is then a homograph, not a missed attestation.
    covered = {key(p) for e in entries if e.get("status") == "attested"
               for x in [e.get("lemma", "")] + [e.get("plural") or ""] + list(e.get("forms") or [])
               for w in WORD_RE.findall(str(x)) for p in [w] + w.split("-")}
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
        if e.get("status") == "southern" and not ((e.get("childs") or {}).get("page") and (e.get("childs") or {}).get("form")):
            errors.append(f"{where}: a 'southern' entry needs childs.page and childs.form (the source of the word)")
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
        elif (e.get("status") == "respelled" and " " not in lemma and lemma and attested(lemma, words)
              and key(lemma) not in covered):
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


TABLE_COLUMNS = ["headword", "status", "part_of_speech", "noun_class", "plural", "other_forms", "gloss_fr",
                 "gloss_en", "semantic_domains", "southern_kissi_sense", "bible_count", "bible_example",
                 "keita_form", "keita_page", "childs_form", "childs_page", "note"]


def export_table(entries, domains, words, delimiter):
    """The lexicon as one row per entry, in Kisiei alphabetical order (kisiei.csv and kisiei.tsv)."""
    out = io.StringIO()
    w = csv.writer(out, delimiter=delimiter, lineterminator="\n")
    w.writerow(TABLE_COLUMNS)
    for e in sorted(entries, key=lambda e: (kisiei_sort(str(e["lemma"])), str(e["lemma"]), e["pos"])):
        b = bible_info(e, words)
        kt, ch = e.get("keita") or {}, e.get("childs") or {}
        doms = " | ".join(f"{d} {domains[str(d)]['en']} / {domains[str(d)]['fr']}" for d in e["domains"])
        row = [e["lemma"], e["status"], e["pos"], e.get("class", ""), e.get("plural", ""),
               "; ".join(map(str, e.get("forms") or [])), e["gloss"]["fr"], e["gloss"]["en"], doms,
               ch.get("sense", ""), b[0] if b else "", (e.get("example") or b[1]) if b else e.get("example", ""),
               kt.get("form", ""), kt.get("page", ""), ch.get("form", ""), ch.get("page", ""), e.get("note", "")]
        w.writerow([str(x).replace("\t", " ") for x in row])
    return out.getvalue()


# CLDF Dictionary module (https://cldf.clld.org), written with the standard library only.
CLDF = "http://cldf.clld.org/v1.0/terms.rdf#"
LANGUAGE = {"ID": "kisiei", "Name": "Kisiei (Northern Kissi)", "Glottocode": "nort2765", "ISO639P3code": "kqs"}
CLDF_SOURCES = ["BKG", "Keita1979", "Childs2000"]
SLUG = {"ɛ": "eh", "ɔ": "oh", "ŋ": "ng", "ɲ": "ny"}


def slug(lemma):
    s = "".join(SLUG.get(c, c) for c in key(str(lemma)))
    return re.sub(r"[^a-z0-9-]+", "_", s).strip("_-") or "x"


def cldf_ids(entries):
    """Stable entry IDs: ASCII headword + part of speech, -2, -3 for homographs (in sorted order)."""
    ids, seen = {}, {}
    for e in sorted(entries, key=lambda e: (kisiei_sort(str(e["lemma"])), str(e["lemma"]), e["pos"], e["gloss"]["en"])):
        base = f"{slug(e['lemma'])}-{e['pos']}"
        seen[base] = seen.get(base, 0) + 1
        ids[id(e)] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return ids


def cldf_metadata():
    def col(name, prop=None, **kw):
        c = {"name": name, "datatype": kw.pop("datatype", "string")}
        if prop:
            c["propertyUrl"] = CLDF + prop
        c.update(kw)
        return c
    ident = {"base": "string", "format": "[a-zA-Z0-9_\\-]+"}
    return {
        "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
        "dc:conformsTo": CLDF + "Dictionary",
        "dc:title": "Kisiei (Northern Kissi) lexicon",
        "dc:description": "Lexicon of Kisiei (Northern Kissi, Guinea), spelled after the Kisiei Bible (BKG), "
                          "classified by SIL Semantic Domains, with glosses in French and English.",
        "dc:license": "https://creativecommons.org/licenses/by-nc/4.0/",
        "dc:source": "sources.bib",
        "dc:identifier": "https://github.com/kebasaa/kisiei-language",
        "tables": [
            {"url": "languages.csv", "dc:conformsTo": CLDF + "LanguageTable", "tableSchema": {
                "columns": [col("ID", "id", datatype=ident), col("Name", "name"), col("Glottocode", "glottocode"),
                            col("ISO639P3code", "iso639P3code")],
                "primaryKey": ["ID"]}},
            {"url": "entries.csv", "dc:conformsTo": CLDF + "EntryTable", "tableSchema": {
                "columns": [col("ID", "id", datatype=ident), col("Language_ID", "languageReference"),
                            col("Headword", "headword"), col("Part_Of_Speech", "partOfSpeech"),
                            col("Status", **{"dc:description": "attested (in the Bible), confirmed (by a speaker), "
                                             "respelled (from Keita 1979), check, or southern (Childs 2000 only)"}),
                            col("Noun_Class"), col("Plural"), col("Variants", separator=";")],
                "primaryKey": ["ID"],
                "foreignKeys": [{"columnReference": ["Language_ID"],
                                 "reference": {"resource": "languages.csv", "columnReference": ["ID"]}}]}},
            {"url": "senses.csv", "dc:conformsTo": CLDF + "SenseTable", "tableSchema": {
                "columns": [col("ID", "id", datatype=ident), col("Entry_ID", "entryReference"),
                            col("Description", "description"), col("Source", "source", separator=";"),
                            col("Description_French"), col("Semantic_Domain", separator=";"),
                            col("Southern_Kissi_Sense"), col("Bible_Count", datatype="integer"),
                            col("Example_Reference", **{"dc:description": "USFM reference of a Bible verse (BKG)"})],
                "primaryKey": ["ID"],
                "foreignKeys": [{"columnReference": ["Entry_ID"],
                                 "reference": {"resource": "entries.csv", "columnReference": ["ID"]}}]}},
        ],
    }


def export_cldf(entries, words):
    """Return {file name: content} for lexicon/cldf/."""
    import json

    def table(header, rows):
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        return out.getvalue()
    ids = cldf_ids(entries)
    ordered = sorted(entries, key=lambda e: ids[id(e)])
    erows, srows = [], []
    for e in ordered:
        b = bible_info(e, words)
        kt, ch = e.get("keita") or {}, e.get("childs") or {}
        src = []
        if b:
            src.append(f"BKG[{e.get('example') or b[1]}]")
        if kt:
            src.append(f"Keita1979[{kt['page']}]" if kt.get("page") else "Keita1979")
        if ch:
            src.append(f"Childs2000[{ch['page']}]" if ch.get("page") else "Childs2000")
        forms = [str(f) for f in e.get("forms") or []]
        erows.append([ids[id(e)], LANGUAGE["ID"], e["lemma"], e["pos"], e["status"], e.get("class", ""),
                      e.get("plural", ""), ";".join(f.replace(";", ",") for f in forms)])
        srows.append([ids[id(e)] + "-s1", ids[id(e)], e["gloss"]["en"], ";".join(src), e["gloss"]["fr"],
                      ";".join(map(str, e["domains"])), ch.get("sense", ""), b[0] if b else "",
                      e.get("example") or (b[1] if b else "")])
    bib = (ROOT / "docs" / "references.bib").read_text(encoding="utf-8")
    entries_bib = [m.group(0) for m in re.finditer(r"^@\w+\{(\w+),.*?^\}", bib, flags=re.S | re.M)
                   if m.group(1) in CLDF_SOURCES]
    assert len(entries_bib) == len(CLDF_SOURCES), "CLDF sources missing from docs/references.bib"
    return {
        "Dictionary-metadata.json": json.dumps(cldf_metadata(), ensure_ascii=False, indent=2) + "\n",
        "languages.csv": table(list(LANGUAGE), [list(LANGUAGE.values())]),
        "entries.csv": table(["ID", "Language_ID", "Headword", "Part_Of_Speech", "Status", "Noun_Class",
                              "Plural", "Variants"], erows),
        "senses.csv": table(["ID", "Entry_ID", "Description", "Source", "Description_French", "Semantic_Domain",
                             "Southern_Kissi_Sense", "Bible_Count", "Example_Reference"], srows),
        "sources.bib": "\n\n".join(entries_bib) + "\n",
    }


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
               "confirmés ; les mots <span class=\"ks-badge ks-south\">kissi du Sud</span> ne sont connus que par le "
               "dictionnaire du kissi du Sud (Childs 2000) : ils ne sont pas attestés au Nord et sont écrits tels que Childs les note. "
               "Le lexique est aussi disponible aux formats CSV, TSV, LIFT (pour FieldWorks) et CLDF.")},
    "en": {"south": "Southern Kissi (Childs 2000)", "title": "Word lists", "kis": "Kisiei", "pos": "Category", "gloss": "English",
           "src": "Source", "intro": (
               "These lists are generated automatically from the project's [lexicon](https://github.com/kebasaa/kisiei-language/tree/main/lexicon) "
               "({n} entries). Words are grouped by **semantic domain** following the "
               "[SIL Semantic Domains](https://semdom.org/v4/) classification; a word may appear in several domains. "
               "Attested words link to their first occurrence in the Kisiei Bible; "
               "<span class=\"ks-badge ks-conf\">Confirmed</span> words are not in the Bible but confirmed by a speaker; "
               "<span class=\"ks-badge ks-res\">Respelled</span> words come from the 1979 description and still need "
               "confirmation; <span class=\"ks-badge ks-south\">Southern Kissi</span> words are known only from the "
               "Southern Kissi dictionary (Childs 2000): they are not attested in the North and are spelled as Childs writes them. "
               "The lexicon is also available as CSV, TSV, LIFT (for FieldWorks) and CLDF.")},
}
FLAG = {"attested": "", "confirmed": "\\|c", "respelled": "\\|r", "check": "\\|?", "southern": "\\|s"}


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
            if e["status"] == "southern":
                pos += " — " + ("**kissi du Sud seulement**" if lang == "fr" else "**Southern Kissi only**")
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


# Alphabetical order proposed in docs/orthography/alphabet: each Kisiei letter follows the nearest
# Latin one; letters only found in loanwords (j q x z) take their Latin place. Tone marks are ignored.
ALPHABET = "a b c d e ɛ f g h i j k l m n ŋ ɲ o ɔ p q r s t u v w x y z".split()
RANK = {c: i for i, c in enumerate(ALPHABET)}
LETTER_ID = {"ɛ": "e-open", "ŋ": "ng", "ɲ": "ny", "ɔ": "o-open"}

DICT_TEXT = {
    "fr": {"title": "Dictionnaire kisiei–français", "rev_title": "Index français–kisiei",
           "abbr": {"noun": "n.", "verb": "v.", "adj": "adj.", "adv": "adv.", "pron": "pron.", "num": "num.",
                    "det": "dét.", "prep": "prép.", "postp": "postp.", "conj": "conj.", "part": "part.",
                    "interj": "interj.", "ideo": "idéo.", "name": "n. pr."},
           "pl": "pl.", "forms": "autres formes", "south_only": "kissi du Sud seulement",
           "south_sense": "kissi du Sud", "letters": "Lettres",
           "intro": (
               "Ce dictionnaire est produit automatiquement à partir du "
               "[lexique](https://github.com/kebasaa/kisiei-language/tree/main/lexicon) du projet ({n} entrées). "
               "Les mots sont classés dans l'[ordre alphabétique du kisiei](../orthography/alphabet.md#ordre-alphabetique) "
               "(*ɛ* après *e*, *ŋ* et *ɲ* après *n*, *ɔ* après *o*) ; les accents de ton ne comptent pas pour le classement. "
               "Le soulignement de chaque mot indique sa source, comme dans le reste du guide : "
               "<span class=\"ks-badge ks-att\">Attesté</span> dans la Bible (avec un renvoi à une occurrence), "
               "<span class=\"ks-badge ks-conf\">Confirmé</span> par un locuteur, "
               "<span class=\"ks-badge ks-res\">Réécrit</span> d'après Keita 1979, "
               "<span class=\"ks-badge ks-chk\">À vérifier</span>, ou "
               "<span class=\"ks-badge ks-south\">kissi du Sud</span> (Childs 2000 seulement, non attesté au Nord). "
               "Pour chercher un mot à partir du français, voir l'[index français–kisiei](reverse-index.md) ; "
               "pour un classement par thèmes, voir les [listes de mots](word-lists.md). "
               "Le lexique complet est aussi disponible aux formats CSV, TSV, LIFT et CLDF dans le [dépôt](https://github.com/kebasaa/kisiei-language/tree/main/lexicon)."),
           "rev_intro": (
               "Cet index renvoie des mots français aux mots kisiei du [dictionnaire](dictionary.md) ({n} mots-clés). "
               "Les mots-clés sont tirés des définitions. Ils sont classés sans tenir compte des accents, "
               "de l'article ni du *se* des verbes pronominaux (*s'asseoir* sous *A*). "
               "Le soulignement de chaque mot kisiei indique sa source (voir le [dictionnaire](dictionary.md))."),
           },
    "en": {"title": "Kisiei–English dictionary", "rev_title": "English–Kisiei index",
           "abbr": {"noun": "n.", "verb": "v.", "adj": "adj.", "adv": "adv.", "pron": "pron.", "num": "num.",
                    "det": "det.", "prep": "prep.", "postp": "postp.", "conj": "conj.", "part": "part.",
                    "interj": "interj.", "ideo": "ideo.", "name": "prop. n."},
           "pl": "pl.", "forms": "other forms", "south_only": "Southern Kissi only",
           "south_sense": "Southern Kissi", "letters": "Letters",
           "intro": (
               "This dictionary is generated automatically from the project's "
               "[lexicon](https://github.com/kebasaa/kisiei-language/tree/main/lexicon) ({n} entries). "
               "Words follow the [Kisiei alphabetical order](../orthography/alphabet.md#alphabetical-order) "
               "(*ɛ* after *e*, *ŋ* and *ɲ* after *n*, *ɔ* after *o*); tone marks are ignored for sorting. "
               "The underline of each word shows its source, as elsewhere in this guide: "
               "<span class=\"ks-badge ks-att\">Attested</span> in the Bible (with a reference to one occurrence), "
               "<span class=\"ks-badge ks-conf\">Confirmed</span> by a speaker, "
               "<span class=\"ks-badge ks-res\">Respelled</span> from Keita 1979, "
               "<span class=\"ks-badge ks-chk\">To check</span>, or "
               "<span class=\"ks-badge ks-south\">Southern Kissi</span> (Childs 2000 only, not attested in the North). "
               "To look up a word from English, see the [English–Kisiei index](reverse-index.md); "
               "for words grouped by theme, see the [word lists](word-lists.md). "
               "The full lexicon is also available as CSV, TSV, LIFT and CLDF in the [repository](https://github.com/kebasaa/kisiei-language/tree/main/lexicon)."),
           "rev_intro": (
               "This index leads from English words to the Kisiei words of the [dictionary](dictionary.md) "
               "({n} keywords). The keywords are taken from the definitions and sorted without a leading *a*, *the* or *to*. "
               "The underline of each Kisiei word shows its source (see the [dictionary](dictionary.md))."),
           },
}


def kisiei_sort(word):
    k = key(word)
    return [RANK.get(c, len(RANK)) for c in k if c in RANK] + [len(RANK) + 1], k


def letter_of(word):
    for c in key(word):
        if c in RANK:
            return c
    return "?"


def letter_heading(c):
    return f"## {c.upper()} {{#{LETTER_ID.get(c, c)}}}"


def letter_bar(letters, label):
    links = " · ".join(f"[{c.upper()}](#{LETTER_ID.get(c, c)})" for c in letters)
    return f'<p class="ks-letters" markdown="1"><strong>{label}</strong> {links}</p>'


def entry_source(e, words, lang):
    b = bible_info(e, words)
    if b:
        return f"[{bible_label(e.get('example') or b[1], lang)}]({BIBLE_URL.format(ref=e.get('example') or b[1])})"
    if e.get("keita"):
        return f"Keita 1979, p. {e['keita'].get('page', '?')}"
    if e["status"] == "southern" and e.get("childs"):
        return f"Childs 2000, p. {e['childs'].get('page', '?')}"
    return ""


def export_dictionary(lang, entries, words):
    t = DICT_TEXT[lang]
    entries = sorted(entries, key=lambda e: (kisiei_sort(str(e["lemma"])), str(e["lemma"]), e["pos"]))
    same = {}
    for e in entries:
        same.setdefault(str(e["lemma"]), []).append(e)
    by_letter = {}
    for e in entries:
        by_letter.setdefault(letter_of(str(e["lemma"])), []).append(e)
    letters = sorted(by_letter, key=lambda c: RANK.get(c, len(RANK)))
    lines = [f"# {t['title']}", "", "<!-- Generated by tools/build_lexicon.py from lexicon/entries/*.yaml; do not edit by hand. -->", "",
             t["intro"].format(n=len(entries)), "", letter_bar(letters, t["letters"]), ""]
    for c in letters:
        lines += [letter_heading(c), "", '<div class="ks-dict" markdown="1">', ""]
        for e in by_letter[c]:
            flag = FLAG[e["status"]].replace("\\", "")
            lemma = str(e["lemma"])
            head = f"**{{{{{lemma}{flag}}}}}**"
            if len(same[lemma]) > 1:
                head += f"<sup>{same[lemma].index(e) + 1}</sup>"
            parts = [head, f"*{t['abbr'][e['pos']]}*" + (f" ({e['class']})" if e.get("class") else "")]
            if e.get("plural"):
                parts[-1] += f", {t['pl']} {{{{{e['plural']}{flag}}}}}"
            text = " ".join(parts)
            if e["status"] == "southern":
                text += f" — **{t['south_only']}**"
            text += " — " + e["gloss"][lang].rstrip(".") + "."
            sense = (e.get("childs") or {}).get("sense")
            if sense and e["status"] != "southern":
                text += f" *{t['south_sense']} (Childs 2000, en anglais) :* {sense.rstrip('.')}." if lang == "fr" else \
                        f" *{t['south_sense']} (Childs 2000):* {sense.rstrip('.')}."
            forms = [str(f) for f in e.get("forms") or [] if str(f) != lemma]
            if forms:
                text += f" {t['forms'].capitalize()}{' :' if lang == 'fr' else ':'} " + ", ".join(f"*{f}*" for f in forms) + "."
            src = entry_source(e, words, lang)
            if src:
                text += f" <span class=\"ks-src\">{src}</span>"
            lines += [text, ""]
        lines += ["</div>", ""]
    return "\n".join(lines)


def split_gloss(gloss):
    """Split a gloss on ';' and ',' outside parentheses; return (display, sort text) pairs."""
    out, depth, cur = [], 0, ""
    for ch in gloss + ",":
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch in ",;" and depth == 0:
            seg = cur.strip().rstrip(".").strip()
            if seg:
                out.append(seg)
            cur = ""
        else:
            cur += ch
    return out


def rev_sort(seg, lang):
    s = re.sub(r"\([^)]*\)", "", seg).strip(" .…«»\"'").lower()
    if lang == "fr":
        s = re.sub(r"^(le |la |les |l'|l’|un |une |des )?(se |s'|s’)?", "", s)
    else:
        s = re.sub(r"^(to |a |an |the )", "", s)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("œ", "oe").replace("æ", "ae")
    return re.sub(r"[^\w ]", "", s).strip()


def export_reverse(lang, entries, words):
    t = DICT_TEXT[lang]
    index = {}
    for e in entries:
        for seg in split_gloss(e["gloss"][lang]):
            sk = rev_sort(seg, lang)
            if not sk or not sk[0].isalpha():
                continue
            index.setdefault((sk, seg), []).append(e)
    keys = sorted(index, key=lambda k: (k[0], k[1].lower(), k[1]))
    by_letter = {}
    for k in keys:
        by_letter.setdefault(k[0][0], []).append(k)
    letters = sorted(by_letter)
    lines = [f"# {t['rev_title']}", "", "<!-- Generated by tools/build_lexicon.py from lexicon/entries/*.yaml; do not edit by hand. -->", "",
             t["rev_intro"].format(n=len(keys)), "", letter_bar(letters, t["letters"]), ""]
    for c in letters:
        lines += [f"## {c.upper()} {{#{c}}}", "", '<div class="ks-dict" markdown="1">', ""]
        for k in by_letter[c]:
            targets = []
            for e in sorted(index[k], key=lambda e: kisiei_sort(str(e["lemma"]))):
                w = f"{{{{{e['lemma']}{FLAG[e['status']].replace(chr(92), '')}}}}} *{t['abbr'][e['pos']]}*"
                if e["status"] == "southern":
                    w += f" ({t['south_only']})"
                targets.append(w)
            lines += [f"**{k[1]}** — " + " ; ".join(targets) if lang == "fr" else f"**{k[1]}** — " + "; ".join(targets), ""]
        lines += ["</div>", ""]
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
    (LEX / "kisiei.csv").write_text(export_table(entries, domains, words, ","), encoding="utf-8")
    (LEX / "kisiei.tsv").write_text(export_table(entries, domains, words, "\t"), encoding="utf-8")
    (LEX / "kisiei.lift").write_text(export_lift(entries, domains, words), encoding="utf-8")
    (LEX / "cldf").mkdir(exist_ok=True)
    for name, content in export_cldf(entries, words).items():
        (LEX / "cldf" / name).write_text(content, encoding="utf-8")
    for lang in ("fr", "en"):
        (ROOT / "docs" / "reference" / f"word-lists.{lang}.md").write_text(
            export_page(lang, entries, domains, words), encoding="utf-8")
        (ROOT / "docs" / "reference" / f"dictionary.{lang}.md").write_text(
            export_dictionary(lang, entries, words), encoding="utf-8")
        (ROOT / "docs" / "reference" / f"reverse-index.{lang}.md").write_text(
            export_reverse(lang, entries, words), encoding="utf-8")
    print("wrote lexicon/kisiei.{csv,tsv,lift}, lexicon/cldf/, docs/reference/{dictionary,reverse-index,word-lists}.{fr,en}.md")


if __name__ == "__main__":
    main()
