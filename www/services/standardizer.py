from www.services.extractor import extract_raw
from www.services.transformer import transform
from www.services.validator import validate
from www.services.field_calculator import add_sr
import os


def convert2df(filepath, source):
    source = source.lower().strip()
    _check_supported(source, filepath)
    raw_records = extract_raw(filepath, source)
    df = transform(raw_records, source, filepath)
    df = add_sr(df)
    validate(df)
    return df


_SUPPORTED = {
    'scopus':     {'.csv', '.bib'},
    'dimensions': {'.csv', '.xlsx'},
    'pubmed':     {'.txt'},
    'wos':        {'.txt', '.bib', '.ciw'},
}


def _check_supported(source, filepath):
    if source not in _SUPPORTED:
        raise ValueError(f'Unknown source: {source}')
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in _SUPPORTED[source]:
        raise ValueError(f'Extension {ext} not supported for {source}')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'File not found: {filepath}')
