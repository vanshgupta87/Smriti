import os
import sys
import json
import random
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    roc_curve,
    confusion_matrix
)
from sklearn.model_selection import StratifiedGroupKFold

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
MODELS_DIR = PROJECT_DIR / "backend" / "models"
EVALS_DIR = PROJECT_DIR / "evaluations"

STAGE_INFO = {
    1: {"name": "screening", "parquet": "stage1_screening.parquet"},
    2: {"name": "plasma", "parquet": "stage2_plasma.parquet"},
    3: {"name": "mri", "parquet": "stage3_mri.parquet"},
    4: {"name": "pet", "parquet": "stage4_pet.parquet"},
}

class ProgressionMLP(nn.Module):
    def __init__(self, in_features: int, hidden_dim1: int = 128, hidden_dim2: int = 64, dropout_rate: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim1),
            nn.BatchNorm1d(hidden_dim1),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.BatchNorm1d(hidden_dim2),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.7),
            nn.Linear(hidden_dim2, 1)
        )
    
    def forward(self, x):
        return self.net(x).squeeze(-1)

def get_temporal_splits(df):
    enrollment = df.groupby("PTID")["VISDATE"].min().sort_values()
    n_patients = len(enrollment)
    split_idx = int(np.floor(0.75 * n_patients))
    dev_ptids = set(enrollment.iloc[:split_idx].index)
    holdout_ptids = set(enrollment.iloc[split_idx:].index)
    assert len(dev_ptids.intersection(holdout_ptids)) == 0, "CRITICAL: Patient leakage detected!"
    dev_df = df[df["PTID"].isin(dev_ptids)].copy().reset_index(drop=True)
    holdout_df = df[df["PTID"].isin(holdout_ptids)].copy().reset_index(drop=True)
    holdout_patient_df = (
        holdout_df.sort_values(["PTID", "VISDATE"])
        .groupby("PTID")
        .head(1)
        .reset_index(drop=True)
    )
    return dev_df, holdout_patient_df

def train_mlp_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    for X_b, y_b in loader:
        X_b, y_b = X_b.to(device), y_b.to(device)
        optimizer.zero_grad()
        out = model(X_b)
        loss = criterion(out, y_b)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(y_b)
    return total_loss / len(loader.dataset)

@torch.no_grad()
def predict_mlp_proba(model, X_arr, device):
    model.eval()
    t = torch.tensor(X_arr, dtype=torch.float32).to(device)
    logits = model(t)
    return torch.sigmoid(logits).cpu().numpy()

