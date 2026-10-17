#!/usr/bin/env python3
"""
StepWise: Stage 3 Master Volumetric MRI Dataset Builder
Merges Stage 2 multimodal features with UCSD structural brain volumetry,
FreeSurfer 7 cortical thickness, and UC Davis White Matter Hyperintensities (WMH).
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
STAGE2_PARQUET = PROCESSED_DIR / "stage2_plasma.parquet"


def clean_keys(df):
    df = df.copy()
    if "PTID" in df.columns:
        df["PTID"] = df["PTID"].astype(str).str.strip()
    if "VISCODE2" in df.columns:
        df["VISCODE2"] = df["VISCODE2"].astype(str).str.strip().str.lower()
    elif "VISCODE" in df.columns:
        df["VISCODE2"] = df["VISCODE"].astype(str).str.strip().str.lower()
    return df


def load_ucsd_vol(ptid_map):
    print("Ingesting UCSD MRI Derived Volumes...")
    fpath = DATASET_DIR / "Structural MRI Atrophy" / "(UCSD) - Derived Volumes" / "UCSDVOL_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    if "RID" in df.columns and "PTID" not in df.columns:
        df["PTID"] = df["RID"].map(ptid_map)
        
    num_cols = ["BRAIN", "EICV", "VENTRICLES", "LHIPPOC", "RHIPPOC", "LMIDTEMP", "RMIDTEMP", "LENTORHIN", "RENTORHIN"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    # Derived Volumetric Ratios
    eicv = df["EICV"]
    df["hippocampus_total_vol"] = df["LHIPPOC"] + df["RHIPPOC"]
    df["hippocampus_icv_ratio"] = np.where(eicv > 0, (df["hippocampus_total_vol"] / eicv) * 1000.0, np.nan)
    df["ventricles_icv_ratio"] = np.where(eicv > 0, df["VENTRICLES"] / eicv, np.nan)
    df["wholebrain_icv_ratio"] = np.where(eicv > 0, df["BRAIN"] / eicv, np.nan)
    df["entorhinal_avg_vol"] = (df["LENTORHIN"] + df["RENTORHIN"]) / 2.0
    df["midtemp_avg_vol"] = (df["LMIDTEMP"] + df["RMIDTEMP"]) / 2.0
    
    out_cols = ["PTID", "VISCODE2", "hippocampus_total_vol", "hippocampus_icv_ratio", 
                "ventricles_icv_ratio", "wholebrain_icv_ratio", "entorhinal_avg_vol", "midtemp_avg_vol"]
    df = df.dropna(subset=["PTID"])
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_wmh():
    print("Ingesting UC Davis White Matter Hyperintensities (WMH)...")
    fpath = DATASET_DIR / "Structural MRI Atrophy" / "White Matter Hyperintensity" / "UCD_WMH_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    for c in ["TOTAL_WMH", "TOTAL_HIPPO", "TOTAL_CSF", "TOTAL_WHITE", "CEREBRUM_TCV"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df["wmh_volume_cm3"] = df["TOTAL_WMH"]
    df["wmh_tcv_ratio"] = np.where(df["CEREBRUM_TCV"] > 0, df["TOTAL_WMH"] / df["CEREBRUM_TCV"], np.nan)
    
    out_cols = ["PTID", "VISCODE2", "wmh_volume_cm3", "wmh_tcv_ratio"]
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def main():
    print("=" * 70)
    print("STEPWISE: BUILDING STAGE 3 VOLUMETRIC MRI DATASET")
    print("=" * 70)
    
    if not STAGE2_PARQUET.exists():
        raise FileNotFoundError(f"Missing {STAGE2_PARQUET}. Run build_stage2_dataset.py first.")
        
    stage2_df = pd.read_parquet(STAGE2_PARQUET)
    print(f"Stage 2 Records Loaded: {len(stage2_df)} rows across {stage2_df['PTID'].nunique()} patients")
    
    ptid_map = stage2_df.dropna(subset=["RID", "PTID"]).drop_duplicates("RID").set_index("RID")["PTID"].to_dict()
    
    ucsd_df = load_ucsd_vol(ptid_map)
    wmh_df = load_wmh()
    
    master = stage2_df.copy()
    if not ucsd_df.empty:
        master = pd.merge(master, ucsd_df, on=["PTID", "VISCODE2"], how="left")
        print(f"  + Merged UCSD Volumetry: {ucsd_df['PTID'].nunique()} patients matched")
    if not wmh_df.empty:
        master = pd.merge(master, wmh_df, on=["PTID", "VISCODE2"], how="left")
        print(f"  + Merged WMH Vascular Data: {wmh_df['PTID'].nunique()} patients matched")
        
    # Filter to patients with structural imaging features
    mri_cols = ["hippocampus_icv_ratio", "ventricles_icv_ratio", "wmh_volume_cm3"]
    has_mri = master[mri_cols].notna().any(axis=1) | master["APOE4_Count"].notna()
    stage3_clean = master[has_mri].copy().reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("STAGE 3 SUMMARY COHORT STATISTICS")
    print("=" * 70)
    print(f"Total Stage 3 Records: {len(stage3_clean)}")
    print(f"Total Unique Patients: {stage3_clean['PTID'].nunique()}")
    print(f"24-Month Progressed Cases (y=1): {(stage3_clean['Progression24m'] == 1).sum()} ({stage3_clean['Progression24m'].mean():.2%})")
    print(f"Total Feature Count:             {len(stage3_clean.columns)}")
    
    parquet_path = PROCESSED_DIR / "stage3_mri.parquet"
    csv_path = PROCESSED_DIR / "stage3_mri.csv"
    stage3_clean.to_parquet(parquet_path, index=False)
    stage3_clean.to_csv(csv_path, index=False)
    
    print(f"\nSuccessfully saved Stage 3 dataset:")
    print(f"  -> {parquet_path}")
    print(f"  -> {csv_path}")

if __name__ == "__main__":
    main()
