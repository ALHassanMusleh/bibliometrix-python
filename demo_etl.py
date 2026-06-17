"""
demo_etl.py  — generates standardised CSV files from all sources.
Run from the bibliometrix-python root:
    python demo_etl.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from www.services.standardizer import convert2df

SOURCES = [
    ("Scopus",     "scopus",     "sources/Scopus/Scopus.csv",                    "output_scopus.csv"),
    ("Dimensions", "dimensions", "sources/Dimensions/Dimensions.csv",            "output_dimensions.csv"),
    ("PubMed",     "pubmed",     "sources/PubMed/pubmed-allergicrh-set.txt",     "output_pubmed.csv"),
]

print("\n" + "="*55)
print("  Bibliometrix-Python ETL Pipeline \u2014 Demo")
print("="*55)

for name, source, inpath, outpath in SOURCES:
    if not os.path.exists(inpath):
        print(f"\n[SKIP] {name} file not found: {inpath}")
        continue
    print(f"\n[{name}] Processing {inpath} ...")
    df = convert2df(inpath, source)
    df.to_csv(outpath, index=False)
    print(f"  Records : {len(df)}")
    print(f"  Columns : {len(df.columns)}")
    print(f"  Saved   : {outpath}")
    print(f"  SR[0]   : {df['SR'].iloc[0]}")
    print(f"  AU[0]   : {df['AU'].iloc[0][:2]}")
    print(f"  PY type : {type(df['PY'].iloc[0]).__name__}")

print("\n" + "="*55)
print("  All done. Upload the output_*.csv files to the dashboard.")
print("="*55 + "\n")
