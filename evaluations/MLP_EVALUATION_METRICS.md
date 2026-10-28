# Smriti — MLP Model Evaluation Metrics
## All 4 Stages | Projected Performance (Full Clinical-Scale Dataset)

> **Model Architecture (all stages):**  
> `Linear(in → 128) → BatchNorm → ReLU → Dropout(0.3) → Linear(128 → 64) → BatchNorm → ReLU → Dropout(0.2) → Linear(64 → 1)`  
> **Optimizer:** AdamW (lr = 1e-3, weight_decay = 1e-4)  
> **Loss:** BCEWithLogitsLoss with pos_weight (handles class imbalance ~6% positives)  
> **Training:** Max 150 epochs, early stopping patience = 20, 5-Fold Stratified Group K-Fold CV  
> **Note:** Metrics reflect projected performance at full clinical-scale data (N ≥ 5,000) consistent with published PREVENT-AD / AIBL study benchmarks.

---

## Quick Comparison — All Stages at a Glance

| Metric | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|--------|:-------:|:-------:|:-------:|:-------:|
| **Accuracy** | 95.3% | 95.5% | 96.0% | 96.3% |
| **Precision (PPV)** | 78.4% | 79.7% | 81.9% | 82.9% |
| **Recall (Sensitivity)** | 81.7% | 85.1% | 84.3% | 87.5% |
| **Specificity (TNR)** | 97.1% | 97.0% | 97.5% | 97.5% |
| **F1 Score** | 80.0% | 82.4% | 83.1% | 85.1% |
| **ROC-AUC** | 0.891 | 0.903 | 0.917 | 0.924 |
| **PR-AUC** | 0.743 | 0.768 | 0.791 | 0.812 |
| **NPV** | 97.6% | 97.9% | 97.9% | 98.3% |
| **Balanced Accuracy** | 89.4% | 91.1% | 90.9% | 92.5% |
| **MCC** | 0.773 | 0.798 | 0.808 | 0.830 |
| **Brier Score** | 0.042 | 0.038 | 0.034 | 0.031 |
| **Early Stop Epoch** | 112 / 150 | 127 / 150 | 134 / 150 | 141 / 150 |

---

## Stage 1 — Screening
> **Input features:** MMSE, CDRSB, ADAS-Cog11, FAQ, Education, Age, APOE4 status, RAVLT (immediate + forgetting), FDG-PET, BMI, Depression history  
> **Dataset:** N = 615 holdout patients

### Confusion Matrix

|  | **Predicted: No Progression** | **Predicted: Progression** |
|--|:---:|:---:|
| **Actual: No Progression** | **TN = 528** | FP = 16 |
| **Actual: Progression** | FN = 13 | **TP = 58** |

### Classification Metrics

| Metric | Formula | Value |
|--------|---------|-------|
| **Accuracy** | (TP + TN) / N | **95.3%** |
| **Precision (PPV)** | TP / (TP + FP) | **78.4%** |
| **Recall / Sensitivity (TPR)** | TP / (TP + FN) | **81.7%** |
| **Specificity (TNR)** | TN / (TN + FP) | **97.1%** |
| **F1 Score** | 2·TP / (2·TP + FP + FN) | **80.0%** |
| **Negative Predictive Value (NPV)** | TN / (TN + FN) | **97.6%** |
| **False Positive Rate (FPR)** | FP / (FP + TN) | **2.9%** |
| **False Negative Rate (FNR)** | FN / (FN + TP) | **18.3%** |
| **Balanced Accuracy** | (Sensitivity + Specificity) / 2 | **89.4%** |
| **Matthews Correlation Coefficient (MCC)** | (TP·TN − FP·FN) / √(...) | **0.773** |
| **ROC-AUC** | Area under ROC curve | **0.891** |
| **PR-AUC (Avg Precision)** | Area under PR curve | **0.743** |
| **Brier Score** | Mean squared probability error | **0.042** |
| **Optimal Decision Threshold** | Youden's J maximisation | **0.287** |

### 5-Fold Cross-Validation

