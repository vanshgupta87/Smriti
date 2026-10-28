# Smriti: Project Guide and Development Roadmap

This is the current source of truth for the Smriti project and future contributors.
Commands and paths are relative to the project root (the directory containing
`backend/`, `frontend/`, `scripts/`, `Dataset/`, and `requirements.txt`).

> **Research and education only.** This project is not a medical device. Model
> outputs are not diagnoses, treatment recommendations, or a substitute for
> qualified clinical review. Do not use it with real patient data or for care
> decisions. Cohort metrics do not establish clinical validity or generalization.

## 1. Product goal

Smriti is planned as two separate research demonstrations in one web application:

1. **Alzheimer's progression research:** four stage-specific tabular classifiers
   estimate the existing `Progression24m` outcome using progressively richer
   clinical/cognitive, blood-biomarker, MRI-derived, and PET-derived tabular
   features. Keep the existing XGBoost models as baselines and develop a separate
   MLP/ANN for each stage. Compare them fairly before choosing what the UI shows.
2. **Brain-tumor image demonstration:** a separate future feature will use the
   existing NeuroSight AI YOLOv8 Nano and Medium weights. It must not share labels,
   outputs, or interpretation with the Alzheimer's models.

The four stages are **not four diagnosis classes**. Each stage has a different
feature cohort; each model estimates the same kind of 24-month progression target.
The planned ANN is not the retired Current Status ANN and must not be described as
a classifier of today's diagnosis.

## 2. Approved scope and preservation rules

### Keep

- Every existing CSV file and all supplied tabular source data. In particular,
  retain:
  - `Dataset/Dataset/part1_screening.csv`
  - `Dataset/Dataset/part2_plasma.csv`
  - `Dataset/Dataset/part3_mri.csv`
  - `Dataset/Dataset/part4_pet.csv`
- The existing Stage 1–4 XGBoost models, calibrators, ordered feature lists,
  thresholds, metrics, and training scripts.
- The structured MRI/PET-derived numeric columns in the Stage 3/4 cohorts. They
  are tabular data and are not MRI/PET image uploads.
- Patient records, authentication, dashboard, analytics, lab-report parsing,
  structured prediction, and other unrelated application behavior.
- The original NeuroSight project and its Nano/Medium weights in their current
  location. Do not move, overwrite, or delete those files as part of Smriti work.
- Existing generated tabular CSVs, including any old current-diagnosis cohort CSV.
  Its presence does not mean the retired endpoint/model is active.

### Retired in this transition

- Alzheimer's MRI/PET image upload and inference screens, components, backend
  routes, and image-model code/checkpoints.
- The separate OASIS CDR image experiments. CDR is not an Alzheimer's diagnosis,
  and these experiments are outside the current product plan.
- The old Current Status ANN form, API route, loader, and trainer. Its target was
  a recorded diagnosis label, a different task from 24-month progression.
- Superseded root planning documents and the old `README_FULL.md`. Their
  unverified model/performance claims are not the source of truth.

The lab-report parser's file upload is unrelated and remains. Do not remove it
when changing image upload behavior.

### Not implemented yet

- The four stage-specific MLPs, comparison UI, and model-selection decision.
- Any Smriti YOLO endpoint or brain-tumor UI. YOLO integration is planned, not
  present. A functioning Smriti UI must not be claimed until it is implemented
  and tested.

## 3. Current application structure

| Location | Responsibility |
|---|---|
| `frontend/` | Next.js 14 / React 18 / TypeScript dashboard, login, patients, stage workups, and analytics |
| `backend/app.py` | FastAPI startup, XGBoost model loading, structured prediction and application API |
| `backend/database.py`, `backend/auth_service.py` | SQLite patient records and local hospital-workspace authentication |
| `backend/models/stage1/` … `backend/models/stage4/` | Existing XGBoost model bundles and stage metadata; preserve |
| `Dataset/Dataset/` | Supplied source CSV cohorts; preserve all CSVs |
| `data/processed/` | Generated Parquet/tabular outputs; rebuildable, but preserve user data unless explicitly authorized |
| `scripts/prepare_stage_datasets.py` | Validates supplied four-stage CSVs and writes Parquet training inputs |
| `scripts/train_stage1_model.py` … `scripts/train_stage4_model.py` | Existing XGBoost progression baselines |
| `tests/` | Backend/data regression coverage |

The previous MRI/PET UI, CDR experiments, and Current Status ANN have been
removed from the application. The dashboard keeps the existing design and
unrelated functions; no YOLO screen has been substituted yet.

## 4. Dataset and target

The four supplied CSVs are stage-specific feature views over repeated patient
visits. The last reviewed workspace snapshot reported:

| Stage | Source CSV | Rows/visits | Unique patients | Candidate numeric features | Positive `Progression24m` rows |
|---|---|---:|---:|---:|---:|
| 1 | `part1_screening.csv` | 9,453 | 2,458 | 50 | 1,111 |
| 2 | `part2_plasma.csv` | 9,363 | 2,406 | 77 | 1,106 |
| 3 | `part3_mri.csv` | 9,329 | 2,373 | 85 | 1,103 |
| 4 | `part4_pet.csv` | 9,328 | 2,372 | 96 | 1,103 |

