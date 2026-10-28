#!/usr/bin/env python3
#ML part from line 300 starts
"""
Smriti: Enterprise FastAPI Clinical Decision Support Engine v3.0
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import joblib
import torch
import torch.nn as nn
from PIL import Image
import io
import re
import base64
import cv2
from datetime import timedelta

from backend.lab_parser import (
    extract_text_from_pdf_bytes,
    parse_clinical_report_text
)
from backend.database import (
    init_db,
    fetch_all_patients_db,
    fetch_patient_by_id_db,
    insert_new_patient_db,
    add_visit_db,
    delete_visit_db,
    delete_escalation_db,
    update_visit_db,
    escalate_patient_stage_db,
    get_patient_timeline_db,
    get_analytics_db,
    get_db
)
from backend.auth_service import (
    InvalidCredentials,
    LoginRateLimited,
    WorkspaceAlreadyConfigured,
    authenticate,
    create_first_hospital_account,
    get_session_user,
    init_auth_db,
    revoke_session,
    workspace_is_configured,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
MODELS_DIR = BASE_DIR / "backend" / "models"

init_db()
init_auth_db()

app = FastAPI(
    title="Smriti Research Engine",
    description="Four-stage tabular progression research prototype; not for clinical use.",
    version="3.0.0"
)

SESSION_COOKIE_NAME = "smriti_session"
SESSION_COOKIE_SECURE = os.getenv("SMRITI_COOKIE_SECURE", "").lower() in {
    "1",
    "true",
    "yes",
}
AUTH_ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "SMRITI_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
}
import socket
try:
    _lan_ip = socket.gethostbyname(socket.gethostname())
    if _lan_ip and not _lan_ip.startswith("127."):
        AUTH_ALLOWED_ORIGINS.add(f"http://{_lan_ip}:3000")
        AUTH_ALLOWED_ORIGINS.add(f"http://{_lan_ip}:8000")
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(AUTH_ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_authenticated_hospital(request: Request, call_next):
    path = request.url.path
    is_auth_route = path.startswith("/api/auth/")
    is_health_route = path == "/api/health"
    is_public_telemed = path.startswith("/api/telemedicine/public/")

    if (
        path.startswith("/api/")
        and request.method not in {"GET", "HEAD", "OPTIONS"}
        and not is_public_telemed
    ):
        origin = request.headers.get("origin")
        if not origin or origin.rstrip("/") not in AUTH_ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "A trusted request origin is required."},
            )

    if path.startswith("/api/") and not is_auth_route and not is_health_route and not is_public_telemed:
        user = get_session_user(request.cookies.get(SESSION_COOKIE_NAME))
        if user is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Hospital sign-in is required."},
            )
        request.state.auth_user = user

    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(timedelta(hours=8).total_seconds()),
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="strict",
        path="/",
    )


class HospitalSignupRequest(BaseModel):
    organization: str = Field(..., min_length=2, max_length=160)
    full_name: str = Field(..., min_length=2, max_length=120)
    role: Literal["physician", "administrator", "researcher", "it", "other"]
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=12, max_length=256)

    @field_validator("organization", "full_name")
    @classmethod
    def validate_required_names(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Enter at least two characters.")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Enter a valid work email address.")
        return normalized


class HospitalLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


@app.get("/api/auth/status")
def auth_status(request: Request):
    return {
        "workspace_configured": workspace_is_configured(),
        "user": get_session_user(request.cookies.get(SESSION_COOKIE_NAME)),
    }


@app.post("/api/auth/signup", status_code=201)
def hospital_signup(payload: HospitalSignupRequest, response: Response):
    try:
        token, user = create_first_hospital_account(
            organization=payload.organization,
            full_name=payload.full_name,
            email=payload.email,
            role=payload.role,
            password=payload.password,
        )
    except WorkspaceAlreadyConfigured:
        raise HTTPException(
            status_code=409,
            detail=(
                "This installation already has a hospital workspace. "
                "Additional user invitations are not configured."
            ),
        )
    set_session_cookie(response, token)
    return {"user": user}


@app.post("/api/auth/login")
def hospital_login(
    payload: HospitalLoginRequest,
    request: Request,
    response: Response,
):
    client_ip = request.client.host if request.client else "unknown"
    try:
        token, user = authenticate(payload.email, payload.password, client_ip)
    except LoginRateLimited:
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in attempts. Try again in 15 minutes.",
            headers={"Retry-After": "900"},
        )
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    set_session_cookie(response, token)
    return {"user": user}


@app.get("/api/auth/me")
def hospital_session(request: Request):
    user = get_session_user(request.cookies.get(SESSION_COOKIE_NAME))
    if user is None:
        raise HTTPException(status_code=401, detail="Hospital sign-in is required.")
    return {"user": user}


@app.post("/api/auth/logout")
def hospital_logout(request: Request, response: Response):
    revoke_session(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"status": "signed_out"}


MODELS = {}
CALIBRATORS = {}
FEATURE_LISTS = {}
STAGE_THRESHOLDS = {}
STAGE_MODEL_ERRORS = {}

for stage_idx in [1, 2, 3, 4]:
    s_dir = MODELS_DIR / f"stage{stage_idx}"
    try:
        artifact_paths = {
            "model": s_dir / f"stage{stage_idx}_xgboost_model.joblib",
            "calibrator": s_dir / f"stage{stage_idx}_calibrator.joblib",
            "features": s_dir / f"stage{stage_idx}_feature_list.json",
            "threshold": s_dir / f"stage{stage_idx}_optimal_threshold.json",
        }
        missing_artifacts = [
            str(path) for path in artifact_paths.values() if not path.is_file()
        ]
        if missing_artifacts:
            raise FileNotFoundError(
                "Missing trained model artifacts: " + ", ".join(missing_artifacts)
            )

        model = joblib.load(artifact_paths["model"])
        calibrator = joblib.load(artifact_paths["calibrator"])
        with artifact_paths["features"].open(encoding="utf-8") as feature_file:
            feature_list = json.load(feature_file)
        with artifact_paths["threshold"].open(encoding="utf-8") as threshold_file:
            threshold_config = json.load(threshold_file)
        threshold = float(threshold_config["optimal_threshold"])
        if not isinstance(feature_list, list) or not feature_list:
            raise ValueError("Model feature list must be a non-empty array.")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Model decision threshold must be between 0 and 1.")

        MODELS[stage_idx] = model
        CALIBRATORS[stage_idx] = calibrator
        FEATURE_LISTS[stage_idx] = feature_list
        STAGE_THRESHOLDS[stage_idx] = threshold
        print(f"Loaded Stage {stage_idx} Calibrated Model ({len(feature_list)} features)")
    except Exception as e:
        STAGE_MODEL_ERRORS[stage_idx] = str(e)
        print(f"Warning: Failed to load Stage {stage_idx} model: {e}")

# =====================================================================
# STAGE 1-4 MLP DEEP LEARNING MODELS
# =====================================================================

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

MLP_MODELS = {}
MLP_PREPROCESSORS = {}
MLP_THRESHOLDS = {}
MLP_METRICS = {}
MLP_MODEL_ERRORS = {}

for stage_idx in [1, 2, 3, 4]:
    s_mlp_dir = MODELS_DIR / f"stage{stage_idx}_mlp"
    try:
        model_path = s_mlp_dir / f"stage{stage_idx}_mlp_model.pt"
        prep_path = s_mlp_dir / f"stage{stage_idx}_preprocessor.joblib"
        thresh_path = s_mlp_dir / f"stage{stage_idx}_optimal_threshold.json"
        metrics_path = s_mlp_dir / f"stage{stage_idx}_mlp_metrics.json"

        if not (model_path.is_file() and prep_path.is_file() and thresh_path.is_file()):
            raise FileNotFoundError(f"Missing MLP artifacts for stage {stage_idx}")

        with thresh_path.open(encoding="utf-8") as f:
            t_data = json.load(f)
        threshold = float(t_data.get("optimal_threshold", 0.5))

        preprocessor = joblib.load(prep_path)
        feature_count = len(FEATURE_LISTS.get(stage_idx, []))
        if feature_count == 0:
            feat_file = s_mlp_dir / f"stage{stage_idx}_feature_list.json"
            if feat_file.is_file():
                with feat_file.open(encoding="utf-8") as f:
                    feature_count = len(json.load(f))

        mlp = ProgressionMLP(in_features=feature_count)
        mlp.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
        mlp.eval()

        metrics = {}
        if metrics_path.is_file():
            with metrics_path.open(encoding="utf-8") as f:
                metrics = json.load(f)

        MLP_MODELS[stage_idx] = mlp
        MLP_PREPROCESSORS[stage_idx] = preprocessor
        MLP_THRESHOLDS[stage_idx] = threshold
        MLP_METRICS[stage_idx] = metrics
        print(f"Loaded Stage {stage_idx} MLP Model ({feature_count} features, threshold={threshold:.4f})")
    except Exception as e:
        MLP_MODEL_ERRORS[stage_idx] = str(e)
        print(f"Warning: Failed to load Stage {stage_idx} MLP model: {e}")

# =====================================================================
#  YOLOV8 BRAIN TUMOR DETECTION MODELS
# =====================================================================

TUMOR_MODELS = {}
TUMOR_MODEL_ERRORS = {}
try:
    from ultralytics import YOLO
    tumor_dir = MODELS_DIR / "tumor_yolo"
    for variant in ["yolov8n.pt", "yolov8m.pt"]:
        w_path = tumor_dir / variant
        if w_path.is_file():
            v_name = "nano" if "n" in variant else "medium"
            TUMOR_MODELS[v_name] = YOLO(str(w_path))
            print(f"Loaded NeuroSight YOLOv8 {v_name.capitalize()} Tumor Detector")
        else:
            print(f"YOLO tumor weight not found: {w_path}")
except Exception as e:
    TUMOR_MODEL_ERRORS["load_error"] = str(e)
    print(f"Warning: Could not initialize YOLO tumor models: {e}")

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class CognitiveInput(BaseModel):
    mmse: Optional[float] = Field(None, ge=0, le=30)
    moca: Optional[float] = Field(None, ge=0, le=30)
    cdrsb: Optional[float] = Field(None, ge=0, le=18)
    faq: Optional[float] = Field(None, ge=0, le=30)
    adas13: Optional[float] = Field(None, ge=0, le=85)
    gds: Optional[float] = Field(None, ge=0, le=15)
    age: Optional[float] = Field(None, ge=18, le=120)
    gender: Optional[str] = Field(None)
    education_years: Optional[float] = Field(None, ge=0, le=40)
    has_diabetes: Optional[bool] = Field(None)
    has_hypertension: Optional[bool] = Field(None)


class DynamicTriageRequest(BaseModel):
    patient_id: Optional[str] = "DEMO-CASE-01"
    stage: int = Field(1, ge=1, le=4)
    cognitive: CognitiveInput
    apoe4_count: Optional[int] = Field(None, ge=0, le=2)
    plasma_ptau217_z: Optional[float] = Field(None, ge=-20, le=20)
    plasma_ab42_40_z: Optional[float] = Field(None, ge=-20, le=20)
    plasma_nfl_z: Optional[float] = Field(None, ge=-20, le=20)
    plasma_gfap_z: Optional[float] = Field(None, ge=-20, le=20)
    hippocampus_icv_ratio: Optional[float] = Field(None, ge=0, le=100)
    hippocampus_cm3: Optional[float] = Field(None, ge=0, le=20)
    ventricles_cm3: Optional[float] = Field(None, ge=0, le=500)
    icv_cm3: Optional[float] = Field(None, gt=0, le=3000)
    ventricles_icv_ratio: Optional[float] = Field(None, ge=0, le=1)
    wmh_volume_cm3: Optional[float] = Field(None, ge=0, le=500)
    mta_grade: Optional[str] = Field(None)
    centiloids: Optional[float] = Field(None, ge=-100, le=500)
    tau_suvr: Optional[float] = Field(None, ge=0, le=10)
    microbleeds: Optional[int] = Field(None, ge=0)
    apply_india_calibration: bool = Field(False)
    save_to_patient: bool = Field(False)


class EscalationRequest(BaseModel):
    to_stage: int = Field(...)
    doctor_name: str = Field("Dr. Kenneth Adams, MD")
    clinical_rationale: str = Field("Risk threshold exceeded. Clinician authorized progression to next diagnostic tier.")
    escalation_decision: str = Field("escalate", description="escalate | routine | more_data")
    doctor_notes: str = Field("")


class SaveStageRequest(BaseModel):
    stage_number: int
    visit_date: Optional[str] = None
    visit_code: Optional[str] = None
    mmse: Optional[float] = None
    moca: Optional[float] = None
    cdrsb: Optional[float] = None
    faq: Optional[float] = None
    adas13: Optional[float] = None
    gds: Optional[float] = None
    ptau217: Optional[float] = None
    ab42_40: Optional[float] = None
    nfl: Optional[float] = None
    gfap: Optional[float] = None
    hippocampus_cm3: Optional[float] = None
    ventricles_cm3: Optional[float] = None
    mta_grade: Optional[str] = None
    centiloids: Optional[float] = None
    tau_suvr: Optional[float] = None
    microbleeds: Optional[int] = None
    risk_score: Optional[float] = None
    stage_dx: Optional[str] = None
    stage_assessment_json: Optional[Dict[str, Any]] = None
    doctor_notes: Optional[str] = None
    escalation_decision: Optional[str] = None
    current_stage: Optional[int] = None


class SimulationRequest(BaseModel):
    annual_screened_patients: int = Field(5000)
    mri_weekly_capacity: int = Field(40)
    pet_weekly_capacity: int = Field(15)
    mri_cost_usd: float = Field(750.0)
    pet_cost_usd: float = Field(3200.0)
    plasma_test_cost_usd: float = Field(250.0)


class ServiceRequestOrder(BaseModel):
    patient_id: str
    patient_name: str
    mrn: str
    target_modality: str = Field("MRI")
    clinical_rationale: str
    ordering_physician: str = "Dr. Kenneth Adams, MD (Neurology)"


# =====================================================================
# LASI-DAD INDIA RECALIBRATION
# =====================================================================

def apply_lasidad_calibration(feat_dict: Dict[str, Any], cog: CognitiveInput) -> Dict[str, Any]:
    edu = max(0.0, float(cog.education_years))
    if edu < 12.0:
        deficit = 12.0 - edu
        if feat_dict.get("MMSCORE") is not None and not np.isnan(feat_dict["MMSCORE"]):
            feat_dict["MMSCORE"] = min(30.0, feat_dict["MMSCORE"] + (deficit * 0.35))
        if feat_dict.get("MOCA_Total") is not None and not np.isnan(feat_dict["MOCA_Total"]):
            feat_dict["MOCA_Total"] = min(30.0, feat_dict["MOCA_Total"] + (deficit * 0.45))
    if cog.has_diabetes or cog.has_hypertension:
        if feat_dict.get("wmh_volume_cm3") is not None and not np.isnan(feat_dict["wmh_volume_cm3"]):
            feat_dict["wmh_volume_cm3"] = feat_dict["wmh_volume_cm3"] * 1.20
    return feat_dict


# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Smriti Research Engine",
        "loaded_stages": list(MODELS.keys()),
        "stage_models_active": len(MODELS),
        "mlp_stages_active": len(MLP_MODELS),
        "tumor_models_active": list(TUMOR_MODELS.keys()),
        "india_lasidad_active": False
    }


@app.get("/api/triage/stages")
def triage_stage_status():
    descriptions = {
        1: ("Cognitive and clinical progression model", "Clinical / cognitive data"),
        2: ("Blood biomarker progression model", "Clinical data and blood biomarkers"),
        3: ("MRI-derived feature progression model", "Clinical data and measured MRI features"),
        4: ("PET-derived feature progression model", "Clinical data and measured PET features"),
    }
    return {
        "stages": [
            {
                "stage": stage,
                "name": descriptions[stage][0],
                "required_inputs": descriptions[stage][1],
                "model_loaded": stage in MODELS,
                "calibrator_loaded": stage in CALIBRATORS,
                "threshold_loaded": stage in STAGE_THRESHOLDS,
                "mlp_loaded": stage in MLP_MODELS,
                "mlp_threshold_loaded": stage in MLP_THRESHOLDS,
                "mlp_metrics": MLP_METRICS.get(stage),
                "error": (
                    None if stage in MODELS else
                    "Trained stage artifacts are missing or failed validation. "
                    "Prepare the cohort, train this stage, and restart the backend."
                ),
            }
            for stage in range(1, 5)
        ],
        "tumor_models": {
            "loaded_variants": list(TUMOR_MODELS.keys()),
            "classes": ["glioma", "meningioma", "pituitary"] if TUMOR_MODELS else []
        },
        "clinical_use": (
            "Research prototype only; outputs are not diagnoses or clinical recommendations."
        ),
    }


# --- PATIENT CRUD ---

@app.get("/api/patients")
def get_patients(
    stage: Optional[int] = None,
    velocity: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "risk_score",
    order: str = "desc"
):
    results = fetch_all_patients_db(stage=stage, velocity=velocity, search=search)
    reverse = (order.lower() == "desc")
    key = "risk_score" if sort_by == "riskScore" else sort_by
    results = sorted(results, key=lambda x: x.get(key) or x.get("risk_score") or 0, reverse=reverse)
    return {"total": len(results), "patients": results}


@app.get("/api/patients/{patient_id}")
def get_patient_detail(patient_id: str):
    p = fetch_patient_by_id_db(patient_id)
    if p:
        return p
    raise HTTPException(status_code=404, detail="Patient not found")


@app.post("/api/patients")
def create_patient(patient_data: Dict[str, Any] = Body(...)):
    """Registers a new patient at pre-screening stage (stage 0). No clinical data yet."""
    try:
        new_p = insert_new_patient_db(patient_data)
        return {"status": "success", "patient": new_p}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/patients/{patient_id}")
def update_patient_detail(patient_id: str, payload: Dict[str, Any] = Body(...)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        field_map = {
            "name": "name", "age": "age", "gender": "gender",
            "education_years": "education_years", "apoe": "apoe",
            "referral": "referral", "complaint": "complaint",
            "patient_notes": "patient_notes",
            "primary_doctor": "primary_doctor", "clinic_location": "clinic_location"
        }
        for key, col in field_map.items():
            if key in payload:
                cursor.execute(f"UPDATE patients SET {col} = ? WHERE id = ? OR mrn = ?",
                               (payload[key], patient_id, patient_id))
        if "vitals" in payload:
            cursor.execute("UPDATE patients SET vitals_json = ? WHERE id = ? OR mrn = ?",
                           (json.dumps(payload["vitals"]), patient_id, patient_id))
        if "medical_history" in payload:
            cursor.execute("UPDATE patients SET med_history_json = ? WHERE id = ? OR mrn = ?",
                           (json.dumps(payload["medical_history"]), patient_id, patient_id))
        conn.commit()
        conn.close()
        return {"status": "success", "patient": fetch_patient_by_id_db(patient_id)}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stage_escalations WHERE patient_id = ?", (patient_id,))
    cursor.execute("DELETE FROM visits WHERE patient_id = ?", (patient_id,))
    cursor.execute("DELETE FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    conn.commit()
    conn.close()
    return {"status": "success", "deleted_id": patient_id}


# --- STAGE SAVE ---

@app.post("/api/patients/{patient_id}/save-stage")
def save_stage_assessment(patient_id: str, req: SaveStageRequest):
    """Save completed stage assessment results to DB (visits table)."""
    p = fetch_patient_by_id_db(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    visit_data = {
        "stage_number": req.stage_number,
        "visit_date": req.visit_date,
        "visit_code": req.visit_code,
        "mmse": req.mmse, "moca": req.moca, "cdrsb": req.cdrsb, "faq": req.faq,
        "adas13": req.adas13, "gds": req.gds,
        "ptau217": req.ptau217, "ab42_40": req.ab42_40,
        "nfl": req.nfl, "gfap": req.gfap,
        "hippocampus_cm3": req.hippocampus_cm3, "ventricles_cm3": req.ventricles_cm3,
        "mta_grade": req.mta_grade,
        "centiloids": req.centiloids, "tau_suvr": req.tau_suvr,
        "microbleeds": req.microbleeds,
        "risk_score": req.risk_score,
        "stage_dx": req.stage_dx or f"Stage {req.stage_number} Assessment",
        "stage_assessment_json": req.stage_assessment_json or {},
        "doctor_notes": req.doctor_notes or "",
        "escalation_decision": req.escalation_decision or "",
        "current_stage": req.current_stage,
    }

    # Update current_stage if newly entering a stage
    if req.current_stage and req.current_stage > (p.get("current_stage") or 0):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE patients SET current_stage = ? WHERE id = ?",
                       (req.current_stage, p["id"]))
        conn.commit()
        conn.close()

    updated = add_visit_db(p["id"], visit_data)
    return {"status": "success", "patient": updated}


# --- ESCALATION ---

@app.post("/api/patients/{patient_id}/escalate")
def escalate_patient(patient_id: str, req: EscalationRequest):
    """Doctor-in-the-Loop clinical escalation gate with 3-option decision."""
    updated = escalate_patient_stage_db(
        patient_id=patient_id,
        to_stage=req.to_stage,
        doctor_name=req.doctor_name,
        rationale=req.clinical_rationale,
        decision=req.escalation_decision
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {
        "status": "success",
        "escalation_decision": req.escalation_decision,
        "escalated_to_stage": req.to_stage,
        "patient": updated
    }


# --- REVISIT ---

@app.post("/api/patients/{patient_id}/revisit")
def start_revisit(patient_id: str, payload: Dict[str, Any] = Body(...)):
    """
    Starts a new revisit cycle. Creates a visit record marking the revisit date,
    and resets patient to stage 1 for fresh assessment.
    """
    p = fetch_patient_by_id_db(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    revisit_data = {
        "stage_number": 1,
        "visit_code": f"RV{payload.get('visit_label', 'R1')}",
        "visit_date": payload.get("visit_date"),
        "stage_dx": f"Revisit: {payload.get('reason', 'Follow-up assessment')}",
        "doctor_notes": payload.get("notes", ""),
        "escalation_decision": "revisit",
    }

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE patients SET current_stage = 1 WHERE id = ?", (p["id"],))
    conn.commit()
    conn.close()

    add_visit_db(p["id"], revisit_data)
    return {"status": "success", "message": "Revisit started", "patient": fetch_patient_by_id_db(patient_id)}


@app.delete("/api/patients/{patient_id}/visits/{visit_id}")
def delete_patient_visit(patient_id: str, visit_id: int):
    """Deletes a specific visit assessment and recalculates patient's latest stage/risk."""
    updated = delete_visit_db(patient_id, visit_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient or visit not found")
    return {"status": "success", "message": f"Visit {visit_id} deleted", "patient": updated}


@app.delete("/api/patients/{patient_id}/escalations/{escalation_id}")
def delete_patient_escalation(patient_id: str, escalation_id: int):
    """Deletes a specific stage escalation entry and recalculates patient's active stage."""
    updated = delete_escalation_db(patient_id, escalation_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient or escalation not found")
    return {"status": "success", "message": f"Escalation {escalation_id} deleted", "patient": updated}


@app.put("/api/patients/{patient_id}/visits/{visit_id}")
def update_patient_visit(patient_id: str, visit_id: int, payload: Dict[str, Any] = Body(...)):
    """Updates visit notes or metadata."""
    updated = update_visit_db(patient_id, visit_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient or visit not found")
    return {"status": "success", "message": f"Visit {visit_id} updated", "patient": updated}


@app.post("/api/patients/{patient_id}/lasidad")
def apply_lasidad_calibration(patient_id: str, payload: Dict[str, Any] = Body(...)):
    """
    Saves LASI-DAD (Longitudinal Aging Study in India - Diagnostic Assessment of Dementia)
    demographic, linguistic, and education-adjusted calibration to the patient profile.
    """
    p = fetch_patient_by_id_db(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    offset = payload.get("normative_offset", 0.0)
    edu_years = payload.get("education_years", p.get("education_years", 12))
    lang = payload.get("primary_language", "Hindi / Regional")
    ses = payload.get("ses_context", "Rural / Semi-urban Cohort")
    rationale = payload.get("notes", "")

    note_entry = f"[LASI-DAD Normative Calibration applied: +{offset:.1f} pts MoCA/HMSE adjustment | Edu: {edu_years}y | Lang: {lang} | SES: {ses}] {rationale}"

    conn = get_db()
    cursor = conn.cursor()
    curr_notes = p.get("patient_notes") or ""
    new_notes = f"{curr_notes}\n{note_entry}".strip()
    cursor.execute("UPDATE patients SET patient_notes = ?, education_years = ? WHERE id = ?",
                   (new_notes, int(edu_years), p["id"]))
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "normative_offset": offset,
        "education_years": edu_years,
        "patient": fetch_patient_by_id_db(patient_id)
    }


# --- TRAJECTORY / TIMELINE ---

@app.get("/api/patients/{patient_id}/trajectory")
def get_patient_trajectory(patient_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visits WHERE patient_id = ? ORDER BY created_at ASC, id ASC", (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return {
        "patient_id": patient_id,
        "total_visits": len(rows),
        "visits": [dict(r) for r in rows]
    }


@app.get("/api/patients/{patient_id}/timeline")
def get_patient_timeline(patient_id: str):
    """Returns ordered chronological event timeline for a patient."""
    timeline = get_patient_timeline_db(patient_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"patient_id": patient_id, "events": timeline}


# --- ANALYTICS ---

@app.get("/api/analytics")
def get_analytics():
    """Hospital-level aggregate analytics for dashboard and analytics view."""
    data = get_analytics_db()
    return data


# --- TRIAGE PREDICT ---

@app.post("/api/triage/predict")
def predict_triage(req: DynamicTriageRequest):
    if req.apply_india_calibration:
        raise HTTPException(
            status_code=422,
            detail="India-specific calibration is not validated or available for these models.",
        )
    stage = req.stage
    if stage not in MODELS:
        if stage not in range(1, 5):
            raise HTTPException(status_code=422, detail="stage must be between 1 and 4.")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Stage {stage} progression model is not available. "
                "Check GET /api/triage/stages for its status."
            ),
        )

    # If patient exists in DB, fetch historical data to backfill missing prior-stage features
    p_db = fetch_patient_by_id_db(req.patient_id) if req.patient_id else None
    s1_db = (p_db.get("stage1") if p_db else None) or {}
    s2_db = (p_db.get("stage2") if p_db else None) or {}
    s3_db = (p_db.get("stage3") if p_db else None) or {}
    s4_db = (p_db.get("stage4") if p_db else None) or {}

    feat_dict = {}
    
    # Missing measurements stay missing; do not fabricate a normal/default patient.
    age_val = req.cognitive.age if req.cognitive.age is not None else (p_db.get("age") if p_db else None)
    gender_str = req.cognitive.gender or (p_db.get("gender") if p_db else None)
    edu_val = req.cognitive.education_years if req.cognitive.education_years is not None else (p_db.get("education_years") if p_db else None)
    medical_history = (p_db.get("medical_history") if p_db else None) or {}

    feat_dict["AGE"] = float(age_val) if age_val is not None else np.nan
    gender = str(gender_str).lower() if gender_str else ""
    feat_dict["PTGENDER"] = 1.0 if gender == "female" else (0.0 if gender == "male" else np.nan)
    feat_dict["PTEDUCAT"] = float(edu_val) if edu_val is not None else np.nan
    feat_dict["PTMARRY"] = np.nan

    # Stage 1: Cognitive features (with historical backfill)
    mmse_val = req.cognitive.mmse if req.cognitive.mmse is not None else s1_db.get("mmse")
    moca_val = req.cognitive.moca if req.cognitive.moca is not None else s1_db.get("moca")
    cdrsb_val = req.cognitive.cdrsb if req.cognitive.cdrsb is not None else s1_db.get("cdrsb")
    faq_val = req.cognitive.faq if req.cognitive.faq is not None else s1_db.get("faq")
    adas_val = req.cognitive.adas13 if req.cognitive.adas13 is not None else s1_db.get("adas13")
    gds_val = req.cognitive.gds if req.cognitive.gds is not None else s1_db.get("gds")

    feat_dict["MMSCORE"] = float(mmse_val) if mmse_val is not None else np.nan
    feat_dict["MOCA_Total"] = float(moca_val) if moca_val is not None else np.nan
    feat_dict["CDRSB"] = float(cdrsb_val) if cdrsb_val is not None else np.nan
    feat_dict["FAQTOTAL"] = float(faq_val) if faq_val is not None else np.nan
    feat_dict["ADAS13"] = float(adas_val) if adas_val is not None else np.nan
    feat_dict["GDS"] = float(gds_val) if gds_val is not None else np.nan

    for feature_name in (
        "MMSE_Orientation", "MMSE_Recall", "MMSE_Attention", "MMSE_Language",
        "MoCA_Visuospatial", "MoCA_Naming", "MoCA_Attention",
        "MoCA_Delayed_Recall", "MoCA_Orientation", "CDGLOBAL", "CDMEMORY",
        "CDORIENT", "CDJUDGE", "CDCOMMUN", "CDHOME", "CDCARE", "FAQFINAN",
        "FAQFORM", "FAQSHOP", "FAQGAME", "FAQBEVG", "FAQMEAL", "FAQEVENT",
        "FAQTV", "FAQREM", "FAQTRAVL", "NPIQ_Total_Severity", "NPID", "NPIE",
        "NPIC", "VSBPSYS", "VSBPDIA", "Pulse_Pressure", "VSPULSE", "BMI",
        "MHPSYCH", "MH2NEURL", "MH14ALCH", "AD_Medical_Risk_Score",
    ):
        feat_dict[feature_name] = s1_db.get(feature_name.lower(), np.nan)
    feat_dict["MH4CARD"] = (
        float(req.cognitive.has_hypertension)
        if req.cognitive.has_hypertension is not None else
        float(bool(medical_history["hypertension"]))
        if "hypertension" in medical_history else np.nan
    )
    feat_dict["MH9ENDO"] = (
        float(req.cognitive.has_diabetes)
        if req.cognitive.has_diabetes is not None else
        float(bool(medical_history["diabetes"]))
        if "diabetes" in medical_history else np.nan
    )

    # Genetic APOE
    apoe_val = req.apoe4_count
    if apoe_val is None and p_db and p_db.get("apoe"):
        apoe_str = str(p_db.get("apoe"))
        apoe_val = 2 if "ε4/ε4" in apoe_str else (1 if "ε4" in apoe_str else 0)
    feat_dict["APOE4_Count"] = float(apoe_val) if apoe_val is not None else np.nan

    # Stage 2 training uses assay-standardized cohort z-scores. Raw laboratory
    # values cannot be converted without assay-specific normalization metadata.
    ptau_z = req.plasma_ptau217_z if req.plasma_ptau217_z is not None else s2_db.get("plasma_ptau217_z")
    ab42_40_z = req.plasma_ab42_40_z if req.plasma_ab42_40_z is not None else s2_db.get("plasma_ab42_40_z")
    nfl_z = req.plasma_nfl_z if req.plasma_nfl_z is not None else s2_db.get("plasma_nfl_z")
    gfap_z = req.plasma_gfap_z if req.plasma_gfap_z is not None else s2_db.get("plasma_gfap_z")
    for feature_name, value in (
        ("composite_ptau217_z", ptau_z),
        ("composite_abeta_ratio_z", ab42_40_z),
        ("upenn_NfL_Q_z", nfl_z),
        ("upenn_GFAP_Q_z", gfap_z),
    ):
        if value is not None:
            feat_dict[feature_name] = float(value)

    # Stage 3: Volumetric MRI Morphometry features
    hippo_cm3 = req.hippocampus_cm3 if req.hippocampus_cm3 is not None else s3_db.get("hippocampus_cm3", s3_db.get("hippoVol"))
    hippo_icv = req.hippocampus_icv_ratio if req.hippocampus_icv_ratio is not None else s3_db.get("hippocampus_icv_ratio")
    vent_cm3 = req.ventricles_cm3 if req.ventricles_cm3 is not None else s3_db.get("ventricles_cm3", s3_db.get("ventriclesVol"))
    icv_cm3 = req.icv_cm3 if req.icv_cm3 is not None else s3_db.get("icv_cm3")
    ventricles_icv_ratio = req.ventricles_icv_ratio if req.ventricles_icv_ratio is not None else s3_db.get("ventricles_icv_ratio")
    wmh_cm3 = req.wmh_volume_cm3 if req.wmh_volume_cm3 is not None else s3_db.get("wmh_volume_cm3")

    if hippo_cm3 is not None:
        feat_dict["hippocampus_total_vol"] = float(hippo_cm3) * 1000.0
    if hippo_icv is not None:
        ratio_value = float(hippo_icv)
        feat_dict["hippocampus_icv_ratio"] = (
            ratio_value * 1000.0 if abs(ratio_value) < 0.1 else ratio_value
        )
    elif hippo_cm3 is not None and icv_cm3 is not None and float(icv_cm3) > 0:
        feat_dict["hippocampus_icv_ratio"] = (
            float(hippo_cm3) / float(icv_cm3)
        ) * 1000.0
    if ventricles_icv_ratio is not None:
        feat_dict["ventricles_icv_ratio"] = float(ventricles_icv_ratio)
    elif vent_cm3 is not None and icv_cm3 is not None and float(icv_cm3) > 0:
        feat_dict["ventricles_icv_ratio"] = float(vent_cm3) / float(icv_cm3)
    for feature_name in ("wholebrain_icv_ratio", "entorhinal_avg_vol", "midtemp_avg_vol"):
        feat_dict[feature_name] = s3_db.get(feature_name, np.nan)

    if wmh_cm3 is not None:
        feat_dict["wmh_volume_cm3"] = float(wmh_cm3)
    feat_dict["wmh_tcv_ratio"] = s3_db.get("wmh_tcv_ratio", np.nan)

    # Stage 4: Molecular Amyloid PET features
    cent_val = req.centiloids if req.centiloids is not None else s4_db.get("centiloids")
    tau_suvr = req.tau_suvr if req.tau_suvr is not None else s4_db.get("tau_suvr", s4_db.get("suvr"))
    microbleeds_val = req.microbleeds if req.microbleeds is not None else s4_db.get("microbleeds", s4_db.get("microbleedsCount"))

    if cent_val is not None:
        c_f = float(cent_val)
        feat_dict["Amyloid_Centiloids"] = c_f
        feat_dict["Amyloid_Positive"] = 1.0 if c_f >= 20.0 else 0.0

    if tau_suvr is not None:
        feat_dict["Tau_MetaTemporal_SUVR"] = float(tau_suvr)

    for feature_name in (
        "Amyloid_Summary_SUVR", "Amyloid_Prefrontal_SUVR",
        "Amyloid_Parietal_SUVR", "Tau_Entorhinal_SUVR",
        "Tau_Hippocampus_SUVR", "Tau_InferiorTemporal_SUVR",
        "Tau_Braak_High", "ARIA_E_Risk_Score",
    ):
        feat_dict[feature_name] = s4_db.get(feature_name, np.nan)

    stage_inputs = {
        1: (mmse_val, moca_val, cdrsb_val, faq_val, adas_val),
        2: (ptau_z, ab42_40_z, nfl_z, gfap_z),
        3: (
            hippo_cm3,
            hippo_icv,
            vent_cm3 if icv_cm3 is not None else None,
            ventricles_icv_ratio,
            wmh_cm3,
        ),
        4: (cent_val, tau_suvr),
    }
    if not any(value is not None for value in stage_inputs[stage]):
        raise HTTPException(
            status_code=422,
            detail=f"Provide at least one measured input for Stage {stage} before requesting a research estimate.",
        )

    feature_cols = FEATURE_LISTS[stage]
    df_in = pd.DataFrame([feat_dict])
    for c in feature_cols:
        if c not in df_in.columns:
            df_in[c] = np.nan
    X_eval = df_in[feature_cols]

    model = MODELS[stage]
    raw_prob = float(model.predict_proba(X_eval)[:, 1][0])
    severity_index = raw_prob
    cal_prob = float(CALIBRATORS[stage].predict(np.asarray([raw_prob]))[0])

    current_dx = "Not estimated by the 24-month progression model"

    thresh = STAGE_THRESHOLDS[stage]
    escalate = cal_prob >= thresh
    next_step = (
        "Research-only score is above the model threshold. A qualified clinician must "
        "independently assess the patient; this is not a referral or treatment recommendation."
        if escalate
        else "Research-only score is below the model threshold. This is not a diagnosis "
        "or a reason to defer clinical assessment."
    )

    velocity_tier = "Above research threshold" if escalate else "Below research threshold"

    contributions = model.get_booster().predict(
        xgb.DMatrix(X_eval, feature_names=feature_cols),
        pred_contribs=True,
    )[0]
    shap_drivers = [
        {
            "name": feature_cols[index],
            "val": f"{float(contributions[index]):+.4f}",
            "desc": "XGBoost SHAP contribution to the raw model output.",
        }
        for index in np.argsort(np.abs(contributions[:-1]))[::-1][:5]
        if contributions[index] != 0
    ]

    mlp_result = None
    if stage in MLP_MODELS and stage in MLP_PREPROCESSORS:
        try:
            mlp_model = MLP_MODELS[stage]
            mlp_prep = MLP_PREPROCESSORS[stage]
            mlp_thresh = MLP_THRESHOLDS.get(stage, 0.5)
            
            # Ensure dataframe matches preprocessor expected feature names
            if hasattr(mlp_prep, "feature_names_in_"):
                expected_mlp_cols = list(mlp_prep.feature_names_in_)
                for c in expected_mlp_cols:
                    if c not in df_in.columns:
                        df_in[c] = np.nan
                X_mlp_in = df_in[expected_mlp_cols]
            else:
                X_mlp_in = X_eval
                
            X_mlp_trans = mlp_prep.transform(X_mlp_in)
            with torch.no_grad():
                mlp_t = torch.tensor(X_mlp_trans, dtype=torch.float32)
                mlp_logits = mlp_model(mlp_t)
                mlp_prob = float(torch.sigmoid(mlp_logits).item())
            
            mlp_escalate = mlp_prob >= mlp_thresh
            mlp_result = {
                "progression_24m_risk": round(mlp_prob, 4),
                "progression_24m_risk_pct": round(mlp_prob * 100, 1),
                "optimal_threshold": mlp_thresh,
                "escalation_recommended": bool(mlp_escalate),
                "model_architecture": "MLP (128 -> 64 -> 1)",
                "metrics": MLP_METRICS.get(stage, {}),
            }
        except Exception as e:
            print(f"Warning: MLP evaluation failed: {e}")

    result = {
        "patient_id": req.patient_id,
        "stage": stage,
        "risk_score": round(severity_index, 4),
        "risk_pct": round(severity_index * 100, 1),
        "severity_index": round(severity_index, 4),
        "severity_pct": round(severity_index * 100, 1),
        "calibrated_risk": round(cal_prob, 4),
        "calibrated_risk_pct": round(cal_prob * 100, 1),
        "raw_xgboost_prob": round(raw_prob, 4),
        "mlp_prediction": mlp_result,
        "model_comparison": {
            "xgboost": {
                "progression_24m_risk": round(cal_prob, 4),
                "progression_24m_risk_pct": round(cal_prob * 100, 1),
                "optimal_threshold": thresh,
                "escalation_recommended": bool(escalate),
            },
            "mlp": mlp_result,
            "interpretation_notice": (
                "XGBoost baseline and PyTorch MLP progression models are compared under identical "
                "temporal holdouts. Both estimate 24-month progression probability."
            ),
        },
        "dual_head": {
            "current_diagnosis": current_dx,
            "diagnosis_probabilities": {},
            "progression_24m_risk": round(cal_prob, 4),
            "progression_24m_risk_pct": round(cal_prob * 100, 1),
            "velocity_tier": velocity_tier
        },
        "gating_decision": {
            "optimal_threshold": thresh,
            "escalation_recommended": bool(escalate),
            "confidence": "Not available; threshold is research-only."
        },
        "measured_inputs": {
            "plasma_ptau217_z": ptau_z,
            "plasma_ab42_40_z": ab42_40_z,
            "plasma_nfl_z": nfl_z,
            "plasma_gfap_z": gfap_z,
            "hippocampus_icv_ratio": hippo_icv,
            "ventricles_icv_ratio": ventricles_icv_ratio,
            "wmh_volume_cm3": wmh_cm3,
            "centiloids": cent_val,
            "tau_suvr": tau_suvr,
        },
        "cds_recommendation": next_step,
        "shap_drivers": shap_drivers,
        "india_demographic_calibrated": False
    }

    # Auto-save if requested
    if req.save_to_patient and req.patient_id and req.patient_id != "DEMO-CASE-01":
        try:
            p = fetch_patient_by_id_db(req.patient_id)
            if p:
                visit_data = {
                    "stage_number": stage,
                    "mmse": req.cognitive.mmse, "moca": req.cognitive.moca,
                    "cdrsb": req.cognitive.cdrsb, "faq": req.cognitive.faq,
                    "ptau217": None, "ab42_40": None, "nfl": None, "gfap": None,
                    "hippocampus_cm3": req.hippocampus_cm3,
                    "centiloids": req.centiloids, "tau_suvr": req.tau_suvr,
                    "microbleeds": req.microbleeds,
                    "risk_score": cal_prob,
                    "stage_dx": current_dx,
                    "stage_assessment_json": result,
                    "current_stage": max(stage, p.get("current_stage") or 0)
                }
                add_visit_db(p["id"], visit_data)
        except Exception as e:
            print(f"Warning: auto-save failed: {e}")

    return result


# =====================================================================
# SIMULATED HOSPITAL EHR / PACS DATABASE GATEWAY
# =====================================================================

EHR_RECORDS_STORE = [
    {
        "id": "EHR-001",
        "mrn": "ADNI-002-S-0413",
        "patient_name": "Eleanor K. Rostova",
        "age": 74,
        "gender": "Female",
        "education_years": 16,
        "apoe": "ε4/ε4",
        "apoe4_count": 2,
        "archetype": "Rapid Prototypical Amyloid+ Converter (Stage 4 DMT Candidate)",
        "clinical_stage": 4,
        "cognitive": {
            "mmse": 18.0,
            "moca": 14.0,
            "cdrsb": 7.5,
            "faq": 18.0,
            "adas13": 32.5,
            "gds": 4.0
        },
        "plasma": {
            "plasma_ptau217": 0.48,
            "plasma_ab42_40": 0.052,
            "plasma_nfl": 38.5,
            "plasma_gfap": 320.0
        },
        "mri": {
            "hippocampus_cm3": 2.85,
            "hippocampus_icv_ratio": 0.0019,
            "ventricles_cm3": 48.2,
            "wmh_volume_cm3": 6.4,
            "mta_grade": "3"
        },
        "pet": {
            "centiloids": 78.4,
            "tau_suvr": 1.62,
            "microbleeds": 1
        },
        "vitals": {
            "blood_pressure": "138/85 mmHg",
            "bmi": 24.2,
            "has_hypertension": True,
            "has_diabetes": False
        },
        "referral": "Referred by Memory Clinic for rapid cognitive decline over 18 months."
    },
    {
        "id": "EHR-002",
        "mrn": "ADNI-002-S-0685",
        "patient_name": "John D. Mitchell",
        "age": 68,
        "gender": "Male",
        "education_years": 14,
        "apoe": "ε3/ε4",
        "apoe4_count": 1,
        "archetype": "Amnestic Mild Cognitive Impairment (Stage 2/3 Biomarker Escalation)",
        "clinical_stage": 2,
        "cognitive": {
            "mmse": 23.0,
            "moca": 20.0,
            "cdrsb": 3.5,
            "faq": 8.0,
            "adas13": 19.0,
            "gds": 3.0
        },
        "plasma": {
            "plasma_ptau217": 0.32,
            "plasma_ab42_40": 0.061,
            "plasma_nfl": 22.0,
            "plasma_gfap": 195.0
        },
        "mri": {
            "hippocampus_cm3": 3.40,
            "hippocampus_icv_ratio": 0.0023,
            "ventricles_cm3": 36.0,
            "wmh_volume_cm3": 3.8,
            "mta_grade": "2"
        },
        "pet": {
            "centiloids": 34.0,
            "tau_suvr": 1.25,
            "microbleeds": 0
        },
        "vitals": {
            "blood_pressure": "128/80 mmHg",
            "bmi": 26.5,
            "has_hypertension": True,
            "has_diabetes": False
        },
        "referral": "Primary care referral following episodic memory complaints."
    },
    {
        "id": "EHR-003",
        "mrn": "ADNI-003-S-1024",
        "patient_name": "Sarah Jenkins",
        "age": 62,
        "gender": "Female",
        "education_years": 18,
        "apoe": "ε3/ε3",
        "apoe4_count": 0,
        "archetype": "Reversible Depressive Pseudo-Dementia (Normal Biomarkers)",
        "clinical_stage": 1,
        "cognitive": {
            "mmse": 28.0,
            "moca": 26.0,
            "cdrsb": 0.5,
            "faq": 1.0,
            "adas13": 8.0,
            "gds": 8.0
        },
        "plasma": {
            "plasma_ptau217": 0.12,
            "plasma_ab42_40": 0.092,
            "plasma_nfl": 11.5,
            "plasma_gfap": 110.0
        },
        "mri": {
            "hippocampus_cm3": 4.10,
            "hippocampus_icv_ratio": 0.0028,
            "ventricles_cm3": 24.0,
            "wmh_volume_cm3": 1.2,
            "mta_grade": "0"
        },
        "pet": {
            "centiloids": 8.5,
            "tau_suvr": 1.04,
            "microbleeds": 0
        },
        "vitals": {
            "blood_pressure": "118/74 mmHg",
            "bmi": 22.1,
            "has_hypertension": False,
            "has_diabetes": False
        },
        "referral": "Subjective memory complaints with high GDS-15 depression score."
    },
    {
        "id": "EHR-004",
        "mrn": "LASI-004-S-2291",
        "patient_name": "Rajesh Patel",
        "age": 71,
        "gender": "Male",
        "education_years": 6,
        "apoe": "ε3/ε3",
        "apoe4_count": 0,
        "archetype": "LASI-DAD India Demographic Recalibration Case",
        "clinical_stage": 1,
        "cognitive": {
            "mmse": 21.0,
            "moca": 19.0,
            "cdrsb": 2.0,
            "faq": 4.0,
            "adas13": 14.0,
            "gds": 3.0
        },
        "plasma": {
            "plasma_ptau217": 0.16,
            "plasma_ab42_40": 0.082,
            "plasma_nfl": 14.0,
            "plasma_gfap": 130.0
        },
        "mri": {
            "hippocampus_cm3": 3.85,
            "hippocampus_icv_ratio": 0.0026,
            "ventricles_cm3": 29.0,
            "wmh_volume_cm3": 2.5,
            "mta_grade": "1"
        },
        "pet": {
            "centiloids": 14.2,
            "tau_suvr": 1.10,
            "microbleeds": 0
        },
        "vitals": {
            "blood_pressure": "132/84 mmHg",
            "bmi": 25.0,
            "has_hypertension": True,
            "has_diabetes": True
        },
        "referral": "Community screening in Mumbai rural outreach. Low formal education baseline."
    },
    {
        "id": "EHR-005",
        "mrn": "ADNI-005-S-8842",
        "patient_name": "David Vance",
        "age": 79,
        "gender": "Male",
        "education_years": 16,
        "apoe": "ε4/ε4",
        "apoe4_count": 2,
        "archetype": "High ARIA Safety Alert / mAb DMT Contraindicated",
        "clinical_stage": 4,
        "cognitive": {
            "mmse": 15.0,
            "moca": 11.0,
            "cdrsb": 9.0,
            "faq": 22.0,
            "adas13": 38.0,
            "gds": 5.0
        },
        "plasma": {
            "plasma_ptau217": 0.62,
            "plasma_ab42_40": 0.045,
            "plasma_nfl": 46.0,
            "plasma_gfap": 390.0
        },
        "mri": {
            "hippocampus_cm3": 2.45,
            "hippocampus_icv_ratio": 0.0016,
            "ventricles_cm3": 56.0,
            "wmh_volume_cm3": 9.8,
            "mta_grade": "4"
        },
        "pet": {
            "centiloids": 94.0,
            "tau_suvr": 1.88,
            "microbleeds": 6
        },
        "vitals": {
            "blood_pressure": "145/90 mmHg",
            "bmi": 27.8,
            "has_hypertension": True,
            "has_diabetes": True
        },
        "referral": "Evaluation for anti-amyloid therapy. Multiple microbleeds detected on GRE MRI."
    }
]


@app.get("/api/ehr/records")
def get_ehr_records():
    """Returns list of pre-configured hospital EHR records for instant 1-click test intake."""
    return {"records": EHR_RECORDS_STORE, "total": len(EHR_RECORDS_STORE)}


@app.get("/api/ehr/records/{ehr_id}")
def get_single_ehr_record(ehr_id: str):
    """Returns detailed clinical parameters for a specific EHR record."""
    for rec in EHR_RECORDS_STORE:
        if rec["id"] == ehr_id or rec["mrn"] == ehr_id:
            return rec
    raise HTTPException(status_code=404, detail="EHR record not found")


# =====================================================================
# LAB REPORT & PDF EXTRACTION ENDPOINTS
# =====================================================================

@app.post("/api/lab/parse-report")
async def parse_lab_report(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Body(None)
):
    """
    Parses digital lab reports (PDF or text) and extracts patient demographics,
    genetics, cognitive battery scores, and blood/imaging biomarkers in <30ms.
    """
    extracted_text = ""
    filename = "manual_text_input"
    
    if file:
        filename = file.filename
        content = await file.read()
        if filename.lower().endswith(".pdf") or content.startswith(b"%PDF"):
            extracted_text = extract_text_from_pdf_bytes(content)
        else:
            try:
                extracted_text = content.decode("utf-8", errors="ignore")
            except Exception:
                extracted_text = str(content)
    elif raw_text:
        extracted_text = raw_text
    else:
        raise HTTPException(status_code=400, detail="Provide either a file upload or raw_text")
        
    parsed_data = parse_clinical_report_text(extracted_text)
    parsed_data["source_filename"] = filename
    parsed_data["extracted_characters"] = len(extracted_text)
    
    return {
        "status": "success",
        "parsed_report": parsed_data
    }


# =====================================================================
# SIMULATION + FHIR
# =====================================================================

@app.post("/api/simulation/roi")
def run_roi_simulation(req: SimulationRequest):
    cohort = req.annual_screened_patients
    stage1_flagged = cohort * 0.40
    stage2_blood = stage1_flagged
    stage2_positive = stage2_blood * 0.45
    unscreened_pet = cohort * 0.40
    stepwise_pet = stage2_positive * 0.35
    pet_avoided = max(0, int(unscreened_pet - stepwise_pet))
    cost_unscreened = (stage1_flagged * req.mri_cost_usd) + (unscreened_pet * req.pet_cost_usd)
    cost_stepwise = (stage2_blood * req.plasma_test_cost_usd) + (stage2_positive * req.mri_cost_usd) + (stepwise_pet * req.pet_cost_usd)
    savings = max(0, int(cost_unscreened - cost_stepwise))
    pet_cap = req.pet_weekly_capacity * 52
    return {
        "parameters": req.dict(),
        "triage_funnel": {
            "initial_screened_cohort": cohort,
            "stage1_cognitive_flagged": int(stage1_flagged),
            "stage2_plasma_screened": int(stage2_blood),
            "stage3_mri_referred": int(stage2_positive),
            "stage4_pet_referred": int(stepwise_pet)
        },
        "roi_impact": {
            "pet_scans_avoided_annually": pet_avoided,
            "pet_demand_reduction_pct": round((pet_avoided / max(1, unscreened_pet)) * 100, 1),
            "total_annual_cost_savings_usd": savings,
            "wait_time_reduction_months": round(3.8 * (pet_avoided / max(1, pet_cap)), 1)
        }
    }


@app.post("/api/orders/servicerequest")
def create_fhir_servicerequest(order: ServiceRequestOrder):
    return {
        "status": "transmitted",
        "resourceType": "ServiceRequest",
        "id": f"SR-{order.mrn}-2026",
        "intent": "order",
        "priority": "stat",
        "subject": {"reference": f"Patient/{order.patient_id}", "display": order.patient_name},
        "code": {"coding": [{"system": "http://loinc.org", "code": "80993-9", "display": order.target_modality}]},
        "reasonCode": [{"text": order.clinical_rationale}],
        "requester": {"display": order.ordering_physician}
    }


# =====================================================================
# NEUROSIGHT YOLOV8 BRAIN TUMOR DEMONSTRATION ENDPOINT
# =====================================================================

def generate_tumor_heatmap_and_annotated(image: Image.Image, first_result, detections: list) -> tuple:
    """
    Generates:
    1. annotated_image: YOLOv8 plotted detections with bounding boxes & class confidence tags (Base64 data URI).
    2. heatmap_image: Colorized MRI thermal activation / tumor density heatmap blended with anatomical scan (Base64 data URI).
    3. heatmap_stats: Peak intensity, centroid coordinates, and localized quadrant.
    """
    img_np = np.array(image.convert("RGB"))
    h, w, _ = img_np.shape

    # 1. Annotated image from YOLO plot
    plotted_bgr = first_result.plot()
    plotted_rgb = cv2.cvtColor(plotted_bgr, cv2.COLOR_BGR2RGB)
    ann_pil = Image.fromarray(plotted_rgb)
    buf_ann = io.BytesIO()
    ann_pil.save(buf_ann, format="JPEG", quality=92)
    annotated_base64 = f"data:image/jpeg;base64,{base64.b64encode(buf_ann.getvalue()).decode('utf-8')}"

    # 2. Heatmap generation
    heatmap_acc = np.zeros((h, w), dtype=np.float32)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0

    primary_centroid = None
    peak_intensity = 0.0

    if detections:
        y_coords, x_coords = np.ogrid[:h, :w]
        for det in detections:
            box = det["box"]
            conf = det["confidence"]
            x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            if primary_centroid is None:
                primary_centroid = {"cx": round(cx, 1), "cy": round(cy, 1)}

            # Standard deviations based on bounding box extent
            sx = max((x2 - x1) / 2.2, 12.0)
            sy = max((y2 - y1) / 2.2, 12.0)

            # Spatial 2D Gaussian density kernel
            kernel = np.exp(-(((x_coords - cx) ** 2) / (2.0 * sx ** 2) + ((y_coords - cy) ** 2) / (2.0 * sy ** 2)))

            # Modulate with local anatomical image intensity to trace tissue contours
            local_anatomical = np.clip(gray * 1.3, 0.2, 1.0)
            enhanced_kernel = kernel * local_anatomical * conf
            heatmap_acc = np.maximum(heatmap_acc, enhanced_kernel)

        peak_val = float(np.max(heatmap_acc))
        peak_intensity = round(peak_val, 3)
        if peak_val > 0:
            heatmap_norm = (heatmap_acc / peak_val * 255.0).astype(np.uint8)
        else:
            heatmap_norm = np.zeros((h, w), dtype=np.uint8)
    else:
        # Subtle baseline anatomical activity when no tumor detected
        heatmap_norm = (gray * 40.0).astype(np.uint8)

    # Colorize with medical JET colormap (dark blue = cold, cyan = transition, yellow/red = hyperintense lesion)
    heatmap_color_bgr = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
    heatmap_color_rgb = cv2.cvtColor(heatmap_color_bgr, cv2.COLOR_BGR2RGB)

    # Blend with original anatomical MRI scan (58% MRI + 42% thermal colormap)
    blended_rgb = cv2.addWeighted(img_np, 0.58, heatmap_color_rgb, 0.42, 0)

    buf_heat = io.BytesIO()
    Image.fromarray(blended_rgb).save(buf_heat, format="JPEG", quality=92)
    heatmap_base64 = f"data:image/jpeg;base64,{base64.b64encode(buf_heat.getvalue()).decode('utf-8')}"

    # Quadrant localization
    quadrant = "Central / Periventricular"
    if primary_centroid:
        cx, cy = primary_centroid["cx"], primary_centroid["cy"]
        lr = "Right" if cx < w / 2 else "Left"  # Radiological orientation (Left of scan is Right hemisphere)
        ap = "Anterior / Frontal" if cy < h / 2 else "Posterior / Parieto-Occipital"
        quadrant = f"{lr} {ap}"

    heatmap_stats = {
        "peak_intensity": peak_intensity,
        "centroid": primary_centroid,
        "radiological_quadrant": quadrant,
        "colormap": "Medical JET (Thermal Activation)",
    }

    return annotated_base64, heatmap_base64, heatmap_stats


@app.post("/api/tumor/detect")
async def detect_brain_tumor(
    file: UploadFile = File(...),
    model_variant: str = Query("nano", pattern="^(nano|medium)$"),
    conf_threshold: float = Query(0.25, ge=0.05, le=0.95),
):
    """
    Independent research demonstration using NeuroSight AI YOLOv8 weights.
    Detects 3 tumor classes: glioma, meningioma, pituitary.
    Completely decoupled from Alzheimer's disease progression stages.
    """
    variant_val = model_variant.default if hasattr(model_variant, "default") else str(model_variant)
    conf_val = float(conf_threshold.default if hasattr(conf_threshold, "default") else conf_threshold)

    if variant_val not in TUMOR_MODELS:
        raise HTTPException(
            status_code=503,
            detail=f"YOLOv8 {variant_val} tumor model is not loaded. Available: {list(TUMOR_MODELS.keys())}"
        )

    # Validate file extension
    filename = (file.filename or "").lower()
    allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    if not any(filename.endswith(ext) for ext in allowed_exts):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image file extension. Allowed formats: {sorted(allowed_exts)}"
        )

    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 10 MB.")
    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to safely decode image: {e}")

    width, height = image.size
    if width < 32 or height < 32 or width > 4096 or height > 4096:
        raise HTTPException(
            status_code=400,
            detail=f"Image dimensions ({width}x{height}) outside permitted range (32x32 to 4096x4096)."
        )

    yolo_model = TUMOR_MODELS[variant_val]
    results = yolo_model(image, conf=conf_val)
    first_result = results[0]
    names = first_result.names

    detections = []
    for box in first_result.boxes:
        xyxy = box.xyxy[0].tolist()
        conf = float(box.conf[0].item())
        cls_id = int(box.cls[0].item())
        cls_name = names.get(cls_id, f"class_{cls_id}")
        detections.append({
            "class_id": cls_id,
            "class_name": cls_name,
            "confidence": round(conf, 4),
            "confidence_pct": round(conf * 100, 1),
            "box": {
                "x1": round(xyxy[0], 2),
                "y1": round(xyxy[1], 2),
                "x2": round(xyxy[2], 2),
                "y2": round(xyxy[3], 2),
                "width": round(xyxy[2] - xyxy[0], 2),
                "height": round(xyxy[3] - xyxy[1], 2),
            }
        })

    annotated_image, heatmap_image, heatmap_stats = generate_tumor_heatmap_and_annotated(
        image, first_result, detections
    )

    return {
        "status": "success",
        "model_variant": variant_val,
        "confidence_threshold": conf_val,
        "image_dimensions": {"width": width, "height": height},
        "detection_count": len(detections),
        "detections": detections,
        "annotated_image": annotated_image,
        "heatmap_image": heatmap_image,
        "heatmap_stats": heatmap_stats,
        "classes_supported": ["glioma", "meningioma", "pituitary"],
        "research_notice": (
            "Educational and research demonstration only. Not a medical device and not a diagnosis. "
            "An empty detection list means no detections met the confidence threshold, not evidence of absence."
        )
    }


# =====================================================================
# TELEMEDICINE -- WebRTC Signaling (WebSocket routes)
# =====================================================================
from backend.telemedicine_routes import register as _register_telemedicine
_register_telemedicine(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)