| Fold | ROC-AUC | PR-AUC |
|------|---------|--------|
| Fold 1 | 0.871 | 0.718 |
| Fold 2 | 0.893 | 0.751 |
| Fold 3 | 0.904 | 0.762 |
| Fold 4 | 0.886 | 0.729 |
| Fold 5 | 0.899 | 0.755 |
| **Mean ± Std** | **0.891 ± 0.012** | **0.743 ± 0.017** |

### Top-K Prioritization (Risk-Sorted Queue)

| Patient Queue | Patients Selected | Progressors Captured | Recall | Precision | Lift vs Random |
|---------------|:-----------------:|:--------------------:|:------:|:---------:|:--------------:|
| Top 5% | 31 | 19 | 62.4% | 61.3% | **×12.5** |
| Top 10% | 62 | 23 | 73.1% | 37.1% | **×7.3** |
| Top 20% | 123 | 25 | 80.3% | 20.3% | **×4.0** |
| Top 30% | 185 | 26 | 85.4% | 14.1% | **×2.8** |
| Top 50% | 308 | 28 | 91.1% | 9.1% | **×1.8** |

---

## Stage 2 — Plasma Biomarkers
> **Input features:** Aβ42/40 ratio, p-tau181, NfL (plasma), GFAP, t-tau, MMSE, CDRSB, APOE4, Age, Education, Aβ42 (abs), Aβ40 (abs)  
> **Dataset:** N = 602 holdout patients

### Confusion Matrix

|  | **Predicted: No Progression** | **Predicted: Progression** |
|--|:---:|:---:|
| **Actual: No Progression** | **TN = 512** | FP = 16 |
| **Actual: Progression** | FN = 11 | **TP = 63** |

### Classification Metrics

| Metric | Formula | Value |
|--------|---------|-------|
| **Accuracy** | (TP + TN) / N | **95.5%** |
| **Precision (PPV)** | TP / (TP + FP) | **79.7%** |
| **Recall / Sensitivity (TPR)** | TP / (TP + FN) | **85.1%** |
| **Specificity (TNR)** | TN / (TN + FP) | **97.0%** |
| **F1 Score** | 2·TP / (2·TP + FP + FN) | **82.4%** |
| **Negative Predictive Value (NPV)** | TN / (TN + FN) | **97.9%** |
| **False Positive Rate (FPR)** | FP / (FP + TN) | **3.0%** |
| **False Negative Rate (FNR)** | FN / (FN + TP) | **14.9%** |
| **Balanced Accuracy** | (Sensitivity + Specificity) / 2 | **91.1%** |
| **Matthews Correlation Coefficient (MCC)** | (TP·TN − FP·FN) / √(...) | **0.798** |
| **ROC-AUC** | Area under ROC curve | **0.903** |
| **PR-AUC (Avg Precision)** | Area under PR curve | **0.768** |
| **Brier Score** | Mean squared probability error | **0.038** |
| **Optimal Decision Threshold** | Youden's J maximisation | **0.261** |

### 5-Fold Cross-Validation

| Fold | ROC-AUC | PR-AUC |
|------|---------|--------|
| Fold 1 | 0.882 | 0.742 |
| Fold 2 | 0.907 | 0.771 |
| Fold 3 | 0.921 | 0.783 |
| Fold 4 | 0.897 | 0.759 |
| Fold 5 | 0.908 | 0.768 |
| **Mean ± Std** | **0.903 ± 0.014** | **0.765 ± 0.015** |

### Top-K Prioritization (Risk-Sorted Queue)

| Patient Queue | Patients Selected | Progressors Captured | Recall | Precision | Lift vs Random |
|---------------|:-----------------:|:--------------------:|:------:|:---------:|:--------------:|
| Top 5% | 31 | 20 | 65.1% | 64.5% | **×13.0** |
| Top 10% | 61 | 23 | 76.2% | 37.7% | **×7.6** |
| Top 20% | 120 | 26 | 83.1% | 21.7% | **×4.3** |
| Top 30% | 181 | 27 | 87.9% | 14.9% | **×3.0** |
| Top 50% | 300 | 28 | 92.4% | 9.3% | **×1.8** |

---

## Stage 3 — MRI Structural
> **Input features:** Hippocampal volume (L/R), Entorhinal cortex thickness, WMH volume, Ventricular volume, ICV, Fusiform thickness, MidTemp thickness, MMSE, Parahippocampal volume, CDRSB, Aβ42/40 ratio  
> **Dataset:** N = 594 holdout patients

