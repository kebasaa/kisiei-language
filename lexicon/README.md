# Kisiei lexicon

A structured, machine- and human-readable lexicon of Kisiei, classified by **semantic domains**.

## Method

- **Classification:** words are grouped by the [SIL Semantic Domains](https://semdom.org/v4/) (DDP version 4, Ronald Moe). This classification is used by FieldWorks (FLEx), the Rapid Word Collection method and many dictionary projects. The codes and their French and English labels are in [`domains.yaml`](domains.yaml). A word can belong to several domains.
- **Sources, in order of authority:**
  1. **The Kisiei Bible (BKG)** gives the spelling standard and most of the vocabulary. Meanings are worked out from the verse contexts.
  2. **Keita (1979)**, the thematic lexicon and verb list of *Kisiei fondamental* (see `archive/`), gives French glosses. Its words are respelled to the current orthography.
  3. **Other older northern sources**, all transcribed in `archive/`: Paulme's *Documents sur la langue kissi* (1964; vocabulary of the 1940s with G./K. dialect marks, and interlinear texts), the anonymous *Lexique kissi–français*, the Académie des Langues terminology lists, and the fables *Sandara Kissia* (Mission Protestante, Kissidougou). They add words and meanings, but none of them follows the Bible's orthography: every form taken from them is respelled to the Bible's rules, and the form as printed is kept in the entry's source field.
  4. **Childs (2000)**, *A Dictionary of the Kisi Language*, describes Southern Kissi. It is used to check words that are not in the Bible (existence, spelling, meaning) and to suggest further senses. It is never copied wholesale; only the page reference and the point checked are recorded.
- **Status of each entry:**
  - `attested`: the lemma (and any plural or variant given) is in the Bible word list, ignoring tone. This is checked at build time.
  - `confirmed`: not in the Bible, but the form and meaning have been confirmed by a speaker of Kisiei (Northern Kissi). Say who or when in `note` if useful.
  - `respelled`: taken from an older written source (Keita 1979, Paulme 1964, the Lexique, the Académie lists, Sandara Kissia) and converted to the Bible's orthography, but not found in the Bible. It needs at least one source field (`keita`, `paulme`, `lexique`, `terminologie`, `sandara`).
  - `southern`: known only from Childs (2000), Southern Kissi, with no northern evidence (not in the Bible, not in Keita). The lemma is Childs's headword exactly as printed, with his tones; `childs.page` and `childs.form` are required. These entries are always shown labelled "Southern Kissi only".
  - `check`: the form or meaning is uncertain and needs a speaker's confirmation.

## Files

| Path | Content |
| --- | --- |
| `entries/*.yaml` | The source data: one file per theme or source, each a list of entries. **Edit these.** |
| `domains.yaml` | The semantic domains used. |
| `kisiei.csv`, `kisiei.tsv` | Generated: one row per entry, headword first, in Kisiei alphabetical order (comma- and tab-separated). |
| `to-check.md` | Generated: every entry with status `check` (form or meaning uncertain), with its source form and the reason, as a list to go through with a speaker. Confirmed words leave the list at the next build. |
| `kisiei.lift` | Generated: [LIFT](https://github.com/sillsdev/lift-standard) 0.13 XML, importable into FieldWorks and other lexicon tools. |
| `cldf/` | Generated: a [CLDF](https://cldf.clld.org) Dictionary (entries, senses, language with Glottocode `nort2765`, sources), for reuse in cross-linguistic databases. Validate with `uv run --with pycldf cldf validate lexicon/cldf/Dictionary-metadata.json`. |
| `../docs/reference/dictionary.*.md` | Generated: the alphabetical dictionary pages (Kisiei–French, Kisiei–English). |
| `../docs/reference/reverse-index.*.md` | Generated: the reverse indexes (French–Kisiei, English–Kisiei). |
| `../docs/reference/word-lists.*.md` | Generated: the word lists by semantic domain. |

Run `uv run tools/build_lexicon.py` after editing to validate the entries and regenerate the outputs. `uv run tools/build_lexicon.py --check` only validates; `--only lexicon/entries/FILE.yaml` validates a single file. The site build on GitHub regenerates the outputs too, so the published dictionary always matches the entries on `main`.

## Entry format

```yaml
- lemma: bollen              # citation form, current (Bible) spelling
  status: attested           # attested | confirmed | respelled | check | southern
  pos: noun                  # noun verb adj adv pron num det prep postp conj part interj ideo name
  class: len                 # noun class (nouns): o, i, an, len, lan; plural classes a, on
  plural: bóltan             # plural form, if known
  forms: [bolle]             # other forms: radical form, verb stems
  variants: [{form: koraa, dialect: K, source: keita}]   # (example from the entry kolaa "cloth")
                             # dialect or pronunciation variants (dialect G = Guéckédou, K = Kissidougou;
                             # source: keita, paulme, lexique, terminologie, sandara, notes1979, speaker, bible)
  gloss: {fr: "tête", en: "head"}
  domains: ["2.1.1"]         # SIL semantic domain codes (quoted strings)
  keita: {form: "Bollen (ten)", page: 131}   # form as printed in Keita 1979, typescript page
  paulme: {form: "bulle", page: 15, dialect: K}   # Paulme 1964: form as printed, typescript page, G, K or G/K
  lexique: {form: "bollen", page: 9}          # Lexique kissi-français: form as printed, page
  terminologie: {form: "...", list: langue, number: 12}   # Académie lists: langue, arts, histoire, ideologie
  sandara: {form: "bulle", section: "fable 3"}  # Sandara Kissia: fable N, or proverb N
  childs: {page: 30, form: "bòlléŋ", sense: "head; top, chief"}
                             # Childs 2000: printed page and headword (read from the page image), and
                             # optionally `sense`: the Southern Kissi meaning in English, in your own words,
                             # when it adds to or differs from the northern (Bible) meaning
  example: GEN.3.15          # a verse showing the word (USFM reference)
  note: "free text, in French"
```

- **Tone marks:** write lemma, plural and forms with the tone accents the Bible uses for this word in this sense (*vílɛ́iyo*, *yàándɔɔ*, *yáá* "three"). Where the same letters are written with different tones for different words, take the spelling of the word meant (*yáá* "three" vs *yáà* "I (past)"; *kolaa* "cloth" vs *kólaa* "cup"). Leave accents out only when the Bible normally writes the word without them. The build warns when the Bible always writes a word with accents and the entry does not.
- **Dialect variants:** the lemma is the Bible form (in practice the Guéckédou type). Forms of other varieties go in `variants`, in the Bible's letters but keeping the variety's pronunciation (a Kissidougou *r* stays *r*). The dictionary shows them after the headword, labelled Guéckédou, Kissidougou or "with r".
- **Verbs:** the lemma is the long form (*tosaa*, *dioo*). The short stems go in `forms`.
- **Glosses:** short and comma-separated. Use the meaning seen in the Bible; add other northern senses from the older written sources after a semicolon, and say in `note` where each comes from (e.g. "Paulme 1964, p. 37 : aussi « piège »").
- **Older written sources:** the lemma is always in the Bible's orthography (Paulme's *ty* is *c*, her bar marks length, her wave nasality; see `docs/orthography/old-and-new`). The source field keeps the form exactly as printed, so every respelling can be traced. A word found in the Bible is `attested` even if it came from one of these sources; the source field may still be added. Childs's Southern Kissi senses go in `childs.sense` (see below).
- **Southern Kissi meanings:** Childs's dictionary may be used whenever a meaning or semantic field is uncertain. A Southern Kissi sense that differs from or adds to the northern meaning goes in `childs.sense`, never in `gloss`; the word lists show it separately, labelled "kissi du Sud (Childs 2000)". `gloss` describes Kisiei as written in Guinea.
- **Bible counts and references:** do not add them by hand. The build script takes them from `references/bible-bkg-wordforms.tsv`.

## License

The lexicon data are licensed under CC BY-NC 4.0, like the rest of the repository. `domains.yaml` contains the SIL Semantic Domains codes and English names, © SIL Global, CC BY-SA 4.0.
