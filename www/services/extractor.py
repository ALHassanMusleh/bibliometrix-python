import os
import pandas as pd
from bibtexparser.bparser import BibTexParser


def extract_raw(filepath, source):
    ext = os.path.splitext(filepath)[1].lower()
    key = (source, ext)
    loader = _DISPATCHER.get(key)
    if loader is None:
        raise ValueError(f'No extractor for source={source}, ext={ext}')
    return loader(filepath)


def _load_scopus_csv(filepath):
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    return df.to_dict(orient='records')


def _load_dimensions_csv(filepath):
    df = pd.read_csv(filepath, skiprows=1, encoding='utf-8-sig')
    return df.to_dict(orient='records')


def _load_dimensions_xlsx(filepath):
    df = pd.read_excel(filepath, skiprows=1)
    return df.to_dict(orient='records')


def _load_pubmed_txt(filepath):
    from www.services.parsers import parse_pubmed_data
    return parse_pubmed_data(filepath)


def _load_wos_txt(filepath):
    from www.services.parsers import parse_wos_data
    return parse_wos_data(filepath)


def _load_bib(filepath):
    parser = BibTexParser()
    with open(filepath, encoding='utf-8') as fh:
        bib_data = parser.parse_file(fh)
    return bib_data.entries


_DISPATCHER = {
    ('scopus',     '.csv'):  _load_scopus_csv,
    ('scopus',     '.bib'):  _load_bib,
    ('dimensions', '.csv'):  _load_dimensions_csv,
    ('dimensions', '.xlsx'): _load_dimensions_xlsx,
    ('pubmed',     '.txt'):  _load_pubmed_txt,
    ('wos',        '.txt'):  _load_wos_txt,
    ('wos',        '.ciw'):  _load_wos_txt,
    ('wos',        '.bib'):  _load_bib,
}
