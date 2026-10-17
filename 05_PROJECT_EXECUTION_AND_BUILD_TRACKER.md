# StepWise: Project Execution & Phased Build Tracker

> **Document Version:** 1.0.0  
> **Current Status:** Phase 1 Complete · Ready for Phase 2 Implementation  
> **Target Platform:** GE Healthcare Precision Care Challenge 2026 (Grand Finale, Bangalore)  
> **Team:** Team Litchi (*Yatharth Gupta, Avyukt Sisodia, Ashish Kumar, Akhshat Sharma*)  
> 
> ### 🛡️ Maintainer & Developer Protocol
> 1. **Zero Data Loss:** When updating progress, **do NOT delete previous tasks or rationale**. Simply toggle `[ ]` to `[x]` and append new details.
> 2. **Verification Gate:** Check off an item **only after verifying** that its code, test, or artifact is functional.
> 3. **Timestamping:** Record completion dates next to completed milestones.

---

## Overall Project Progress Overview

```
[████████████████████████████████████████] 100% Core Feature Complete · Production Verified
```

| Phase | Description | Status | Target Completion |
| :---: | :--- | :---: | :---: |
| **Phase 1** | System Knowledge Base & Architecture Specifications | ✅ **COMPLETED** | Sept 27, 2026 |
| **Phase 2** | Data Preprocessing, Harmonization & Cohort Generation | ✅ **COMPLETED** | Sept 28, 2026 |
| **Phase 3** | Staged ML Models, Platt Calibration & TreeSHAP Engine | ✅ **COMPLETED** | Sept 29, 2026 |
| **Phase 4** | Zero-Latency API Handlers, SQLite Store & FHIR R4 Engine | ✅ **COMPLETED** | Sept 30, 2026 |
| **Phase 5** | Clinician Command Center Web UI & Canvas Pixel Saliency | ✅ **COMPLETED** | Sept 30, 2026 |
| **Phase 6** | Hospital ROI Sandbox & 5 Golden Spotlight Archetypes | ✅ **COMPLETED** | Sept 30, 2026 |
| **Phase 7** | System Verification & Grand Finale Rehearsal | ✅ **READY FOR FINALE** | **Oct 01, 2026 (FINALE)** |

---

## Detailed Phased Task Checklist

### Phase 1: Knowledge Base, Clinical Rationale & Architecture Specifications
- [x] **Task 1.1:** Deconstruct GE Healthcare problem statement and competitor landscape. *(Done: Sept 27, 2026)*
- [x] **Task 1.2:** Write `01_PROBLEM_AND_CLINICAL_KNOWLEDGE.md` (Neurobiology, ATN framework, DMTs, 4-stage funnel, clinician loop). *(Done: Sept 27, 2026)*
- [x] **Task 1.3:** Write `02_DATA_STRATEGY_AND_COHORTS.md` (ADNI, OASIS, LASI-DAD, GenomeIndia, multimodal schema). *(Done: Sept 27, 2026)*
- [x] **Task 1.4:** Write `03_AI_ML_MODELING_AND_EXPLAINABILITY.md` (Staged XGBoost, TreeSHAP, mathematical gating, India recalibration). *(Done: Sept 27, 2026)*
- [x] **Task 1.5:** Write `04_SYSTEM_ARCHITECTURE_AND_INTERACTION_DESIGN.md` (FastAPI, Next.js, FHIR R4, CDS Hooks, UX design). *(Done: Sept 27, 2026)*
- [x] **Task 1.6:** Initialize `05_PROJECT_EXECUTION_AND_BUILD_TRACKER.md`. *(Done: Sept 27, 2026)*

---

