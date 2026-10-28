# Kisie

A grammar and orthography guide-book for **Kisiei** (Northern Kissi, also written *Kisie* or *Kissi*; ISO 639-3 `kqs`), published as a bilingual French/English website, together with the source material it is based on.

Kisiei belongs to the Mel branch of the Atlantic–Congo languages. It is spoken mainly in the Guéckédou and Kissidougou region of south-eastern Guinea, and also in neighbouring parts of Sierra Leone and Liberia.

## The guide-book

The site in `docs/` is written for people who **write and teach** Kisiei. It covers:

- **Orthography:** alphabet, vowels and vowel length, consonants, tone marks, word division and hyphens, punctuation, names and loanwords, and how to read the old (1970s) spelling.
- **Grammar:** noun classes and agreement, determiners, pronouns and relative clauses, the verb (stems, tense–aspect–mood, negation, derived verbs), invariable words, and the sentence.
- **Reference:** verb tables, word lists, everyday phrases, a glossary and a list of open questions.

French is the main language (at `/`); English is at `/en/`. A small language icon at the top right switches between them.

### Sources and standard

1. **The Kisiei Bible** (*Bii Bila*, BKG, © Alliance Biblique en Guinée; [bible.com version 1394](https://www.bible.com/bible/1394/GEN.1.BKG)) is the **spelling and usage standard**. It is the most recent and by far the longest text in the current orthography, and it always takes precedence. Grammar rules are derived from its texts, and examples are quoted from it with their verse reference.
2. **Keita (1979)**, *Essai d'élaboration d'un Kisiei fondamental* (see `archive/`), is the background description of the grammar. Its spelling is outdated and it contains errors, so every point taken from it is checked against the Bible and against Childs.
3. **Childs (1995)**, *A Grammar of Kisi*, and **Childs (2000)**, *A Dictionary of the Kisi Language*, describe mainly Southern Kissi (Liberia, Sierra Leone). They are used for comparison and analysis, never as the norm. These books are not distributed in this repository.

Every Kisiei example on the site carries a status: **attested** (the form occurs in the Bible), **respelled** (taken from Keita 1979 and converted to the current spelling, but not found in the Bible) or **to check**. Citations use author–date with page numbers, for example "(Keita 1979, p. 57)", and Bible references are written as ordinary Markdown links to the verse on bible.com, so they also work when reading the files on GitHub.

### Building the site locally

The site uses [MkDocs](https://www.mkdocs.org/) with the Material theme and `mkdocs-static-i18n`. With [uv](https://docs.astral.sh/uv/):

```bash
uv run --with-requirements requirements-docs.txt mkdocs serve
```

```bash
uv run --with-requirements requirements-docs.txt mkdocs build --strict
```

The build fails if a Kisiei example marked as attested is not in the Bible word list, if a citation key is unknown, or if a link is broken. `python tools/check_i18n.py` reports pages missing in either language. On every push to `main`, GitHub Actions builds the site and publishes it to GitHub Pages (enable Pages with source "GitHub Actions" in the repository settings).

### Bible tools

The Bible text itself is **not** stored in the repository. The tools download it into the git-ignored `.cache/bible/` folder for local analysis; only the list of word forms is committed.

| Command | Purpose |
| --- | --- |
| `uv run tools/fetch_bible.py [--delay 1.0] [--books GEN,EXO]` | Download the BKG chapters (slowly, about one per second) into `.cache/bible/`. Already downloaded chapters are skipped. |
| `uv run tools/build_wordlist.py` | Rebuild `references/bible-bkg-wordforms.tsv` (distinct word forms, counts, spellings with tone marks, first reference). |
| `uv run tools/bible_concordance.py -w REGEX` | Search the cached text by word or pattern (`-v` for whole-verse patterns) and show each hit in context with its reference. |

## Repository contents

| Path | Description |
| --- | --- |
| `docs/` | The guide-book pages (`page.fr.md` and `page.en.md` side by side), the bibliography `references.bib` and the site stylesheet. |
| `tools/` | MkDocs hook (example checking, citations, Bible links), Bible download and word-list tools, translation check. |
| `references/bible-bkg-wordforms.tsv` | Word forms of the Kisiei Bible, used to check the examples. |
| [`archive/kissie fondamental (original scan).pdf`](archive/kissie%20fondamental%20(original%20scan).pdf) | Scan (189 pages) of Sékou Sondo Keita's 1979 thesis (Institut Polytechnique Gamal Abdel Nasser de Conakry): phonetics, grammar, conjugation, syntax and a Kisiei–French lexicon, in French and Kisiei, old orthography. |
| [`archive/kissie fondamental (transcription).md`](archive/kissie%20fondamental%20(transcription).md) | Complete Markdown transcription of the scan, in the original orthography, with handwritten corrections inline. |
| [`archive/kissie fondamental (handwritten notes).md`](archive/kissie%20fondamental%20(handwritten%20notes).md) | Handwritten annotations found on the scan (French glosses, translations, Kissidougou variants), page by page. |
| [`archive/nouvel orthographe kissi.pdf`](archive/nouvel%20orthographe%20kissi.pdf) | One-page table of correspondences between the old and the new orthography. |

### The Keita transcription

The transcription of Keita (1979) is **complete and final**: all 189 PDF pages (typescript pp. 1–165 and the bibliography; the annex of tales is missing from the scan). It deliberately keeps the old orthography and the author's typos, and it will not be converted to the new spelling; the guide-book uses it as a source instead. Its conventions were:

- the text reproduced exactly (spelling, diacritics, punctuation, capitalisation), in precomposed Unicode (NFC);
- handwritten corrections of the typed text inline, as `~~struck text~~` and `<ins>replacement</ins>`;
- all other handwritten annotations in the separate notes file, linked from the transcription with `> ✎ [Handwritten notes, p. N](…)` lines.

## Orthography in brief

The old spelling used in the archive differs from the current one mainly in these letters:

| Old | New | Example |
| --- | --- | --- |
| ty | c | *tyuaa* → *cuaa* |
| nh | ŋ | *Nhömmèw* → *ŋɔmmɛw* |
| ny | ɲ | *nyèm* → *ɲɛm* |
| è | ɛ | *Söèi* → *sɔɛi* |
| ö | ɔ | *Kolöö* → *kolɔɔ* |

The current orthography, as used in the Bible, also writes long vowels double (*aa*, *ɔɔ*), marks tone with accents where it matters grammatically (*mí* / *mì*, *háá*), keeps *mb*, and writes *ŋ* at the end of a stem before *-nd-* endings (*lɛŋnden*). The guide-book's [orthography chapter](docs/orthography/) describes the rules in full.

## License

The guide-book text and the transcriptions are licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/) (CC BY-NC 4.0); see [`LICENSE`](LICENSE). The code in `tools/` is under the MIT License; see [`LICENSE-CODE`](LICENSE-CODE).

The original works in `archive/`, such as Sékou Sondo Keita's 1979 thesis, remain the work of their authors. Bible quotations are short excerpts from the Kisiei Bible, © Alliance Biblique en Guinée. When using this material, credit the original authors as well as this repository.
