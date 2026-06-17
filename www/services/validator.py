import math
import pandas as pd

_MANDATORY_LISTS = {'AU', 'AF', 'C1', 'CR', 'DE', 'ID'}
_MANDATORY_INTS  = {'TC'}
_MANDATORY_STRS  = {'DB', 'UT', 'TI', 'SO', 'PY', 'SR', 'DI', 'PMID',
                    'LA', 'AB', 'DT', 'JI', 'VL', 'IS', 'BP', 'EP', 'RP'}
ALL_MANDATORY = _MANDATORY_LISTS | _MANDATORY_INTS | _MANDATORY_STRS


def validate(df):
    errors = []

    missing = ALL_MANDATORY - set(df.columns)
    if missing:
        errors.append(f'Missing mandatory columns: {sorted(missing)}')

    present = ALL_MANDATORY & set(df.columns)

    for col in present:
        n_null = df[col].apply(_is_null).sum()
        if n_null > 0:
            errors.append(f"Column '{col}' contains {n_null} null value(s).")

    for col in _MANDATORY_LISTS & present:
        bad = df[col].apply(lambda x: not isinstance(x, list)).sum()
        if bad > 0:
            errors.append(f"Column '{col}' has {bad} row(s) not typed as list.")

    if errors:
        raise ValueError('DataFrame validation failed:\n  ' + '\n  '.join(errors))

    print(f'[Validator] ✓  {len(df)} records passed all checks. '
          f'Columns: {sorted(df.columns.tolist())}')


def _is_null(value):
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False
