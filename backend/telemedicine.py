"""
Smriti Telemedicine & Video Consultation Engine
Enables WebRTC peer-to-peer video calls between doctors and specific patients.
Includes:
  - Persistent SMTP email configuration (Gmail App Password, custom SMTP)
  - Patient invitation dispatch with verified live email delivery
  - Direct 1-click consultation links for patients
  - WebRTC WebSocket signaling server (relays offer/answer/ICE candidates)
  - Consultation session state management
"""

import os
import smtplib
import asyncio
import json
import uuid
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("smriti.telemedicine")

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "data" / "email_config.json"

# ── Active in-memory consultation sessions ─────────────────────────────────────
# room_id -> dict with session metadata
consultation_sessions: Dict[str, Dict[str, Any]] = {}


# ── Room registry for WebRTC signaling ─────────────────────────────────────────
class Room:
    def __init__(self, room_id: str, creator_name: str = "Host"):
        self.room_id = room_id
        self.created_at = datetime.utcnow().isoformat()
        self.creator_name = creator_name
        self.peers: Dict[str, WebSocket] = {}   # peer_id -> websocket
        self.peer_names: Dict[str, str] = {}    # peer_id -> display name
        self.peer_roles: Dict[str, str] = {}    # peer_id -> "doctor" | "patient"

    def is_full(self) -> bool:
        return len(self.peers) >= 2

    def other_peer_id(self, my_peer_id: str) -> Optional[str]:
        for pid in self.peers:
            if pid != my_peer_id:
                return pid
        return None


rooms: Dict[str, Room] = {}          # room_id -> Room


# ── Helper for WebSocket message delivery ──────────────────────────────────────
async def _send(ws: WebSocket, payload: dict):
    try:
        await ws.send_text(json.dumps(payload))
    except Exception:
        pass


