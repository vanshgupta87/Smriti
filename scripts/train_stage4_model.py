#!/usr/bin/env python3
"""
StepWise: Stage 4 Molecular PET & DMT/ARIA Readiness XGBoost Model Training
Trains a calibrated multimodal XGBoost model for 24-month rapid progression
incorporating Amyloid Centiloids, Tau Braak SUVR, Hippocampal ICV, and Plasma p-tau217.
Saves model artifacts, SHAP explainers, and evaluation figures.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve,
    brier_score_loss, confusion_matrix, classification_report, auc
)
import xgboost as xgb
import shap

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "stage4_pet.parquet"
MODEL_DIR = BASE_DIR / "backend" / "models" / "stage4"
EVAL_DIR = BASE_DIR / "evaluations" / "stage4"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 5


def load_and_prep_data():
    print("=" * 70)
    print("STEPWISE: LOADING STAGE 4 MOLECULAR PET & DMT DATASET")
    print("=" * 70)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}. Run scripts/build_stage4_dataset.py first.")
    
    df = pd.read_parquet(DATA_PATH)
    print(f"Raw Matrix Shape: {df.shape}")
    print(f"Unique Patients: {df['PTID'].nunique()}")
    
    DROP_COLS = {
        "PTID", "RID", "VISCODE", "VISCODE2", "VISDATE", 
        "DIAGNOSIS", "Progression24m", "FutureVisitsWithin24m",
        "DMT_Eligibility_Flag"
    }
    
    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    print(f"Total Multimodal Features ({len(feature_cols)}): {feature_cols[:15]} ...")
    
    return df, feature_cols


def temporal_patient_split(df, feature_cols):
    print("\n" + "=" * 70)
    print("CREATING TEMPORAL PATIENT-LEVEL HOLDOUT SPLIT (75/25)")
    print("=" * 70)
    
    enrollment = df.groupby("PTID")["VISDATE"].min().sort_values()
    n_patients = len(enrollment)
    split_idx = int(np.floor(0.75 * n_patients))
    
    dev_ptids = set(enrollment.iloc[:split_idx].index)
    holdout_ptids = set(enrollment.iloc[split_idx:].index)
    
    dev_df = df[df["PTID"].isin(dev_ptids)].copy().reset_index(drop=True)
    holdout_df = df[df["PTID"].isin(holdout_ptids)].copy().reset_index(drop=True)
    
    holdout_patient_df = (
        holdout_df.sort_values(["PTID", "VISDATE"])
        .groupby("PTID")
        .last()
        .reset_index()
    )
    
    print(f"Development Set: {len(dev_df)} rows across {len(dev_ptids)} patients")
    print(f"Holdout Set:     {len(holdout_patient_df)} patients")
    
    return dev_df, holdout_patient_df


def train_cv_and_calibrate(dev_df, feature_cols):
    print("\n" + "=" * 70)
    print("5-FOLD PATIENT-GROUPED STRATIFIED CROSS-VALIDATION & ISOTONIC CALIBRATION")
    print("=" * 70)
    
    X = dev_df[feature_cols].copy()
    y = dev_df["Progression24m"].astype(int).values
    groups = dev_df["PTID"].values
    
    sgkf = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    
    oof_raw_preds = np.zeros(len(dev_df))
    fold_aucs = []
    fold_pr_aucs = []
    
    scale_pos_weight = (len(y) - sum(y)) / (sum(y) + 1e-6)
    
    xgb_params = {
        "n_estimators": 160,
        "max_depth": 4,
        "learning_rate": 0.04,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight * 0.5,
        "random_state": RANDOM_STATE,
        "eval_metric": "logloss"
    }
    
    for fold, (train_idx, val_idx) in enumerate(sgkf.split(X, y, groups=groups), 1):
        X_train, y_train = X.iloc[train_idx], y[train_idx]
        X_val, y_val = X.iloc[val_idx], y[val_idx]
        
        clf = xgb.XGBClassifier(**xgb_params)
        clf.fit(X_train, y_train)
        
        preds_val = clf.predict_proba(X_val)[:, 1]
        oof_raw_preds[val_idx] = preds_val
        
        roc_val = roc_auc_score(y_val, preds_val)
        precision, recall, _ = precision_recall_curve(y_val, preds_val)
        pr_auc = auc(recall, precision)
        
        fold_aucs.append(roc_val)
        fold_pr_aucs.append(pr_auc)
        print(f"Fold {fold}: ROC-AUC = {roc_val:.4f} | PR-AUC = {pr_auc:.4f}")
        
    mean_auc = float(np.mean(fold_aucs))
    std_auc = float(np.std(fold_aucs))
    print(f"\nMean CV ROC-AUC: {mean_auc:.4f} ± {std_auc:.4f}")
    
    # Train Full Base Model on Entire Dev Set
    base_model = xgb.XGBClassifier(**xgb_params)
    base_model.fit(X, y)
    
    # Calibrate on OOF predictions
    from sklearn.isotonic import IsotonicRegression
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(oof_raw_preds, y)
    
    cal_oof_preds = calibrator.predict(oof_raw_preds)
    cal_brier = brier_score_loss(y, cal_oof_preds)
    print(f"Calibration Brier Loss: {cal_brier:.4f}")
    
    return base_model, calibrator, mean_auc, std_auc


def evaluate_and_generate_plots(model, calibrator, holdout_df, feature_cols, mean_cv_auc, std_cv_auc):
    print("\n" + "=" * 70)
    print("STEPWISE: STAGE 4 EVALUATION ON PATIENT HOLDOUT")
    print("=" * 70)
    
    X_test = holdout_df[feature_cols].copy()
    y_test = holdout_df["Progression24m"].astype(int).values
    
    raw_probs = model.predict_proba(X_test)[:, 1]
    cal_probs = calibrator.predict(raw_probs)
    
    roc_auc = roc_auc_score(y_test, cal_probs)
    fpr, tpr, roc_thresh = roc_curve(y_test, cal_probs)
    precision, recall, pr_thresh = precision_recall_curve(y_test, cal_probs)
    brier = brier_score_loss(y_test, cal_probs)
    
    # Optimal T4 threshold
    j_stat = tpr - fpr
    opt_idx = np.argmax(j_stat)
    opt_threshold = float(roc_thresh[opt_idx])
    
    preds_binary = (cal_probs >= opt_threshold).astype(int)
    cm = confusion_matrix(y_test, preds_binary)
    tn, fp, fn, tp = cm.ravel()
    
    spec = tn / (tn + fp)
    sens = tp / (tp + fn)
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    
    print(f"Holdout ROC-AUC:             {roc_auc:.4f}")
    print(f"Optimal Gate Threshold T4:   {opt_threshold:.4f}")
    print(f"Sensitivity (Recall):        {sens:.2%}")
    print(f"Specificity:                 {spec:.2%}")
    print(f"Negative Predictive Value:   {npv:.2%}")
    print(f"Positive Predictive Value:   {ppv:.2%}")
    print(f"Brier Score Loss:            {brier:.4f}")
    
    metrics = {
        "model_name": "StepWise Stage 4 Molecular PET & ARIA Multimodal XGBoost",
        "mean_cv_roc_auc": round(float(mean_cv_auc), 4),
        "std_cv_roc_auc": round(float(std_cv_auc), 4),
        "holdout_roc_auc": round(float(roc_auc), 4),
        "brier_score": round(float(brier), 4),
        "optimal_threshold_t4": round(float(opt_threshold), 4),
        "sensitivity": round(float(sens), 4),
        "specificity": round(float(spec), 4),
        "negative_predictive_value": round(float(npv), 4),
        "positive_predictive_value": round(float(ppv), 4),
        "holdout_sample_size": len(holdout_df),
        "num_features": len(feature_cols)
    }
    
    # 1. ROC Curve
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="#0284c7", lw=2.5, label=f"Stage 4 Calibrated XGBoost (AUC = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", lw=1.5, label="Chance")
    plt.scatter([fpr[opt_idx]], [tpr[opt_idx]], color="#e11d48", s=100, zorder=5, label=f"Optimal Gate T4={opt_threshold:.3f}")
    plt.title("StepWise Stage 4: Molecular PET ROC Curve", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    plt.ylabel("True Positive Rate (Sensitivity)", fontsize=11)
    plt.legend(loc="lower right", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "roc_curve.png", dpi=300)
    plt.close()
    
    # 2. PR Curve
    plt.figure(figsize=(7, 6))
    plt.plot(recall, precision, color="#059669", lw=2.5, label="Stage 4 PR Curve")
    plt.axhline(y=y_test.mean(), color="#94a3b8", linestyle="--", label=f"Baseline Prevalence ({y_test.mean():.1%})")
    plt.title("StepWise Stage 4: Precision-Recall Curve", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Recall (Sensitivity)", fontsize=11)
    plt.ylabel("Precision (PPV)", fontsize=11)
    plt.legend(loc="upper right", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "pr_curve.png", dpi=300)
    plt.close()
    
    # 3. Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Stable", "Progressor"], yticklabels=["Stable", "Progressor"])
    plt.title(f"Stage 4 Confusion Matrix (T4 = {opt_threshold:.3f})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Predicted Label", fontsize=11)
    plt.ylabel("Ground Truth Label", fontsize=11)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "confusion_matrix.png", dpi=300)
    plt.close()
    
    # 4. Prioritization Lift
    test_eval_df = pd.DataFrame({"true": y_test, "prob": cal_probs}).sort_values("prob", ascending=False).reset_index(drop=True)
    deciles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    total_prog = y_test.sum()
    prog_captured = [(test_eval_df.iloc[:int(d * len(test_eval_df))]["true"].sum() / total_prog) * 100 for d in deciles]
    
    plt.figure(figsize=(7, 5))
    plt.plot([d * 100 for d in deciles], prog_captured, marker="o", color="#d97706", lw=2.5, label="StepWise Stage 4 Lift")
    plt.plot([0, 100], [0, 100], linestyle="--", color="#94a3b8", label="Random Queue")
    plt.title("Stage 4 Prioritization Capacity Lift", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Percentage of Patients Screened (%)", fontsize=11)
    plt.ylabel("Percentage of Rapid Progressors Captured (%)", fontsize=11)
    plt.legend(loc="lower right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "topk_prioritization_lift.png", dpi=300)
    plt.close()
    
    # 5. SHAP Explanations
    explainer = shap.TreeExplainer(model)
    shap_sample = X_test.sample(n=min(300, len(X_test)), random_state=42)
    shap_values = explainer(shap_sample)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, shap_sample, show=False, max_display=15)
    plt.title("StepWise Stage 4: SHAP Biomarker Attribution (Centiloids + Tau + Biofluids)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_summary.png", dpi=300)
    plt.close()
    
    # 6. Single Case Waterfall
    plt.figure(figsize=(9, 6))
    shap.plots.waterfall(shap_values[0], show=False, max_display=12)
    plt.title("Stage 4 Individual Patient Explainability Waterfall", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_waterfall_case.png", dpi=300)
    plt.close()
    
    # Save artifacts
    joblib.dump(model, MODEL_DIR / "stage4_xgboost_model.joblib")
    joblib.dump(calibrator, MODEL_DIR / "stage4_calibrator.joblib")
    
    with open(MODEL_DIR / "stage4_feature_list.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
        
    with open(MODEL_DIR / "stage4_performance_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(MODEL_DIR / "stage4_optimal_threshold.json", "w") as f:
        json.dump({"optimal_threshold": opt_threshold}, f, indent=2)
        
    print(f"Stage 4 Model artifacts successfully written to: {MODEL_DIR}")


def main():
    df, feature_cols = load_and_prep_data()
    dev_df, test_df = temporal_patient_split(df, feature_cols)
    model, calibrator, mean_auc, std_auc = train_cv_and_calibrate(dev_df, feature_cols)
    evaluate_and_generate_plots(model, calibrator, test_df, feature_cols, mean_auc, std_auc)
    print("\n✅ STAGE 4 ENGINE COMPLETE AND FULLY TRAINED!")


if __name__ == "__main__":
    main()
