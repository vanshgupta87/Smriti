# StepWise: System Architecture, Full-Stack Stack & Interaction Design

> **Document Version:** 1.0.0  
> **Last Updated:** September 2026  
> **Target Platform:** GE Healthcare Precision Care Challenge 2026 (Grand Finale, Bangalore)  
> **Team:** Team Litchi (*Yatharth Gupta, Avyukt Sisodia, Ashish Kumar, Akhshat Sharma*)  
> **Maintainer Protocol:** This is a permanent living document. When modifying API endpoints, UI components, or data models, **update endpoint contracts and wireframes**.

---

## Table of Contents
1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Technology Stack & Architectural Decisions](#2-technology-stack--architectural-decisions)
   - [Backend: FastAPI (Python 3.11+)](#backend-fastapi-python-311)
   - [Frontend: Next.js 14 / React with Tailwind CSS & Lucide Icons](#frontend-nextjs-14--react-with-tailwind-css--lucide-icons)
   - [Persistence Layer & FHIR Object Store](#persistence-layer--fhir-object-store)
   - [Inference & Explainability Engine](#inference--explainability-engine)
3. [User Experience & Clinical Interface Design Philosophy](#3-user-experience--clinical-interface-design-philosophy)
   - [Core Visual Design Language (Clinical High-Trust)](#core-visual-design-language-clinical-high-trust)
   - [Key Dashboard Modules](#key-dashboard-modules)
     - [Module A: The Prioritized Triage Command Queue](#module-a-the-prioritized-triage-command-queue)
     - [Module B: Patient 4-Stage Progressive Journey Tracker](#module-b-patient-4-stage-progressive-journey-tracker)
     - [Module C: Explainable CDS & TreeSHAP Decomposition Panel](#module-c-explainable-cds--treeshap-decomposition-panel)
     - [Module D: ARIA Safety Profiling & DMT Readiness Badge](#module-d-aria-safety-profiling--dmt-readiness-badge)
     - [Module E: Hospital Capacity & Health-Economic ROI Simulator](#module-e-hospital-capacity--health-economic-roi-simulator)
4. [Healthcare Interoperability: HL7 FHIR R4 & CDS Hooks](#4-healthcare-interoperability-hl7-fhir-r4--cds-hooks)
   - [FHIR R4 Schema Mapping](#fhir-r4-schema-mapping)
   - [CDS Hooks Implementation (`patient-view` & `order-select`)](#cds-hooks-implementation-patient-view--order-select)
   - [FHIR `ServiceRequest` 1-Click Order Writeback Flow](#fhir-servicerequest-1-click-order-writeback-flow)
5. [Dynamic Hospital Simulation Engine](#5-dynamic-hospital-simulation-engine)
   - [Realistic Cohort Data Generator](#realistic-cohort-data-generator)
   - [Live Scenario Testing (Rapid Declinor vs. Stable Healthy vs. High-ARIA Case)](#live-scenario-testing-rapid-declinor-vs-stable-healthy-vs-high-aria-case)
6. [API Specifications & Data Contracts](#6-api-specifications--data-contracts)

---

## 1. High-Level System Architecture

StepWise is architected as an **enterprise-ready, SMART on FHIR compliant Clinical Decision Support System (CDSS)** that sits seamlessly on top of existing Hospital Information Systems (HIS), EHRs, and PACS networks:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          STEPWISE SYSTEM TOPOLOGY                                      │
└────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                         CLINICIAN INTERFACE (WEB)                            │
    │  Next.js 14 / React / Tailwind CSS / Radix UI / Recharts / Lucide Icons      │
    │  ┌───────────────────────┬─────────────────────────┬──────────────────────┐  │
    │  │ Triage Command Queue  │ 4-Stage Journey Tracker │ SHAP XAI Waterfall   │  │
    │  ├───────────────────────┼─────────────────────────┼──────────────────────┤  │
    │  │ ARIA Safety Profiler  │ 1-Click Order Writeback │ ROI Capacity Sandbox │  │
    │  └───────────────────────┴─────────────────────────┴──────────────────────┘  │
    └──────────────────────────────────────┬───────────────────────────────────────┘
                                           │ HTTPS / REST / JSON
                                           ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                         STEPWISE FASTAPI BACKEND                             │
    │  ┌────────────────────────────────────────────────────────────────────────┐  │
    │  │ REST API & CDS Hooks Dispatcher (`/api/v1/triage`, `/cds-services`)    │  │
    │  ├────────────────────────────────────────────────────────────────────────┤  │
    │  │ AI Inference & Gating Engine (XGBoost Stages 1-4 + Platt Calibration)  │  │
    │  ├────────────────────────────────────────────────────────────────────────┤  │
    │  │ TreeSHAP Calculation & Clinical Narrative Formatter                    │  │
    │  ├────────────────────────────────────────────────────────────────────────┤  │
    │  │ India Calibration Transformer (LASI-DAD Education & Comorbidity Offset)│  │
    │  ├────────────────────────────────────────────────────────────────────────┤  │
    │  │ Hospital Capacity & Economic Simulation Engine                         │  │
    │  └────────────────────────────────────────────────────────────────────────┘  │
    └───────────────────────┬───────────────────────────────┬──────────────────────┘
                            │                               │
                            ▼                               ▼
    ┌──────────────────────────────────────┐  ┌────────────────────────────────────┐
    │         DATA & PERSISTENCE           │  │      FHIR R4 INTEROPERABILITY      │
    │  • SQLite / SQLAlchemy Patient Store │  │  • FHIR Bundle Converter           │
    │  • ADNI / OASIS Harmonized Parquet   │  │  • Patient, Observation, Condition │
    │  • Model Weights & Scalers (.joblib) │  │  • ServiceRequest Writeback Mock   │
    └──────────────────────────────────────┘  └────────────────────────────────────┘
```

---

## 2. Technology Stack & Architectural Decisions

| Layer | Technology Selected | Rationale for Selection |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI (Python 3.11+)** | Asynchronous, ultra-low latency ($<5\text{ms}$), native OpenAPI/Swagger documentation, seamless integration with scikit-learn, XGBoost, and SHAP libraries. |
| **Data Validation** | **Pydantic v2** | Strict type enforcement, zero runtime overhead data parsing, automatic serialization of FHIR JSON payloads. |
| **ML & XAI Engine** | **XGBoost, Scikit-learn, SHAP** | Gold-standard for tabular clinical modeling, polynomial-time TreeSHAP calculations, high portability via `.joblib`. |
| **Frontend Framework** | **Next.js 14 / React 18** | Server-side rendering (SSR), high responsiveness, clean component modularity, instant hot-reloading. |
| **Styling & UI Library** | **Tailwind CSS + Radix UI + Lucide** | Clean, modern clinical aesthetic; accessible components (dialogs, tooltips, tabs, dropdowns); lightweight Lucide icons. |
| **Visualizations** | **Recharts & Tremor** | Interactive, beautifully styled clinical risk curves, SHAP waterfalls, longitudinal cognitive timelines, and capacity gauge charts. |
| **Storage Layer** | **SQLite + SQLAlchemy ORM** | Lightweight, self-contained, zero-configuration persistence for demo reproducibility; effortlessly migrates to PostgreSQL for production. |
| **Interoperability** | **HL7 FHIR R4 Specification** | Standard healthcare data schema for patient observations and diagnostic test requisitions. |

---

## 3. User Experience & Clinical Interface Design Philosophy

### Core Visual Design Language (Clinical High-Trust)
* **Aesthetic Standard:** Sleek, modern, and uncluttered. Dark slate sidebar navigation (`bg-slate-900`), crisp white card canvas (`bg-white`), subtle neutral borders (`border-slate-200`), and semantic clinical badges:
  * 🔴 **Critical / Rapid Declinor:** Crimson (`bg-rose-50 text-rose-700 border-rose-200`)
  * 🟠 **High Priority Escalation:** Amber (`bg-amber-50 text-amber-700 border-amber-200`)
  * 🟡 **Moderate / Watchful Monitoring:** Yellow (`bg-yellow-50 text-yellow-700 border-yellow-200`)
  * 🟢 **Low Risk / Stable Primary Care:** Emerald (`bg-emerald-50 text-emerald-700 border-emerald-200`)

### Key Dashboard Modules

#### Module A: The Prioritized Triage Command Queue
* **Role:** The primary landing screen for neurologists and memory clinic triage coordinators.
* **Features:**
  * Displays all screened patients ranked dynamically by **Prioritization Score** and **Cognitive Velocity ($\Delta \text{MoCA}/\text{yr}$)**.
  * Search & Filter bar by Stage (Stage 1 to Stage 4), Risk Band, and Care Facility.
  * "One-Click Review" button launching the full patient deep-dive modal.

#### Module B: Patient 4-Stage Progressive Journey Tracker
* **Role:** Interactive stepper bar visualizing the patient's exact progression through the diagnostic funnel.
* **Visual Elements:**
  * **Stage 1 (Cognitive):** Completed $\checkmark$ (MoCA: 22, MMSE: 24, CDR-SB: 1.5).
  * **Stage 2 (Plasma):** Completed $\checkmark$ (p-tau217: $0.28\text{ pg/mL}$, $A\beta_{42/40}$: $0.078$).
  * **Stage 3 (MRI Volumetry):** Current Active Stage ⏳ (Hippocampal Volume: $2800\text{ mm}^3$, MTLA Grade 2).
  * **Stage 4 (PET & Safety):** Recommended Next Step (Pending Clinician Approval).

#### Module C: Explainable CDS & TreeSHAP Decomposition Panel
* **Role:** Eradicates the "black-box" dilemma for physicians.
* **Visual Elements:**
  * **Horizontal SHAP Waterfall Bar Chart:** Visually separates positive risk drivers (red/amber) from protective factors (green).
  * **Automated Clinical CDS Summary Box:** Clear natural language synthesis of findings.

#### Module D: ARIA Safety Profiling & DMT Readiness Badge
* **Role:** Dedicated panel for Stage 4 patients evaluated for Leqembi/Donanemab eligibility.
* **Visual Elements:**
  * **Centiloid Meter:** Visual gauge showing Amyloid PET level (e.g., $48 \text{ CL} \rightarrow \text{Amyloid Positive}$).
  * **Microbleed Risk Tag:** SWI microbleed count ($0-3 \rightarrow \text{Favorable}$ vs $\ge 4 \rightarrow \text{Severe ARIA Warning}$).
  * **APOE Genotype Indicator:** Displays allele pairing ($\varepsilon3/\varepsilon4$ vs $\varepsilon4/\varepsilon4$).

#### Module E: Hospital Capacity & Health-Economic ROI Simulator
* **Role:** Executive-level operational analytics tool for hospital administrators and GE Healthcare adjudicators.
* **Interactive Sliders:**
  * Annual Screened Patient Cohort Size ($500 - 10,000$).
  * MRI Scanner Capacity & Amyloid-PET Availability.
* **Live KPI Counters:**
  * 💰 Total Diagnostic Cost Saved (\$ / ₹).
  * ⏱️ Average Days Reduced to Confirmed Diagnosis.
  * 📉 Unnecessary High-Cost PET Scans Prevented (%).

---

## 4. Healthcare Interoperability: HL7 FHIR R4 & CDS Hooks

### FHIR R4 Schema Mapping
StepWise exposes standard FHIR resources:
* **`Patient` Resource:** Demographics, identifier, birthdate, gender.
* **`Observation` Resource:** MoCA score (LOINC `72106-8`), Plasma p-tau217 (LOINC `98254-6`), Hippocampal volume, Centiloid PET.
* **`Condition` Resource:** Mild Cognitive Impairment (ICD-10 `G31.84`), Alzheimer's Disease (ICD-10 `G30.9`).
* **`ServiceRequest` Resource:** Diagnostic order requisition generated upon clinician approval.

### CDS Hooks Implementation (`patient-view` & `order-select`)
StepWise implements the standard CDS Hooks protocol (`/cds-services/stepwise-triage`):
```json
{
  "hook": "patient-view",
  "hookInstance": "d78d2824-de5f-49ce",
  "context": {
    "userId": "Practitioner/neurologist-01",
    "patientId": "Patient/adni-1042"
  },
  "prefetch": {
    "patient": { "resourceType": "Patient", "id": "adni-1042" },
    "observations": { "resourceType": "Bundle" }
  }
}
```
**Response Card Returned:**
```json
{
  "cards": [
    {
      "summary": "High Risk of Rapid AD Progression (StepWise Score: 0.86)",
      "indicator": "critical",
      "detail": "Patient exhibits rapid MoCA decline (-4.2 pts/yr) and elevated plasma p-tau217 (0.28 pg/mL). Escalation to 3D Volumetric Brain MRI strongly recommended.",
      "source": { "label": "StepWise CDSS", "url": "https://stepwise.health" },
      "suggestions": [
        {
          "label": "Order 3D Volumetric Brain MRI",
          "actions": [
            {
              "type": "create",
              "description": "Create FHIR ServiceRequest for Volumetric MRI",
              "resource": {
                "resourceType": "ServiceRequest",
                "status": "draft",
                "intent": "order",
                "code": { "coding": [{ "system": "http://loinc.org", "code": "RAD-MRI-BRAIN", "display": "3D Volumetric Brain MRI" }] }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### FHIR `ServiceRequest` 1-Click Order Writeback Flow
When the clinician clicks **"Approve & Order Next Test"**:
1. Frontend calls `POST /api/v1/orders/create`.
2. Backend creates a validated FHIR R4 `ServiceRequest` payload.
3. System writes back to EHR / PACS worklist, eliminating manual re-entry.

---

## 5. Dynamic Hospital Simulation Engine

### Realistic Cohort Data Generator
To provide an unforgettable live demo in Bangalore, StepWise includes a **High-Fidelity Synthetic Patient Generator** seeded with authentic ADNI/LASI-DAD distributions:
* **Cohort of 50 Realistic Patients** spanning all 4 clinical stages.
* **Pre-configured Spotlight Patients for Demo Walkthrough:**
  1. *Patient A (Rapid Prototypical Case):* Age 72, rapid MoCA decline, p-tau217 elevated, hippocampal atrophy, candidate for Vizamyl PET.
  2. *Patient B (Reversible Mimic / Non-Escalated):* Age 64, low MoCA due to severe untreated sleep apnea + B12 deficiency; low p-tau217; successfully diverted from expensive PET to primary care loop.
  3. *Patient C (High ARIA Safety Alert):* Age 78, ApoE4/4 homozygote, Amyloid positive, but has 6 microbleeds on SWI; system flags **ARIA Contradiction** warning.
  4. *Patient D (LASI-DAD India Calibration Case):* Age 68, 4 years education, low raw MoCA (19) recalibrated to normal range, avoiding false-positive escalation.

---

## 6. API Specifications & Data Contracts

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/patients` | Retrieves prioritized triage patient worklist with risk bands and filters. |
| `GET` | `/api/v1/patients/{id}` | Retrieves complete clinical dossier, 4-stage feature values, and visit history. |
| `POST` | `/api/v1/triage/evaluate` | Evaluates raw patient data through the 4-stage pipeline and returns risk scores. |
| `GET` | `/api/v1/explain/{id}` | Generates TreeSHAP waterfall values and automated clinical narrative. |
| `POST` | `/api/v1/orders/servicerequest` | Writes back an approved FHIR R4 `ServiceRequest` order. |
| `POST` | `/cds-services/stepwise-triage` | HL7 CDS Hooks standard endpoint for EHR embedding. |
| `GET` | `/api/v1/simulation/roi-metrics` | Computes dynamic hospital cost, time, and PET capacity savings. |

---
*End of Document 04. Proceed to [05_PROJECT_EXECUTION_AND_BUILD_TRACKER.md](./05_PROJECT_EXECUTION_AND_BUILD_TRACKER.md).*
