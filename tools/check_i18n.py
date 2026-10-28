"""Check that every page of the guide exists in both languages.

Pages use the suffix layout of mkdocs-static-i18n: ``page.fr.md`` and ``page.en.md``
side by side. Exit code 1 lists every page that has only one of the two.
"""
import pathlib
import sys

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
LANGS = ("fr", "en")


def main():
    pages = {}
    for p in DOCS.rglob("*.md"):
        parts = p.name.split(".")
        if len(parts) < 3 or parts[-2] not in LANGS:
            print(f"{p.relative_to(DOCS)}: no language suffix (.fr.md / .en.md)")
            pages.setdefault(str(p), set())
            continue
        base = str(p.relative_to(DOCS).with_name(".".join(parts[:-2])))
        pages.setdefault(base, set()).add(parts[-2])
    missing = {b: set(LANGS) - l for b, l in pages.items() if set(LANGS) - l}
    for base, langs in sorted(missing.items()):
        print(f"{base}: missing {', '.join(sorted(langs))}")
    print(f"{len(pages)} pages, {len(missing)} incomplete")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
