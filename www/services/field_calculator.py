import pandas as pd
from www.services.format_functions import format_sr_column

_DB_TO_SOURCE = {
    'SCOPUS':         'Scopus',
    'DIMENSIONS':     'Dimensions',
    'PUBMED':         'PubMed',
    'WEB_OF_SCIENCE': 'Web_of_Science',
}

_DB_TO_EXT = {
    'SCOPUS':         '.csv',
    'DIMENSIONS':     '.csv',
    'PUBMED':         '.txt',
    'WEB_OF_SCIENCE': '.txt',
}


def add_sr(df):
    if 'SR' not in df.columns:
        df['SR'] = ''
    df['SR'] = df.apply(_compute_sr, axis=1)
    return df


def _compute_sr(row):
    if str(row.get('SR', '')).strip():
        return row['SR']
    db     = str(row.get('DB', '')).upper()
    source = _DB_TO_SOURCE.get(db, 'Scopus')
    ext    = _DB_TO_EXT.get(db, '.csv')
    raw    = _row_to_raw(row, db)
    try:
        result = format_sr_column(raw, source, ext)
        return result if result else _fallback_sr(row)
    except Exception:
        return _fallback_sr(row)


def _row_to_raw(row, db):
    au_list  = row.get('AU', [])
    first_au = au_list[0] if au_list else ''
    if db == 'SCOPUS':
        return {
            'Authors':      first_au,
            'Year':         str(row.get('PY', '')),
            'Source title': row.get('SO', ''),
        }
    elif db == 'DIMENSIONS':
        return {
            'Authors':      first_au + '; ',
            'PubYear':      str(row.get('PY', '')),
            'Source title': row.get('SO', ''),
        }
    elif db == 'PUBMED':
        return {
            'AU': first_au,
            'DP': str(row.get('PY', '')),
            'TA': row.get('JI', row.get('SO', '')),
        }
    else:
        return {
            'AU': au_list if au_list else [''],
            'PY': [str(row.get('PY', ''))],
            'SO': [row.get('SO', '')],
        }


def _fallback_sr(row):
    au_list = row.get('AU', [])
    first   = au_list[0] if au_list else ''
    year    = str(row.get('PY', ''))
    so      = str(row.get('SO', ''))
    return f'{first}, {year}, {so}'
