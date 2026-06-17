import time
import re
import requests


def retrieve_from_api(query, platform, max_results=200,
                      email='bibliometrix-etl@example.com'):
    platform = platform.lower().strip()
    if platform == 'pubmed':
        return _retrieve_pubmed(query, max_results, email)
    elif platform == 'openalex':
        return _retrieve_openalex(query, max_results)
    else:
        raise ValueError(f"Unknown platform '{platform}'. Use 'pubmed' or 'openalex'.")


_NCBI_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
_PAGE_SIZE  = 100


def _retrieve_pubmed(query, max_results, email):
    pmids = _pubmed_esearch(query, max_results, email)
    if not pmids:
        return []
    records = []
    for i in range(0, len(pmids), _PAGE_SIZE):
        batch = pmids[i: i + _PAGE_SIZE]
        records.extend(_pubmed_efetch(batch, email))
        time.sleep(0.35)
    return records


def _pubmed_esearch(query, max_results, email):
    params = {'db': 'pubmed', 'term': query, 'retmax': max_results,
              'retmode': 'json', 'email': email}
    resp = _get_with_retry(f'{_NCBI_BASE}/esearch.fcgi', params)
    return resp.json().get('esearchresult', {}).get('idlist', [])


def _pubmed_efetch(pmids, email):
    params = {'db': 'pubmed', 'id': ','.join(pmids),
              'rettype': 'medline', 'retmode': 'text', 'email': email}
    resp = _get_with_retry(f'{_NCBI_BASE}/efetch.fcgi', params)
    return _parse_medline(resp.text)


def _parse_medline(text):
    records, current, last_key = [], {}, None
    for line in text.splitlines():
        if line.strip() == '':
            if current:
                records.append(current)
                current, last_key = {}, None
            continue
        m = re.match(r'^([A-Z]+)\s+-\s+(.+)', line)
        if m:
            key, value = m.group(1), m.group(2)
            current[key] = current.get(key, '') + (';' if key in current else '') + value
            last_key = key
        elif last_key and line.startswith('      '):
            current[last_key] += ' ' + line.strip()
    if current:
        records.append(current)
    return records


_OA_BASE    = 'https://api.openalex.org/works'
_OA_PAGE_SZ = 200


def _retrieve_openalex(query, max_results):
    records, cursor = [], '*'
    per_page = min(_OA_PAGE_SZ, max_results)
    while len(records) < max_results:
        remaining = max_results - len(records)
        params = {'search': query, 'per-page': min(per_page, remaining),
                  'cursor': cursor,
                  'select': ('id,doi,title,publication_year,primary_location,'
                             'authorships,abstract_inverted_index,cited_by_count,'
                             'keywords,type,biblio')}
        resp = _get_with_retry(_OA_BASE, params)
        data = resp.json()
        results = data.get('results', [])
        if not results:
            break
        for item in results:
            records.append(_openalex_to_raw(item))
        cursor = data.get('meta', {}).get('next_cursor')
        if not cursor:
            break
        time.sleep(0.1)
    return records[:max_results]


def _openalex_to_raw(item):
    authors = '; '.join(
        a.get('author', {}).get('display_name', '') or ''
        for a in item.get('authorships', [])
    )
    affiliations = '; '.join(
        inst.get('display_name', '')
        for a in item.get('authorships', [])
        for inst in a.get('institutions', [])
    )
    abstract = _reconstruct_abstract(item.get('abstract_inverted_index') or {})
    loc    = item.get('primary_location') or {}
    source = loc.get('source') or {}
    journal = source.get('display_name', '')
    biblio  = item.get('biblio') or {}
    doi = (item.get('doi') or '').replace('https://doi.org/', '')
    return {
        'Authors': authors, 'Author full names': authors,
        'Author(s) ID': '', 'Title': item.get('title', ''),
        'Year': str(item.get('publication_year', '')),
        'Source title': journal,
        'Volume': str(biblio.get('volume', '') or ''),
        'Issue':  str(biblio.get('issue',  '') or ''),
        'Page start': str(biblio.get('first_page', '') or ''),
        'Page end':   str(biblio.get('last_page',  '') or ''),
        'Cited by': str(item.get('cited_by_count', 0)),
        'DOI': doi, 'Affiliations': affiliations,
        'Abstract': abstract,
        'Author Keywords': '; '.join(
            k.get('keyword', '') for k in (item.get('keywords') or [])),
        'Index Keywords': '', 'Document Type': item.get('type', ''),
        'Language of Original Document': '',
        'Abbreviated Source Title': journal, 'ISSN': '',
        'EID': item.get('id', '').replace('https://openalex.org/', ''),
        'PubMed ID': '', 'Open Access': '', 'References': '',
        'Correspondence Address': '', 'Publisher': '',
        'Funding Details': '', 'Funding Texts': '',
    }


def _reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ''
    positions = [(pos, word) for word, pos_list in inverted_index.items()
                 for pos in pos_list]
    positions.sort()
    return ' '.join(w for _, w in positions)


def _get_with_retry(url, params, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
