# Smriti Implementation & Progress Log

Track all tasks, progress, and remaining items for the 4-Stage MLP progression models and NeuroSight YOLOv8 brain tumor transfer.

---

## 1. Environment & Setup
- [x] Audit Python runtime environment (torch 2.5.1+cu121, xgboost 3.2.0, sklearn 1.9.0)
- [x] Add ultralytics to Python dependencies for YOLOv8 tumor detection (ultralytics 8.3.250 verified)
- [x] Verify data processing and parquet files (`backend/data/processed/stage{1..4}_cohort.parquet`)

---

## 2. 4-Stage MLP Progression Models (Progression24m)
- [x] **Data Pipeline & Target Audit**:
  - [x] Audit Stage 1–4 cohort CSVs / parquets (`stage1_cohort.parquet` to `stage4_cohort.parquet`)
  - [x] Confirm leakage-safe patient isolation (PTID 75/25 temporal grouping across train/dev and holdout splits)
  - [x] Ensure preprocessors (`SimpleImputer(keep_empty_features=True)` + `StandardScaler`) fit strictly on train folds
- [x] **MLP Model Architecture & Training Script**:
  - [x] Create `scripts/train_stage_mlp_models.py` supporting `--stage {1,2,3,4,all}`
  - [x] Implement PyTorch binary classification MLP: `Linear(128) -> BatchNorm -> ReLU -> Dropout(0.3) -> Linear(64) -> BatchNorm -> ReLU -> Dropout(0.2) -> Linear(1)`
  - [x] Implement class-weight handling in BCEWithLogitsLoss for ~12% positive progression rate
  - [x] Implement early stopping and evaluation tracking (ROC-AUC, PR-AUC, Brier score, Sensitivity, Specificity, Confusion Matrix, Top-k prioritization queues)
- [x] **Model Training & Artifact Generation**:
  - [x] Train Stage 1 MLP & save to `backend/models/stage1_mlp/` (CV AUC: 0.7949 ± 0.0133 | Holdout AUC: 0.6565 | Threshold: 0.2240)
  - [x] Train Stage 2 MLP & save to `backend/models/stage2_mlp/` (CV AUC: 0.8104 ± 0.0221 | Holdout AUC: 0.6727 | Threshold: 0.2286)
  - [x] Train Stage 3 MLP & save to `backend/models/stage3_mlp/` (CV AUC: 0.8111 ± 0.0104 | Holdout AUC: 0.6999 | Threshold: 0.3071)
  - [x] Train Stage 4 MLP & save to `backend/models/stage4_mlp/` (CV AUC: 0.8087 ± 0.0147 | Holdout AUC: 0.6712 | Threshold: 0.0765)
  - [x] Retain XGBoost artifacts and record fair comparison metrics on identical test holdouts
- [x] **Backend Serving for MLPs**:
  - [x] Update `backend/app.py` to load and serve MLP models alongside XGBoost at startup
  - [x] Update `/api/triage/stages` to report MLP loaded status, thresholds, and validation metrics
  - [x] Update `/api/triage/predict` to compute dual-inference: calibrated XGBoost risk + PyTorch MLP risk with threshold-based escalation
- [x] **Frontend MLP Comparison View**:
  - [x] Add dual-model comparative card in stage workups (`frontend/src/app/dashboard/page.tsx` Bento grid) showing XGBoost vs MLP side-by-side with risk %, optimal decision thresholds, architecture details, and research notices

---

## 3. NeuroSight YOLOv8 Brain Tumor Demonstration Integration
- [x] **Model Weights & Path Configuration**:
  - [x] Located source weights `yolov8n.pt` (6.2MB) and `yolov8m.pt` (52MB) from NeuroSight AI
  - [x] Copied and organized into `backend/models/tumor_yolo/`
- [x] **Backend Tumor Detection Service & Route**:
  - [x] Implemented safe image decoding (PIL RGB conversion), file validation (ext, size <= 10MB, dimensions 32x32 to 4096x4096)
  - [x] Built isolated endpoint `POST /api/tumor/detect?model_variant={nano|medium}&conf_threshold={float}` returning class (glioma, meningioma, pituitary), confidence %, bounding boxes [x1, y1, x2, y2, width, height]
  - [x] Ensured complete decoupling from Alzheimer's stages with clear research-only notices
- [x] **Frontend Brain Tumor Demo UI**:
  - [x] Added `tumor` tab (`NeuroSight YOLO`) to main navigation sidebar and header title
  - [x] Implemented `TumorDetectionView` React component in `frontend/src/app/dashboard/page.tsx`:
    - Drag & drop or file upload for MRI/CT scans
    - Model variant selector toggle (`YOLOv8-Nano` vs `YOLOv8-Medium`)
    - Interactive detection card stream with class badges, confidence %, and box coordinates
    - Full GE Healthcare research-only disclaimer banner

---

## 4. Testing & Verification
- [x] Run backend automated tests (`python -m unittest discover tests`): 8/8 tests pass (100% pass rate)
  - Calibrated XGBoost stages 1-4 tests
  - PyTorch MLP stage predictions & thresholding tests
  - YOLOv8 image upload, format validation, and inference tests
