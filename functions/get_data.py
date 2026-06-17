import ast
import pandas as pd
from www.services import *


_ETL_SIGNATURE = {'AU', 'TI', 'SO', 'SR', 'PY', 'TC', 'CR', 'DE', 'DB'}


def _is_etl_output(filepath):
    try:
        peek = pd.read_csv(filepath, nrows=0, encoding='utf-8-sig')
        return _ETL_SIGNATURE.issubset(set(peek.columns))
    except Exception:
        return False


def _load_etl_csv(filepath):
    df = pd.read_csv(filepath, encoding='utf-8-sig', low_memory=False)

    LIST_COLS = {'AU', 'AF', 'C1', 'CR', 'DE', 'ID', 'EM', 'OI', 'OA',
                 'SC', 'FU', 'AU_UN'}

    def _to_list(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return []
        s = str(v).strip()
        if s in ('', 'nan', 'None', '[]'):
            return []
        if s.startswith('['):
            try:
                result = ast.literal_eval(s)
                if isinstance(result, list):
                    return [str(x) for x in result if x]
            except Exception:
                pass
        return [p.strip() for p in s.split(';') if p.strip()]

    for col in LIST_COLS:
        if col not in df.columns:
            df[col] = [[] for _ in range(len(df))]
        else:
            df[col] = df[col].apply(_to_list)

    if 'PY' in df.columns:
        df['PY'] = pd.to_numeric(df['PY'], errors='coerce').fillna(0).astype(int)

    if 'TC' in df.columns:
        df['TC'] = pd.to_numeric(df['TC'], errors='coerce').fillna(0).astype(int)

    str_cols = {'DB', 'UT', 'DI', 'PMID', 'TI', 'SO', 'JI', 'DT', 'LA', 'AB',
                'VL', 'IS', 'BP', 'EP', 'SR', 'RP', 'FX', 'SN', 'PU', 'AU1_UN'}
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
            df[col] = df[col].replace({'nan': '', 'None': ''})

    return df


def get_data(input, database, df, reset_callback=None):
    file: list[FileInfo] | None = input.Dataset()

    if file is None:
        text = ui.h5('Please select a file to begin importing your data.')

    elif input.select() == '1A':
        ui.update_action_button('action_button_save', disabled=False)
        source = input.database()
        author = input.author()

        try:
            if len(file) > 1:
                all_etl = all(
                    _is_etl_output(f['datapath'])
                    for f in file if f['name'].endswith('.csv')
                )
                if all_etl and all(f['name'].endswith('.csv') for f in file):
                    frames = [_load_etl_csv(f['datapath']) for f in file]
                    combined = pd.concat(frames, ignore_index=True)
                    df.set(combined)
                    if reset_callback:
                        reset_callback()
                    text = ui.p(
                        f'Loaded {len(file)} pre-standardised ETL files. '
                        f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
                    )
                else:
                    json = process_multiple_files(file, source, author)
                    df.set(pd.read_json(StringIO(json)))
                    if reset_callback:
                        reset_callback()
                    text = ui.p(
                        f"{database}'s files uploaded and processed successfully! "
                        f'{len(file)} files processed. '
                        f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
                    )
            else:
                filepath = file[0]['datapath']
                filename = file[0]['name']

                if filename.endswith('.csv') and _is_etl_output(filepath):
                    loaded_df = _load_etl_csv(filepath)
                    df.set(loaded_df)
                    if reset_callback:
                        reset_callback()
                    db_label = loaded_df['DB'].iloc[0] if 'DB' in loaded_df.columns else database
                    text = ui.p(
                        f'Pre-standardised ETL file loaded successfully ({db_label}). '
                        f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
                    )
                else:
                    json = biblio_json(filepath, source, filename, author)
                    df.set(pd.read_json(StringIO(json)))
                    if reset_callback:
                        reset_callback()
                    if filename.endswith('.zip'):
                        text = ui.p(
                            f"{database}'s ZIP archive uploaded successfully! "
                            f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
                        )
                    else:
                        text = ui.p(
                            f"{database}'s file uploaded successfully! "
                            f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
                        )

        except Exception as e:
            text = ui.div(
                ui.h5('Error processing file(s):', style='color: red;'),
                ui.p(str(e), style='color: red;'),
                ui.p('Please check that your files are in the correct format and try again.',
                     style='color: gray;'),
            )

    elif input.select() == '1B':
        df.set(pd.read_excel(file[0]['datapath']))
        if reset_callback:
            reset_callback()
        text = ui.p(
            f"{database}'s file uploaded successfully! "
            f'Dataset: {df.get().shape[0]} rows, {df.get().shape[1]} columns.'
        )

    else:
        text = ''

    return text
