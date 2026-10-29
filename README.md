# Kisie

A grammar and orthography guide-book for **Kisiei** (Northern Kissi, also written *Kisie* or *Kissi*; ISO 639-3 `kqs`), published as a bilingual French/English website, together with the source material it is based on.

**Read the guide-book:** <https://kebasaa.github.io/kisiei-language/> (français) · <https://kebasaa.github.io/kisiei-language/en/> (English)

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

The build fails if a Kisiei example marked as attested is not in the Bible word list, if a citation key is unknown, or if a link is broken. `python tools/check_i18n.py` reports pages missing in either language. On every push to `main`, GitHub Actions runs these checks, regenerates the lexicon pages (dictionary, reverse index, word lists) from `lexicon/entries/`, builds the site and pushes the result to the `gh-pages` branch, from which GitHub Pages serves it at <https://kebasaa.github.io/kisiei-language/>. In the repository **Settings → Pages → Build and deployment**, the source is "Deploy from a branch", branch `gh-pages`, folder `/ (root)`; the site address is also shown there. Do not edit `gh-pages` by hand: it is overwritten on every deployment. GitHub only sees commits once they are pushed: a local commit updates the site at the next `git push`.

To keep the generated lexicon files in the repository in step with the entries, you can enable the optional pre-commit hook once per clone; it runs `tools/build_lexicon.py` whenever lexicon entries are committed and adds the regenerated files to the commit:

```bash
git config core.hooksPath tools/hooks
```

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
| `lexicon/` | The lexicon: source entries in `entries/*.yaml`, and generated exports as CSV and TSV (`kisiei.csv`, `kisiei.tsv`), LIFT (`kisiei.lift`, for FieldWorks) and a CLDF Dictionary (`cldf/`). See [`lexicon/README.md`](lexicon/README.md). |
| `references/bible-bkg-wordforms.tsv` | Word forms of the Kisiei Bible, used to check the examples. |
| `archive/` | Source documents: older descriptions, word lists and texts (see below). |

## The archive

