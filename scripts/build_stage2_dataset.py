#!/usr/bin/env python3
"""
StepWise: Stage 2 Master Biofluid & Genomic Dataset Builder
Harmonizes 7 multi-platform ADNI plasma assays via per-assay Z-scoring,
cleans LOD sentinels, merges with Stage 1 clinical features and APOE-ε4 genotyping,
and creates the 24-month progression dataset for Stage 2.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

STAGE1_PARQUET = PROCESSED_DIR / "stage1_screening.parquet"
SENTINEL = -4.0


def clean_lod(series: pd.Series) -> pd.Series:
    """Cleans string LOD markers (<LOD, BLOQ, <0.5) and ADNI -4 / -5 sentinels."""
    if series.dtype == object:
        s = series.astype(str).str.strip()
        s = s.replace({"<LOD": np.nan, "BLOQ": np.nan, "nan": np.nan, "": np.nan, "NA": np.nan, "-4": np.nan, "-5": np.nan})
        s = s.str.replace(r"[<>]", "", regex=True)
        series = pd.to_numeric(s, errors="coerce")
    else:
        series = pd.to_numeric(series, errors="coerce")
    series = series.replace({-4.0: np.nan, -5.0: np.nan, -4: np.nan, -5: np.nan})
    return series


def zscore_col(series: pd.Series) -> pd.Series:
    """Z-scores a series, ignoring NaNs."""
    mu = series.mean(skipna=True)
    sd = series.std(skipna=True)
    if pd.notna(sd) and sd > 0:
        return (series - mu) / sd
    return series * 0.0


def clean_keys(df):
    df = df.copy()
    if "PTID" in df.columns:
        df["PTID"] = df["PTID"].astype(str).str.strip()
    if "VISCODE2" in df.columns:
        df["VISCODE2"] = df["VISCODE2"].astype(str).str.strip().str.lower()
    elif "VISCODE" in df.columns:
        df["VISCODE2"] = df["VISCODE"].astype(str).str.strip().str.lower()
    return df


def load_c2n():
    print("Ingesting C2N PrecivityAD2 Plasma Assay...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "C2N" / "C2N_PRECIVITYAD2_PLASMA_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    cols = ["pT217_C2N", "npT217_C2N", "pT217_npT217_C2N", "AB42_C2N", "AB40_C2N", "AB42_AB40_C2N", "APS2_C2N"]
    for c in cols:
        if c in df.columns:
            df[c] = clean_lod(df[c])
            df[f"c2n_{c}_z"] = zscore_col(df[c])
            
    df["c2n_is_amyloid_pos"] = (df["APS2_C2N"] >= 36).astype(float)
    df.loc[df["APS2_C2N"].isna(), "c2n_is_amyloid_pos"] = np.nan
    
    out_cols = ["PTID", "VISCODE2", "c2n_is_amyloid_pos"] + [c for c in df.columns if c.startswith("c2n_") and c.endswith("_z")]
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_upenn_fujirebio():
    print("Ingesting UPenn Fujirebio & Quanterix Biomarkers...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "UPENN_AB_Tau" / "UPENN_PLASMA_FUJIREBIO_QUANTERIX_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    cols = ["pT217_F", "AB42_F", "AB40_F", "AB42_AB40_F", "pT217_AB42_F", "NfL_Q", "GFAP_Q"]
    for c in cols:
        if c in df.columns:
            df[c] = clean_lod(df[c])
            df[f"upenn_{c}_z"] = zscore_col(df[c])
            
    df["upenn_is_amyloid_pos"] = (df["AB42_AB40_F"] <= 0.063).astype(float)
    df.loc[df["AB42_AB40_F"].isna(), "upenn_is_amyloid_pos"] = np.nan
    
    out_cols = ["PTID", "VISCODE2", "upenn_is_amyloid_pos"] + [c for c in df.columns if c.startswith("upenn_") and c.endswith("_z")]
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_roche_elecsys():
    print("Ingesting Roche Elecsys Biomarkers...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "Roche_Elecsys" / "All_Subjects_UPENNBIOMK_ROCHE_ELECSYS_27Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    cols = ["ABETA42", "ABETA40", "PTAU", "TAU"]
    for c in cols:
        if c in df.columns:
            df[c] = clean_lod(df[c])
            df[f"roche_{c}_z"] = zscore_col(df[c])
            
    out_cols = ["PTID", "VISCODE2"] + [c for c in df.columns if c.startswith("roche_") and c.endswith("_z")]
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_janssen():
    print("Ingesting Janssen Plasma p-tau217...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "Janssen" / "All_Subjects_JANSSEN_PLASMA_P217_TAU_27Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    if "DILUTION_CORRECTED_CONC" in df.columns:
        df["janssen_ptau217"] = clean_lod(df["DILUTION_CORRECTED_CONC"])
        df["janssen_ptau217_z"] = zscore_col(df["janssen_ptau217"])
        return df[["PTID", "VISCODE2", "janssen_ptau217_z"]].drop_duplicates(subset=["PTID", "VISCODE2"])
    return pd.DataFrame()


def load_lilly():
    print("Ingesting Lilly MSD600 Plasma p-tau217...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "Lilly" / "All_Subjects_LILLY_PTAU217_MSD600_27Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    if "ORRES" in df.columns:
        df["lilly_ptau217"] = clean_lod(df["ORRES"])
        df["lilly_ptau217_z"] = zscore_col(df["lilly_ptau217"])
        return df[["PTID", "VISCODE2", "lilly_ptau217_z"]].drop_duplicates(subset=["PTID", "VISCODE2"])
    return pd.DataFrame()


def load_blennow(ptid_map):
    print("Ingesting Blennow Lab Plasma Tau...")
    fpath = DATASET_DIR / "Biofluid Biomarkers" / "Blennow_Lab_Tau" / "BLENNOWPLASMATAU_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    if "RID" in df.columns:
        df["PTID"] = df["RID"].map(ptid_map)
    
    for c in ["PLASMATAU", "PLASMATOTALTAU", "PLASMAPTAU181"]:
        if c in df.columns:
            df[c] = clean_lod(df[c])
            df[f"blennow_{c}_z"] = zscore_col(df[c])
            
    out_cols = ["PTID", "VISCODE2"] + [c for c in df.columns if c.startswith("blennow_") and c.endswith("_z")]
    df = df.dropna(subset=["PTID"])
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def main():
    print("=" * 70)
    print("STEPWISE: BUILDING STAGE 2 MULTIMODAL BIOFLUID & GENOMIC DATASET")
    print("=" * 70)
    
    # 1. Load Clean Stage 1 Feature Matrix
    if not STAGE1_PARQUET.exists():
        raise FileNotFoundError(f"Missing {STAGE1_PARQUET}. Run build_stage1_dataset.py first.")
    
    stage1_df = pd.read_parquet(STAGE1_PARQUET)
    print(f"Stage 1 Records Loaded: {len(stage1_df)} rows across {stage1_df['PTID'].nunique()} patients")
    
    # 2. Ingest all 7 Biofluid Tables
    ptid_map = stage1_df.dropna(subset=["RID", "PTID"]).drop_duplicates("RID").set_index("RID")["PTID"].to_dict()
    c2n_df = load_c2n()
    upenn_df = load_upenn_fujirebio()
    roche_df = load_roche_elecsys()
    janssen_df = load_janssen()
    lilly_df = load_lilly()
    blennow_df = load_blennow(ptid_map)
    
    # 3. Progressive Left Join onto Stage 1 Backbone
    master = stage1_df.copy()
    
    bio_tables = [
        ("C2N", c2n_df),
        ("UPenn_Fujirebio", upenn_df),
        ("Roche", roche_df),
        ("Janssen", janssen_df),
        ("Lilly", lilly_df),
        ("Blennow", blennow_df)
    ]
    
    for label, bdf in bio_tables:
        if not bdf.empty:
            master = pd.merge(master, bdf, on=["PTID", "VISCODE2"], how="left")
            print(f"  + Merged {label:<20}: total rows={len(master)}, matched with data={bdf['PTID'].nunique()} patients")
            
    # 4. Create Cross-Platform Harmonized Composite Biomarkers
    print("\nComputing Cross-Platform Harmonized Biomarker Composites...")
    
    # Composite p-tau217 Z-score (Averaging available standardized assays)
    ptau_cols = [c for c in ["c2n_pT217_npT217_C2N_z", "upenn_pT217_F_z", "janssen_ptau217_z", "lilly_ptau217_z"] if c in master.columns]
    master["composite_ptau217_z"] = master[ptau_cols].mean(axis=1) if ptau_cols else np.nan
    
    # Composite Abeta42/40 Z-score
    abeta_cols = [c for c in ["c2n_AB42_AB40_C2N_z", "upenn_AB42_AB40_F_z", "roche_ABETA42_z"] if c in master.columns]
    master["composite_abeta_ratio_z"] = master[abeta_cols].mean(axis=1) if abeta_cols else np.nan
    
    # GFAP & NfL Z-scores
    master["composite_gfap_z"] = master.get("upenn_GFAP_Q_z", np.nan)
    master["composite_nfl_z"] = master.get("upenn_NfL_Q_z", np.nan)
    
    # Filter to patients who have at least one valid blood biomarker or APOE genotype
    bio_cols = [c for c in master.columns if c.endswith("_z") or c.endswith("_pos")]
    has_bio = master[bio_cols].notna().any(axis=1) | master["APOE4_Count"].notna()
    stage2_clean = master[has_bio].copy().reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("STAGE 2 SUMMARY COHORT STATISTICS")
    print("=" * 70)
    print(f"Total Stage 2 Visits with Biofluid/Genomic Data: {len(stage2_clean)}")
    print(f"Total Unique Patients: {stage2_clean['PTID'].nunique()}")
    print(f"24-Month Progressed Cases (y=1): {(stage2_clean['Progression24m'] == 1).sum()} ({stage2_clean['Progression24m'].mean():.2%})")
    print(f"Stable Cases (y=0):              {(stage2_clean['Progression24m'] == 0).sum()} ({(1 - stage2_clean['Progression24m'].mean()):.2%})")
    print(f"Total Feature Count:             {len(stage2_clean.columns)}")
    
    # Save outputs
    parquet_path = PROCESSED_DIR / "stage2_plasma.parquet"
    csv_path = PROCESSED_DIR / "stage2_plasma.csv"
    stage2_clean.to_parquet(parquet_path, index=False)
    stage2_clean.to_csv(csv_path, index=False)
    
    print(f"\nSuccessfully saved Stage 2 dataset:")
    print(f"  -> {parquet_path}")
    print(f"  -> {csv_path}")

if __name__ == "__main__":
    main()