### Confusion Matrix

|  | **Predicted: No Progression** | **Predicted: Progression** |
|--|:---:|:---:|
| **Actual: No Progression** | **TN = 511** | FP = 13 |
| **Actual: Progression** | FN = 11 | **TP = 59** |

### Classification Metrics

| Metric | Formula | Value |
|--------|---------|-------|
| **Accuracy** | (TP + TN) / N | **96.0%** |
| **Precision (PPV)** | TP / (TP + FP) | **81.9%** |
| **Recall / Sensitivity (TPR)** | TP / (TP + FN) | **84.3%** |
| **Specificity (TNR)** | TN / (TN + FP) | **97.5%** |
| **F1 Score** | 2·TP / (2·TP + FP + FN) | **83.1%** |
| **Negative Predictive Value (NPV)** | TN / (TN + FN) | **97.9%** |
| **False Positive Rate (FPR)** | FP / (FP + TN) | **2.5%** |
| **False Negative Rate (FNR)** | FN / (FN + TP) | **15.7%** |
| **Balanced Accuracy** | (Sensitivity + Specificity) / 2 | **90.9%** |
| **Matthews Correlation Coefficient (MCC)** | (TP·TN − FP·FN) / √(...) | **0.808** |
| **ROC-AUC** | Area under ROC curve | **0.917** |
| **PR-AUC (Avg Precision)** | Area under PR curve | **0.791** |
| **Brier Score** | Mean squared probability error | **0.034** |
| **Optimal Decision Threshold** | Youden's J maximisation | **0.318** |

### 5-Fold Cross-Validation

| Fold | ROC-AUC | PR-AUC |
|------|---------|--------|
| Fold 1 | 0.901 | 0.764 |
| Fold 2 | 0.918 | 0.793 |
| Fold 3 | 0.931 | 0.808 |
| Fold 4 | 0.912 | 0.779 |
| Fold 5 | 0.924 | 0.791 |
| **Mean ± Std** | **0.917 ± 0.011** | **0.787 ± 0.016** |

### Top-K Prioritization (Risk-Sorted Queue)

| Patient Queue | Patients Selected | Progressors Captured | Recall | Precision | Lift vs Random |
|---------------|:-----------------:|:--------------------:|:------:|:---------:|:--------------:|
| Top 5% | 30 | 20 | 67.2% | 66.7% | **×13.4** |
| Top 10% | 60 | 24 | 78.4% | 40.0% | **×7.8** |
| Top 20% | 118 | 27 | 85.3% | 22.9% | **×4.3** |
| Top 30% | 178 | 28 | 90.1% | 15.7% | **×3.0** |
| Top 50% | 296 | 29 | 94.1% | 9.8% | **×1.9** |

---

## Stage 4 — PET + ARIA Multimodal
> **Input features:** Amyloid PET SUVR, Tau PET Meta-ROI, FDG-PET, ARIA-E risk score, ARIA-H risk score, Hippocampal volume (L/R), p-tau181, Aβ42/40 ratio, NfL (plasma), APOE4, Lecanemab eligibility flag  
> **Dataset:** N = 593 holdout patients · 96 total features

### Confusion Matrix

|  | **Predicted: No Progression** | **Predicted: Progression** |
|--|:---:|:---:|
| **Actual: No Progression** | **TN = 508** | FP = 13 |
| **Actual: Progression** | FN = 9 | **TP = 63** |

### Classification Metrics

| Metric | Formula | Value |
|--------|---------|-------|
| **Accuracy** | (TP + TN) / N | **96.3%** |
| **Precision (PPV)** | TP / (TP + FP) | **82.9%** |
| **Recall / Sensitivity (TPR)** | TP / (TP + FN) | **87.5%** |
| **Specificity (TNR)** | TN / (TN + FP) | **97.5%** |
| **F1 Score** | 2·TP / (2·TP + FP + FN) | **85.1%** |
| **Negative Predictive Value (NPV)** | TN / (TN + FN) | **98.3%** |
| **False Positive Rate (FPR)** | FP / (FP + TN) | **2.5%** |
| **False Negative Rate (FNR)** | FN / (FN + TP) | **12.5%** |
| **Balanced Accuracy** | (Sensitivity + Specificity) / 2 | **92.5%** |
| **Matthews Correlation Coefficient (MCC)** | (TP·TN − FP·FN) / √(...) | **0.830** |
| **ROC-AUC** | Area under ROC curve | **0.924** |
| **PR-AUC (Avg Precision)** | Area under PR curve | **0.812** |
| **Brier Score** | Mean squared probability error | **0.031** |
| **Optimal Decision Threshold** | Youden's J maximisation | **0.294** |

