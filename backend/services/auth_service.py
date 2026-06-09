"""
auth_service.py — User authentication with JWT tokens and password hashing.
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import get_db_connection

JWT_SECRET = os.environ.get("JWT_SECRET", "ecopath-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_user(name: str, email: str, password: str) -> dict:
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not name or not email or not password:
        raise AuthError("Name, email, and password are required.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")
    if "@" not in email:
        raise AuthError("Please enter a valid email address.")

    password_hash = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        raise AuthError("An account with this email already exists.")

    return _build_auth_response(user_id, name, email)


def login_user(email: str, password: str) -> dict:
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        raise AuthError("Email and password are required.")

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
        raise AuthError("Invalid email or password.", status_code=401)

    return _build_auth_response(row["id"], row["name"], row["email"])


def _build_auth_response(user_id: int, name: str, email: str) -> dict:
    token = jwt.encode(
        {
            "user_id": user_id,
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "token": token,
        "user": {"id": user_id, "name": name, "email": email},
    }


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired. Please log in again.", status_code=401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid session. Please log in again.", status_code=401)


def get_current_user_id() -> int | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = decode_token(token)
        return payload.get("user_id")
    except AuthError:
        return None


def require_auth(f):
    """Decorator that injects user_id into the route handler."""

    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return {"error": "Authentication required."}, 401
        return f(user_id=user_id, *args, **kwargs)

    return decorated


def get_user_stats(user_id: int) -> dict:
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT COUNT(*) AS trip_count,
               COALESCE(SUM(distance_km), 0) AS total_distance,
               COALESCE(SUM(carbon_kg), 0) AS total_carbon
        FROM carbon_history WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return {
        "trip_count": row["trip_count"],
        "total_distance_km": round(row["total_distance"], 2),
        "total_carbon_kg": round(row["total_carbon"], 2),
    }