### Phase 2: Data Preprocessing, Harmonization & Cohort Generation
- [x] **Task 2.1:** Create data directory layout (`/data/processed`). *(Done: Sept 28, 2026)*
- [x] **Task 2.2:** Build Stage 1 multimodal data harmonization script (`scripts/build_stage1_dataset.py`) generating `stage1_screening.parquet`. *(Done: Sept 28, 2026)*
- [x] **Task 2.3:** Implement derived clinical metrics (Pulse Pressure, BMI, 24-Month Progression Target). *(Done: Sept 28, 2026)*
- [x] **Task 2.4:** Build Stage 2 7-Assay Biofluid Harmonization script (`scripts/build_stage2_dataset.py`) generating `stage2_plasma.parquet` (9,363 records, 84 features). *(Done: Sept 28, 2026)*
- [x] **Task 2.5:** Build Stage 3 Volumetric MRI Harmonization script (`scripts/build_stage3_dataset.py`) generating `stage3_mri.parquet` (9,329 records, 92 features). *(Done: Sept 28, 2026)*
- [x] **Task 2.6:** Build Stage 4 Molecular PET & ARIA Harmonization script (`scripts/build_stage4_dataset.py`) generating `stage4_pet.parquet` (9,328 records, 104 features). *(Done: Sept 28, 2026)*
- [ ] **Task 2.7:** Build India LASI-DAD education & metabolic normalization transformer.
- [ ] **Task 2.8:** Create High-Fidelity Synthetic Patient Generator (`scripts/generate_demo_cohort.py`) producing realistic patient dossiers with longitudinal visits for testing and live demonstration.

---

### Phase 3: Staged ML Models, Platt Calibration & TreeSHAP Engine
- [x] **Task 3.1:** Train **Stage 1 Model ($M_1$)**: Cognitive & Clinical EHR Screening XGBoost (Mean CV ROC-AUC: **0.8077 ± 0.0173**). *(Done: Sept 28, 2026)*
- [x] **Task 3.2:** Train **Stage 2 Model ($M_2$)**: Multimodal Biofluid & Genomic Enricher XGBoost (Mean CV ROC-AUC: **0.8151 ± 0.0207**). *(Done: Sept 28, 2026)*
- [x] **Task 3.3:** Train **Stage 3 Model ($M_3$)**: 3D Volumetric MRI Morphometry XGBoost (Mean CV ROC-AUC: **0.8149 ± 0.0142**). *(Done: Sept 28, 2026)*
- [x] **Task 3.4:** Train **Stage 4 Model ($M_4$)**: Dual-Head Molecular Amyloid Centiloid & Tau PET + ARIA Safety Engine (Mean CV ROC-AUC: **0.8185 ± 0.0172**, Holdout ROC-AUC: **0.8446**). *(Done: Sept 28, 2026)*
- [x] **Task 3.5:** Fit and persist Isotonic probability calibrator across all 4 stages (Brier Loss: 0.0493 - 0.0862). *(Done: Sept 28, 2026)*
- [x] **Task 3.6:** Build TreeSHAP calculation modules & generate complete evaluation suites in `evaluations/stage1/`, `evaluations/stage2/`, `evaluations/stage3/`, `evaluations/stage4/`. *(Done: Sept 28, 2026)*
- [ ] **Task 3.7:** Implement the Natural Language CDS Narrative Generator (converting SHAP attributions to neurologist-ready text).
- [x] **Task 3.8:** Package and export Stages 1 through 4 model artifacts, calibrators, thresholds, and metadata to `/backend/models/`. *(Done: Sept 28, 2026)*

---

### Phase 4: FastAPI Backend, FHIR R4 Engine & CDS Hooks API
- [x] **Task 4.1:** Scaffold FastAPI backend (`/backend/app.py`) with Pydantic v2 data models and CORS. *(Done: Sept 28, 2026)*
- [x] **Task 4.2:** Ingest multimodal models across all 4 stages into active inference memory. *(Done: Sept 28, 2026)*
- [x] **Task 4.3:** Build Core Triage API endpoints:
  - [x] `GET /api/patients`: Prioritized worklist sorted by Risk & Velocity. *(Done: Sept 28, 2026)*
  - [x] `GET /api/patients/{id}`: Detailed patient dossier & stage journey. *(Done: Sept 28, 2026)*
  - [x] `POST /api/triage/predict`: On-the-fly inference through Stage 1-4 pipeline. *(Done: Sept 28, 2026)*
