# scripts/01_explore_imr.py
import pandas as pd

df = pd.read_csv("data/raw/imr/independent-medical-review-imr-determinations-trend.csv")

print(f"Total cases: {len(df):,}")
print(f"\nDetermination breakdown:\n{df['Determination'].value_counts()}")
print(f"\nType breakdown:\n{df['Type'].value_counts()}")
print(f"\nTop 15 diagnosis categories:\n{df['DiagnosisCategory'].value_counts().head(15)}")
print(f"\nTop 15 treatment categories:\n{df['TreatmentCategory'].value_counts().head(15)}")
print(f"\nYear range: {df['ReportYear'].min()} to {df['ReportYear'].max()}")
print(f"\nSample Findings (overturned):\n")
print(df[df['Determination'].str.contains('Overturned')].iloc[0]['Findings'][:500])

# Stratified sample for eval
overturned = df[df['Determination'].str.contains('Overturned')]
upheld = df[df['Determination'].str.contains('Upheld')]
recent = df[df['ReportYear'].astype(str).str.contains('202[3-6]', regex=True)]

# 100 overturned + 100 upheld, recent, stratified by Type
eval_set = pd.concat([
    overturned[overturned['ReportYear'].astype(str).str.contains('202[3-6]', regex=True)]
        .groupby('Type', group_keys=False).apply(lambda x: x.sample(min(len(x), 35))),
    upheld[upheld['ReportYear'].astype(str).str.contains('202[3-6]', regex=True)]
        .groupby('Type', group_keys=False).apply(lambda x: x.sample(min(len(x), 35))),
]).reset_index(drop=True)

eval_set.to_parquet("data/processed/eval_set_imr.parquet")
print(f"\nSaved eval set: {len(eval_set)} cases")