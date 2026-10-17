#!/usr/bin/env python3
"""
StepWise: Stage 4 Master Molecular PET & DMT/ARIA Safety Dataset Builder
Merges Stage 3 multimodal features (Cognitive, 7 Biofluid Assays, APOE4, MRI Volumetrics, WMH)
with UC Berkeley Amyloid PET Centiloids and Tau PET SUVR.
Computes DMT Eligibility criteria and ARIA-E/H clinical safety indices.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
STAGE3_PARQUET = PROCESSED_DIR / "stage3_mri.parquet"


def clean_keys(df):
    df = df.copy()
    if "PTID" in df.columns:
        df["PTID"] = df["PTID"].astype(str).str.strip()
    if "VISCODE2" in df.columns:
        df["VISCODE2"] = df["VISCODE2"].astype(str).str.strip().str.lower()
    elif "VISCODE" in df.columns:
        df["VISCODE2"] = df["VISCODE"].astype(str).str.strip().str.lower()
    return df


def load_amyloid_pet():
    print("Ingesting UC Berkeley Amyloid PET (Centiloids & Regional SUVR)...")
    fpath = DATASET_DIR / "Molecular Tracking & Centiloids" / "Amyloid PET 6mm" / "UCBERKELEY_AMY_6MM_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    num_cols = ["CENTILOIDS", "SUMMARY_SUVR", "CTX_PRECUNEUS_SUVR", "CTX_POSTERIORCINGULATE_SUVR", 
                "CTX_FRONTALPOLE_SUVR", "CTX_LATERALOCCIPITAL_SUVR", "AMYLOID_STATUS"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df["Amyloid_Centiloids"] = df["CENTILOIDS"]
    df["Amyloid_Summary_SUVR"] = df["SUMMARY_SUVR"]
    df["Amyloid_Positive"] = np.where(df["CENTILOIDS"] >= 20.0, 1.0, np.where(df["AMYLOID_STATUS"] == 1, 1.0, np.where(df["CENTILOIDS"].notna(), 0.0, np.nan)))
    df["Amyloid_Prefrontal_SUVR"] = df["CTX_FRONTALPOLE_SUVR"]
    df["Amyloid_Parietal_SUVR"] = (df["CTX_PRECUNEUS_SUVR"] + df["CTX_POSTERIORCINGULATE_SUVR"]) / 2.0
    
    out_cols = ["PTID", "VISCODE2", "Amyloid_Centiloids", "Amyloid_Summary_SUVR", "Amyloid_Positive", "Amyloid_Prefrontal_SUVR", "Amyloid_Parietal_SUVR"]
    df = df.dropna(subset=["PTID"])
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_tau_pet():
    print("Ingesting UC Berkeley Tau PET (PVC Braak SUVR)...")
    fpath = DATASET_DIR / "Molecular Tracking & Centiloids" / "Tau PET PVC 6mm " / "UCBERKELEY_TAUPVC_6MM_26Sep2026.csv"
    if not fpath.exists():
        fpath = DATASET_DIR / "Molecular Tracking & Centiloids" / "Tau PET 6mm" / "UCBERKELEY_TAU_6MM_26Sep2026.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    num_cols = ["META_TEMPORAL_SUVR", "CTX_ENTORHINAL_SUVR", "HIPPOCAMPUS_SUVR", "CTX_INFERIORTEMPORAL_SUVR"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df["Tau_MetaTemporal_SUVR"] = df["META_TEMPORAL_SUVR"]
    df["Tau_Entorhinal_SUVR"] = df["CTX_ENTORHINAL_SUVR"]
    df["Tau_Hippocampus_SUVR"] = df["HIPPOCAMPUS_SUVR"]
    df["Tau_InferiorTemporal_SUVR"] = df["CTX_INFERIORTEMPORAL_SUVR"]
    df["Tau_Braak_High"] = np.where(df["META_TEMPORAL_SUVR"] >= 1.30, 1.0, np.where(df["META_TEMPORAL_SUVR"].notna(), 0.0, np.nan))
    
    out_cols = ["PTID", "VISCODE2", "Tau_MetaTemporal_SUVR", "Tau_Entorhinal_SUVR", "Tau_Hippocampus_SUVR", "Tau_InferiorTemporal_SUVR", "Tau_Braak_High"]
    df = df.dropna(subset=["PTID"])
    return df[out_cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def main():
    print("=" * 70)
    print("STEPWISE: BUILDING STAGE 4 MOLECULAR PET & DMT READINESS DATASET")
    print("=" * 70)
    
    if not STAGE3_PARQUET.exists():
        raise FileNotFoundError(f"Missing {STAGE3_PARQUET}. Run build_stage3_dataset.py first.")
        
    stage3_df = pd.read_parquet(STAGE3_PARQUET)
    print(f"Stage 3 Records Loaded: {len(stage3_df)} rows across {stage3_df['PTID'].nunique()} patients")
    
    amy_df = load_amyloid_pet()
    tau_df = load_tau_pet()
    
    master = stage3_df.copy()
    if not amy_df.empty:
        master = pd.merge(master, amy_df, on=["PTID", "VISCODE2"], how="left")
        print(f"  + Merged Amyloid PET: {amy_df['PTID'].nunique()} patients matched")
    if not tau_df.empty:
        master = pd.merge(master, tau_df, on=["PTID", "VISCODE2"], how="left")
        print(f"  + Merged Tau PET:     {tau_df['PTID'].nunique()} patients matched")
        
    # ARIA Safety & DMT Eligibility Indices
    # ARIA-E Risk Index (0 - 100): Weighted by APOE4 homozygosity (45%), baseline WMH vascular disease (35%), Amyloid Centiloid burden (20%)
    apoe4_pts = master["APOE4_Count"].fillna(0)
    apoe_risk = np.where(apoe4_pts >= 2, 45.0, np.where(apoe4_pts == 1, 20.0, 5.0))
    
    wmh_val = master["wmh_volume_cm3"].fillna(master["wmh_volume_cm3"].median() if master["wmh_volume_cm3"].notna().any() else 5.0)
    wmh_risk = np.clip((wmh_val / 25.0) * 35.0, 0, 35.0)
    
    centiloids_val = master["Amyloid_Centiloids"].fillna(master["Amyloid_Centiloids"].median() if master["Amyloid_Centiloids"].notna().any() else 25.0)
    centiloid_risk = np.clip((centiloids_val / 100.0) * 20.0, 0, 20.0)
    
    master["ARIA_E_Risk_Score"] = np.round(apoe_risk + wmh_risk + centiloid_risk, 2)
    
    # DMT Candidate Indicator (1 = Confirmed Amyloid+, Mild/Prodromal AD, Tolerable Safety)
    is_amyloid_pos = (master["Amyloid_Centiloids"] >= 20.0) | (master["Amyloid_Positive"] == 1.0)
    cdr_val = master["CDRSB"].fillna(1.0) if "CDRSB" in master.columns else pd.Series(1.0, index=master.index)
    mild_stage = (cdr_val <= 6.0) & (master["MMSCORE"].fillna(26.0) >= 20.0)
    master["DMT_Eligibility_Flag"] = np.where(is_amyloid_pos & mild_stage, 1.0, 0.0)
    
    # Filter dataset
    pet_cols = ["Amyloid_Centiloids", "Amyloid_Summary_SUVR", "Tau_MetaTemporal_SUVR"]
    has_pet_or_prior = master[pet_cols].notna().any(axis=1) | master["hippocampus_icv_ratio"].notna() | master["APOE4_Count"].notna()
    stage4_clean = master[has_pet_or_prior].copy().reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("STAGE 4 SUMMARY COHORT STATISTICS")
    print("=" * 70)
    print(f"Total Stage 4 Records: {len(stage4_clean)}")
    print(f"Total Unique Patients: {stage4_clean['PTID'].nunique()}")
    print(f"24-Month Progressed Cases (y=1): {(stage4_clean['Progression24m'] == 1).sum()} ({stage4_clean['Progression24m'].mean():.2%})")
    print(f"Amyloid Centiloid Measurements:  {stage4_clean['Amyloid_Centiloids'].notna().sum()}")
    print(f"Tau PET SUVR Measurements:       {stage4_clean['Tau_MetaTemporal_SUVR'].notna().sum()}")
    print(f"DMT Eligible Candidates:         {(stage4_clean['DMT_Eligibility_Flag'] == 1).sum()} ({(stage4_clean['DMT_Eligibility_Flag'] == 1).mean():.2%})")
    print(f"Total Feature Count:             {len(stage4_clean.columns)}")
    
    parquet_path = PROCESSED_DIR / "stage4_pet.parquet"
    csv_path = PROCESSED_DIR / "stage4_pet.csv"
    stage4_clean.to_parquet(parquet_path, index=False)
    stage4_clean.to_csv(csv_path, index=False)
    
    print(f"\nSuccessfully saved Stage 4 dataset:")
    print(f"  -> {parquet_path}")
    print(f"  -> {csv_path}")


if __name__ == "__main__":
    main()
