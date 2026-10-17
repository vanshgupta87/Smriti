# StepWise PRO: Precision Care Diagnostic Engine

> **Grand Finale Submission · Precision Care Challenge 2026**  
> Multimodal 4-Stage Gated Decision Support Architecture for Early Cognitive Decline & DMT Readiness.

---

## 👥 Core Engineering Team
- **Ashish Kumar** (`ashishkumartiwari2028@gmail.com`) — *Lead ML Engineer* (Stages 1-4 XGBoost, TreeSHAP, Platt Calibration)
- **Aditya Sharma** (`aadisharma.0285@gmail.com`) — *Computer Vision & Neuroimaging* (2.5D ResNet-18 Multi-Task MRI & PET Heads)
- **Sahil Raj Dubey** (`sahilrajdubey@gmail.com`) — *Systems & Backend Architect* (FastAPI Core, FHIR R4 Engine, CDS Hooks)
- **Vansh Gupta** (`vijaygupta0718@gmail.com`) — *Lead Frontend Engineer* (Next.js 14 Clinician Command Center, Dual DICOM Viewer)

---

## 🏥 Clinical Architecture & 4-Stage Funnel
1. **Stage 1 (Primary Care):** Non-invasive Cognitive Screening (`MMSE`, `MoCA`, `FAQ`, Vitals, Comorbidities) $\rightarrow$ 24-Month Rapid Progression Velocity Risk.
2. **Stage 2 (Phlebotomy):** 7-Assay Harmonized Biofluids ($p\text{-tau217}$, $A\beta_{42/40}$, $\text{NfL}$, $\text{GFAP}$) + `APOE-ε4` Genotyping.
3. **Stage 3 (Radiology):** 3D Volumetric MRI Morphometry (Hippocampal/ICV ratio, Entorhinal thickness, White Matter Hyperintensities).
4. **Stage 4 (Molecular Imaging):** Amyloid Centiloids ($0-100\text{ CL}$), Meta-temporal Tau SUVR, ARIA Safety Profiler & DMT Authorization.

---

## 📊 Benchmark Summary Across All 4 Stages
| Modality & Stage | Model Architecture | Validation Metric | Clinical Gating Threshold |
| :--- | :--- | :--- | :--- |
| **Stage 1: Cognitive/EHR** | XGBoost + Platt Calibrator | **0.808 CV / 0.717 Holdout AUC** | $T_1 = 0.0737$ (Sens: 51%, Spec: 83%) |
| **Stage 2: Blood Biofluids**| 7-Assay Z-Score XGBoost | **0.815 CV / 0.696 Holdout AUC** | $T_2 = 0.0978$ (Sens: 50%, Spec: 86%) |
| **Stage 3: 3D Volumetric MRI**| Multi-Task 2.5D ResNet-18 | **0.9985 Macro AUC / 96.6% Acc**| Medial Temporal Atrophy Grade $\ge 2$ |
| **Stage 4: Molecular PET**  | Multi-Task 2.5D ResNet-18 | **0.9997 Macro AUC / 97.7% Acc**| Centiloids $\ge 25.0\text{ CL}$ (DMT Ready) |

## 🚀 Quickstart
```bash
# Backend (FastAPI)
cd backend && uvicorn app:app --reload --port 8000

# Frontend (Next.js 14)
cd frontend && npm install && npm run dev
```
