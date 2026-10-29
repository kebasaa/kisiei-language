# Kisiei lexicon

A structured, machine- and human-readable lexicon of Kisiei, classified by **semantic domains**.

## Method

- **Classification:** words are grouped by the [SIL Semantic Domains](https://semdom.org/v4/) (DDP version 4, Ronald Moe). This classification is used by FieldWorks (FLEx), the Rapid Word Collection method and many dictionary projects. The codes and their French and English labels are in [`domains.yaml`](domains.yaml). A word can belong to several domains.
- **Sources, in order of authority:**
  1. **The Kisiei Bible (BKG)** gives the spelling standard and most of the vocabulary. Meanings are worked out from the verse contexts.
  2. **Keita (1979)**, the thematic lexicon and verb list of *Kisiei fondamental* (see `archive/`), gives French glosses. Its words are respelled to the current orthography.
  3. **Childs (2000)**, *A Dictionary of the Kisi Language*, describes Southern Kissi. It is used to check words that are not in the Bible (existence, spelling, meaning) and to suggest further senses. It is never copied wholesale; only the page reference and the point checked are recorded.
- **Status of each entry:**
  - `attested`: the lemma (and any plural or variant given) is in the Bible word list, ignoring tone. This is checked at build time.
  - `confirmed`: not in the Bible, but the form and meaning have been confirmed by a speaker of Kisiei (Northern Kissi). Say who or when in `note` if useful.
  - `respelled`: taken from Keita 1979 and converted to the current orthography, but not found in the Bible.
  - `southern`: known only from Childs (2000), Southern Kissi, with no northern evidence (not in the Bible, not in Keita). The lemma is Childs's headword exactly as printed, with his tones; `childs.page` and `childs.form` are required. These entries are always shown labelled "Southern Kissi only".
  - `check`: the form or meaning is uncertain and needs a speaker's confirmation.

## Files

| Path | Content |
| --- | --- |
| `entries/*.yaml` | The source data: one file per theme or source, each a list of entries. **Edit these.** |
| `domains.yaml` | The semantic domains used. |
| `kisiei.csv` | Generated: one row per entry. |
| `kisiei.lift` | Generated: [LIFT](https://github.com/sillsdev/lift-standard) 0.13 XML, importable into FieldWorks and other lexicon tools. |
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
  forms: [bolle]             # other forms: radical form, verb stems, variants
  gloss: {fr: "tête", en: "head"}
  domains: ["2.1.1"]         # SIL semantic domain codes (quoted strings)
  keita: {form: "Bollen (ten)", page: 131}   # form as printed in Keita 1979, typescript page
  childs: {page: 30, form: "bòlléŋ", sense: "head; top, chief"}
                             # Childs 2000: printed page and headword (read from the page image), and
                             # optionally `sense`: the Southern Kissi meaning in English, in your own words,
                             # when it adds to or differs from the northern (Bible) meaning
  example: GEN.3.15          # a verse showing the word (USFM reference)
  note: "free text, in French"
```

- **Tone marks:** write lemma, plural and forms with the tone accents the Bible uses for this word in this sense (*vílɛ́iyo*, *yàándɔɔ*, *yáá* "three"). Where the same letters are written with different tones for different words, take the spelling of the word meant (*yáá* "three" vs *yáà* "I (past)"; *kolaa* "cloth" vs *kólaa* "cup"). Leave accents out only when the Bible normally writes the word without them. The build warns when the Bible always writes a word with accents and the entry does not.
- **Verbs:** the lemma is the long form (*tosaa*, *dioo*). The short stems go in `forms`.
- **Glosses:** short and comma-separated. Use the meaning seen in the Bible; add Keita's other northern senses after a semicolon. Childs's Southern Kissi senses go in `childs.sense` (see below).
- **Southern Kissi meanings:** Childs's dictionary may be used whenever a meaning or semantic field is uncertain. A Southern Kissi sense that differs from or adds to the northern meaning goes in `childs.sense`, never in `gloss`; the word lists show it separately, labelled "kissi du Sud (Childs 2000)". `gloss` describes Kisiei as written in Guinea.
- **Bible counts and references:** do not add them by hand. The build script takes them from `references/bible-bkg-wordforms.tsv`.

## License

The lexicon data are licensed under CC BY-NC 4.0, like the rest of the repository. `domains.yaml` contains the SIL Semantic Domains codes and English names, © SIL Global, CC BY-SA 4.0.