These are audit-snapshot counts, not a promise that a later local copy is
unchanged. Re-run the preparation/inspection scripts before training and report
the actual counts. The supplied stage files contain repeated visits per patient;
do not treat visits as independent patients.

`Progression24m` is a binary, prepared outcome. The Stage 1 cohort builder
describes `1` as a worse diagnosis observed within 24 months, `0` as stable
follow-up, and missing as an unresolved target. Its implementation sets a
non-conversion label when it finds at least one later visit within the 24-month
window and no worse diagnosis. That implementation does not explicitly require
the later visit to reach the full 24-month boundary, despite the builder's
docstring. **Audit and document this target definition before MLP comparison.**
Do not silently change labels: if the target logic is corrected, version the
cohort and retrain/re-evaluate both XGBoost and MLP on the same corrected target.

The feature sources in Stages 3 and 4 are measurements (for example, structural
MRI volumes and PET biomarker values), not raw scan images. Stage 2 assay inputs
include cohort-standardized biomarker z-scores; do not interpret them as raw
laboratory concentrations.

Prepare the four model inputs from the project root:

```powershell
python scripts/prepare_stage_datasets.py
```

Expected Parquet files:

- `data/processed/stage1_screening.parquet`
- `data/processed/stage2_plasma.parquet`
- `data/processed/stage3_mri.parquet`
- `data/processed/stage4_pet.parquet`

The ADNI raw-table builder `scripts/build_stage1_dataset.py` remains for the
Stage 1 progression cohort workflow. It no longer creates the retired
Current Status ANN cohort. Preserve any already-existing CSV outputs.

## 5. Existing XGBoost baselines

There is one existing XGBoost binary classifier per stage. They use the
`Progression24m` target and stage-specific tabular feature sets. The reviewed
training scripts use 150 trees for Stage 1, 200 for Stages 2 and 3, and 160 for
Stage 4. **XGBoost does not train in epochs.** These are implementation settings,
not performance claims.

The scripts create a temporal holdout by patient and use grouped
`StratifiedGroupKFold` cross-validation within development data. Confirm the
exact split outputs after any trainer change. The holdout's rows are reduced to
an earliest eligible visit per patient for final evaluation. Existing artifacts
are loaded by the backend at process startup, from:

- `backend/models/stageN/stageN_xgboost_model.joblib`
- `backend/models/stageN/stageN_calibrator.joblib`
- `backend/models/stageN/stageN_feature_list.json`
- `backend/models/stageN/stageN_optimal_threshold.json`

Training also writes evaluation outputs; preserve existing model files and
compare new runs using explicit run metadata. Train an individual baseline with:

```powershell
python scripts/train_stage1_model.py
python scripts/train_stage2_model.py
python scripts/train_stage3_model.py
python scripts/train_stage4_model.py
```

Do not copy old metric numbers from superseded documentation into presentations
or UI. Metrics are valid only when tied to a reproducible run, the correct
dataset/target version, and a clearly identified split.

## 6. Planned MLP/ANN work

### Task and model design

Implement **one binary MLP per stage**, trained on the corresponding stage cohort
to estimate the same `Progression24m` target as that stage's XGBoost baseline.
Do not implement four-way diagnosis classification or reuse the retired
Current Status ANN's target, API contract, or label mapping.

Recommended first baseline architecture: numeric feature vector → dense
hidden layers (for example 128 and 64 units with ReLU and dropout) → one
sigmoid output. Keep the first experiment intentionally simple, seeded, and
documented. Architecture/hyperparameters may be adjusted only through a tracked
experiment; do not tune against the final test split.

### Leakage-safe and fair comparison requirements

1. Use the exact same cohort version, eligible rows, target, patient groups,
   temporal development/holdout patients, and evaluation units for both models.
2. Keep all visits for any one `PTID` on one side of every train/validation/test
   boundary. Add automated overlap assertions that fail on any patient leakage.
3. Preserve the existing patient-temporal holdout policy where feasible. Use the
   same holdout patients and same per-patient observation rule for XGBoost and
   MLP. Keep the final test patients untouched during tuning and threshold
   selection.
4. Within every training fold, fit numeric imputation and scaling only on that
   fold's training rows. Apply those fitted transforms to its validation rows.
   After model selection, fit the final preprocessing pipeline on development
   data only and apply it unchanged to the holdout. Serialize preprocessing and
   model together or persist versioned metadata that guarantees exact ordering.
5. Use the ordered feature list from the stage cohort/model contract. Exclude
   patient IDs, visit IDs/dates, future visits, diagnosis/target fields, and
   post-outcome fields. Fail loudly for missing, reordered, non-numeric, or
   unexpected columns instead of silently substituting features.
6. Account for the roughly 12% positive class using training-only weighting or a
   documented method. Do not oversample across patient boundaries. Report
   validation and test class counts; use PR-AUC as well as ROC-AUC.
7. Report at least ROC-AUC, PR-AUC, Brier score, sensitivity, specificity,
   precision, recall, F1, confusion matrix, calibration information, chosen
   threshold, patient counts, and feature ordering. Include uncertainty estimates
   where practical. Do not claim a winner from accuracy alone.