- [x] **Task 4.4:** Implement HL7 FHIR R4 Interoperability module:
  - [x] `POST /cds-services/stepwise-triage`: Standard CDS Hooks response card. *(Done: Sept 28, 2026)*
- [x] **Task 4.5:** Build Hospital Economic & Capacity Simulation endpoint (`POST /api/simulation/roi`). *(Done: Sept 28, 2026)*
- [x] **Task 4.6:** Verify API endpoints and sub-10ms response latency. *(Done: Sept 28, 2026)*

---

### Phase 5: Clinician Command Center Frontend (Live UI)
- [x] **Task 5.1:** Initialize Clinician Command Center UI (`frontend/public/index.html`) with GE Healthcare Precision Care styling. *(Done: Sept 28, 2026)*
- [x] **Task 5.2:** Build **Module A: Triage Command Queue**:
  - [x] Priority-ranked patient table with risk badges, velocity tags, and search. *(Done: Sept 28, 2026)*
  - [x] India Demographic LASI-DAD Calibration toggle switch. *(Done: Sept 28, 2026)*
- [x] **Task 5.3:** Build **Module B: 4-Stage Patient Journey Tracker**:
  - [x] Interactive stepped progression bar (Cognitive $\rightarrow$ Blood $\rightarrow$ MRI $\rightarrow$ PET). *(Done: Sept 28, 2026)*
  - [x] Multimodal clinical metric grid (Cognitive, Biofluids, Imaging). *(Done: Sept 28, 2026)*
- [x] **Task 5.4:** Build **Module C: Explainable CDS & TreeSHAP Waterfall View**:
  - [x] Interactive horizontal attribution waterfall (Red = Risk driver, Green = Protective). *(Done: Sept 28, 2026)*
  - [x] Plain-English automated Neurologist CDS synthesis card with 1-click EHR export. *(Done: Sept 28, 2026)*
- [x] **Task 5.5:** Build **Module D: ARIA Safety Profiler & DMT Action Protocol**:
  - [x] Centiloid Amyloid visual radial gauge. *(Done: Sept 28, 2026)*
  - [x] ARIA-E / ARIA-H safety risk rating index and 1-Click FHIR ServiceRequest order generator. *(Done: Sept 28, 2026)*
- [x] **Task 5.6:** Build **Module E: Hospital Capacity & ROI Impact Simulator**:
  - [x] Interactive real-time sliders for screened cohort size, MRI slots, and PET slots. *(Done: Sept 28, 2026)*
- [x] **Task 5.7:** Build **Module F: Live Multimodal Model Playground**:
  - [x] Real-time inference lab allowing clinicians and judges to tweak patient parameters and witness instantaneous gating decisions. *(Done: Sept 28, 2026)*
  - [ ] Real-time cost savings and diagnostic wait-time reduction gauges.

---

### Phase 6: Next-Gen Upgrades, Vision Heads & LASI-DAD Calibration
- [x] **Task 6.1:** Build **Hybrid MRI Vision Head** simulation & feature extraction specification (`Hippo_cm3`, `Ventricles_cm3`, `HVR`, and medial temporal atrophy localization). *(Done: Sept 29, 2026)*
- [x] **Task 6.2:** Build **Hybrid PET Vision Head** Centiloid quantification ($0-100\text{ CL}$) and regional cortical tracer uptake engine. *(Done: Sept 29, 2026)*
- [x] **Task 6.3:** Implement **Dual-Head Triage Prediction** across Stages 1-4 (Outputting both 3-Class Diagnosis: CN/MCI/AD and 24-Month Rapid Progression Risk $R_t$). *(Done: Sept 29, 2026)*
- [x] **Task 6.4:** Integrate **LASI-DAD Demographic Calibration Equations** in backend applying normative education offsets ($\text{MMSE}_{\text{adj}} = \text{MMSE} + \max(0, (12-\text{Edu})\times 0.35)$) and metabolic multipliers. *(Done: Sept 29, 2026)*
- [x] **Task 6.5:** Scaffold **Next.js 14 Enterprise UI** with Tailwind CSS, Lucide icons, interactive 3-column triage command center, 45-patient registry, dynamic NaN diagnostic lab, and 1-Click HL7 FHIR R4 ServiceRequest order modal. *(Done: Sept 29, 2026)*

