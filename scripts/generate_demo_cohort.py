#!/usr/bin/env python3
"""
StepWise: High-Fidelity Demo Patient & Spotlight Cohort Generator
Generates realistic patient dossiers with longitudinal visits, raw biomarkers,
SHAP risk drivers, and CDS recommendations for the clinician command center.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
BACKEND_DATA = BASE_DIR / "backend" / "data"
BACKEND_DATA.mkdir(parents=True, exist_ok=True)


def generate_cohort():
    print("Generating StepWise Clinician Command Center Demo Cohort...")
    
    # Load Stage 4 dataset to get full multimodal records
    df = pd.read_parquet(PROCESSED_DIR / "stage4_pet.parquet")
    
    # Select diverse patients
    # We want ~40 patients with rich records
    patients = []
    
    # Group by PTID
    pt_groups = df.groupby("PTID")
    
    first_names_m = ["David", "Robert", "James", "William", "Joseph", "Richard", "Thomas", "Charles", "Daniel", "Matthew", "Rajesh", "Suresh", "Amit", "Vikram", "Anil"]
    first_names_f = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Priya", "Sunita", "Ananya", "Deepa", "Kavita"]
    last_names = ["Miller", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Davis", "Sharma", "Verma", "Patel", "Rao", "Nair", "Iyer", "Gupta"]
    
    np.random.seed(42)
    
    sample_ptids = list(pt_groups.groups.keys())[:45]
    
    for i, ptid in enumerate(sample_ptids):
        pt_records = pt_groups.get_group(ptid).sort_values("VISDATE")
        latest = pt_records.iloc[-1]
        
        is_female = (latest.get("PTGENDER", 1) == 2)
        fname = np.random.choice(first_names_f if is_female else first_names_m)
        lname = np.random.choice(last_names)
        
        age = int(latest.get("AGE", 72) if pd.notna(latest.get("AGE")) else 72)
        gender = "Female" if is_female else "Male"
        mmse = float(latest.get("MMSCORE", 26)) if pd.notna(latest.get("MMSCORE")) else 26.0
        moca = float(latest.get("MOCA_Total", 24)) if pd.notna(latest.get("MOCA_Total")) else 24.0
        cdrsb = float(latest.get("CDRSB", 1.0)) if pd.notna(latest.get("CDRSB")) else 1.0
        apoe = int(latest.get("APOE4_Count", 1)) if pd.notna(latest.get("APOE4_Count")) else 1
        
        ptau = float(latest.get("plasma_ptau217_fuji", 0.35)) if pd.notna(latest.get("plasma_ptau217_fuji")) else 0.32
        ab_ratio = float(latest.get("plasma_ab42_ab40_c2n", 0.088)) if pd.notna(latest.get("plasma_ab42_ab40_c2n")) else 0.091
        hippo_icv = float(latest.get("hippocampus_icv_ratio", 4.1)) if pd.notna(latest.get("hippocampus_icv_ratio")) else 4.2
        wmh_vol = float(latest.get("wmh_volume_cm3", 6.5)) if pd.notna(latest.get("wmh_volume_cm3")) else 5.2
        centiloids = float(latest.get("Amyloid_Centiloids", 34.0)) if pd.notna(latest.get("Amyloid_Centiloids")) else 30.0
        tau_suvr = float(latest.get("Tau_MetaTemporal_SUVR", 1.25)) if pd.notna(latest.get("Tau_MetaTemporal_SUVR")) else 1.15
        
        prog24 = int(latest.get("Progression24m", 0))
        
        # Risk score synthesis
        base_risk = 0.15
        if mmse < 26: base_risk += 0.25
        if ptau > 0.40: base_risk += 0.25
        if hippo_icv < 4.0: base_risk += 0.15
        if centiloids > 30: base_risk += 0.15
        if apoe == 2: base_risk += 0.15
        
        risk_score = round(min(0.96, max(0.04, base_risk + np.random.uniform(-0.05, 0.05))), 3)
        velocity = "High Velocity" if risk_score > 0.65 else ("Moderate" if risk_score > 0.35 else "Stable")
        
        # Current Stage
        if centiloids > 20 and pd.notna(latest.get("Amyloid_Centiloids")):
            current_stage = 4
            stage_name = "Stage 4: Molecular PET & DMT Readiness"
            status = "DMT Evaluation Pending"
        elif hippo_icv > 0 and pd.notna(latest.get("hippocampus_icv_ratio")):
            current_stage = 3
            stage_name = "Stage 3: Volumetric MRI"
            status = "Escalation Recommended" if risk_score > 0.4 else "MRI Negative"
        elif ptau > 0 and pd.notna(latest.get("plasma_ptau217_fuji")):
            current_stage = 2
            stage_name = "Stage 2: Plasma Biomarkers"
            status = "Phlebotomy Completed"
        else:
            current_stage = 1
            stage_name = "Stage 1: Primary Care Cognitive"
            status = "Intake Screening"
            
        aria_score = int(latest.get("ARIA_E_Risk_Score", 25)) if pd.notna(latest.get("ARIA_E_Risk_Score")) else (65 if apoe == 2 else 20)
        
        dossier = {
            "id": ptid,
            "name": f"{fname} {lname}",
            "age": age,
            "gender": gender,
            "mrn": f"GE-HC-{1000 + i}",
            "lastVisit": str(latest.get("VISDATE", "2026-03-15"))[:10],
            "riskScore": risk_score,
            "velocity": velocity,
            "currentStage": current_stage,
            "stageName": stage_name,
            "status": status,
            "progression24m": prog24,
            "cognitive": {
                "mmse": round(mmse, 1),
                "moca": round(moca, 1),
                "cdrsb": round(cdrsb, 1),
                "faq": float(latest.get("FAQTOTAL", 3.0) if pd.notna(latest.get("FAQTOTAL")) else 2.0)
            },
            "biomarkers": {
                "apoe4": apoe,
                "plasmaPtau217": round(ptau, 3),
                "plasmaAbRatio": round(ab_ratio, 4),
                "nfl": round(float(latest.get("plasma_nfl_fnih", 18.5) if pd.notna(latest.get("plasma_nfl_fnih")) else 16.0), 1),
                "gfap": round(float(latest.get("plasma_gfap_fnih", 145.0) if pd.notna(latest.get("plasma_gfap_fnih")) else 130.0), 1)
            },
            "mri": {
                "hippocampalIcvRatio": round(hippo_icv, 2),
                "ventriclesIcvRatio": round(float(latest.get("ventricles_icv_ratio", 0.028) if pd.notna(latest.get("ventricles_icv_ratio")) else 0.025), 4),
                "wmhVolumeCm3": round(wmh_vol, 2)
            },
            "pet": {
                "centiloids": round(centiloids, 1),
                "amyloidPositive": bool(centiloids >= 20.0),
                "tauSuvr": round(tau_suvr, 2),
                "ariaRiskScore": aria_score,
                "dmtCandidate": bool(centiloids >= 20.0 and cdrsb <= 6.0 and aria_score < 70)
            },
            "shapDrivers": [
                {"feature": "Plasma p-tau217 Elevated", "impact": round(0.28 * (risk_score / 0.8), 3), "type": "risk" if risk_score > 0.4 else "protective"},
                {"feature": "Hippocampal Volume Loss", "impact": round(0.21 * (risk_score / 0.8), 3), "type": "risk" if risk_score > 0.4 else "protective"},
                {"feature": "APOE-ε4 Carrier (Allele: " + str(apoe) + ")", "impact": round(0.18 * (risk_score / 0.8), 3), "type": "risk" if apoe > 0 else "protective"},
                {"feature": "Delayed Recall Sub-score", "impact": round(0.14 * (risk_score / 0.8), 3), "type": "risk" if mmse < 26 else "protective"},
                {"feature": "Vascular White Matter Load", "impact": round(0.09 * (risk_score / 0.8), 3), "type": "risk" if wmh_vol > 10 else "protective"}
            ],
            "cdsRecommendation": (
                f"High rapid progression probability ({risk_score:.0%}). Stage {current_stage} complete. "
                + ("Recommend immediate Leqembi/Donanemab DMT evaluation with routine MRI ARIA monitoring." if current_stage == 4 and centiloids >= 20 
                   else ("Recommend Escalation to Amyloid PET scan (Centiloids)." if current_stage == 3 
                   else ("Order 3D Volumetric MRI (Hippocampal/Ventricle index)." if current_stage == 2 
                   else "Order Plasma p-tau217 Biomarker Panel.")))
            )
        }
        patients.append(dossier)
        
    # Save to json
    with open(BACKEND_DATA / "patients.json", "w") as f:
        json.dump(patients, f, indent=2)
        
    print(f"Generated {len(patients)} complete patient dossiers in: {BACKEND_DATA / 'patients.json'}")


if __name__ == "__main__":
    generate_cohort()
