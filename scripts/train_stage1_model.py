#!/usr/bin/env python3
"""
StepWise: Stage 1 ML Training, Calibration & Explainability Engine
Trains the Stage 1 Calibrated XGBoost Prioritizer with Temporal Validation,
Isotonic Calibration, TreeSHAP Explainability, and Top-K Prioritization Metrics.
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
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import StratifiedGroupKFold
from xgboost import XGBClassifier
import shap

warnings.filterwarnings("ignore")

# Setup Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "stage1_screening.parquet"
MODEL_DIR = BASE_DIR / "backend" / "models" / "stage1"
EVAL_DIR = BASE_DIR / "evaluations" / "stage1"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
N_SPLITS = 5


def load_and_prep_data():
    print("=" * 70)
    print("STEPWISE: LOADING STAGE 1 CLEANED DATASET")
    print("=" * 70)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}. Run scripts/build_stage1_dataset.py first.")
    
    df = pd.read_parquet(DATA_PATH)
    print(f"Raw Matrix Shape: {df.shape}")
    print(f"Unique Patients: {df['PTID'].nunique()}")
    
    # Exclude non-feature columns
    DROP_COLS = {
        "PTID", "RID", "VISCODE", "VISCODE2", "VISDATE", 
        "DIAGNOSIS", "Progression24m", "FutureVisitsWithin24m"
    }
    
    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    print(f"Candidate Features ({len(feature_cols)}): {feature_cols}")
    
    return df, feature_cols


def temporal_patient_split(df, feature_cols):
    """
    Splits 75% development / 25% temporal holdout based on earliest patient visit date.
    """
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
    
    # Holdout is evaluated on the earliest eligible visit per patient
    holdout_patient_df = (
        holdout_df.sort_values(["PTID", "VISDATE"])
        .groupby("PTID")
        .head(1)
        .reset_index(drop=True)
    )
    
    print(f"Development Set: {len(dev_df)} rows across {dev_df['PTID'].nunique()} patients (Progression Rate: {dev_df['Progression24m'].mean():.2%})")
    print(f"Holdout Set:     {len(holdout_patient_df)} patients (Progression Rate: {holdout_patient_df['Progression24m'].mean():.2%})")
    
    return dev_df, holdout_patient_df


def train_and_cross_validate(dev_df, feature_cols):
    print("\n" + "=" * 70)
    print("5-FOLD PATIENT-GROUPED STRATIFIED CROSS-VALIDATION & ISOTONIC CALIBRATION")
    print("=" * 70)
    
    X_dev = dev_df[feature_cols].copy()
    y_dev = dev_df["Progression24m"].astype(int).values
    groups = dev_df["PTID"].values
    
    # Imbalance handling
    pos_count = (y_dev == 1).sum()
    neg_count = (y_dev == 0).sum()
    scale_pos = neg_count / max(1, pos_count)
    print(f"Class Imbalance: Neg={neg_count}, Pos={pos_count} (scale_pos_weight={scale_pos:.2f})")
    
    # XGBoost Classifier
    base_xgb = XGBClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
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
    
    # Fit Isotonic Probability Calibrator on OOF predictions
    calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    calibrator.fit(oof_raw, y_dev)
    oof_calibrated = calibrator.predict(oof_raw)
    
    raw_brier = brier_score_loss(y_dev, oof_raw)
    cal_brier = brier_score_loss(y_dev, oof_calibrated)
    print(f"Calibration Brier Loss: Raw = {raw_brier:.4f} -> Calibrated = {cal_brier:.4f}")
    
    # Train Final Model on entire development cohort
    print("\nFitting Final Production XGBoost on all Development Data...")
    final_xgb = clone(base_xgb)
    final_xgb.fit(X_dev, y_dev)
    
    return final_xgb, calibrator, fold_metrics, oof_raw, oof_calibrated


def evaluate_temporal_holdout(final_xgb, calibrator, holdout_df, feature_cols):
    print("\n" + "=" * 70)
    print("PROSPECTIVE EVALUATION ON UNTOUCHED TEMPORAL HOLDOUT")
    print("=" * 70)
    
    X_test = holdout_df[feature_cols].copy()
    y_test = holdout_df["Progression24m"].astype(int).values
    
    raw_probs = final_xgb.predict_proba(X_test)[:, 1]
    cal_probs = calibrator.predict(raw_probs)
    
    test_auc = roc_auc_score(y_test, cal_probs)
    test_pr_auc = average_precision_score(y_test, cal_probs)
    test_brier = brier_score_loss(y_test, cal_probs)
    
    print(f"Test Temporal ROC-AUC : {test_auc:.4f}")
    print(f"Test Temporal PR-AUC  : {test_pr_auc:.4f}")
    print(f"Test Brier Score Loss : {test_brier:.4f}")
    
    # Optimal Threshold Selection via Youden's J
    fpr, tpr, thresholds = roc_curve(y_test, cal_probs)
    j_scores = tpr - fpr
    opt_idx = np.argmax(j_scores)
    optimal_threshold = float(thresholds[opt_idx])
    
    preds_binary = (cal_probs >= optimal_threshold).astype(int)
    cm = confusion_matrix(y_test, preds_binary)
    
    print(f"\nOptimal Escalation Threshold (Youden's J): {optimal_threshold:.4f}")
    print(f"Sensitivity (Recall on True Progressors) : {tpr[opt_idx]:.2%}")
    print(f"Specificity (Correct Non-Escalations)    : {1 - fpr[opt_idx]:.2%}")
    print("\nConfusion Matrix:")
    print(cm)
    
    # Top-K Prioritization Queue Metrics
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
        
    print("\n" + "=" * 70)
    print("TOP-K CLINICIAN PRIORITIZATION QUEUE PERFORMANCE")
    print("=" * 70)
    print(pd.DataFrame(topk_summary).to_string(index=False))
    
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


def generate_shap_and_visualizations(final_xgb, calibrator, dev_df, holdout_df, feature_cols, metrics, roc_data, topk_summary):
    print("\n" + "=" * 70)
    print("GENERATING EVALUATION PLOTS & TREESHAP VISUALIZATIONS")
    print("=" * 70)
    
    sns.set_theme(style="whitegrid", font="sans-serif")
    X_dev = dev_df[feature_cols]
    X_test = holdout_df[feature_cols]
    y_test = holdout_df["Progression24m"].values
    cal_probs = calibrator.predict(final_xgb.predict_proba(X_test)[:, 1])
    
    # 1. ROC-AUC Curve
    fpr, tpr = roc_data
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="#2563eb", lw=2.5, label=f"StepWise Stage 1 (AUC = {metrics['temporal_roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", lw=1.5, label="Random Chance (AUC = 0.500)")
    plt.scatter([metrics['specificity'] if False else 1-metrics['specificity']], [metrics['sensitivity']], color="#dc2626", s=100, zorder=5, label=f"Decision Gate (T={metrics['optimal_threshold']:.2f})")
    plt.title("Stage 1 ROC-AUC: Prospective Temporal Holdout", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    plt.ylabel("True Positive Rate (Sensitivity)", fontsize=11)
    plt.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "roc_curve.png", dpi=300)
    plt.close()
    
    # 2. Precision-Recall Curve
    prec, rec, _ = precision_recall_curve(y_test, cal_probs)
    plt.figure(figsize=(7, 6))
    plt.plot(rec, prec, color="#059669", lw=2.5, label=f"PR Curve (PR-AUC = {metrics['temporal_pr_auc']:.3f})")
    plt.title("Stage 1 Precision-Recall Curve", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Recall (True Progressors Captured)", fontsize=11)
    plt.ylabel("Precision (Positive Predictive Value)", fontsize=11)
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "pr_curve.png", dpi=300)
    plt.close()
    
    # 3. Confusion Matrix Heatmap
    cm = np.array(metrics["confusion_matrix"])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Predicted: Stable", "Predicted: Escalate"],
                yticklabels=["Actual: Stable", "Actual: Progressed"])
    plt.title(f"Stage 1 Confusion Matrix (Threshold = {metrics['optimal_threshold']:.2f})", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "confusion_matrix.png", dpi=300)
    plt.close()
    
    # 4. Top-K Prioritization Lift Chart
    topk_df = pd.DataFrame(topk_summary)
    plt.figure(figsize=(8, 5))
    bar = sns.barplot(data=topk_df, x="Top_Queue", y="Capture_Recall", palette="crest")
    plt.title("Clinician Triage Queue: Progressor Capture Rate by Percentile", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Recall (% of All Progressors Captured)", fontsize=11)
    plt.xlabel("Proportion of Patient Queue Reviewed by Clinician", fontsize=11)
    plt.ylim(0, 1.1)
    for p in bar.patches:
        bar.annotate(f"{p.get_height():.1%}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="center", xytext=(0, 7), textcoords="offset points", fontweight="bold")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "topk_prioritization_lift.png", dpi=300)
    plt.close()
    
    # 5. TreeSHAP Feature Summary Plot
    print("Computing TreeSHAP Attributions...")
    explainer = shap.TreeExplainer(final_xgb)
    shap_values = explainer.shap_values(X_test)
    
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_test, feature_names=feature_cols, max_display=15, show=False)
    plt.title("Stage 1 TreeSHAP Global Feature Importance (Top 15 Biomarkers)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_summary.png", dpi=300)
    plt.close()
    
    # 6. TreeSHAP Waterfall for a High-Risk Progressor
    high_risk_idx = int(np.argmax(cal_probs))
    sample_shap = explainer(X_test.iloc[[high_risk_idx]])
    plt.figure(figsize=(9, 6))
    shap.plots.waterfall(sample_shap[0], max_display=10, show=False)
    plt.title(f"Patient Dossier SHAP Decomposition (Risk: {cal_probs[high_risk_idx]:.2f})", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "shap_waterfall_case.png", dpi=300)
    plt.close()
    
    print("All evaluation plots successfully saved in evaluations/stage1/")


def main():
    df, feature_cols = load_and_prep_data()
    dev_df, holdout_df = temporal_patient_split(df, feature_cols)
    
    final_xgb, calibrator, cv_metrics, oof_raw, oof_calibrated = train_and_cross_validate(dev_df, feature_cols)
    raw_probs, cal_probs, metrics, roc_data, topk_summary = evaluate_temporal_holdout(final_xgb, calibrator, holdout_df, feature_cols)
    
    generate_shap_and_visualizations(final_xgb, calibrator, dev_df, holdout_df, feature_cols, metrics, roc_data, topk_summary)
    
    # Save Model Artifacts
    print("\n" + "=" * 70)
    print("SAVING PRODUCTION MODEL ARTIFACTS")
    print("=" * 70)
    
    joblib.dump(final_xgb, MODEL_DIR / "stage1_xgboost_model.joblib")
    joblib.dump(calibrator, MODEL_DIR / "stage1_calibrator.joblib")
    
    with open(MODEL_DIR / "stage1_feature_list.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
        
    with open(MODEL_DIR / "stage1_optimal_threshold.json", "w") as f:
        json.dump({"optimal_threshold": metrics["optimal_threshold"]}, f, indent=2)
        
    with open(MODEL_DIR / "stage1_performance_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Model artifacts successfully written to: {MODEL_DIR}")
    print("\n✅ STAGE 1 ENGINE COMPLETE AND FULLY TRAINED!")

if __name__ == "__main__":
    main()
