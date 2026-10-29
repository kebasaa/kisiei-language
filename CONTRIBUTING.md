# Writing for the guide-book

## Pages

- Every page exists in French and English, side by side: `page.fr.md` and `page.en.md`. `python tools/check_i18n.py` reports a missing translation, and the site build runs it.
- The Kisiei Bible (BKG) is the spelling standard. Take examples from the Bible where possible, with their reference.
- Check the site with `uv run --with-requirements requirements-docs.txt mkdocs build --strict` before committing.

## Marking Kisiei, references and citations

| Write | For | Result |
| --- | --- | --- |
| `{{cɛiyo}}` | a Kisiei word or phrase found in the Bible | italic, solid underline; the build fails if a word is not in `references/bible-bkg-wordforms.tsv` |
| `{{word\|c}}` | confirmed by a speaker, not in the Bible | double underline |
| `{{word\|r}}` | respelled from Keita 1979, not in the Bible | dashed underline |
| `{{word\|s}}` | Southern Kissi only (Childs 2000) | wavy underline |
| `{{word\|?}}` | uncertain form or meaning | dotted underline |
| `[[GEN.1.3]]` | a Bible verse | link to bible.com, with the book abbreviation of the page language |
| `[[Keita1979, p. 57]]`, `[[(Keita1979, p. 57)]]` | a citation from `docs/references.bib` | Keita (1979, p. 57), (Keita 1979, p. 57) |

Inside a Markdown table, write the flag separator as `\|`.

Boxes: `!!! rule "Règle"` (a rule to remember), `!!! keita "Usage de 1979"` (where Keita differs from the Bible), `!!! note "Note"`.

## Diagrams

Use a diagram when a rule is a choice or a sequence that is easier to follow as a picture than as text. A diagram shows only what its page already says, and appears in both language versions with translated labels.

- **Flowcharts and decision trees:** a Mermaid block inside a figure, with a one-line caption:

  ````markdown
  <figure class="ks-figure" markdown="1">

  ```mermaid
  flowchart TD
      Q{"After n, m, ŋ, l?"} -- yes --> A["{{te}}"]
      Q -- no --> B["{{le}}"]
  ```

  <figcaption>Choosing the final particle.</figcaption>
  </figure>
  ````

  Kisiei inside the diagram is written with `{{…}}` like anywhere else: the build checks it against the Bible list and shows it in italics. For that reason, Mermaid's hexagon shape `{{…}}` and the subroutine shape `[[…]]` cannot be used. Colours are given as hex values (`classDef att stroke:#2e9e63`), since Mermaid does not accept CSS variables; pick mid tones that read in both light and dark mode.
- **Charts** (vowel chart, timelines, sentence slots): inline SVG inside `<figure class="ks-figure">`, with no blank lines inside the figure. Use `viewBox` so it scales, and the classes `line`, `accent`, `primary`, `muted` and `box` from `docs/assets/site.css` instead of fixed colours, so the figure follows the light and dark themes. SVG text is not checked by the build: keep Kisiei words in SVG to forms already attested on the page.
