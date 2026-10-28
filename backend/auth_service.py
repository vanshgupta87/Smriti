"""Local, single-hospital account and session storage for Smriti."""

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.database import get_db

PASSWORD_ITERATIONS = 310_000
SESSION_LIFETIME = timedelta(hours=8)
LOGIN_WINDOW = timedelta(minutes=15)
MAX_FAILED_LOGINS = 8
DUMMY_PASSWORD_HASH = (
    "pbkdf2_sha256$310000$"
    "c29tZXNhbHRmb3RpbWluZ2Vjb21wYXJpc29u"
    "$"
    "9f6dc39552b3b9d9a80d0cb16eeb1752e5ea09f27f70e0865e07f7387c69d27b"
)


class WorkspaceAlreadyConfigured(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class LoginRateLimited(Exception):
    pass


def init_auth_db() -> None:
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS auth_organizations (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL REFERENCES auth_organizations(id),
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                role TEXT NOT NULL,
                is_workspace_admin INTEGER NOT NULL DEFAULT 1,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS auth_sessions_expiry_idx
                ON auth_sessions(expires_at);
            CREATE TABLE IF NOT EXISTS auth_login_attempts (
                attempt_key TEXT NOT NULL,
                attempted_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS auth_login_attempts_key_idx
                ON auth_login_attempts(attempt_key, attempted_at);
            """
        )
        user_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(auth_users)")
        }
        if "is_workspace_admin" not in user_columns:
            conn.execute(
                "ALTER TABLE auth_users ADD COLUMN "
                "is_workspace_admin INTEGER NOT NULL DEFAULT 1"
            )
    finally:
        conn.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        salt.hex(),
        derived.hex(),
    )


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, expected_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 1_000_000:
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            iterations,
        )
        return hmac.compare_digest(derived.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def _new_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()
    conn.execute(
        "INSERT INTO auth_sessions (token_hash, user_id, expires_at, created_at) "
        "VALUES (?, ?, ?, ?)",
        (
            hashlib.sha256(token.encode("ascii")).hexdigest(),
            user_id,
            _iso(now + SESSION_LIFETIME),
            _iso(now),
        ),
    )
    return token


def _user_payload(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["role"],
        "is_workspace_admin": bool(row["is_workspace_admin"]),
        "organization": row["organization_name"],
    }


def create_first_hospital_account(
    organization: str,
    full_name: str,
    email: str,
    role: str,
    password: str,
) -> tuple[str, dict[str, Any]]:
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        configured = conn.execute(
            "SELECT 1 FROM auth_organizations WHERE id = 1"
        ).fetchone()
        if configured:
            raise WorkspaceAlreadyConfigured

        now = _iso(_now())
        cursor = conn.execute(
            "INSERT INTO auth_organizations (id, name, created_at) VALUES (1, ?, ?)",
            (organization.strip(), now),
        )
        cursor = conn.execute(
            """
            INSERT INTO auth_users
                (organization_id, full_name, email, role, is_workspace_admin, password_hash, created_at)
            VALUES (1, ?, ?, ?, 1, ?, ?)
            """,
            (
                full_name.strip(),
                email.strip().lower(),
                role,
                _hash_password(password),
                now,
            ),
        )
        user_id = cursor.lastrowid
        token = _new_session(conn, user_id)
        row = conn.execute(
            """
            SELECT u.id, u.full_name, u.email, u.role, u.is_workspace_admin,
                   o.name AS organization_name
            FROM auth_users u
            JOIN auth_organizations o ON o.id = u.organization_id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
        conn.commit()
        return token, _user_payload(row)
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise WorkspaceAlreadyConfigured from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _attempt_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _check_login_rate_limit(conn: sqlite3.Connection, email: str, client_ip: str) -> None:
    cutoff = _iso(_now() - LOGIN_WINDOW)
    email_key = _attempt_key(f"email:{email.lower()}")
    ip_key = _attempt_key(f"ip:{client_ip}")
    conn.execute("DELETE FROM auth_login_attempts WHERE attempted_at < ?", (cutoff,))
    for key in (email_key, ip_key):
        count = conn.execute(
            "SELECT COUNT(*) FROM auth_login_attempts "
            "WHERE attempt_key = ? AND attempted_at >= ?",
            (key, cutoff),
        ).fetchone()[0]
        if count >= MAX_FAILED_LOGINS:
            raise LoginRateLimited


def _record_failed_login(
    conn: sqlite3.Connection, email: str, client_ip: str
) -> None:
    attempted_at = _iso(_now())
    conn.executemany(
        "INSERT INTO auth_login_attempts (attempt_key, attempted_at) VALUES (?, ?)",
        (
            (_attempt_key(f"email:{email.lower()}"), attempted_at),
            (_attempt_key(f"ip:{client_ip}"), attempted_at),
        ),
    )


def authenticate(
    email: str, password: str, client_ip: str
) -> tuple[str, dict[str, Any]]:
    conn = get_db()
    try:
        normalized_email = email.strip().lower()
        _check_login_rate_limit(conn, normalized_email, client_ip)
        row = conn.execute(
            """
            SELECT u.id, u.full_name, u.email, u.role, u.is_workspace_admin,
                   u.password_hash,
                   o.name AS organization_name
            FROM auth_users u
            JOIN auth_organizations o ON o.id = u.organization_id
            WHERE u.email = ?
            """,
            (normalized_email,),
        ).fetchone()

        stored_hash = row["password_hash"] if row else DUMMY_PASSWORD_HASH
        password_valid = _verify_password(password, stored_hash)
        if row is None or not password_valid:
            _record_failed_login(conn, normalized_email, client_ip)
            conn.commit()
            raise InvalidCredentials

        conn.execute(
            "DELETE FROM auth_login_attempts WHERE attempt_key IN (?, ?)",
            (
                _attempt_key(f"email:{normalized_email}"),
                _attempt_key(f"ip:{client_ip}"),
            ),
        )
        conn.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (_iso(_now()),))
        token = _new_session(conn, row["id"])
        conn.commit()
        return token, _user_payload(row)
    finally:
        conn.close()


def get_session_user(token: Optional[str]) -> Optional[dict[str, Any]]:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
    now = _iso(_now())
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.full_name, u.email, u.role, u.is_workspace_admin,
                   o.name AS organization_name
            FROM auth_sessions s
            JOIN auth_users u ON u.id = s.user_id
            JOIN auth_organizations o ON o.id = u.organization_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()
    finally:
        conn.close()
    return _user_payload(row) if row else None


def revoke_session(token: Optional[str]) -> None:
    if not token:
        return
    token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
    conn = get_db()
    try:
        conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,))
    finally:
        conn.close()


def workspace_is_configured() -> bool:
    conn = get_db()
    try:
        return conn.execute(
            "SELECT 1 FROM auth_organizations WHERE id = 1"
        ).fetchone() is not None
    finally:
        conn.close()
