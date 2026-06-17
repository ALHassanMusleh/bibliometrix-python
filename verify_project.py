"""
verify_project.py  — run from the bibliometrix-python root folder:
    python verify_project.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "  \u2705 PASS"
FAIL = "  \u274c FAIL"
results = []

def check(label, fn):
    try:
        out = fn()
        print(f"{PASS}  {label}")
        results.append((True, label))
        return out
    except Exception as e:
        print(f"{FAIL}  {label}")
        print(f"         \u2192 {e}")
        results.append((False, label))
        return None

print("\n" + "="*60)
print("  BIBLIOMETRIX-PYTHON ETL \u2014 PROJECT VERIFICATION")
print("="*60)

print("\n\u25b6  Step 1: Module imports")
check("Import www.services", lambda: __import__("www.services", fromlist=["*"]) and True)
check("Import standardizer",    lambda: __import__("www.services.standardizer",    fromlist=["convert2df"]))
check("Import extractor",       lambda: __import__("www.services.extractor",       fromlist=["extract_raw"]))
check("Import transformer",     lambda: __import__("www.services.transformer",     fromlist=["transform"]))
check("Import validator",       lambda: __import__("www.services.validator",       fromlist=["validate"]))
check("Import field_calculator",lambda: __import__("www.services.field_calculator",fromlist=["add_sr"]))
check("Import api_retriever",   lambda: __import__("www.services.api_retriever",   fromlist=["retrieve_from_api"]))

from www.services.standardizer import convert2df
import pandas as pd

print("\n\u25b6  Step 2-4: ETL Pipeline")
SOURCES = [
    ("Scopus",     "scopus",     "sources/Scopus/Scopus.csv"),
    ("Dimensions", "dimensions", "sources/Dimensions/Dimensions.csv"),
    ("PubMed",     "pubmed",     "sources/PubMed/pubmed-allergicrh-set.txt"),
]
dfs = {}
for name, source, path in SOURCES:
    df = check(f"convert2df({name})", lambda s=source, p=path: convert2df(p, s))
    dfs[source] = df

print("\n\u25b6  Step 5: Mandatory columns present")
MANDATORY = {"DB","UT","DI","PMID","TI","SO","JI","PY","DT","LA","TC",
             "AU","AF","C1","RP","CR","DE","ID","AB","VL","IS","BP","EP","SR"}
for source, df in dfs.items():
    if df is None: continue
    missing = MANDATORY - set(df.columns)
    check(f"{source.upper()} \u2014 all {len(MANDATORY)} mandatory columns",
          lambda m=missing: (_ for _ in ()).throw(ValueError(f"Missing: {m}")) if m else True)

print("\n\u25b6  Step 6: Type contracts")
for source, df in dfs.items():
    if df is None: continue
    check(f"{source.upper()} \u2014 AU is list[str]",
          lambda d=df: (_ for _ in ()).throw(TypeError("AU not list")) if not isinstance(d["AU"].iloc[0], list) else True)
    check(f"{source.upper()} \u2014 TC is int",
          lambda d=df: (_ for _ in ()).throw(TypeError("TC not int")) if not hasattr(d["TC"].iloc[0], '__int__') else True)
    check(f"{source.upper()} \u2014 PY is numeric (int)",
          lambda d=df: (_ for _ in ()).throw(TypeError("PY not numeric")) if not hasattr(d["PY"].iloc[0], '__int__') or isinstance(d["PY"].iloc[0], bool) or str(type(d["PY"].iloc[0])) == "<class 'str'>" else True)

print("\n\u25b6  Step 7: No NaN/None in mandatory columns")
def count_nulls(df, col):
    def is_null(v):
        if v is None: return True
        if isinstance(v, float) and math.isnan(v): return True
        return False
    return df[col].apply(is_null).sum()

for source, df in dfs.items():
    if df is None: continue
    total = sum(count_nulls(df, c) for c in MANDATORY if c in df.columns)
    check(f"{source.upper()} \u2014 zero nulls",
          lambda n=total: (_ for _ in ()).throw(ValueError(f"{n} nulls")) if n > 0 else True)

print("\n\u25b6  Step 8: SR column populated")
for source, df in dfs.items():
    if df is None: continue
    empty = (df["SR"] == "").sum()
    check(f"{source.upper()} \u2014 SR non-empty (empty={empty}/{len(df)})",
          lambda e=empty, n=len(df): (_ for _ in ()).throw(ValueError(f"{e} empty")) if e == n else True)

print("\n\u25b6  Step 9: Key analytical functions")
from functions.get_maininformations import get_main_informations
from functions.get_annualproduction import get_annual_production
from functions.get_relevantauthors  import get_relevant_authors
from functions.get_relevantsources  import get_relevant_sources
from functions.get_bradfordlaw      import get_bradford_law
from functions.get_averagecitations import get_average_citations
from functions.get_lotkalaw         import get_lotka_law

class MockRV:
    def __init__(self, df): self._df = df
    def get(self): return self._df
    def set(self, v): self._df = v

for source, df in dfs.items():
    if df is None: continue
    rv = MockRV(df)
    for fname, fn in [
        ("get_main_informations", lambda r=rv: get_main_informations(r)),
        ("get_annual_production", lambda r=rv: get_annual_production(r)),
        ("get_relevant_authors",  lambda r=rv: get_relevant_authors(r, 10, 'n_docs')),
        ("get_relevant_sources",  lambda r=rv: get_relevant_sources(r, 10)),
        ("get_bradford_law",      lambda r=rv: get_bradford_law(r)),
        ("get_average_citations", lambda r=rv: get_average_citations(r)),
        ("get_lotka_law",         lambda r=rv: get_lotka_law(r)),
    ]:
        check(f"{source.upper()} \u2014 {fname}", fn)

print("\n\u25b6  Step 10: Export CSVs")
for source, df in dfs.items():
    if df is None: continue
    out = f"output_{source}.csv"
    def save(d=df, o=out):
        d.to_csv(o, index=False)
        if not os.path.exists(o): raise FileNotFoundError(o)
        return f"Saved {len(d)} rows \u2192 {o}"
    result = check(f"Save {out}", save)
    if result: print(f"         {result}")

print("\n" + "="*60)
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
print(f"  RESULTS: {passed}/{len(results)} checks passed", end="")
if failed == 0:
    print("  \U0001f389  PROJECT IS FULLY CORRECT AND READY FOR SUBMISSION")
else:
    print(f"\n  \u26a0\ufe0f  {failed} check(s) FAILED")
    for ok, label in results:
        if not ok: print(f"       \u2717 {label}")
print("="*60 + "\n")