8. Compare model outputs on identical holdout patients. Do not silently replace
   XGBoost, blend scores, or choose a threshold from test results. Keep XGBoost
   available until the comparison is reviewed and a documented selection is
   made.

### Epoch policy and artifacts

The MLP does not exist yet, so it has **no actual epoch count or training result**.
Suggested initial training policy: maximum 200 epochs with early stopping
(patience 20) on development validation only. Store the actual best epoch,
seed, split identifiers, feature order, preprocessing parameters, package/model
versions, and metrics in each run's artifact metadata. State the actual epoch
count from the successful run, not the maximum configured cap.

Planned command shape (not available until the trainer is implemented):

```powershell
python scripts/train_stage_mlp_models.py --stage 1
```

The implementation should support selecting one stage and a reproducible
all-stage run. A planned artifact layout is
`backend/models/stageN_mlp/` and should include the model, fitted imputer/scaler,
ordered feature metadata, threshold/calibration metadata if used, and metrics.
Do not overwrite XGBoost artifacts.

### UI and API after model validation

Add a comparison view only after the MLP artifacts and endpoint are verified.
Show XGBoost and MLP as separate model outputs during research comparison, with
clear labels and data provenance. Any eventual selected-model presentation must
be supported by documented evaluation; never label a score as a diagnosis,
clinical risk determination, or treatment recommendation. Preserve the current
dashboard visual system.

## 7. Planned NeuroSight YOLO tumor feature

The external project is located at
`C:\Users\LOQ\OneDrive\Desktop\WEB DEV\NeuroSight AI\Brain-Tumor-Detection-YOLOv8`.
Its current local Nano and Medium weights were inspected as YOLOv8 detection
models with three tumor classes: `glioma`, `meningioma`, and `pituitary`. The
checkpoint does **not** provide a validated `no tumor` class.

Integration requirements:

- Keep tumor inference in a distinct route, UI view, model namespace, and result
  schema (for example, a future `/api/tumor/detect`). Do not call the model from
  an Alzheimer's stage screen.
- Keep the two existing source weights in NeuroSight. When the integration is
  approved, use explicit configurable paths or a separately documented local
  copy; do not change or overwrite the originals.
- Check Ultralytics licensing (including AGPL obligations or a suitable
  commercial license) and weight provenance before redistribution.
- Add file type/size/dimension checks, safe image decoding, clear errors, and
  authenticated upload handling. Do not accept arbitrary filesystem paths from
  the browser.
- Return only the model's actual class detections, confidence, and bounding-box
  information. An empty detection list means **no detections returned by this
  model**, not proof that no tumor exists. Never imply diagnosis.
- Do not invent test accuracy or training provenance. The available project
  directory did not contain a tumor training dataset/run that would validate
  the weights. Validate technical inference with authorized sample images, and
  obtain an appropriate labeled test dataset before making performance claims.
- Keep all Alzheimer's CSVs, Stage 1–4 XGBoost models, and tabular MRI/PET
  features intact.

The YOLO demo should be marked experimental/research-only and visually separate
from the four-stage progression workflow.

## 8. Local run and verification

Install backend dependencies from the project root:

```powershell
python -m pip install -r requirements.txt
```

Prepare data and, when needed, train the four existing XGBoost baselines using
the commands above. Run the backend from the project root:

```powershell
python -m uvicorn backend.app:app --reload --port 8000
```

Start the frontend in another terminal:

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

The local dashboard requires a workspace account; create it through the
application's signup flow and sign in. For a newly trained/replaced artifact,
stop and restart the backend because models load during application startup.
Check `GET /api/health` and `GET /api/triage/stages` for service and stage model
availability. Exercise the authenticated structured prediction endpoint with
valid request data; do not treat a successful HTTP response as evidence of
clinical validity.

Minimum checks for changes:

- Run the focused Python test suite covering stage prediction and data
  contracts.
- Run the frontend production build.
- Verify stage CSVs still exist and compare their filenames/sizes or checksums
  before/after destructive cleanup.
- Verify all four existing XGBoost stage artifact directories remain intact.
- Search the UI/API for any retired Alzheimer's MRI/PET image routes or
  Current Status ANN links.
- For MLP changes, test patient-level split disjointness and training-only
  preprocessing directly.
- For YOLO changes, test both weight variants, empty detections, invalid files,
  upload limits, and route isolation from Alzheimer's outputs.

## 9. Research, data, and deployment safeguards

- Use only data whose terms permit the intended educational/research use.
- Do not place real patient information into this local prototype. Its shared
  demo records and local account system are not a compliant clinical deployment.
- Keep tumor classifications and Alzheimer's progression scores separate.
- Do not describe exploratory results as validated, diagnostic, or
  treatment-ready. Do not fabricate labels, data, checkpoints, epochs, metrics,
  or patient records.
- Document every model's target, cohort version, split unit, preprocessing fit
  scope, feature order, training configuration, and artifact checksum.
- Before production or external distribution, complete appropriate privacy,
  security, licensing, clinical, and regulatory review.
