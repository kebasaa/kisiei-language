# Kisie

A collection of sources on the **Northern Kissi** language (also written *Kisie*, *Kisiei* or *Kissi*; ISO 639-3 `kqs`), being digitised for further use.

Northern Kissi belongs to the Mel branch of the Atlantic–Congo languages. It is spoken mainly in the Guéckédou and Kissidougou region of south-eastern Guinea, and also in neighbouring parts of Sierra Leone and Liberia.

## Purpose

Many written sources on Kisiei exist only as paper typescripts or scans, and most use an older spelling. This repository:

1. keeps the original scans in `archive/`;
2. transcribes them into Markdown **exactly as written**, in the original orthography;
3. later produces versions in the current orthography from those faithful transcriptions.

Keeping step 2 separate from step 3 means the original text can always be checked, and spelling conversion errors can be traced back.

## Repository contents

| Path | Description |
| --- | --- |
| [`archive/kissie fondamental (original scan).pdf`](archive/kissie%20fondamental%20(original%20scan).pdf) | Scan (189 pages) of *Essai d'élaboration d'un Kisiei fondamental à l'usage des locuteurs non Kisi*, a 1979 thesis by Sékou Sondo Keita (Institut Polytechnique Gamal Abdel Nasser de Conakry). It covers phonetics, grammar, verb conjugation, syntax, a Kisiei–French lexicon and Kisiei texts in an annex. Written in French and Kisiei, old orthography. |
| [`archive/kissie fondamental (transcription).md`](archive/kissie%20fondamental%20(transcription).md) | Markdown transcription of the scan above, in the original orthography. |
| [`archive/kissie fondamental (handwritten notes).md`](archive/kissie%20fondamental%20(handwritten%20notes).md) | Handwritten annotations found on the scan (mostly French glosses and translations, plus Kissidougou variants), listed page by page next to the typed text they refer to. |
| [`archive/nouvel orthographe kissi.pdf`](archive/nouvel%20orthographe%20kissi.pdf) | One-page guide mapping the old orthography to the new one. |

## Orthography

The archive documents use the **old orthography**. The main correspondences with the new orthography are:

| Old | New |
| --- | --- |
| ty | c |
| nh | ŋ |
| ny | ɲ |
| è | ɛ |
| ö | ɔ |
| mb | nb |

Example: *Söèi tasei* (old) → *Sɔɛi tasei* (new).

The new orthography also marks things the old one did not:

- **tone**, with accents on vowels (for example `ɔ́`);
- **vowel length**, by writing the vowel twice (for example `aa`, `ɔɔ`).

**Archive transcriptions deliberately keep the old spelling.** Do not "correct" them to the new orthography; converted versions will be separate files.

## Workflow and status

```
scan (PDF)  →  faithful transcription (old orthography)  →  converted text (new orthography)
```

| Source | Transcription | Conversion |
| --- | --- | --- |
| Kissie fondamental (1979) | In progress: typescript pp. 1–131, up to the Kisiei–French lexicon (PDF pp. 1–148 of 189) | Not started |

### Transcription conventions

- Reproduce the text exactly: spelling (including the author's typos), diacritics, punctuation and capitalisation.
- Use precomposed Unicode characters (NFC), for example `ö` as U+00F6.
- Use Markdown only for structure: headings, tables for lexicons and paradigms, and paragraphs.
- Handwritten corrections of the typed text go into the transcription: the struck text as `~~strikethrough~~`, the handwritten replacement as `<ins>…</ins>`.
- All other handwritten annotations go in a separate `(handwritten notes).md` file: one table per page, each note next to the typed text it refers to, labelled as gloss, translation, variant or comment, with `[?]` for uncertain readings. In the transcription, a `> ✎ [Handwritten notes, p. N](…#p-n-pdf-m)` line where that page's content begins links to the matching notes section. The glosses and translations there can later be collected into a Kisiei–French word list.

## External resources

- **Kisiei Bible** (YouVersion): <https://www.bible.com/bible/1394/GEN.1.BKG>. A large text in the modern orthography, including tone marks and long vowels. It is the main reference for modern spelling conventions when converting the archive transcriptions.

## License

The contents of this repository are licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/) (CC BY-NC 4.0); see [`LICENSE`](LICENSE). You may share and adapt the material for non-commercial purposes, as long as you give appropriate credit.

The original works in `archive/`, such as Sékou Sondo Keita's 1979 thesis, remain the work of their authors. When using them or their transcriptions, credit the original author as well as this repository.
