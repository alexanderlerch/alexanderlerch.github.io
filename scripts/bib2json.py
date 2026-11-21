"""Convert the BibTeX publication list into JSON for the Jekyll publications page.

usage: python scripts/bib2json.py bib/lerch.bib _data/publications.json
"""
import json
import sys

import bibtexparser
from bibtexparser.bparser import BibTexParser
from pylatexenc.latex2text import LatexNodes2Text

# fields shown on the page; everything else (abstract, file, keywords, ...) is dropped
FIELDS = ['title', 'url', 'journal', 'booktitle', 'editor', 'publisher', 'institution',
          'address', 'volume', 'number', 'pages', 'month', 'year']

latex = LatexNodes2Text(math_mode='verbatim')


def clean(value):
    # resolve LaTeX accents/escapes and strip protective braces
    return ' '.join(latex.latex_to_text(value).split())


def format_names(value):
    # 'Last, First and Last2, First2' -> 'First Last, and First2 Last2'
    names = []
    for name in value.replace('\n', ' ').split(' and '):
        parts = [p.strip() for p in name.split(',')]
        if len(parts) == 2:
            name = parts[1] + ' ' + parts[0]
        elif len(parts) == 3:  # 'von Last, Jr, First'
            name = parts[2] + ' ' + parts[0] + ', ' + parts[1]
        names.append(clean(name))
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ', and ' + names[-1]


def convert(entry):
    pub = {'key': entry['ID'], 'type': entry['ENTRYTYPE']}
    for field in FIELDS:
        if entry.get(field):
            pub[field] = entry[field].strip() if field == 'url' else clean(entry[field])
    if entry.get('pages'):
        pub['pages'] = pub['pages'].replace('--', '-')
    for field in ['author', 'editor']:
        if entry.get(field):
            pub[field] = format_names(entry[field])
    return pub


def main(bib_path, json_path):
    parser = BibTexParser(common_strings=True)  # resolves month macros (jul -> July)
    parser.ignore_nonstandard_types = False
    with open(bib_path, encoding='utf-8') as f:
        entries = bibtexparser.load(f, parser=parser).entries
    pubs = [convert(e) for e in entries]

    # newest year first; within a year, journal articles first (descending by
    # journal name), then everything else in file order
    years = sorted({p['year'] for p in pubs}, reverse=True)
    groups = []
    for year in years:
        in_year = [p for p in pubs if p['year'] == year]
        articles = sorted([p for p in in_year if p.get('journal')], key=lambda p: p['journal'], reverse=True)
        others = [p for p in in_year if not p.get('journal')]
        groups.append({'year': year, 'publications': articles + others})

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=1)
    print(f'{len(pubs)} publications in {len(groups)} years written to {json_path}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