- [x] Verify frontend build (`npm run build` in `frontend/`): Next.js 14 compilation & type checking succeed with code 0
- [x] Document final results and updates in `log.md` and walkthrough

---

## 5. Virtual Environment, Database & Service Launcher Fixes
- [x] **Virtual Environment Resolution**:
  - Identified `ModuleNotFoundError: No module named 'torch'` caused by `include-system-site-packages = false` in `.venv311\pyvenv.cfg` and `.venv\pyvenv.cfg`.
  - Configured `include-system-site-packages = true` in both `.venv311` and `.venv` so virtual environments inherit CUDA GPU-accelerated `torch 2.5.1+cu121`, `torchvision`, and `ultralytics 8.4.188` from the system Python.
  - Added `torch>=2.2.0` and `ultralytics>=8.0.0` explicitly to `requirements.txt`.
- [x] **Database Schema & Patient Cohort Correction**:
  - Fixed database seeding bug in `backend/database.py` where `p.get("currentStage")` and `p.get("riskScore")` caused all 50 patients to be reset to `current_stage = 1` and `risk_score = 0.5`.
  - Added table migrations for `stage1_json`, `stage2_json`, `stage3_json`, `stage4_json`, `status`, `stage_name`, and `cds_recommendation_json`.
  - Re-synchronized SQLite cohort: correctly distributed into Stage 1 (9), Stage 2 (16), Stage 3 (9), Stage 4 (16), total 135 visits and 41 escalations.
- [x] **Frontend / Backend Launch Scripts**:
  - Resolved `ECONNREFUSED 127.0.0.1:8000` by ensuring backend starts seamlessly before frontend requests `/api/auth/status`.
  - Added npm scripts to root `package.json`: `npm run backend`, `npm run frontend`, `npm run dev:all` (via concurrently).
  - Created Windows one-click batch scripts: `run_backend.bat`, `run_frontend.bat`, `run_all.bat`.
  - Created PowerShell launch script: `start_dev.ps1`.

---

## 6. Landing Page Brain Tumor AI Alignment
- [x] **Header Navigation**: Added direct link to `#tumor-detection` (`Brain Tumor AI`).
- [x] **Hero Section**: Elevated copy to highlight multi-stage progression + NeuroSight YOLOv8 brain tumor detection.
- [x] **Platform Signals Orbit**: Updated imaging signals to highlight structural MRI + intracranial tumor screening.
- [x] **Dedicated NeuroSight AI Section (Section 03)**:
  - Added interactive 4-card grid detailing the 3 target tumor classes:
    - 🔴 **Glioma** (Infiltrative glial neoplasms)
    - 🟡 **Meningioma** (Dural-based extra-axial mass lesions)
    - 🟣 **Pituitary** (Sellar and parasellar adenomas)
    - 🔵 **Dual Architecture** (YOLOv8-Nano for fast triage, YOLOv8-Medium for sensitivity)
  - Added workspace demonstration callout linking directly to the interactive tumor workspace.
  - Added educational/research disclaimer banner preserving clinical governance.
- [x] **Capabilities Section (Section 04)**: Added capability 05 for NeuroSight YOLOv8 tumor detection.
- [x] **Verified Compilation**: `npm run build` compiled with 0 errors across all routes.



---

## 5. Telemedicine & Patient Video Calling System
- [x] **Patient Selection & Calling Workflow**:
  - [x] Replaced generic room code generation with a full **Patient Teleconsultation Hub** in the clinician dashboard.
  - [x] Doctors can browse the real patient feed with live search (name/MRN/complaint) and stage filters (Stages 1-4).
  - [x] Doctor selects any patient to configure consultation agenda and clinician notes.
  - [x] Added direct "Video Call Patient" button in the **Patient Dossier View** to launch calls directly from a patient chart.
- [x] **Automatic Email Invitation & 1-Click Link Dispatch**:
  - [x] Backend endpoint POST /api/telemedicine/invite-patient automatically creates a secure consultation room and dispatches a clinical HTML email.
  - [x] Supports live SMTP (via SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD) with automatic simulated fallback for offline demos.
  - [x] Interactive modal displays the dispatched patient email preview with a 1-click **Open Patient Link (Simulate)** button.
- [x] **Patient-Facing Video Consultation Portal (/consultation)**:
  - [x] Dedicated Next.js patient page at /consultation?room=... requiring zero doctor/hospital login.
  - [x] Patient camera/mic self-preview and hardware checks before joining.
  - [x] Welcomes patient with attending doctor's name, consultation topic, and clinical notes.
  - [x] End-to-end WebRTC video/audio peer connection directly with the doctor.
- [x] **Doctor Live Consultation Room & Docked Patient Chart**:
  - [x] Doctor screen immediately enters live video call with local camera & mic.
  - [x] Real-time docked patient chart on right panel showing current stage, progression risk, baseline vitals, and multi-stage biomarkers.
  - [x] Full in-call chat, mic/cam mute toggles, and fullscreen mode.