# ── SMTP Configuration Management ──────────────────────────────────────────────
def get_email_config() -> Dict[str, Any]:
    """Reads SMTP configuration from email_config.json or environment."""
    config = {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "sender_email": os.getenv("SMTP_FROM", ""),
        "sender_name": "Smriti TeleHealth"
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
                if isinstance(stored, dict):
                    config.update(stored)
        except Exception as e:
            logger.warning(f"Could not load email_config.json: {e}")

    return config


def save_email_config(config_data: Dict[str, Any]) -> bool:
    """Saves SMTP credentials to email_config.json."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Strip whitespace from app password
        if "smtp_password" in config_data and isinstance(config_data["smtp_password"], str):
            config_data["smtp_password"] = config_data["smtp_password"].replace(" ", "").strip()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save email config: {e}")
        return False


# ── Email Dispatcher ──────────────────────────────────────────────────────────
def send_patient_consultation_email(
    to_email: str,
    patient_name: str,
    doctor_name: str,
    consultation_link: str,
    call_reason: str,
    custom_notes: str = "",
    doctor_email: Optional[str] = None,
    lan_link: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an invitation email to the patient with their 1-click video call link.
    Connects to SMTP (e.g. Gmail with App Password).
    If SMTP credentials are not yet configured or fail, reports exact error status.
    """
    doc_title = doctor_name if doctor_name.strip().lower().startswith("dr") else f"Dr. {doctor_name}"
    subject = f"Urgent Video Call Invitation from {doc_title} - Smriti Health"

    notes_html = ""
    if custom_notes and custom_notes.strip():
        notes_html = f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0; font-size: 13px; font-weight: bold; color: #1e293b;">Doctor's Note:</p>
            <p style="margin: 4px 0 0; font-size: 13px; color: #475569;">{custom_notes}</p>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Video Consultation Invitation</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); padding: 28px 32px; text-align: left;">
                    <table width="100%">
                        <tr>
                            <td>
                                <span style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">Smriti Precision Health</span>
                                <div style="font-size: 11px; color: #bfdbfe; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Tele-Neurology Consultation Service</div>
                            </td>
                            <td align="right">
                                <span style="background: rgba(255,255,255,0.18); color: #ffffff; font-size: 11px; font-weight: 700; padding: 6px 12px; border-radius: 20px;">LIVE CALL READY</span>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- Body -->
            <tr>
                <td style="padding: 32px;">
                    <h2 style="font-size: 20px; font-weight: 700; color: #0f172a; margin: 0 0 16px;">Dear {patient_name},</h2>
                    <p style="font-size: 14px; line-height: 22px; color: #334155; margin: 0 0 16px;">
                        <strong>{doc_title}</strong> is currently waiting in your consultation room to discuss your neurological health evaluation and clinical reports.
                    </p>

                    <!-- Consultation Details Card -->
                    <div style="background-color: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; padding: 18px; margin: 20px 0;">
                        <table width="100%">
                            <tr>
                                <td style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Attending Clinician</td>
                                <td style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Consultation Agenda</td>
                            </tr>
                            <tr>
                                <td style="font-size: 14px; font-weight: 700; color: #1e3a8a; padding-top: 4px;">{doc_title}</td>
                                <td style="font-size: 14px; font-weight: 700; color: #1e3a8a; padding-top: 4px;">{call_reason}</td>
                            </tr>
                        </table>
                    </div>

                    {notes_html}

                    <!-- CTA Button -->
                    <div style="text-align: center; margin: 32px 0 24px;">
                        <a href="{consultation_link}" style="display: inline-block; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 700; padding: 16px 36px; border-radius: 12px; box-shadow: 0 4px 14px rgba(37,99,235,0.35);">
                            👉 Join Video Call with {doc_title}
                        </a>
                    </div>

                    <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 8px;">
                        No sign-in or installation required. Works on any smartphone, tablet, or laptop browser.
                    </p>
                    <p style="font-size: 12px; color: #64748b; text-align: center; word-break: break-all; margin: 0;">
                        <strong>Click Link to Join:</strong><br>
                        • On this computer: <a href="{consultation_link}" style="color: #2563eb; font-weight: 600;">{consultation_link}</a><br>
                        • On mobile phone (same Wi-Fi): <a href="{lan_link or consultation_link}" style="color: #2563eb; font-weight: 600;">{lan_link or consultation_link}</a>
                    </p>
                </td>
            </tr>

            <!-- Footer -->
            <tr>
                <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; font-size: 11px; color: #94a3b8; text-align: center;">
                    This communication contains confidential medical information.
                    <br>© 2026 Smriti Precision Care Clinical Command Center. All rights reserved.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    plain_text = f"""
    Smriti Tele-Neurology Video Consultation

    Dear {patient_name},

    {doc_title} has requested an immediate video consultation to discuss your health evaluation.

    Consultation Reason: {call_reason}
    Doctor's Note: {custom_notes or 'Please join as soon as possible.'}

    Click the link below to enter the video call directly (no login required):
    {consultation_link}

    This secure video session is encrypted peer-to-peer.
    """

    cfg = get_email_config()
    smtp_host = cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(cfg.get("smtp_port", 587))
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pass = cfg.get("smtp_password", "").strip()
    sender_email = cfg.get("sender_email", "") or smtp_user

    is_configured = bool(smtp_user and smtp_pass)
    sent_successfully = False
    delivery_mode = "not_configured"
    delivery_note = ""

    if is_configured:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            from_header = f"{doc_title} via Smriti <{sender_email}>"
            msg["From"] = from_header
            msg["To"] = to_email
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender_email, [to_email], msg.as_string())

            sent_successfully = True
            delivery_mode = "smtp_success"
            delivery_note = f"Real email delivered via SMTP to {to_email}"
            logger.info(f"Successfully sent live consultation email to {to_email}")

        except Exception as e:
            logger.error(f"Live SMTP sending error: {e}")
            sent_successfully = False
            delivery_mode = "smtp_error"
            delivery_note = f"SMTP error: {str(e)}"
    else:
        # Not configured yet
        sent_successfully = False
        delivery_mode = "smtp_missing_credentials"
        delivery_note = "Live email not sent: Gmail App Password is not yet configured. Please configure your email in Email Settings."

    return {
        "success": sent_successfully,
        "mode": delivery_mode,
        "to": to_email,
        "subject": subject,
        "delivery_note": delivery_note,
        "timestamp": datetime.utcnow().isoformat(),
        "preview_html": html_content,
        "preview_text": plain_text
    }


