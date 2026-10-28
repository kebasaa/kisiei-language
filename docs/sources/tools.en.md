# Tools

The rules of this guide are drawn from the texts of the Kisiei Bible [[(BKG)]] with the help of a few tools, available in the [`tools/`](https://github.com/kebasaa/Kisie/tree/main/tools) folder of the repository. They are run with [uv](https://docs.astral.sh/uv/).

## The Bible text

`tools/fetch_bible.py` downloads the chapters of the Kisiei Bible from bible.com, slowly (about one per second), into a local `.cache/bible/` folder that is **not** added to the repository: the text remains the property of the Alliance Biblique en Guinée. Only the list of word forms is published.

```bash
uv run tools/fetch_bible.py --delay 1.0
```

## The list of word forms

`tools/build_wordlist.py` produces [`references/bible-bkg-wordforms.tsv`](https://github.com/kebasaa/Kisie/blob/main/references/bible-bkg-wordforms.tsv): each word form of the Bible (ignoring tones and capitals), its number of occurrences, its spellings with tone accents and a first reference. The complete Bible (1,188 chapters) contains about 939,000 words and nearly 22,000 different forms.

## The concordance

`tools/bible_concordance.py` searches the local text for a word, part of a word or a pattern, and shows each occurrence in its context with its reference. It is the main tool for checking a rule:

```bash
uv run tools/bible_concordance.py -w "ndɔ(ɔ|a|lan|len)"
```

## The automatic checks

Every time the site is built (`mkdocs build --strict`), a module (`tools/kisiei_hooks.py`):

- checks that every Kisiei example marked as attested is in the list of Bible word forms; otherwise, the build fails;
- turns citations (“(Keita 1979, p. 57)”) into links to the [bibliography](bibliography.md) and reports unknown keys;
- also accepts an abbreviation in double square brackets (book code, chapter and verse, for example GEN.1.3) for a Bible reference, but the pages write references as plain Markdown links to the verse on bible.com (`[Gen 1:3](https://www.bible.com/bible/1394/GEN.1.3.BKG)`), which are also readable outside the site.

`tools/check_i18n.py` checks that every page exists in French and in English.