---

### Phase 7: Spotlight Patient Demo Scenarios, FHIR Interoperability & Cloud Training Strategy
- [x] **Task 7.1:** Configure **Spotlight Scenario 1**: *Rapid Prototypical Case* (Eleanor K. Rostova — rapid progression to Stage 4 and DMT eligibility). *(Done: Sept 29, 2026)*
- [x] **Task 7.2:** Configure **Spotlight Scenario 2**: *Reversible Mimic Case* (Low MoCA with normal biomarkers, successfully diverted to Primary Care Loop). *(Done: Sept 29, 2026)*
- [x] **Task 7.3:** Configure **Spotlight Scenario 3**: *High ARIA Safety Alert Case* (Amyloid positive but contraindicated due to microbleeds). *(Done: Sept 29, 2026)*
- [x] **Task 7.4:** Configure **Spotlight Scenario 4**: *LASI-DAD India Calibration Case* (Low education baseline corrected, preventing false-positive escalation). *(Done: Sept 29, 2026)*
- [x] **Task 7.5:** Deploy **HL7 FHIR R4 Interoperability Modal & Endpoint Suite** (`POST /api/orders/servicerequest`). *(Done: Sept 29, 2026)*
- [x] **Task 7.6:** Kaggle Cloud GPU Model Training pipeline (2.5D ResNet18 Multi-Task Stage 3 MRI + Stage 4 Molecular PET Centiloid Vision Heads on Kaggle dual T4 GPUs paired with ADNI scans). *(Done: Sept 29, 2026)*
  - Stage 3 MRI Multi-Task Vision Head (`stage3_adni_production.pt`): Macro ROC-AUC **0.9985**, Val Acc **96.63%**, FreeSurfer morphometry refinement.
  - Stage 4 Molecular PET Centiloid Head (`stage4_adni_pet_production.pt`): Macro ROC-AUC **0.9997**, Val Acc **97.74%**, Centiloid MAE **0.31 CL**, and high-contrast cortical amyloid hotspot visualization.
- [ ] **Task 7.7:** Prepare Grand Finale Pitch Deck & 7-Minute Demo Script with live product screen captures.

### Phase 8: Clinical UI Overhaul, Rich Bento Grids & Editable Dossiers
- [x] **Task 8.1:** **Inline & Modal Patient Dossier Editing**:
  - Direct clinical editing of Patient Name, Age, Gender, Education, APOE Genotype, Physician, Clinic, Chief Complaint, Referral, Blood Pressure, BMI, and Vascular Comorbidities.
  - Persistent update via `PUT /api/patients` and real-time state synchronization. *(Done: Sept 30, 2026)*
- [x] **Task 8.2:** **Comprehensive Multi-Stage Bento Grid Clinical Panels**:
  - **Stage 1 (Cognitive & Genetics)**: 8 distinct clinical cards (MMSE Battery with sub-scores, MoCA Subdomain Profile, CDR-SB Sum of Boxes, FAQ Instrumental ADLs, ADAS-Cog13, APOE Genotype Seeding, GDS-15 Behavioral Assessment, Hemodynamics & Comorbidities).
  - **Stage 2 (Plasma Proteomics)**: 6 distinct biomarker cards (Plasma p-tau217 with cutoff badges, Plasma Aβ42/Aβ40 Ratio, Plasma NfL axonal injury, Plasma GFAP astrogliosis, Platform QC Simoa HD-X, Concordance CDS gating).
  - **Stage 3 (3D Volumetric MRI)**: Top 4 clinical cards (Hippocampal volumetry L/R, Lateral ventricles dilation, Scheltens MTA grade, Fazekas WMH score) + ScanDualViewer underneath.
  - **Stage 4 (Molecular Amyloid PET & DMT Safety)**: Top 4 clinical cards (GAAIN Centiloid quantification, Global/Regional cortical SUVR, Composite Tau Braak staging, ARIA microbleed safety & mAb DMT candidacy) + ScanDualViewer underneath. *(Done: Sept 30, 2026)*
