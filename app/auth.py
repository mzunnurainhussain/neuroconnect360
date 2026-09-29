from __future__ import annotations
import base64, hashlib, hmac, os, secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from .db import db

COOKIE_NAME = "nc360_session"
SESSION_HOURS = 24


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 240_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = stored.split("$")
        if algo != "pbkdf2_sha256": return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(rounds))
        return hmac.compare_digest(base64.b64encode(derived).decode(), digest_b64)
    except Exception:
        return False

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_session(user_id: int, response: Response):
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    with db() as con:
        con.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
        con.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)", (_token_hash(token), user_id, expires.isoformat()))
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=bool(os.getenv("VERCEL")), samesite="lax", max_age=SESSION_HOURS*3600, path="/")

def clear_session(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        with db() as con:
            con.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))
    response.delete_cookie(COOKIE_NAME, path="/")

def current_user(request: Request, required: bool=True):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        if required: raise HTTPException(401, "Authentication required")
        return None
    now = datetime.now(timezone.utc).isoformat()
    with db() as con:
        row = con.execute("""SELECT u.id,u.email,u.full_name,u.role,u.preferred_language,u.is_verified
            FROM sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=? AND s.expires_at>?""", (_token_hash(token), now)).fetchone()
    if not row:
        if required: raise HTTPException(401, "Session expired or invalid")
        return None
    return dict(row)

def require_roles(request: Request, *roles):
    user = current_user(request)
    if user['role'] not in roles:
        raise HTTPException(403, "Insufficient permissions")
    return user
