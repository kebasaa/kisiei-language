# Outils

Les règles de ce guide sont dégagées des textes de la Bible en kisiei [[(BKG)]] à l'aide de quelques outils, disponibles dans le dossier [`tools/`](https://github.com/kebasaa/Kisie/tree/main/tools) du dépôt. Ils s'exécutent avec [uv](https://docs.astral.sh/uv/).

## Le texte de la Bible

`tools/fetch_bible.py` télécharge les chapitres de la Bible en kisiei depuis bible.com, lentement (environ un par seconde), dans un dossier local `.cache/bible/` qui **n'est pas** versé dans le dépôt : le texte reste la propriété de l'Alliance Biblique en Guinée. Seule la liste des formes de mots est publiée.

```bash
uv run tools/fetch_bible.py --delay 1.0
```

## La liste des formes de mots

`tools/build_wordlist.py` produit [`references/bible-bkg-wordforms.tsv`](https://github.com/kebasaa/Kisie/blob/main/references/bible-bkg-wordforms.tsv) : chaque forme de mot de la Bible (sans tenir compte des tons ni des majuscules), son nombre d'occurrences, ses graphies avec accents de ton et une première référence. La Bible complète (1 188 chapitres) compte environ 939 000 mots et près de 22 000 formes différentes.

## La concordance

`tools/bible_concordance.py` cherche dans le texte local un mot, une partie de mot ou un motif, et affiche chaque occurrence dans son contexte avec sa référence. C'est l'outil principal pour vérifier une règle :

```bash
uv run tools/bible_concordance.py -w "ndɔ(ɔ|a|lan|len)"
```

## Les vérifications automatiques

À chaque construction du site (`mkdocs build --strict`), un module (`tools/kisiei_hooks.py`) :

- vérifie que chaque exemple kisiei marqué comme attesté figure dans la liste des formes de la Bible ; sinon, la construction échoue ;
- transforme les citations (« (Keita 1979, p. 57) ») en liens vers la [bibliographie](bibliography.md) et signale les clés inconnues ;
- accepte aussi l'abréviation `[[GEN.1.3]]` pour une référence biblique, mais les pages écrivent les références comme de simples liens Markdown vers le verset sur bible.com (`[Gn 1,3](https://www.bible.com/bible/1394/GEN.1.3.BKG)`), lisibles aussi hors du site.

`tools/check_i18n.py` vérifie que chaque page existe en français et en anglais.