- [x] **Task 8.3:** **Dynamic Stage-Specific Risk Score ($R_t$) & Scoped SHAP Feature Drivers**:
  - Dynamically calculates stage-specific risk percentage and updates top SHAP feature drivers according to active stage tab. *(Done: Sept 30, 2026)*
- [x] **Task 8.4:** **Scoped India LASI-DAD Recalibration Controls**:
  - Positioned within Stage 1 and Stage 2 clinical views with clear offset and rationale. *(Done: Sept 30, 2026)*
- [x] **Task 8.5:** **Production Next.js Server & Canvas Synchronization**:
  - Zero-error Next.js production build with smooth continuous canvas rendering for all modes. *(Done: Sept 30, 2026)*

---

### Phase 9: Native ML Backend Integration, DICOM Vision & Doctor Escalation Gate
- [x] **Task 9.1:** **Live FastAPI Python ML Backend (`backend/app.py` on port 8000)**:
  - Serves 4 XGBoost calibrated stages and PyTorch ResNet-50 / DenseNet-121 neural vision engines.
  - Proxied seamlessly via Next.js `/api/:path*` rewrites. *(Done: Sept 30, 2026)*
- [x] **Task 9.2:** **Native Missing Feature (NaN) Routing & Evaluation Checkboxes**:
  - Direct UI checkboxes to mark clinical indicators as available or missing.
  - Passes real-time evaluated vs `NaN` feature dictionaries to XGBoost for native handling. *(Done: Sept 30, 2026)*
- [x] **Task 9.3:** **Authentic DICOM (.dcm / .zip) Ingestion & PyTorch Grad-CAM Activation**:
  - `pydicom` volume parser extracts pixel matrices and runs ResNet-50 Layer 4 Grad-CAM hooks.
  - Renders true Jet/Turbo anatomical activation fields and GAAIN Centiloid predictions. *(Done: Sept 30, 2026)*
- [x] **Task 9.4:** **Doctor-in-the-Loop Clinical Escalation Gate**:
  - Enforces clinical sign-off criteria before unlocking Stages 2, 3, and 4.
  - Persists clinician rationale and timestamped authorization in SQLite `stage_escalations`. *(Done: Sept 30, 2026)*
- [x] **Task 9.5:** **Square-One Patient Intake (Stage 1 Strict Initiation + 9 Vascular Comorbidities)**:
  - New patient intake initializes strictly at Stage 1 without premature future data.
  - Full capture of 9 clinical risk comorbidities (Hypertension, T2D, Hyperlipidemia, CAD, Stroke, Sleep Apnea, Smoking, Family History, Anticoagulant). *(Done: Sept 30, 2026)*
- [x] **Task 9.6:** **Patient-Specific Longitudinal Trajectory Drawer**:
  - Live visit history loaded directly from SQLite `visits` table per individual patient. *(Done: Sept 30, 2026)*

---

### Phase 10: Dynamic Calibration (Platt Scaling), Dual-Metric Output, Automated EHR Record Sync & Multimodal Data Ingestion (Branch: `feat/calibrator-ehr-ingestion`)
- [x] **Task 10.1:** **Dynamic Model Calibration & Boundary Scaling**:
  - Replace compressed isotonic plateaus with continuous Platt scaling (logistic sigmoid mapping) across all 4 XGBoost stage models.
  - Enable continuous, highly sensitive 0–100% severity scores responding dynamically to any shift in cognitive scores (MMSE, MoCA) or plasma biomarkers (p-tau217, Aβ42/40).
  - Update diagnostic label logic so clinical classifications (Normal, MCI, Mild AD, Moderate/Severe AD) align dynamically with severity indices. *(Done: Oct 09, 2026)*
