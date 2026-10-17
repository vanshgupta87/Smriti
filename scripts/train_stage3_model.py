#!/usr/bin/env python3
"""
StepWise: Stage 3 ML Training, Calibration & Explainability Engine
Trains the Stage 3 Volumetric MRI Morphometry XGBoost Classifier with
Temporal Holdout Validation, Isotonic Calibration, TreeSHAP Explainability,
and Top-K Prioritization Queue Metrics.
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.base import clone
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    roc_curve,
    precision_recall_curve,
    confusion_matrix
)
from sklearn.model_selection import StratifiedGroupKFold
from xgboost import XGBClassifier
import shap

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "stage3_mri.parquet"
MODEL_DIR = BASE_DIR / "backend" / "models" / "stage3"
EVAL_DIR = BASE_DIR / "evaluations" / "stage3"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 5


def load_and_prep_data():
    print("=" * 70)
    print("STEPWISE: LOADING STAGE 3 VOLUMETRIC MRI DATASET")
    print("=" * 70)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}. Run scripts/build_stage3_dataset.py first.")
    
    df = pd.read_parquet(DATA_PATH)
    print(f"Raw Matrix Shape: {df.shape}")
    print(f"Unique Patients: {df['PTID'].nunique()}")
    
    DROP_COLS = {
        "PTID", "RID", "VISCODE", "VISCODE2", "VISDATE", 
        "DIAGNOSIS", "Progression24m", "FutureVisitsWithin24m"
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
        .head(1)
        .reset_index(drop=True)
    )
    
    print(f"Development Set: {len(dev_df)} rows across {dev_df['PTID'].nunique()} patients")
    print(f"Holdout Set:     {len(holdout_patient_df)} patients")
    
    return dev_df, holdout_patient_df


def train_and_cross_validate(dev_df, feature_cols):
    print("\n" + "=" * 70)
    print("5-FOLD PATIENT-GROUPED STRATIFIED CROSS-VALIDATION & ISOTONIC CALIBRATION")
    print("=" * 70)
    
    X_dev = dev_df[feature_cols].copy()
    y_dev = dev_df["Progression24m"].astype(int).values
    groups = dev_df["PTID"].values
    
    pos_count = (y_dev == 1).sum()
    neg_count = (y_dev == 0).sum()
    scale_pos = neg_count / max(1, pos_count)
    
    monotone_constraints = {}
    if "hippocampus_icv_ratio" in feature_cols:
        monotone_constraints["hippocampus_icv_ratio"] = -1
    if "ventricles_icv_ratio" in feature_cols:
        monotone_constraints["ventricles_icv_ratio"] = 1
    if "composite_ptau217_z" in feature_cols:
        monotone_constraints["composite_ptau217_z"] = 1
    if "APOE4_Count" in feature_cols:
        monotone_constraints["APOE4_Count"] = 1
    if "CDRSB" in feature_cols:
        monotone_constraints["CDRSB"] = 1
    if "MMSCORE" in feature_cols:
        monotone_constraints["MMSCORE"] = -1
        
    monotone_tuple = tuple(monotone_constraints.get(col, 0) for col in feature_cols)
    
    base_xgb = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos,
        monotone_constraints=monotone_tuple,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        eval_metric="logloss"
    )
    
    cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    oof_raw = np.full(len(X_dev), np.nan)
    fold_metrics = []
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(X_dev, y_dev, groups=groups), start=1):
        X_tr, y_tr = X_dev.iloc[train_idx], y_dev[train_idx]
        X_va, y_va = X_dev.iloc[val_idx], y_dev[val_idx]
        
        clf = clone(base_xgb)
        clf.fit(X_tr, y_tr)
        
        p_val = clf.predict_proba(X_va)[:, 1]
        oof_raw[val_idx] = p_val
        
        auc = roc_auc_score(y_va, p_val)
        pr_auc = average_precision_score(y_va, p_val)
        
        fold_metrics.append({"fold": fold, "ROC_AUC": auc, "PR_AUC": pr_auc})
        print(f"Fold {fold}: ROC-AUC = {auc:.4f} | PR-AUC = {pr_auc:.4f}")
        
    mean_auc = np.mean([m["ROC_AUC"] for m in fold_metrics])
    std_auc = np.std([m["ROC_AUC"] for m in fold_metrics])
    print(f"\nMean CV ROC-AUC: {mean_auc:.4f} ± {std_auc:.4f}")
    
    calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    calibrator.fit(oof_raw, y_dev)
    oof_calibrated = calibrator.predict(oof_raw)
    
    print(f"Calibration Brier Loss: {brier_score_loss(y_dev, oof_calibrated):.4f}")
    
    final_xgb = clone(base_xgb)
    final_xgb.fit(X_dev, y_dev)
    
    return final_xgb, calibrator, fold_metrics, oof_raw, oof_calibrated


def evaluate_temporal_holdout(final_xgb, calibrator, holdout_df, feature_cols):
    X_test = holdout_df[feature_cols].copy()
    y_test = holdout_df["Progression24m"].astype(int).values
    
    raw_probs = final_xgb.predict_proba(X_test)[:, 1]
    cal_probs = calibrator.predict(raw_probs)
    
    test_auc = roc_auc_score(y_test, cal_probs)
    test_pr_auc = average_precision_score(y_test, cal_probs)
    test_brier = brier_score_loss(y_test, cal_probs)
    
    fpr, tpr, thresholds = roc_curve(y_test, cal_probs)
    j_scores = tpr - fpr
    opt_idx = np.argmax(j_scores)
    optimal_threshold = float(thresholds[opt_idx])
    
    preds_binary = (cal_probs >= optimal_threshold).astype(int)
    cm = confusion_matrix(y_test, preds_binary)
    
    order = np.argsort(-cal_probs)
    total_pos = y_test.sum()
    topk_summary = []
    
    for frac in [0.05, 0.10, 0.20, 0.30, 0.50]:
        k = max(1, int(np.ceil(len(y_test) * frac)))
        selected = order[:k]
        tp = y_test[selected].sum()
        prec = tp / k
        rec = tp / total_pos if total_pos > 0 else 0
        topk_summary.append({
            "Top_Queue": f"Top {int(frac*100)}%",
            "Selected_Patients": int(k),
            "Progressors_Captured": int(tp),
            "Capture_Recall": round(float(rec), 4),
            "Queue_Precision": round(float(prec), 4)
        })
        
    metrics = {
        "temporal_roc_auc": round(float(test_auc), 4),
        "temporal_pr_auc": round(float(test_pr_auc), 4),
        "temporal_brier": round(float(test_brier), 4),
        "optimal_threshold": round(float(optimal_threshold), 4),
        "sensitivity": round(float(tpr[opt_idx]), 4),
        "specificity": round(float(1 - fpr[opt_idx]), 4),
        "confusion_matrix": cm.tolist(),
        "topk_prioritization": topk_summary
    }
    
    return raw_probs, cal_probs, metrics, (fpr, tpr), topk_summary


def generate_visualizations(final_xgb, calibrator, dev_df, holdout_df, feature_cols, metrics, roc_data, topk_summary):
    sns.set_theme(style="whitegrid", font="sans-serif")
    X_test = holdout_df[feature_cols]
    y_test = holdout_df["Progression24m"].values
    cal_probs = calibrator.predict(final_xgb.predict_proba(X_test)[:, 1])
    
    # 1. ROC
    fpr, tpr = roc_data
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="#0284c7", lw=2.5, label=f"Stage 3 MRI (AUC = {metrics['temporal_roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", lw=1.5)
    plt.scatter([1-metrics['specificity']], [metrics['sensitivity']], color="#dc2626", s=100, zorder=5, label=f"Decision Gate (T3={metrics['optimal_threshold']:.2f})")
    plt.title("Stage 3 ROC-AUC: Volumetric MRI Morphometry Holdout", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate", fontsize=11)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "roc_curve.png", dpi=300)
    plt.close()
    
    # 2. PR
    prec, rec, _ = precision_recall_curve(y_test, cal_probs)
    plt.figure(figsize=(7, 6))
    plt.plot(rec, prec, color="#059669", lw=2.5, label=f"PR Curve (PR-AUC = {metrics['temporal_pr_auc']:.3f})")
    plt.title("Stage 3 Precision-Recall Curve", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Recall", fontsize=11)
    plt.ylabel("Precision", fontsize=11)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "pr_curve.png", dpi=300)
    plt.close()
    
    # 3. Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(np.array(metrics["confusion_matrix"]), annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Predicted: No PET", "Predicted: Escalate to PET"],
                yticklabels=["Actual: Stable", "Actual: Progressed"])
    plt.title(f"Stage 3 Confusion Matrix (Threshold = {metrics['optimal_threshold']:.2f})", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "confusion_matrix.png", dpi=300)
    plt.close()
    
    # 4. Top-K Lift
    plt.figure(figsize=(8, 5))
    bar = sns.barplot(data=pd.DataFrame(topk_summary), x="Top_Queue", y="Capture_Recall", palette="viridis")
    plt.title("Stage 3 Triage Queue: Progressor Capture Rate by Percentile", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Recall (% of All Progressors Captured)", fontsize=11)
    plt.xlabel("Proportion of Patient Queue Escalated to PET", fontsize=11)
    plt.ylim(0, 1.1)
    for p in bar.patches:
        bar.annotate(f"{p.get_height():.1%}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="center", xytext=(0, 7), textcoords="offset points", fontweight="bold")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "topk_prioritization_lift.png", dpi=300)
    plt.close()
    
    # 5. TreeSHAP Summary
    explainer = shap.TreeExplainer(final_xgb)
    shap_values = explainer.shap_values(X_test)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_test, feature_names=feature_cols, max_display=15, show=False)
    plt.title("Stage 3 TreeSHAP Global Feature Importance (Top 15 Features)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_summary.png", dpi=300)
    plt.close()
    
    # 6. Waterfall
    high_risk_idx = int(np.argmax(cal_probs))
    sample_shap = explainer(X_test.iloc[[high_risk_idx]])
    plt.figure(figsize=(9, 6))
    shap.plots.waterfall(sample_shap[0], max_display=10, show=False)
    plt.title(f"Stage 3 Patient Dossier SHAP Decomposition (Risk: {cal_probs[high_risk_idx]:.2f})", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_waterfall_case.png", dpi=300)
    plt.close()


def main():
    df, feature_cols = load_and_prep_data()
    dev_df, holdout_df = temporal_patient_split(df, feature_cols)
    
    final_xgb, calibrator, cv_metrics, oof_raw, oof_calibrated = train_and_cross_validate(dev_df, feature_cols)
    raw_probs, cal_probs, metrics, roc_data, topk_summary = evaluate_temporal_holdout(final_xgb, calibrator, holdout_df, feature_cols)
    
    generate_visualizations(final_xgb, calibrator, dev_df, holdout_df, feature_cols, metrics, roc_data, topk_summary)
    
    joblib.dump(final_xgb, MODEL_DIR / "stage3_xgboost_model.joblib")
    joblib.dump(calibrator, MODEL_DIR / "stage3_calibrator.joblib")
    
    with open(MODEL_DIR / "stage3_feature_list.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    with open(MODEL_DIR / "stage3_optimal_threshold.json", "w") as f:
        json.dump({"optimal_threshold": metrics["optimal_threshold"]}, f, indent=2)
    with open(MODEL_DIR / "stage3_performance_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Stage 3 Model artifacts successfully written to: {MODEL_DIR}")
    print("\n✅ STAGE 3 ENGINE COMPLETE AND FULLY TRAINED!")

if __name__ == "__main__":
    main()
