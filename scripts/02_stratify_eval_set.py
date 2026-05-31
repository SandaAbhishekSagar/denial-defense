"""
Stratified sampling of the CA DMHC IMR dataset for Weave evaluation.

Produces a balanced eval set across:
- Determination (Overturned / Upheld / Overturned in Part)
- Type (Medical Necessity / Experimental / Urgent Care)
- Recent cases (last 4 years preferred)

Output: data/processed/eval_set_imr.parquet (~200 cases)
Also: data/processed/eval_set_imr_preview.csv (first 20 rows for manual inspection)
Also: data/processed/imr_stats.json (dataset characterization for the README)

Run: python scripts/02_stratify_eval_set.py
"""

from __future__ import annotations
import io
import json
import sys
from pathlib import Path
import pandas as pd

# Fix Windows Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data" / "raw" / "imr" / "independent-medical-review-imr-determinations-trend.csv"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_TOTAL = 200          # final eval set size
RECENT_YEAR_FLOOR = 2023    # prefer cases from 2023+
PER_STRATUM_TARGET = 35     # cap per (Determination × Type) cell

def main() -> int:
    if not RAW_CSV.exists():
        print(f"❌ Cannot find {RAW_CSV}")
        print("   Expected the IMR CSV at data/raw/imr/")
        return 1

    print(f"Loading {RAW_CSV.name}...")
    df = pd.read_csv(RAW_CSV, low_memory=False)
    print(f"✓ Loaded {len(df):,} cases\n")

    # ---- Basic characterization ----
    df["ReportYear"] = pd.to_numeric(df["ReportYear"], errors="coerce").astype("Int64")
    df["Determination"] = df["Determination"].astype(str).str.strip()
    df["Type"] = df["Type"].astype(str).str.strip()

    stats = {
        "total_cases": int(len(df)),
        "year_min": int(df["ReportYear"].min()) if df["ReportYear"].notna().any() else None,
        "year_max": int(df["ReportYear"].max()) if df["ReportYear"].notna().any() else None,
        "determination_counts": df["Determination"].value_counts().to_dict(),
        "type_counts": df["Type"].value_counts().to_dict(),
        "top_15_diagnosis_categories": df["DiagnosisCategory"].value_counts().head(15).to_dict(),
        "top_15_treatment_categories": df["TreatmentCategory"].value_counts().head(15).to_dict(),
    }

    print(f"Year range: {stats['year_min']} - {stats['year_max']}")
    print(f"\nDetermination breakdown:")
    for k, v in stats["determination_counts"].items():
        print(f"  {k}: {v:,}")
    print(f"\nType breakdown:")
    for k, v in stats["type_counts"].items():
        print(f"  {k}: {v:,}")

    # ---- Build stratified eval set ----
    print(f"\nBuilding stratified eval set (target n≈{TARGET_TOTAL})...")

    # Prefer recent cases, but fall back to all if recent is sparse
    recent = df[df["ReportYear"] >= RECENT_YEAR_FLOOR]
    if len(recent) < TARGET_TOTAL * 2:
        print(f"  ⚠ Only {len(recent)} recent cases; using full history for stratification")
        pool = df
    else:
        print(f"  Using {len(recent):,} cases from {RECENT_YEAR_FLOOR}+ as pool")
        pool = recent

    # Stratify across Determination × Type cells, capped per stratum
    strata = []
    for det in pool["Determination"].dropna().unique():
        for typ in pool["Type"].dropna().unique():
            cell = pool[(pool["Determination"] == det) & (pool["Type"] == typ)]
            if len(cell) == 0:
                continue
            n = min(len(cell), PER_STRATUM_TARGET)
            sampled = cell.sample(n=n, random_state=42)
            strata.append(sampled)
            print(f"  {det[:30]:30} × {typ[:25]:25} → {n} cases (of {len(cell)} available)")

    eval_set = pd.concat(strata, ignore_index=True)

    # Keep useful columns only — drops noise
    keep_cols = [
        "ReferenceID", "ReportYear", "DiagnosisCategory", "DiagnosisSubCategory",
        "TreatmentCategory", "TreatmentSubCategory", "Determination", "Type",
        "AgeRange", "PatientGender", "IMRType", "Findings",
    ]
    eval_set = eval_set[keep_cols]

    # Add derived columns the harness will use
    eval_set["was_overturned"] = eval_set["Determination"].str.contains(
        "Overturned", case=False, na=False
    )
    eval_set["findings_length"] = eval_set["Findings"].astype(str).str.len()
    eval_set["case_signature"] = (
        eval_set["DiagnosisCategory"].astype(str) + " | " +
        eval_set["TreatmentCategory"].astype(str) + " | " +
        eval_set["Type"].astype(str)
    )

    # ---- Save outputs ----
    parquet_path = OUT_DIR / "eval_set_imr.parquet"
    eval_set.to_parquet(parquet_path, index=False)
    print(f"\n✓ Saved {len(eval_set)} cases to {parquet_path}")

    preview_path = OUT_DIR / "eval_set_imr_preview.csv"
    eval_set.head(20).to_csv(preview_path, index=False)
    print(f"✓ Saved 20-row preview to {preview_path}")

    stats["eval_set_size"] = int(len(eval_set))
    stats["eval_set_overturn_rate"] = float(eval_set["was_overturned"].mean())
    stats_path = OUT_DIR / "imr_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"✓ Saved dataset stats to {stats_path}")

    # ---- Summary for the user ----
    print("\n" + "=" * 60)
    print("EVAL SET READY")
    print("=" * 60)
    print(f"Total: {len(eval_set)} cases")
    print(f"Overturn rate: {eval_set['was_overturned'].mean():.1%}")
    print(f"Type distribution:")
    for k, v in eval_set["Type"].value_counts().items():
        print(f"  {k}: {v}")
    print(f"\nNext: use eval_set_imr.parquet in your Weave evaluation harness.")
    return 0


if __name__ == "__main__":
    sys.exit(main())