The documents in `archive/` are older descriptions, word lists and texts, mostly scans of typescripts. Except where noted, they predate the current orthography (Keita's documents use *ty*, *nh*, *ny*, *è*, *ö*; see [Orthography in brief](#orthography-in-brief)) and are not a spelling model; the guide-book uses them as background, checked against the Bible.

### Sékou Sondo Keita and the Académie des Langues (Conakry)

| File | Description |
| --- | --- |
| [`Sekou Sondo Keita - kissie fondamental (original scan).pdf`](archive/Sekou%20Sondo%20Keita%20-%20kissie%20fondamental%20(original%20scan).pdf) | Scan (189 pages) of Keita's 1979 thesis, *Essai d'élaboration d'un kisiei fondamental à l'usage des locuteurs non kisi* (Institut Polytechnique Gamal Abdel Nasser de Conakry): phonetics, grammar, conjugation, syntax and a Kisiei–French lexicon of about 700 words, in French and Kisiei. |
| [`Sekou Sondo Keita - kissie fondamental (transcription).md`](archive/Sekou%20Sondo%20Keita%20-%20kissie%20fondamental%20(transcription).md) | Complete Markdown transcription of the scan, in the original orthography, with handwritten corrections inline (see [below](#the-keita-transcription)). |
| [`Sekou Sondo Keita - kissie fondamental (handwritten notes).md`](archive/Sekou%20Sondo%20Keita%20-%20kissie%20fondamental%20(handwritten%20notes).md) | Handwritten annotations found on the scan (French glosses, translations, Kissidougou variants), page by page. |
| [`Sekou Sondo Keita - kissie fondamental (annexe proverbes contes devinettes).pdf`](archive/Sekou%20Sondo%20Keita%20-%20kissie%20fondamental%20(annexe%20proverbes%20contes%20devinettes).pdf) | Scan (18 pages) of the thesis annex, *Annexe : Proverbes, Contes, Devinettes* (typescript pp. 166–184 in the thesis contents), which is missing from the main scan: Kisiei tales (among them the *Suluku* stories), each followed by proverbs (*talelan*) and riddles (*budon pialan*), with handwritten French glosses. It was found as a separate scan; its spelling, typewriter and tales match the annex listed by Keita. Not transcribed. |
| [`Sekou Sondo Keita - Terminologie_Kissi_Langue.PDF`](archive/Sekou%20Sondo%20Keita%20-%20Terminologie_Kissi_Langue.PDF) | *Terminologie : langue* (16 pages): numbered French terms of language and grammar (*abstrait*, *accent*, *adjectif*…) with their Kisiei translation. Issued by the Ministère de l'Enseignement Supérieur et de la Recherche Scientifique, Académie des Langues; undated. |
| [`Sekou Sondo Keita - Terminologie_Kissi_Arts.PDF`](archive/Sekou%20Sondo%20Keita%20-%20Terminologie_Kissi_Arts.PDF) | *Terminologie : arts* (12 pages), same series: terms of the arts, music and performance. |
| [`Sekou Sondo Keita - Terminologie_Kissi_Histoire.PDF`](archive/Sekou%20Sondo%20Keita%20-%20Terminologie_Kissi_Histoire.PDF) | *Terminologie : histoire* (21 pages), same series: terms of history and politics. |
| [`Sekou Sondo Keita - Terminologie_Kissi_Ideologie.PDF`](archive/Sekou%20Sondo%20Keita%20-%20Terminologie_Kissi_Ideologie.PDF) | *Terminologie : idéologie* (13 pages), same series: terms of ideology, economy and society. |
| [`nouvel orthographe kissi.pdf`](archive/nouvel%20orthographe%20kissi.pdf) | One-page table of correspondences between the old and the new orthography. |

The four terminology lists name no author on the pages; the attribution to Keita comes from the file names.

### Denise Paulme

| File | Description |
| --- | --- |
| [`Denise Paulme - Documents sur la langue kissi.pdf`](archive/Denise%20Paulme%20-%20Documents%20sur%20la%20langue%20kissi.pdf) | *Documents sur la langue kissi : lexique et textes* (Glottolog dates it 1964), printed in 2013 from the University of Florida Digital Collections (record UF00073317), 173 pages. Vocabulary and texts collected by the ethnologist Denise Paulme during two field trips to the Kissi country with André Schaeffner (October 1945–June 1946 and October 1948–May 1949), around Kissidougou and Guéckédou; it includes a bibliography of earlier work on Kissi. |
| [`Denise Paulme - Kissi Vocabulaire_compressed.pdf`](archive/Denise%20Paulme%20-%20Kissi%20Vocabulaire_compressed.pdf) | Another copy of the same work (151 pages), scanned from a typescript, with some handwritten notes. |

### Other

| File | Description |
| --- | --- |
| [`Lexique Kissi - Français_compressed.pdf`](archive/Lexique%20Kissi%20-%20Fran%C3%A7ais_compressed.pdf) | *Lexique Kissi–Français* (68 pages), author unknown according to its title page: an alphabetical Kisiei–French word list, typed in the **current orthography** (*ɛ*, *ɔ*), with handwritten additions. |

The OCR text of Childs (1995, 2000) may be kept locally as `archive/Childs 1995 - … (text).md` and `archive/Childs 2000 - … (text).md`; these files are git-ignored and not distributed.

### The Keita transcription

The transcription of Keita (1979) is **complete and final**: all 189 PDF pages (typescript pp. 1–165 and the bibliography). The annex of tales (pp. 166–184) is not in that scan; it is the separate annex file listed above, and is not transcribed. The transcription deliberately keeps the old orthography and the author's typos, and it will not be converted to the new spelling; the guide-book uses it as a source instead. Its conventions were:

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
