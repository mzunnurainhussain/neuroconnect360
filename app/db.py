DB_PATH = ROOT / "data" / "neuroconnect360.db"
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path("/tmp/neuroconnect360.db") if os.getenv("VERCEL") else ROOT / "data" / "neuroconnect360.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('parent','professional','teacher','researcher','admin')),
    preferred_language TEXT NOT NULL DEFAULT 'en',
    is_verified INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS child_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    birth_year INTEGER,
    communication_level TEXT,
    school_status TEXT,
    primary_concerns TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    audience TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    summary TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    content_type TEXT NOT NULL DEFAULT 'article',
    published INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL REFERENCES child_profiles(id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('achieved','emerging','not_observed','unsure')),
    note TEXT,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS screening_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    child_id INTEGER REFERENCES child_profiles(id) ON DELETE SET NULL,
    instrument_code TEXT NOT NULL,
    score INTEGER NOT NULL,
    category TEXT NOT NULL,
    consented INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS professionals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    specialization TEXT NOT NULL,
    city TEXT NOT NULL,
    languages TEXT NOT NULL,
    consultation_modes TEXT NOT NULL,
    experience_years INTEGER NOT NULL DEFAULT 0,
    verified INTEGER NOT NULL DEFAULT 0,
    bio TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    professional_id INTEGER NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    requested_date TEXT NOT NULL,
    mode TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'requested',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_child_parent ON child_profiles(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_milestones_child ON milestones(child_id);
CREATE INDEX IF NOT EXISTS idx_screening_user ON screening_results(user_id);
CREATE INDEX IF NOT EXISTS idx_resources_filters ON resources(category,audience,language,published);
CREATE INDEX IF NOT EXISTS idx_professionals_city ON professionals(city,verified);
CREATE INDEX IF NOT EXISTS idx_appointments_requester ON appointments(requester_user_id,status);
"""


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

@contextmanager
def db():
    con = connect()
    try:
        yield con
        con.commit()
    finally:
        con.close()

def init_db():
    with db() as con:
        con.executescript(SCHEMA)
