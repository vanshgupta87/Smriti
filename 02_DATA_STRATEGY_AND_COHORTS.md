# StepWise: Data Strategy, Cohorts & Multimodal Feature Schema

> **Document Version:** 3.0.0  
> **Last Updated:** September 28, 2026  
> **Target Platform:** GE Healthcare Precision Care Challenge 2026 (Grand Finale, Bangalore - Oct 1, 2026)  
> **Team:** Team Litchi (*Yatharth Gupta, Avyukt Sisodia, Ashish Kumar, Akhshat Sharma*)  
> **Maintainer Protocol:** This is a permanent living document. When modifying schemas or data sources, **append revision notes and preserve data dictionaries**.

---

## Table of Contents
1. [Data Repositories & Master Multi-Platform Inventory](#1-data-repositories--master-multi-platform-inventory)
   - [ADNI Core Laboratories Breakdown](#adni-core-laboratories-breakdown)
   - [The 7 Multi-Platform Biofluid Assays](#the-7-multi-platform-biofluid-assays)
   - [Master Data Dictionary Cryptographic Verification](#master-data-dictionary-cryptographic-verification)
2. [Multimodal 4-Stage Feature Blueprint & Placement Rationale](#2-multimodal-4-stage-feature-blueprint--placement-rationale)
   - [The APOE-ε4 Clinical Placement Strategy (Stage 1 vs. Stage 2)](#the-apoe-ε4-clinical-placement-strategy-stage-1-vs-stage-2)
   - [Stage 1: Cognitive Screening & Clinical EHR Feature Schema (50 Features + Engineered Interactions)](#stage-1-cognitive-screening--clinical-ehr-feature-schema-50-features--engineered-interactions)
   - [Stage 2: Plasma Fluid Biomarker & Genotypic Schema (7-Assay Harmonization)](#stage-2-plasma-fluid-biomarker--genotypic-schema-7-assay-harmonization)
   - [Stage 3: Volumetric MRI Morphometry Schema](#stage-3-volumetric-mri-morphometry-schema)
   - [Stage 4: Amyloid / Tau PET & ARIA Safety Schema](#stage-4-amyloid--tau-pet--aria-safety-schema)
3. [Cohort Linkage, Keys & Ground Truth Target Formulation](#3-cohort-linkage-keys--ground-truth-target-formulation)
   - [Primary Linking Composite Keys (`RID`, `PTID`, `VISCODE2`)](#primary-linking-composite-keys-rid-ptid-viscode2)
   - [The 24-Month Clinical Progression Horizon (`Progression24m`)](#the-24-month-clinical-progression-horizon-progression24m)
   - [Why Progression Prediction Outperforms Static Diagnosis Classification](#why-progression-prediction-outperforms-static-diagnosis-classification)
4. [Indian Demographic & Genomic Adaptation Strategy](#4-indian-demographic--genomic-adaptation-strategy)
   - [Education & Literacy Adjustment Offsets](#education--literacy-adjustment-offsets)
   - [Cardiometabolic Burden Recalibration](#cardiometabolic-burden-recalibration)
5. [Automated Data Preprocessing & Parquet Build Pipeline](#5-automated-data-preprocessing--parquet-build-pipeline)

---

## 1. Data Repositories & Master Multi-Platform Inventory

### ADNI Core Laboratories Breakdown
The raw study tables are sourced from official USC LONI ADNI Core Laboratories:
* **Clinical Assessment Core:** `MMSE`, `MOCA`, `CDR`, `FAQ`, `ADAS_COG`, `NPIQ`, `PTDEMOG`, `DXSUM`.
* **Medical History Core:** `MEDHIST`, `INITHEALTH`, `VITALS`, `RECCMEDS`.
* **Genetics Core:** `APOERES` (APOE $\varepsilon2, \varepsilon3, \varepsilon4$ allele counts).
* **Biofluid Biomarker Core (7 Multi-Platform Assays):**
  1. `C2N_PRECIVITYAD2_PLASMA`: C2N Mass-Spectrometry %p-tau217 ratio, $A\beta_{42/40}$, APS2 score.
  2. `UPENN_PLASMA_FUJIREBIO_QUANTERIX`: Fujirebio Lumipulse pT217, $A\beta_{42/40}$, Quanterix Simoa GFAP, NfL.
  3. `BLENNOWPLASMATAU`: Kaj Blennow lab plasma total-tau and p-tau181.
  4. `UPENNBIOMK_ROCHE_ELECSYS`: Roche Elecsys electrochemiluminescence $A\beta_{42/40}$, pTau181.
  5. `JANSSEN_PLASMA_P217_TAU`: Janssen dilution-corrected plasma p-tau217.
  6. `LILLY_PTAU217_MSD600`: Eli Lilly MSD600 plasma p-tau217 assay.
  7. `FNIHBC_BLOOD_BIOMARKER_TRAJECTORIES`: FNIH multi-assay longitudinal trajectory panel (17 target biomarkers).
* **MRI Neuroimaging Core:** `UCSDVOL` (derived subcortical volumes), `UCSFFSX7` (FreeSurfer 7 cortical thickness), `UCD_WMH` (White Matter Hyperintensities).
* **PET Molecular Imaging Core:** `UCBERKELEY_AMY_6MM` (Centiloid Amyloid PET SUVR), `UCBERKELEY_TAU_6MM` (AV-1451 Tau PET).

### Master Data Dictionary Cryptographic Verification
* All 24 `DATADIC_26Sep2026.csv` files across the subdirectories are verified byte-for-byte identical (MD5: `1ed66356ba8d5ae6cc0421b85a47ec55`).

---

## 2. Multimodal 4-Stage Feature Blueprint & Placement Rationale

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STEPWISE 4-STAGE GATED WORKFLOW                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [Stage 1: Primary Care / PHC]  ──▶ 100% Non-Invasive Intake (MMSE/MoCA, Vitals, Comorbidities, FAQ)
                                      │ (If prior ApoE in EHR, optional booster; missing handled natively)
                                      ▼ (Escalation Gate 1: R1 >= T1)
 [Stage 2: Phlebotomy Lab]      ──▶ Single Blood Draw: Multi-Platform Plasma p-tau217/Aβ + APOE-ε4
                                      │
                                      ▼ (Escalation Gate 2: R2 >= T2)
 [Stage 3: Radiology Suite]     ──▶ 3D Volumetric MRI (Hippocampal/ICV Ratio, Entorhinal Thickness, WMH)
                                      │
                                      ▼ (Escalation Gate 3: R3 >= T3)
 [Stage 4: Molecular PET]       ──▶ Amyloid PET Centiloids + Tau SUVR + ARIA Microbleed Safety
                                      │
                                      ▼
                        [Neurologist DMT Readiness Dossier]
```

### The APOE-ε4 Clinical Placement Strategy (Stage 1 vs. Stage 2)
* **Stage 1 (Primary Care):** Operates on 100% non-invasive intake. If historical APOE is present in the EHR, it acts as an optional risk booster; if absent, XGBoost routes it seamlessly.
* **Stage 2 (Laboratory):** When a patient is escalated from Stage 1, a **single phlebotomy blood draw** simultaneously extracts plasma for biofluid assays (p-tau217, $A\beta_{42/40}$) and buffy coat DNA for **APOE-$\varepsilon4$ genotyping**.

---

### Stage 1: Cognitive Screening & Clinical EHR Feature Schema (50 Features + Engineered Interactions)

| Feature Group | Features Extracted | Clinical Rationale |
| :--- | :--- | :--- |
| **Demographics** (4) | `AGE`, `PTGENDER`, `PTEDUCAT`, `PTMARRY` | Baseline unmodifiable covariates & cognitive reserve proxy. |
| **MMSE Subdomains** (6) | `MMSCORE`, `MMSE_Orientation`, `MMSE_Registration`, `MMSE_Attention`, `MMSE_Recall`, `MMSE_Language` | Classic bedside cognitive screening signature. |
| **MoCA Subdomains** (8) | `MOCA_Total`, `MoCA_Visuospatial`, `MoCA_Naming`, `MoCA_Attention`, `MoCA_Delayed_Recall`, `MoCA_Orientation` | Highly sensitive to early Mild Cognitive Impairment (MCI). |
| **CDR Sub-scores** (8) | `CDRSB`, `CDGLOBAL`, `CDMEMORY`, `CDORIENT`, `CDJUDGE`, `CDCOMMUN`, `CDHOME`, `CDCARE` | Gold-standard clinical staging anchor. |
| **Functional FAQ** (11) | `FAQTOTAL`, `FAQFINAN`, `FAQFORM`, `FAQSHOP`, `FAQGAME`, `FAQBEVG`, `FAQMEAL`, `FAQEVENT`, `FAQTV`, `FAQREM`, `FAQTRAVL` | Informant-reported loss in daily functional autonomy. |
| **Neuropsychiatric** (4) | `NPIQ_Total_Severity`, `NPID` (Depression), `NPIE` (Anxiety), `NPIC` (Agitation) | Earliest neuropsychiatric and behavioral flags of neurodegeneration. |
| **Vitals & Calculated** (5) | `VSBPSYS`, `VSBPDIA`, `Pulse_Pressure` ($\text{SYS}-\text{DIA}$), `BMI` ($\text{kg/m}^2$), `VSPULSE` | Arterial stiffness and systemic metabolic metrics. |
| **Medical Comorbidities** (6) | `MHPSYCH`, `MH2NEURL`, `MH4CARD` (Cardiac), `MH9ENDO` (Diabetes/Thyroid), `MH14ALCH`, `AD_Medical_Risk_Score` | Multipliers for cerebrovascular and metabolic cognitive burden. |
| **Engineered Interactions** (3) | `MoCA_Memory_Index` ($\frac{\text{Delayed Recall}}{\text{MoCA}+1}$), `Pulse_Pressure_Ratio` ($\frac{\text{PP}}{\text{SYS}}$), `Vascular_Cog_Risk` ($\text{PP} \times (30-\text{MMSE})$) | Clinical domain interactions boosting AUC. |

---

### Stage 2: Plasma Fluid Biomarker & Genotypic Schema (7-Assay Harmonization)

| Feature Name | Source Assays | Transformation | Clinical Role |
| :--- | :--- | :--- | :--- |
| `APOE4_Count` | `APOERES` | Discrete ($0, 1, 2$) | Major genetic susceptibility driver for sporadic AD. |
| `ptau217_harmonized_z` | C2N, Fujirebio, Janssen, Lilly | Per-Assay Z-Score | #1 validated blood biomarker for amyloid plaque deposition. |
| `abeta42_40_harmonized_z` | C2N, Fujirebio, Roche | Per-Assay Z-Score | Inverse amyloid ratio; drops as plaques sequester $A\beta_{42}$. |
| `gfap_harmonized_z` | Quanterix Simoa, Roche | Per-Assay Z-Score | Reactive astrogliosis and early neuroinflammatory cascade. |
| `nfl_harmonized_z` | Quanterix Simoa, Roche | Per-Assay Z-Score | Axonal breakdown rate; indicates ongoing structural injury. |
| `aps2_c2n_score` | C2N PrecivityAD2 | Continuous ($0 - 100$) | Commercial mass-spec Amyloid Probability Score. |
| `upenn_is_amyloid_pos` | Fujirebio Lumipulse | Binary ($A\beta_{42/40} \le 0.063$) | Clinical AT(N) biological threshold. |

---

### Stage 3: Volumetric MRI Morphometry Schema

| Feature Name | Source Table | Derivation | Clinical Rationale |
| :--- | :--- | :--- | :--- |
| `hippocampus_icv_ratio` | `UCSDVOL` | $\frac{\text{LHIPPOC} + \text{RHIPPOC}}{\text{EICV}} \times 1000$ | Medial Temporal Lobe Atrophy (MTLA) hallmark. |
| `entorhinal_thickness` | `UCSFFSX7` | Cortical thickness ($\text{mm}$) | First cortical region affected by Braak tau tangles. |
| `ventricular_icv_ratio` | `UCSDVOL` | $\frac{\text{VENTRICLES}}{\text{EICV}}$ | Ventricular enlargement reflects cerebral parenchymal volume loss. |
| `wmh_volume_cm3` | `UCD_WMH` | $\text{TOTAL\_WMH}$ ($\text{cm}^3$) | White matter hyperintensity volume (vascular dementia burden). |

---

### Stage 4: Amyloid / Tau PET & ARIA Safety Schema

| Feature Name | Source Table | Scale / Range | Clinical Rationale |
| :--- | :--- | :--- | :--- |
| `centiloids` | `UCBERKELEY_AMY` | $0 - 150 \text{ CL}$ | Standardized Amyloid PET scale ($>25\text{ CL} \implies \text{Positive}$). |
| `tau_meta_temporal_suvr` | `UCBERKELEY_TAU` | SUVR Ratio | Regional tau neurofibrillary tangle burden (Braak staging). |
| `microbleed_count` | `UCD_WMH` / Clinical | Integer ($0 - 25$) | $\ge 4$ microbleeds triggers **High ARIA-H Contradiction Alert**. |
| `aria_composite_risk` | Composite | Low / Mod / High | Integrates APOE-$\varepsilon4/\varepsilon4$ homozygosity + microbleed count. |

---

## 3. Cohort Linkage, Keys & Ground Truth Target Formulation

### Primary Linking Composite Keys
* **`PTID`:** Unique Patient Identifier across all study visits.
* **`VISCODE2`:** Standardized longitudinal milestone (`bl`, `m06`, `m12`, `m24`, `m36`, `m48`, `m60`).

### The 24-Month Clinical Progression Horizon (`Progression24m`)
$$\text{Progression24m}^{(i, t)} = \begin{cases} 1 & \text{if } \max_{t < t' \le t+24\text{mo}} \left(\text{DIAGNOSIS}(t')\right) > \text{DIAGNOSIS}(t) \\ 0 & \text{if followed } \ge 24 \text{ months without cognitive worsening} \end{cases}$$

### Why Progression Prediction Outperforms Static Diagnosis Classification
* **Static Classification (Flawed):** Merely guesses what is already written on the patient's chart today.
* **24-Month Progression (StepWise):** Identifies **rapid progressors**—patients currently diagnosed with mild symptoms who will deteriorate into dementia within 2 years unless escalated to disease-modifying intervention.

---

## 5. Persistent SQLite & CSV Production Data Architecture

StepWise PRO maintains a high-fidelity persistent SQLite database (`backend/data/stepwise.db`) synchronized with an auditable CSV cohort (`backend/data/stepwise_curated_cohort.csv`) and JSON store (`frontend/src/data/patients.json`).

### Database Relational Schema
```sql
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    mrn TEXT UNIQUE,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    dob TEXT,
    education_years INTEGER,
    handedness TEXT,
    apoe TEXT,
    apoe4_count INTEGER,
    referral TEXT,
    complaint TEXT,
    primary_doctor TEXT,
    clinic_location TEXT,
    current_stage INTEGER DEFAULT 1,
    risk_score REAL DEFAULT 0.5,
    velocity TEXT DEFAULT 'Moderate',
    status TEXT,
    vitals_json TEXT,
    med_history_json TEXT,
    stage1_json TEXT,
    stage2_json TEXT,
    stage3_json TEXT,
    stage4_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    visit_code TEXT NOT NULL, -- 'M00' (Baseline), 'M12' (Month 12), 'M24' (Month 24)
    visit_date TEXT,
    mmse REAL,
    moca REAL,
    ptau217 REAL,
    ab42_40 REAL,
    hippocampus_cm3 REAL,
    centiloids REAL,
    risk_score REAL,
    stage_dx TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

### The 5 "Golden Patient Archetypes" (Live Demonstration Targets)

1. **Rapid Converter (Early MCI $\rightarrow$ AD): Elena Rostova (71F, APOE $\varepsilon4/\varepsilon4$)**
   - *Key Biomarkers:* MMSE 23, MoCA 21, p-tau217 0.38 pg/mL, Hippocampus 3.12 cm³, Centiloids 88.5 CL.
   - *Clinical Action:* Full 4-stage escalation; confirms heavy cortical amyloid burden ($88.5\text{ CL}$) with 0 microbleeds, clearing patient for FDA/DCGI Lecanemab/Donanemab DMT therapy.

2. **"Worried Well" Rule-Out (Hospital Cost Saver): Arthur Pendelton (66M, APOE $\varepsilon3/\varepsilon3$)**
   - *Key Biomarkers:* MMSE 29, MoCA 28, p-tau217 0.08 pg/mL, Normal MRI.
   - *Clinical Action:* **STOPS AT STAGE 2**. Safely rules out Alzheimer's pathology without expensive PET/MRI, saving \$4,700 and eliminating waitlist backlog.

3. **Indian Demographic-Calibrated (LASI-DAD): Sunita Devi (64F, 4 yrs formal schooling)**
   - *Key Biomarkers:* Baseline MMSE $21 \rightarrow$ LASI-DAD Calibrated $23.2$, p-tau217 0.14 pg/mL.
   - *Clinical Action:* LASI-DAD literacy/socioeconomic adjustment (+2.2 pts) prevents false-positive dementia misdiagnosis.

4. **Borderline Gray Zone Patient: Clara Barton (68F, APOE $\varepsilon3/\varepsilon4$)**
   - *Key Biomarkers:* p-tau217 0.19 pg/mL (in intermediate gray zone [0.17–0.22]), MoCA 24.
   - *Clinical Action:* Escalates to Stage 3 Volumetric MRI to resolve ambiguity before ordering molecular PET.

5. **Vascular / Mixed Pathology: Rajesh K. Sharma (74M, High WMH)**
   - *Key Biomarkers:* p-tau217 0.16 pg/mL, Plasma NfL 42.6 pg/mL, Fazekas Grade 3 Confluent WMH, 6 Microbleeds.
   - *Clinical Action:* Routes to vascular stroke & memory care pathway; strictly contraindicates anti-amyloid mAbs due to high ARIA-H hemorrhage risk.

---

## 6. Longitudinal Revisit & Disease Velocity ($\Delta$) Protocol

### Clinical Justification: How Re-testing Works in Practice
In clinical memory centers (NIA-AA 2024 / Alzheimer's Association standard of care):
1. **Stage 1 (Cognitive Re-assessment):** Performed at every 6–12 month follow-up visit to measure $\Delta \text{MMSE}/\Delta t$ and functional decline.
2. **Stage 2 (Plasma Biomarker Re-draw):** Triggered if cognitive decline accelerates ($\Delta \text{MMSE} \le -1.5\text{ pts/yr}$) to assess annualized p-tau217 trajectory ($\sim +15-30\%/\text{yr}$ in converters).
3. **Stage 3 (Annual Volumetric MRI):** Monitored annually for hippocampal atrophy rate ($\text{mm}^3/\text{yr}$) and ARIA-H safety surveillance.
4. **Stage 4 (Post-DMT Amyloid PET Clearance):** Evaluated at 12–18 months under active monoclonal antibody therapy to verify Centiloid plaque reduction.

---
*End of Document 02. Proceed to [03_AI_ML_MODELING_AND_EXPLAINABILITY.md](./03_AI_ML_MODELING_AND_EXPLAINABILITY.md).*

