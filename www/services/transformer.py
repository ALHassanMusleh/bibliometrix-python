import os
import math
import pandas as pd

from www.services.format_functions import (
    format_ab_column, format_af_column, format_au_column,
    format_au_un_column, format_au1_un_column, format_bp_column,
    format_c1_column, format_cr_column, format_de_column,
    format_di_column, format_dt_column, format_em_column,
    format_ep_column, format_fu_column, format_fx_column,
    format_id_column, format_is_column, format_ji_column,
    format_la_column, format_oa_column, format_oi_column,
    format_pmid_column, format_pu_column, format_py_column,
    format_rp_column, format_sc_column, format_sn_column,
    format_so_column, format_tc_column, format_ti_column,
    format_ut_column, format_vl_column,
)

_SOURCE_ALIAS = {
    'scopus':     'Scopus',
    'dimensions': 'Dimensions',
    'pubmed':     'PubMed',
    'wos':        'Web_of_Science',
}

_EXT_ALIAS = {
    '.csv': '.csv', '.xlsx': '.xlsx',
    '.txt': '.txt', '.bib': '.bib', '.ciw': '.ciw',
}

_DB_LABEL = {
    'scopus':     'SCOPUS',
    'dimensions': 'DIMENSIONS',
    'pubmed':     'PUBMED',
    'wos':        'WEB_OF_SCIENCE',
}

_LIST_COLUMNS = {'AU', 'AF', 'C1', 'CR', 'DE', 'ID', 'EM', 'OI', 'OA', 'SC', 'FU', 'AU_UN'}
_INT_COLUMNS  = {'TC'}
_NUM_COLUMNS  = {'PY'}
_STR_COLUMNS  = {'DB', 'UT', 'DI', 'PMID', 'TI', 'SO', 'JI', 'DT', 'LA', 'AB',
                 'VL', 'IS', 'BP', 'EP', 'SR', 'RP', 'FX', 'SN', 'PU', 'AU1_UN'}
_ALL_COLUMNS  = sorted(_LIST_COLUMNS | _INT_COLUMNS | _NUM_COLUMNS | _STR_COLUMNS)

_FIELD_BUILDERS = {
    'AB': format_ab_column,   'AF': format_af_column,   'AU': format_au_column,
    'AU_UN': format_au_un_column, 'AU1_UN': format_au1_un_column,
    'BP': format_bp_column,   'C1': format_c1_column,   'CR': format_cr_column,
    'DE': format_de_column,   'DI': format_di_column,   'DT': format_dt_column,
    'EM': format_em_column,   'EP': format_ep_column,   'FU': format_fu_column,
    'FX': format_fx_column,   'ID': format_id_column,   'IS': format_is_column,
    'JI': format_ji_column,   'LA': format_la_column,   'OA': format_oa_column,
    'OI': format_oi_column,   'PMID': format_pmid_column, 'PU': format_pu_column,
    'PY': format_py_column,   'RP': format_rp_column,   'SC': format_sc_column,
    'SN': format_sn_column,   'SO': format_so_column,   'TC': format_tc_column,
    'TI': format_ti_column,   'UT': format_ut_column,   'VL': format_vl_column,
}


def transform(raw_records, source, filepath):
    src = _SOURCE_ALIAS[source]
    ext = _EXT_ALIAS.get(os.path.splitext(filepath)[1].lower(), '.txt')
    db  = _DB_LABEL[source]

    rows = []
    for entry in raw_records:
        row = {'DB': db}
        for tag, fn in _FIELD_BUILDERS.items():
            try:
                row[tag] = fn(entry, src, ext)
            except Exception:
                if tag in _LIST_COLUMNS:
                    row[tag] = []
                elif tag in (_INT_COLUMNS | _NUM_COLUMNS):
                    row[tag] = 0
                else:
                    row[tag] = ''
        rows.append(row)

    df = pd.DataFrame(rows)

    for col in _ALL_COLUMNS:
        if col not in df.columns:
            if col in _LIST_COLUMNS:
                df[col] = [[] for _ in range(len(df))]
            elif col in (_INT_COLUMNS | _NUM_COLUMNS):
                df[col] = 0
            else:
                df[col] = ''

    return _apply_type_contracts(df)


def _apply_type_contracts(df):
    for col in _LIST_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(_to_list)
    for col in _INT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(_to_int)
    for col in _NUM_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    for col in _STR_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(_to_str)
    return df


def _to_list(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if x is not None and str(x).strip() not in ('', 'nan', 'None')]
    if isinstance(v, str):
        s = v.strip()
        if s in ('', 'nan', 'None', '[]'):
            return []
        return [p.strip() for p in s.split(';') if p.strip()]
    return []


def _to_int(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 0
    try:
        return int(float(str(v).strip()))
    except Exception:
        return 0


def _to_str(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ''
    s = str(v).strip()
    return '' if s in ('nan', 'None', 'NaN') else s