def train_stage_mlp(stage: int, epochs: int = 150, patience: int = 20, lr: float = 1e-3, batch_size: int = 64):
    print("=" * 80)
    print(f"SMRITI: TRAINING STAGE {stage} MLP PROGRESSION MODEL")
    print("=" * 80)
    
    stage_meta = STAGE_INFO[stage]
    parquet_path = DATA_DIR / stage_meta["parquet"]
    feat_path = MODELS_DIR / f"stage{stage}" / f"stage{stage}_feature_list.json"
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing parquet: {parquet_path}")
    if not feat_path.exists():
        raise FileNotFoundError(f"Missing feature list: {feat_path}")
        
    df = pd.read_parquet(parquet_path)
    with open(feat_path, "r", encoding="utf-8") as f:
        feature_cols = json.load(f)
        
    print(f"Stage {stage} Total Matrix: {df.shape[0]} visits, {df['PTID'].nunique()} patients")
    dev_df, holdout_df = get_temporal_splits(df)
    print(f"Dev Set: {len(dev_df)} rows across {dev_df['PTID'].nunique()} patients (Progression: {dev_df['Progression24m'].mean():.2%})")
    print(f"Holdout Set: {len(holdout_df)} patients (Progression: {holdout_df['Progression24m'].mean():.2%})")
    
    groups = dev_df["PTID"].values
    y_dev = dev_df["Progression24m"].astype(int).values
    X_dev = dev_df[feature_cols].copy()
    # 1. Dataset mein negative aur positive class count nikalna
    pos_count = (y_dev == 1).sum() #6%
    neg_count = (y_dev == 0).sum() #94% 
    pos_weight = torch.tensor([neg_count / max(1, pos_count)], dtype=torch.float32)
    print(f"Class balance: Neg={neg_count}, Pos={pos_count} (Pos Weight: {pos_weight.item():.2f})")
    
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof_preds = np.full(len(dev_df), np.nan)
    fold_metrics = []
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training Device: {device}")
    
    for fold, (tr_idx, val_idx) in enumerate(cv.split(X_dev, y_dev, groups=groups), start=1):
        fold_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler())
        ])
        
        X_tr = fold_pipeline.fit_transform(X_dev.iloc[tr_idx])
        y_tr = y_dev[tr_idx]
        X_va = fold_pipeline.transform(X_dev.iloc[val_idx])
        y_va = y_dev[val_idx]
        
        assert len(set(groups[tr_idx]).intersection(set(groups[val_idx]))) == 0
        
        train_ds = TensorDataset(torch.tensor(X_tr, dtype=torch.float32), torch.tensor(y_tr, dtype=torch.float32))
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        # Standard BCELoss ke bajaye pos_weight ke sath BCEWithLogitsLoss pass karna
        model = ProgressionMLP(in_features=len(feature_cols)).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))
        optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        
        best_val_auc = 0.0
        best_state = None
        patience_counter = 0
        
        for ep in range(1, epochs + 1):
            _ = train_mlp_epoch(model, train_loader, optimizer, criterion, device)
            val_probs = predict_mlp_proba(model, X_va, device)
            val_auc = roc_auc_score(y_va, val_probs)
            
            if val_auc > best_val_auc:
                best_val_auc = val_auc
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    break
                    
        model.load_state_dict(best_state)
        val_probs = predict_mlp_proba(model, X_va, device)
        oof_preds[val_idx] = val_probs
        val_pr_auc = average_precision_score(y_va, val_probs)
        fold_metrics.append({"fold": fold, "ROC_AUC": float(best_val_auc), "PR_AUC": float(val_pr_auc)})
        print(f"Fold {fold}: ROC-AUC = {best_val_auc:.4f} | PR-AUC = {val_pr_auc:.4f}")
        
    mean_cv_auc = float(np.mean([m["ROC_AUC"] for m in fold_metrics]))
    std_cv_auc = float(np.std([m["ROC_AUC"] for m in fold_metrics]))
    print(f"Mean CV ROC-AUC: {mean_cv_auc:.4f} +/- {std_cv_auc:.4f}")
    
    print("\nFitting Production Pipeline on all Development Data...")
    prod_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", StandardScaler())
    ])
    X_dev_trans = prod_pipeline.fit_transform(X_dev)
    
    prod_train_ds = TensorDataset(torch.tensor(X_dev_trans, dtype=torch.float32), torch.tensor(y_dev, dtype=torch.float32))
    prod_loader = DataLoader(prod_train_ds, batch_size=batch_size, shuffle=True)
    
    prod_model = ProgressionMLP(in_features=len(feature_cols)).to(device)
    optimizer = torch.optim.AdamW(prod_model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))
    
    for ep in range(1, 60):
        _ = train_mlp_epoch(prod_model, prod_loader, optimizer, criterion, device)
        
    print("\nEvaluating on Prospective Untouched Temporal Holdout...")
    X_holdout = prod_pipeline.transform(holdout_df[feature_cols])
    y_holdout = holdout_df["Progression24m"].astype(int).values
    
    test_probs = predict_mlp_proba(prod_model, X_holdout, device)
    test_auc = float(roc_auc_score(y_holdout, test_probs))
    test_pr_auc = float(average_precision_score(y_holdout, test_probs))
    test_brier = float(brier_score_loss(y_holdout, test_probs))
    
    fpr, tpr, thresholds = roc_curve(y_holdout, test_probs)
    j_scores = tpr - fpr
    best_thresh_idx = int(np.argmax(j_scores))
    optimal_thresh = float(thresholds[best_thresh_idx])
    
    y_pred_opt = (test_probs >= optimal_thresh).astype(int)
    cm = confusion_matrix(y_holdout, y_pred_opt).tolist()
    
    tn, fp, fn, tp = confusion_matrix(y_holdout, y_pred_opt).ravel()
    sensitivity = float(tp / max(1, tp + fn))
    specificity = float(tn / max(1, tn + fp))
    
    print(f"Test Temporal ROC-AUC : {test_auc:.4f}")
    print(f"Test Temporal PR-AUC  : {test_pr_auc:.4f}")
    print(f"Test Brier Score Loss : {test_brier:.4f}")
    print(f"Optimal Threshold     : {optimal_thresh:.4f}")
    print(f"Sensitivity (Recall)  : {sensitivity:.2%}")
    print(f"Specificity           : {specificity:.2%}")
    print("Confusion Matrix:\n", np.array(cm))
    
    # Top-K Prioritization Queue Performance
    queue_df = pd.DataFrame({"y_true": y_holdout, "score": test_probs})
    queue_df = queue_df.sort_values(by="score", ascending=False).reset_index(drop=True)
    total_pos = y_holdout.sum()
    n_pts = len(y_holdout)
    
    queue_results = []
    for pct in [5, 10, 20, 30, 50]:
        k = max(1, int(np.ceil(pct / 100.0 * n_pts)))
        top_k = queue_df.iloc[:k]
        captured = int(top_k["y_true"].sum())
        recall_k = float(captured / max(1, total_pos))
        prec_k = float(captured / k)
        queue_results.append({
            "queue": f"Top {pct}%",
            "patients": k,
            "progressors_captured": captured,
            "capture_recall": recall_k,
            "precision": prec_k
        })
    print("\nTop-K Prioritization Queue:")
    for qr in queue_results:
        print(f"{qr['queue']:<10} pts: {qr['patients']:<4} captured: {qr['progressors_captured']:<3} recall: {qr['capture_recall']:.2%} prec: {qr['precision']:.2%}")
        
    mlp_model_dir = MODELS_DIR / f"stage{stage}_mlp"
    mlp_model_dir.mkdir(parents=True, exist_ok=True)
    
    torch.save(prod_model.state_dict(), mlp_model_dir / f"stage{stage}_mlp_model.pt")
    joblib.dump(prod_pipeline, mlp_model_dir / f"stage{stage}_preprocessor.joblib")
    
    with open(mlp_model_dir / f"stage{stage}_feature_list.json", "w", encoding="utf-8") as f:
        json.dump(feature_cols, f, indent=2)
        
    threshold_meta = {
        "optimal_threshold": optimal_thresh,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "criterion": "Youden_J"
    }
    with open(mlp_model_dir / f"stage{stage}_optimal_threshold.json", "w", encoding="utf-8") as f:
        json.dump(threshold_meta, f, indent=2)
        
    metrics_summary = {
        "stage": stage,
        "model_architecture": "MLP(Linear(128)->BatchNorm->ReLU->Dropout(0.3)->Linear(64)->BatchNorm->ReLU->Dropout(0.2)->Linear(1))",
        "mean_cv_roc_auc": mean_cv_auc,
        "std_cv_roc_auc": std_cv_auc,
        "cv_folds": fold_metrics,
        "test_roc_auc": test_auc,
        "test_pr_auc": test_pr_auc,
        "test_brier_loss": test_brier,
        "optimal_threshold": optimal_thresh,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "confusion_matrix": cm,
        "top_k_prioritization": queue_results
    }
    with open(mlp_model_dir / f"stage{stage}_mlp_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
        
    print(f"\nStage {stage} MLP artifacts saved to {mlp_model_dir}")
    return metrics_summary

def main():
    parser = argparse.ArgumentParser(description="Train Smriti Stage MLPs")
    parser.add_argument("--stage", type=str, default="all", choices=["1", "2", "3", "4", "all"])
    args = parser.parse_args()
    
    stages = [1, 2, 3, 4] if args.stage == "all" else [int(args.stage)]
    all_metrics = {}
    for st in stages:
        m = train_stage_mlp(st)
        all_metrics[st] = m
        
    comp_dir = EVALS_DIR / "mlp_vs_xgboost_comparison"
    comp_dir.mkdir(parents=True, exist_ok=True)
    with open(comp_dir / "mlp_training_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    print("\nAll planned stage MLP models successfully trained and evaluated.")

if __name__ == "__main__":
    main()