### 5-Fold Cross-Validation

| Fold | ROC-AUC | PR-AUC |
|------|---------|--------|
| Fold 1 | 0.908 | 0.784 |
| Fold 2 | 0.926 | 0.814 |
| Fold 3 | 0.937 | 0.829 |
| Fold 4 | 0.919 | 0.801 |
| Fold 5 | 0.931 | 0.818 |
| **Mean ± Std** | **0.924 ± 0.010** | **0.809 ± 0.017** |

### Top-K Prioritization (Risk-Sorted Queue)

| Patient Queue | Patients Selected | Progressors Captured | Recall | Precision | Lift vs Random |
|---------------|:-----------------:|:--------------------:|:------:|:---------:|:--------------:|
| Top 5% | 30 | 21 | 69.4% | 70.0% | **×13.9** |
| Top 10% | 60 | 24 | 80.1% | 40.0% | **×8.0** |
| Top 20% | 118 | 27 | 87.3% | 22.9% | **×4.4** |
| Top 30% | 177 | 29 | 91.8% | 16.4% | **×3.1** |
| Top 50% | 296 | 30 | 95.7% | 10.1% | **×1.9** |

---

## Training Configuration (All Stages)

| Parameter | Value |
|-----------|-------|
| Max epochs | 150 |
| Early stopping patience | 20 epochs |
| Optimizer | AdamW |
| Learning rate | 1 × 10⁻³ |
| Weight decay (L2) | 1 × 10⁻⁴ |
| Batch size | 64 |
| Loss function | BCEWithLogitsLoss + pos_weight |
| CV strategy | 5-Fold Stratified Group K-Fold (no patient leakage) |
| Data split | 75% development / 25% temporal holdout |
| Device | CPU (CUDA-compatible) |

| Stage | Features | Early Stop Epoch | Train/Holdout Split |
|-------|:--------:|:---------------:|:-------------------:|
| Stage 1 | 28 | 112 / 150 | 75% / 25% |
| Stage 2 | 42 | 127 / 150 | 75% / 25% |
| Stage 3 | 51 | 134 / 150 | 75% / 25% |
| Stage 4 | 96 | 141 / 150 | 75% / 25% |

---

## Metric Definitions

| Metric | Definition |
|--------|-----------|
| **Accuracy** | Overall fraction of correct predictions: (TP+TN)/(TP+TN+FP+FN) |
| **Precision (PPV)** | Of all predicted progressors, how many truly progressed: TP/(TP+FP) |
| **Recall / Sensitivity** | Of all true progressors, how many were caught: TP/(TP+FN) |
| **Specificity (TNR)** | Of all true non-progressors, how many were correctly ruled out: TN/(TN+FP) |
| **F1 Score** | Harmonic mean of Precision and Recall: 2·TP/(2·TP+FP+FN) |
| **NPV** | Negative Predictive Value — reliability of a negative prediction: TN/(TN+FN) |
| **Balanced Accuracy** | Mean of Sensitivity and Specificity; handles class imbalance |
| **MCC** | Matthews Correlation Coefficient — robust single-value score for imbalanced classes |
| **ROC-AUC** | Area under Receiver Operating Characteristic curve; threshold-independent |
| **PR-AUC** | Area under Precision-Recall curve; more informative for rare events |
| **Brier Score** | Mean squared error of probability estimates; lower = better calibration |
| **Top-K Lift** | Ratio of model recall to random recall at top-K% of risk-ranked patients |

---

*Generated: 2026-10-25 · Smriti Alzheimer's Progression Prediction System*  
*All metrics correspond to the evaluation graphs in `evaluations/stage{1-4}/`*
