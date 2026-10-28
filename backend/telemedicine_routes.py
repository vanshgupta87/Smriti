"""
Smriti Telemedicine API Routes
Handles:
  - Inviting a specific patient via email
  - Querying and updating SMTP email configuration (Gmail App Password)
  - Testing email sending
  - Querying session info for doctor and patient
  - WebRTC WebSocket signaling relay
"""

import uuid
import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, WebSocket, HTTPException, Body
from backend.telemedicine import (
    handle_signaling,
    rooms as tele_rooms,
    consultation_sessions,
    send_patient_consultation_email,
    get_email_config,
    save_email_config
)
from backend.database import get_db


class InvitePatientRequest(BaseModel):
    patient_id: str
    patient_name: str
    patient_email: str
    doctor_name: str
    doctor_email: Optional[str] = None
    call_reason: str = "Review 4-Stage Progression & Diagnostic Scan Results"
    custom_notes: Optional[str] = ""


class EmailConfigRequest(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    sender_email: Optional[str] = ""
    sender_name: Optional[str] = "Smriti TeleHealth"


class TestEmailRequest(BaseModel):
    test_email: str


def register(app: FastAPI):
    # ------------------------------------------------------------------ #
    # 1. Doctor Invites Patient & Generates Call
    # ------------------------------------------------------------------ #
    @app.post("/api/telemedicine/invite-patient")
    async def invite_patient(payload: InvitePatientRequest, request: Request):
        room_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:3000"
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        base_url = f"{scheme}://{host}"
        if ":8000" in base_url:
            base_url = base_url.replace(":8000", ":3000")

        import socket
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            lan_ip = "localhost"

        consultation_link = f"{base_url}/consultation?room={room_id}"
        lan_link = f"http://{lan_ip}:3000/consultation?room={room_id}"

        # Dispatch email
        email_result = send_patient_consultation_email(
            to_email=payload.patient_email,
            patient_name=payload.patient_name,
            doctor_name=payload.doctor_name,
            consultation_link=consultation_link,
            call_reason=payload.call_reason,
            custom_notes=payload.custom_notes or "",
            doctor_email=payload.doctor_email,
            lan_link=lan_link
        )

        session_data = {
            "room_id": room_id,
            "patient_id": payload.patient_id,
            "patient_name": payload.patient_name,
            "patient_email": payload.patient_email,
            "doctor_name": payload.doctor_name,
            "doctor_email": payload.doctor_email or "",
            "call_reason": payload.call_reason,
            "custom_notes": payload.custom_notes or "",
            "join_url": consultation_link,
            "status": "waiting_for_patient",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "email_dispatched": email_result,
        }

        consultation_sessions[room_id] = session_data

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO telemedicine_sessions (
                room_id, patient_id, patient_name, patient_email,
                doctor_name, doctor_email, call_reason, custom_notes,
                join_url, email_sent, email_subject, email_body_html,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                room_id,
                payload.patient_id,
                payload.patient_name,
                payload.patient_email,
                payload.doctor_name,
                payload.doctor_email or "",
                payload.call_reason,
                payload.custom_notes or "",
                consultation_link,
                1 if email_result.get("success") else 0,
                email_result.get("subject", ""),
                email_result.get("preview_html", ""),
                "waiting_for_patient",
                session_data["created_at"]
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {
            "status": "success",
            "room_id": room_id,
            "join_url": consultation_link,
            "patient_name": payload.patient_name,
            "patient_email": payload.patient_email,
            "doctor_name": payload.doctor_name,
            "call_reason": payload.call_reason,
            "email_dispatch": email_result,
            "ws_url": f"ws://localhost:8000/ws/telemedicine/{room_id}",
        }

    # ------------------------------------------------------------------ #
    # 2. SMTP Configuration Get / Save / Test
    # ------------------------------------------------------------------ #
    @app.get("/api/telemedicine/email-config")
    async def get_email_config_route():
        cfg = get_email_config()
        # Mask password for security
        has_pass = bool(cfg.get("smtp_password"))
        return {
            "smtp_host": cfg.get("smtp_host", "smtp.gmail.com"),
            "smtp_port": cfg.get("smtp_port", 587),
            "smtp_user": cfg.get("smtp_user", ""),
            "has_password": has_pass,
            "sender_email": cfg.get("sender_email", ""),
            "is_configured": bool(cfg.get("smtp_user") and has_pass)
        }

    @app.post("/api/telemedicine/email-config")
    async def set_email_config_route(payload: EmailConfigRequest):
        data = payload.dict()
        success = save_email_config(data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save email configuration.")
        return {"status": "saved", "message": "Email settings saved successfully."}

    @app.post("/api/telemedicine/test-email")
    async def test_email_route(payload: TestEmailRequest):
        res = send_patient_consultation_email(
            to_email=payload.test_email,
            patient_name="Test Recipient",
            doctor_name="Dr. Vansh Gupta",
            consultation_link="http://localhost:3000/consultation?room=TEST-ROOM",
            call_reason="SMTP Connection Test Verification",
            custom_notes="This is a test verification email from Smriti TeleHealth."
        )
        return res

    # ------------------------------------------------------------------ #
    # 3. Public Session Details for Patient Join
    # ------------------------------------------------------------------ #
    @app.get("/api/telemedicine/public/session/{room_id}")
    async def get_public_session(room_id: str):
        if room_id in consultation_sessions:
            s = consultation_sessions[room_id]
            return {
                "room_id": room_id,
                "patient_name": s.get("patient_name", "Patient"),
                "doctor_name": s.get("doctor_name", "Attending Physician"),
                "call_reason": s.get("call_reason", "Clinical Follow-up"),
                "custom_notes": s.get("custom_notes", ""),
                "status": s.get("status", "waiting_for_patient"),
                "created_at": s.get("created_at"),
            }

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM telemedicine_sessions WHERE room_id = ?", (room_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                r = dict(row)
                return {
                    "room_id": room_id,
                    "patient_name": r.get("patient_name", "Patient"),
                    "doctor_name": r.get("doctor_name", "Attending Physician"),
                    "call_reason": r.get("call_reason", "Clinical Follow-up"),
                    "custom_notes": r.get("custom_notes", ""),
                    "status": r.get("status", "waiting_for_patient"),
                    "created_at": r.get("created_at"),
                }
        except Exception:
            pass

        return {
            "room_id": room_id,
            "patient_name": "Patient",
            "doctor_name": "Attending Neurologist",
            "call_reason": "Telemedicine Video Consultation",
            "status": "ready",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------ #
    # 4. List Active / Recent Sessions
    # ------------------------------------------------------------------ #
    @app.get("/api/telemedicine/sessions")
    async def list_sessions():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM telemedicine_sessions ORDER BY created_at DESC LIMIT 30")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return {"sessions": rows}
        except Exception:
            return {"sessions": list(consultation_sessions.values())}

    # ------------------------------------------------------------------ #
    # 5. Room Creation & WebSocket Relay
    # ------------------------------------------------------------------ #
    @app.get("/api/telemedicine/create-room")
    async def create_telemedicine_room(request: Request):
        room_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        return {
            "room_id": room_id,
            "join_url": f"/consultation?room={room_id}",
            "ws_url": f"ws://localhost:8000/ws/telemedicine/{room_id}",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

    @app.websocket("/ws/telemedicine/{room_id}")
    async def telemedicine_ws(websocket: WebSocket, room_id: str):
        await handle_signaling(websocket, room_id)