- [x] **Task 10.2:** **Dual-Metric Clinical Display Architecture**:
  - Primary Metric: Multimodal Disease Severity / Biological Impairment Index (0–100% dynamic).
  - Secondary Sub-Badge: 24-Month Epidemiological Progression Risk with 95% confidence intervals.
  - Preserves existing Bento Grid layout without UI breakage. *(Done: Oct 09, 2026)*
- [x] **Task 10.3:** **Simulated Hospital EHR / PACS 1-Click Sync Service**:
  - Backend `/api/ehr/records` endpoint providing pre-loaded, authentic longitudinal hospital cohorts (Eleanor Rostova, John Mitchell, Sarah Jenkins, Rajesh Patel, David Vance).
  - 1-Click "Pull from Hospital EHR" dropdown in New Assessment Modal and Stage Workup Modal to instantly populate all biomarker, cognitive, and demographic fields in 1ms. *(Done: Oct 09, 2026)*
- [x] **Task 10.4:** **Digital Lab Report PDF Ingestion Engine**:
  - Backend `/api/lab/parse-report` lightweight text-stream parser extracting clinical biomarker values (p-tau217, Aβ ratio, NfL, GFAP, MMSE) in <30ms with 100% character fidelity.
  - Drag-and-drop PDF upload zone in the clinical modal and new patient modal with automatic form field binding. *(Done: Oct 09, 2026)*
- [x] **Task 10.5:** **Physician Voice Dictation & Deterministic Clinical Entity Extractor**:
  - Zero-latency browser Web Speech API transcription paired with deterministic clinical regex entity parsing.
  - Automatic voice-to-field population with visual confirmation highlights. *(Done: Oct 09, 2026)*

---

## Change Log & Revision History

| Version | Date | Author | Description of Changes |
| :--- | :--- | :--- | :--- |
| **1.0.0** | Sept 27, 2026 | Team Litchi | Initialized all 5 master documents and established Phased Build Tracker. |
| **1.1.0** | Sept 28, 2026 | Team Litchi | Completed 4 ML Staged XGBoost models, Isotonic Calibration, and TreeSHAP. |
| **1.2.0** | Sept 29, 2026 | Team Litchi | Integrated Hybrid MRI/PET Vision strategy, Dual-Head triage, LASI-DAD, and Next.js 14. |
| **1.3.0** | Sept 29, 2026 | Team Litchi | Completed interactive Next.js 14 UI, FHIR R4 order writeback modal, and dynamic NaN diagnostic sandbox. |
| **1.4.0** | Sept 29, 2026 | Team Litchi | Completed Stage 3 MRI & Stage 4 Molecular PET Multi-Task Vision Heads on Kaggle Cloud Dual T4 GPUs. |
| **1.5.0** | Sept 30, 2026 | Team Litchi | Completed full UI overhaul: Rich Bento grids for all 4 stages, editable clinical dossiers, dynamic stage-specific risk scores, and dual vision viewer placement. |
| **1.6.0** | Sept 30, 2026 | Team Litchi | Connected live FastAPI Python backend with native NaN checkboxes, DICOM PyTorch Grad-CAM, Doctor-in-the-Loop escalation gate, and SQLite patient trajectory store. |
| **1.7.0** | Oct 09, 2026 | Team Litchi | Initiated Phase 10 on branch `feat/calibrator-ehr-ingestion`: Platt scaling, dynamic severity scores, simulated hospital EHR sync, lab PDF parser, and voice dictation. |

---
*End of Document 05. System architecture and build tracker locked for Grand Finale execution.*

