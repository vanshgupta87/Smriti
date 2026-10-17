#!/usr/bin/env python3
"""
StepWise: Stage 1 Master Dataset Builder
Ingests raw ADNI core tables and produces the clean Stage 1 multimodal feature matrix
with 24-month longitudinal progression ground truth.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
STAGE1_RAW_DIR = BASE_DIR / "Step_Wise-PCC" / "Stage_1_data"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

PROGRESSION_MONTHS = 24


def clean_keys(df):
    """Standardizes PTID, RID, VISCODE, VISCODE2, VISDATE."""
    df = df.copy()
    if "PTID" in df.columns:
        df["PTID"] = df["PTID"].astype(str).str.strip()
    if "RID" in df.columns:
        df["RID"] = pd.to_numeric(df["RID"], errors="coerce").fillna(-1).astype(int)
    if "VISCODE" in df.columns:
        df["VISCODE"] = df["VISCODE"].astype(str).str.strip().str.lower()
    if "VISCODE2" in df.columns:
        df["VISCODE2"] = df["VISCODE2"].astype(str).str.strip().str.lower()
    else:
        df["VISCODE2"] = df.get("VISCODE", "")
    
    date_cols = [c for c in ["VISDATE", "EXAMDATE", "USERDATE"] if c in df.columns]
    if date_cols:
        df["VISDATE"] = pd.to_datetime(df[date_cols[0]], errors="coerce")
    
    return df


def load_demographics():
    print("Loading Demographics...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "DEMOGRAPHY" / "PTDEMOG_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    # Extract baseline age, gender, education
    df["PTGENDER"] = df["PTGENDER"].map({1: 0, 2: 1, "1": 0, "2": 1})  # 0=Male, 1=Female
    df["PTEDUCAT"] = pd.to_numeric(df["PTEDUCAT"], errors="coerce")
    df["PTMARRY"] = pd.to_numeric(df["PTMARRY"], errors="coerce")
    
    # Calculate Age
    df["PTDOBYY"] = pd.to_numeric(df["PTDOBYY"], errors="coerce")
    if "VISDATE" in df.columns:
        df["AGE"] = df["VISDATE"].dt.year - df["PTDOBYY"]
    else:
        df["AGE"] = np.nan
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "PTGENDER", "PTEDUCAT", "PTMARRY", "AGE"]
    cols = [c for c in cols if c in df.columns]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_mmse():
    print("Loading MMSE...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "MMSE" / "MMSE_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    # MMSCORE
    df["MMSCORE"] = pd.to_numeric(df["MMSCORE"], errors="coerce")
    
    # Subdomain grouping (orientation, registration, attention, recall, language)
    orient_cols = [c for c in ["MMDATE", "MMYEAR", "MMMONTH", "MMDAY", "MMSEASON", "MMHOSPIT", "MMFLOOR", "MMCITY", "MMAREA", "MMSTATE"] if c in df.columns]
    for c in orient_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["MMSE_Orientation"] = df[orient_cols].sum(axis=1) if orient_cols else np.nan
    
    recall_cols = [c for c in ["WORD1DL", "WORD2DL", "WORD3DL"] if c in df.columns]
    for c in recall_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["MMSE_Recall"] = df[recall_cols].sum(axis=1) if recall_cols else np.nan
    
    df["MMSE_Attention"] = pd.to_numeric(df.get("WORLDSCORE", 0), errors="coerce").fillna(0)
    
    lang_cols = [c for c in ["MMWATCH", "MMPENCIL", "MMREPEAT", "MMHAND", "MMFOLD", "MMONFLR", "MMREAD", "MMWRITE", "MMDRAW"] if c in df.columns]
    for c in lang_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["MMSE_Language"] = df[lang_cols].sum(axis=1) if lang_cols else np.nan
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "MMSCORE", "MMSE_Orientation", "MMSE_Recall", "MMSE_Attention", "MMSE_Language"]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_moca():
    print("Loading MoCA...")
    fpath = STAGE1_RAW_DIR / "All_Subjects_MOCA_26Sep2026.csv"
    if not fpath.exists():
        return None
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    numeric_moca = ["TRAILS", "CUBE", "CLOCKCON", "CLOCKNO", "CLOCKHAN", "LION", "RHINO", "CAMEL", 
                    "DIGFOR", "DIGBAC", "LETTERS", "SERIAL1", "SERIAL2", "SERIAL3", "SERIAL4", "SERIAL5",
                    "REPEAT1", "REPEAT2", "FFLUENCY", "ABSTR1", "ABSTR2", "DELW1", "DELW2", "DELW3", 
                    "DELW4", "DELW5", "DATE", "MONTH", "YEAR", "DAY", "PLACE", "CITY", "MOCA"]
    for c in numeric_moca:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    
    visuo = [c for c in ["TRAILS", "CUBE", "CLOCKCON", "CLOCKNO", "CLOCKHAN"] if c in df.columns]
    df["MoCA_Visuospatial"] = df[visuo].sum(axis=1) if visuo else np.nan
    
    naming = [c for c in ["LION", "RHINO", "CAMEL"] if c in df.columns]
    df["MoCA_Naming"] = df[naming].sum(axis=1) if naming else np.nan
    
    atten = [c for c in ["DIGFOR", "DIGBAC", "LETTERS", "SERIAL1", "SERIAL2", "SERIAL3", "SERIAL4", "SERIAL5"] if c in df.columns]
    df["MoCA_Attention"] = df[atten].sum(axis=1) if atten else np.nan
    
    recall = [c for c in ["DELW1", "DELW2", "DELW3", "DELW4", "DELW5"] if c in df.columns]
    df["MoCA_Delayed_Recall"] = df[recall].sum(axis=1) if recall else np.nan
    
    orient = [c for c in ["DATE", "MONTH", "YEAR", "DAY", "PLACE", "CITY"] if c in df.columns]
    df["MoCA_Orientation"] = df[orient].sum(axis=1) if orient else np.nan
    
    df["MOCA_Total"] = pd.to_numeric(df.get("MOCA", np.nan), errors="coerce")
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "MOCA_Total", "MoCA_Visuospatial", "MoCA_Naming", "MoCA_Attention", "MoCA_Delayed_Recall", "MoCA_Orientation"]
    return df[[c for c in cols if c in df.columns]].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_cdr():
    print("Loading CDR-SB...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "CDR_SB" / "CDR_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    cdr_cols = ["CDRSB", "CDGLOBAL", "CDMEMORY", "CDORIENT", "CDJUDGE", "CDCOMMUN", "CDHOME", "CDCARE"]
    for c in cdr_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE"] + [c for c in cdr_cols if c in df.columns]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_faq():
    print("Loading FAQ...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "FAQ" / "FAQ_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    faq_cols = ["FAQTOTAL", "FAQFINAN", "FAQFORM", "FAQSHOP", "FAQGAME", "FAQBEVG", "FAQMEAL", "FAQEVENT", "FAQTV", "FAQREM", "FAQTRAVL"]
    for c in faq_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE"] + [c for c in faq_cols if c in df.columns]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_npiq():
    print("Loading NPI-Q...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "NPI_Q" / "NPIQ_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    npi_cols = ["NPIA", "NPIB", "NPIC", "NPID", "NPIE", "NPIF", "NPIG", "NPIH", "NPII", "NPIJ", "NPIK", "NPIL"]
    for c in npi_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["NPIQ_Total_Severity"] = df[npi_cols].sum(axis=1) if npi_cols else np.nan
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "NPIQ_Total_Severity"] + [c for c in ["NPID", "NPIE", "NPIC"] if c in df.columns]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_vitals():
    print("Loading Vitals...")
    fpath = DATASET_DIR / "Medical HIstory" / "VITAL_SIGNS" / "VITALS_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    df["VSBPSYS"] = pd.to_numeric(df.get("VSBPSYS", np.nan), errors="coerce")
    df["VSBPDIA"] = pd.to_numeric(df.get("VSBPDIA", np.nan), errors="coerce")
    df["VSPULSE"] = pd.to_numeric(df.get("VSPULSE", np.nan), errors="coerce")
    df["Pulse_Pressure"] = df["VSBPSYS"] - df["VSBPDIA"]
    
    # BMI calculation
    wt = pd.to_numeric(df.get("VSWEIGHT", np.nan), errors="coerce")
    ht = pd.to_numeric(df.get("VSHEIGHT", np.nan), errors="coerce")
    wt_unit = df.get("VSWTUNIT", 2)  # 1=kg, 2=lbs
    ht_unit = df.get("VSHTUNIT", 2)  # 1=cm, 2=inches
    
    # Convert to kg and meters
    wt_kg = np.where(wt_unit == 2, wt * 0.453592, wt)
    ht_m = np.where(ht_unit == 2, ht * 0.0254, ht / 100.0)
    df["BMI"] = np.where((ht_m > 0.5) & (wt_kg > 20), wt_kg / (ht_m ** 2), np.nan)
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "VSBPSYS", "VSBPDIA", "Pulse_Pressure", "VSPULSE", "BMI"]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_medhist():
    print("Loading Medical History...")
    fpath = DATASET_DIR / "Medical HIstory" / "Medical History [ADNI1,GO,2]" / "MEDHIST_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    # Clinical flags
    df["MHPSYCH"] = pd.to_numeric(df.get("MHPSYCH", 0), errors="coerce").fillna(0)
    df["MH2NEURL"] = pd.to_numeric(df.get("MH2NEURL", 0), errors="coerce").fillna(0)
    df["MH4CARD"] = pd.to_numeric(df.get("MH4CARD", 0), errors="coerce").fillna(0)  # Cardiac/HTN
    df["MH9ENDO"] = pd.to_numeric(df.get("MH9ENDO", 0), errors="coerce").fillna(0)  # Diabetes/Endocrine
    df["MH14ALCH"] = pd.to_numeric(df.get("MH14ALCH", 0), errors="coerce").fillna(0)
    
    df["AD_Medical_Risk_Score"] = df["MHPSYCH"] + df["MH2NEURL"] + df["MH4CARD"]*1.5 + df["MH9ENDO"]*1.5
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "MHPSYCH", "MH2NEURL", "MH4CARD", "MH9ENDO", "MH14ALCH", "AD_Medical_Risk_Score"]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def load_apoe():
    print("Loading APOE Genotyping...")
    fpath = DATASET_DIR / "Genome" / "ApoE Genotyping Results" / "APOERES_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    # Parse genotype (e.g. '3/3' -> 0, '3/4' -> 1, '4/4' -> 2)
    def parse_apoe4(geno):
        if pd.isna(geno):
            return np.nan
        s = str(geno)
        c = s.count("4")
        return c
    
    df["APOE4_Count"] = df["GENOTYPE"].apply(parse_apoe4)
    cols = ["PTID", "RID", "APOE4_Count"]
    return df[cols].drop_duplicates(subset=["PTID"])


def load_dxsum():
    print("Loading Ground Truth DXSUM...")
    fpath = DATASET_DIR / "Clinical Assessments & Questionnaires" / "DXSUM" / "DXSUM_26Sep2026.csv"
    df = pd.read_csv(fpath, low_memory=False)
    df = clean_keys(df)
    
    df["DIAGNOSIS"] = pd.to_numeric(df["DIAGNOSIS"], errors="coerce")
    df = df[df["DIAGNOSIS"].isin([1, 2, 3])].copy()
    
    cols = ["PTID", "RID", "VISCODE2", "VISDATE", "DIAGNOSIS"]
    return df[cols].drop_duplicates(subset=["PTID", "VISCODE2"])


def build_progression_target(df):
    """
    Computes 24-month progression target:
    1 = converted to worse diagnosis within 24 months
    0 = followed >= 24 months and remained stable
    np.nan = not enough follow-up and did not convert
    """
    print("Computing 24-Month Progression Target...")
    df = df.sort_values(["PTID", "VISDATE"]).reset_index(drop=True)
    target = np.full(len(df), np.nan)
    future_visits = np.zeros(len(df), dtype=int)
    
    for ptid, group in df.groupby("PTID", sort=False):
        idx = group.index.to_numpy()
        dates = pd.to_datetime(group["VISDATE"]).values
        dx = group["DIAGNOSIS"].to_numpy(dtype=float)
        
        for i in range(len(idx)):
            current_dx = dx[i]
            if current_dx >= 3:  # Already dementia
                continue
            
            curr_date = pd.Timestamp(dates[i])
            if pd.isna(curr_date):
                continue
                
            cutoff = curr_date + pd.DateOffset(months=PROGRESSION_MONTHS)
            cutoff_dt64 = np.datetime64(cutoff.to_pydatetime())
            
            # Future visits within 24 months
            mask = (dates > dates[i]) & (dates <= cutoff_dt64)
            future_dx = dx[mask]
            
            if len(future_dx) == 0:
                continue
            
            future_visits[idx[i]] = len(future_dx)
            # Progression = any future diagnosis higher than baseline
            target[idx[i]] = int(np.nanmax(future_dx) > current_dx)
            
    df["Progression24m"] = target
    df["FutureVisitsWithin24m"] = future_visits
    return df


def main():
    print("=" * 70)
    print("STEPWISE: BUILDING STAGE 1 COMPREHENSIVE SCREENING DATASET")
    print("=" * 70)
    
    # 1. Load Ground Truth First
    dx_df = load_dxsum()
    print(f"DXSUM records: {len(dx_df)} across {dx_df['PTID'].nunique()} patients")
    
    # 2. Load Assessment Modalities
    demog = load_demographics()
    mmse = load_mmse()
    moca = load_moca()
    cdr = load_cdr()
    faq = load_faq()
    npiq = load_npiq()
    vitals = load_vitals()
    medhist = load_medhist()
    apoe = load_apoe()
    
    # 3. Master Longitudinal Merge on ['PTID', 'VISCODE2']
    master = dx_df.copy()
    
    for name, tbl in [("Demog", demog), ("MMSE", mmse), ("MoCA", moca), 
                      ("CDR", cdr), ("FAQ", faq), ("NPIQ", npiq), 
                      ("Vitals", vitals), ("MedHist", medhist)]:
        if tbl is None:
            continue
        # Drop overlapping non-key columns
        drop_cols = [c for c in ["RID", "VISDATE"] if c in tbl.columns and c in master.columns]
        tbl_clean = tbl.drop(columns=drop_cols)
        master = pd.merge(master, tbl_clean, on=["PTID", "VISCODE2"], how="left")
    
    # Merge APOE by PTID only (time-invariant)
    if apoe is not None:
        apoe_clean = apoe.drop(columns=[c for c in ["RID"] if c in apoe.columns])
        master = pd.merge(master, apoe_clean, on="PTID", how="left")
    
    print(f"\nMaster merged shape before target generation: {master.shape}")
    
    # 4. Build 24-Month Progression Target
    master = build_progression_target(master)
    
    # Filter to eligible training rows (where 24-month progression status is determinable)
    trainable = master[master["Progression24m"].notna()].copy()
    trainable["Progression24m"] = trainable["Progression24m"].astype(int)
    
    print("\n" + "=" * 70)
    print("STAGE 1 SUMMARY COHORT STATISTICS")
    print("=" * 70)
    print(f"Total Eligible Visits: {len(trainable)}")
    print(f"Total Unique Patients: {trainable['PTID'].nunique()}")
    print(f"Progressed Cases (y=1): {(trainable['Progression24m'] == 1).sum()} ({trainable['Progression24m'].mean():.2%})")
    print(f"Stable Cases (y=0):     {(trainable['Progression24m'] == 0).sum()} ({(1 - trainable['Progression24m'].mean()):.2%})")
    print(f"Feature Count:          {len(trainable.columns)}")
    
    # Save processed outputs
    parquet_path = PROCESSED_DIR / "stage1_screening.parquet"
    csv_path = PROCESSED_DIR / "stage1_screening.csv"
    trainable.to_parquet(parquet_path, index=False)
    trainable.to_csv(csv_path, index=False)
    
    print(f"\nSuccessfully saved:")
    print(f"  -> {parquet_path}")
    print(f"  -> {csv_path}")

if __name__ == "__main__":
    main()