# ── WebRTC Signaling Handler ──────────────────────────────────────────────────
async def handle_signaling(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint: /ws/telemedicine/{room_id}
    Connects doctor and patient in peer-to-peer WebRTC session.
    """
    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = Room(room_id)

    room = rooms[room_id]

    if room.is_full():
        await _send(websocket, {"type": "error", "message": "Consultation room is already full (max 2 participants)."})
        await websocket.close(code=4001)
        return

    peer_id = str(uuid.uuid4())
    room.peers[peer_id] = websocket

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=20)
        join_msg = json.loads(raw)
        if join_msg.get("type") != "join":
            await _send(websocket, {"type": "error", "message": "Expected join message."})
            await websocket.close(code=4002)
            return
        display_name = str(join_msg.get("name", "Participant"))[:80]
        role = str(join_msg.get("role", "guest"))[:20]
    except Exception:
        await websocket.close(code=4003)
        return

    room.peer_names[peer_id] = display_name
    room.peer_roles[peer_id] = role
    logger.info(f"[Room {room_id}] {display_name} ({role}) joined as peer {peer_id}")

    # Update session status
    if room_id in consultation_sessions:
        if len(room.peers) >= 2:
            consultation_sessions[room_id]["status"] = "active"

    # Acknowledge self
    await _send(websocket, {
        "type": "joined",
        "peer_id": peer_id,
        "room_id": room_id,
        "role": role,
        "peer_count": len(room.peers),
    })

    # Notify other peer if present
    other_id = room.other_peer_id(peer_id)
    if other_id and other_id in room.peers:
        other_ws = room.peers[other_id]
        # Notify the other peer
        await _send(other_ws, {
            "type": "peer_joined",
            "peer_id": peer_id,
            "name": display_name,
            "role": role,
        })
        # Tell newcomer about existing peer
        await _send(websocket, {
            "type": "peer_joined",
            "peer_id": other_id,
            "name": room.peer_names.get(other_id, "Participant"),
            "role": room.peer_roles.get(other_id, "guest"),
        })

    # Relay loop
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")
            target_id = room.other_peer_id(peer_id)

            if msg_type in ("offer", "answer", "ice_candidate"):
                if target_id and target_id in room.peers:
                    await _send(room.peers[target_id], {**msg, "from": peer_id})
                else:
                    await _send(websocket, {"type": "error", "message": "Waiting for other party to connect..."})

            elif msg_type == "ping":
                await _send(websocket, {"type": "pong"})

            elif msg_type == "chat":
                if target_id and target_id in room.peers:
                    await _send(room.peers[target_id], {
                        "type": "chat",
                        "from": display_name,
                        "text": str(msg.get("text", ""))[:500],
                        "ts": datetime.utcnow().isoformat(),
                    })
    except WebSocketDisconnect:
        logger.info(f"[Room {room_id}] {display_name} disconnected")
    finally:
        room.peers.pop(peer_id, None)
        room.peer_names.pop(peer_id, None)
        room.peer_roles.pop(peer_id, None)

        remaining_id = room.other_peer_id(peer_id)
        if remaining_id and remaining_id in room.peers:
            await _send(room.peers[remaining_id], {
                "type": "peer_left",
                "peer_id": peer_id,
                "name": display_name,
            })

        if not room.peers:
            rooms.pop(room_id, None)
            if room_id in consultation_sessions:
                consultation_sessions[room_id]["status"] = "ended"
