from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db, db
from .auth import (
    hash_password,
    verify_password,
    create_session,
    clear_session,
    current_user,
    require_roles,
)
from .models import (
    RegisterIn,
    LoginIn,
    ChildIn,
    MilestoneIn,
    ScreeningIn,
    AppointmentIn,
    ChatIn,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"


app = FastAPI(
    title="NeuroConnect 360 API",
    version="0.1.0",
    description=(
        "Phase-1 MVP APIs for a multilingual autism awareness "
        "and support ecosystem."
    ),
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC),
    name="static",
)


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():
    init_db()

    # Vercel's filesystem is ephemeral.
    # Seed demo data whenever a fresh Vercel function starts.
    if __import__("os").getenv("VERCEL"):
        from .seed import seed
        seed()


# =========================================================
# AUDIT
# =========================================================

def audit(
    user_id,
    action,
    entity_type=None,
    entity_id=None,
):
    with db() as con:
        con.execute(
            """
            INSERT INTO audit_logs(
                user_id,
                action,
                entity_type,
                entity_id
            )
            VALUES(?,?,?,?)
            """,
            (
                user_id,
                action,
                entity_type,
                str(entity_id) if entity_id else None,
            ),
        )


# =========================================================
# PUBLIC
# =========================================================

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "NeuroConnect 360",
        "medical_use": "educational_support_only",
    }


# =========================================================
# AUTHENTICATION
# =========================================================

@app.post("/api/auth/register")
def register(
    payload: RegisterIn,
    response: Response,
):
    email = payload.email.strip().lower()

    if "@" not in email:
        raise HTTPException(
            400,
            "Enter a valid email address",
        )

    with db() as con:
        existing = con.execute(
            "SELECT 1 FROM users WHERE email=?",
            (email,),
        ).fetchone()

        if existing:
            raise HTTPException(
                409,
                "Email already registered",
            )

        cur = con.execute(
            """
            INSERT INTO users(
                email,
                password_hash,
                full_name,
                role,
                preferred_language
            )
            VALUES(?,?,?,?,?)
            """,
            (
                email,
                hash_password(payload.password),
                payload.full_name.strip(),
                payload.role,
                payload.preferred_language,
            ),
        )

        user_id = cur.lastrowid

    create_session(
        user_id,
        response,
    )

    audit(
        user_id,
        "register",
        "user",
        user_id,
    )

    return {
        "ok": True,
    }


@app.post("/api/auth/login")
def login(
    payload: LoginIn,
    response: Response,
):
    with db() as con:
        row = con.execute(
            "SELECT * FROM users WHERE email=?",
            (
                payload.email.strip().lower(),
            ),
        ).fetchone()

    if not row or not verify_password(
        payload.password,
        row["password_hash"],
    ):
        raise HTTPException(
            401,
            "Invalid email or password",
        )

    create_session(
        row["id"],
        response,
    )

    audit(
        row["id"],
        "login",
        "user",
        row["id"],
    )

    return {
        "ok": True,
        "role": row["role"],
    }


@app.post("/api/auth/logout")
def logout(
    request: Request,
    response: Response,
):
    user = current_user(
        request,
        False,
    )

    clear_session(
        request,
        response,
    )

    if user:
        audit(
            user["id"],
            "logout",
        )

    return {
        "ok": True,
    }


@app.get("/api/me")
def me(request: Request):
    return current_user(request)


# =========================================================
# CHILD PROFILES
# =========================================================

@app.get("/api/children")
def children(request: Request):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    with db() as con:
        rows = con.execute(
            """
            SELECT *
            FROM child_profiles
            WHERE parent_user_id=?
            ORDER BY id DESC
            """,
            (user["id"],),
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


@app.post("/api/children")
def add_child(
    payload: ChildIn,
    request: Request,
):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    with db() as con:
        cur = con.execute(
            """
            INSERT INTO child_profiles(
                parent_user_id,
                display_name,
                birth_year,
                communication_level,
                school_status,
                primary_concerns
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                user["id"],
                payload.display_name,
                payload.birth_year,
                payload.communication_level,
                payload.school_status,
                payload.primary_concerns,
            ),
        )

        cid = cur.lastrowid

    audit(
        user["id"],
        "create",
        "child_profile",
        cid,
    )

    return {
        "id": cid,
    }


# =========================================================
# MILESTONES
# =========================================================

@app.get("/api/milestones")
def milestones(
    request: Request,
    child_id: int,
):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    with db() as con:
        owner = con.execute(
            """
            SELECT 1
            FROM child_profiles
            WHERE id=?
              AND parent_user_id=?
            """,
            (
                child_id,
                user["id"],
            ),
        ).fetchone()

        if (
            not owner
            and user["role"] != "admin"
        ):
            raise HTTPException(
                403,
                "No access to this child profile",
            )

        rows = con.execute(
            """
            SELECT *
            FROM milestones
            WHERE child_id=?
            ORDER BY recorded_at DESC
            """,
            (child_id,),
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


@app.post("/api/milestones")
def add_milestone(
    payload: MilestoneIn,
    request: Request,
):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    with db() as con:
        owner = con.execute(
            """
            SELECT 1
            FROM child_profiles
            WHERE id=?
              AND parent_user_id=?
            """,
            (
                payload.child_id,
                user["id"],
            ),
        ).fetchone()

        if (
            not owner
            and user["role"] != "admin"
        ):
            raise HTTPException(
                403,
                "No access to this child profile",
            )

        cur = con.execute(
            """
            INSERT INTO milestones(
                child_id,
                domain,
                title,
                status,
                note
            )
            VALUES(?,?,?,?,?)
            """,
            (
                payload.child_id,
                payload.domain,
                payload.title,
                payload.status,
                payload.note,
            ),
        )

        mid = cur.lastrowid

    audit(
        user["id"],
        "create",
        "milestone",
        mid,
    )

    return {
        "id": mid,
    }


# =========================================================
# RESOURCE LIBRARY
# =========================================================

@app.get("/api/resources")
def resources(
    category: str | None = None,
    audience: str | None = None,
    language: str = "en",
):
    sql = """
    SELECT
        id,
        title,
        category,
        audience,
        language,
        summary,
        source_name,
        source_url,
        content_type
    FROM resources
    WHERE published=1
      AND language=?
    """

    params = [language]

    if category:
        sql += " AND category=?"
        params.append(category)

    if audience and audience != "all":
        sql += """
        AND (
            audience=?
            OR audience='all'
        )
        """
        params.append(audience)

    sql += " ORDER BY id DESC"

    with db() as con:
        rows = con.execute(
            sql,
            params,
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


# =========================================================
# SCREENING SUPPORT
# =========================================================

@app.post("/api/screenings/demo")
def screening(
    payload: ScreeningIn,
    request: Request,
):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    if not payload.consented:
        raise HTTPException(
            400,
            "Consent is required before screening support",
        )

    if any(
        value not in (0, 1)
        for value in payload.responses
    ):
        raise HTTPException(
            400,
            "Responses must be 0 or 1",
        )

    score = sum(
        payload.responses
    )

    if score <= 1:
        category = (
            "Lower screening indication"
        )

    elif score <= 3:
        category = (
            "Additional monitoring may be appropriate"
        )

    else:
        category = (
            "Professional developmental assessment "
            "may be appropriate"
        )

    if payload.child_id:
        with db() as con:
            owner = con.execute(
                """
                SELECT 1
                FROM child_profiles
                WHERE id=?
                  AND parent_user_id=?
                """,
                (
                    payload.child_id,
                    user["id"],
                ),
            ).fetchone()

            if (
                not owner
                and user["role"] != "admin"
            ):
                raise HTTPException(
                    403,
                    "No access to this child profile",
                )

    with db() as con:
        cur = con.execute(
            """
            INSERT INTO screening_results(
                user_id,
                child_id,
                instrument_code,
                score,
                category,
                consented
            )
            VALUES(?,?,?,?,?,1)
            """,
            (
                user["id"],
                payload.child_id,
                "NC360-DEMO-6",
                score,
                category,
            ),
        )

        rid = cur.lastrowid

    audit(
        user["id"],
        "complete",
        "screening_result",
        rid,
    )

    return {
        "id": rid,
        "score": score,
        "category": category,
        "instrument": (
            "NC360 Demonstration Screener"
        ),
        "disclaimer": (
            "This screening result is not a diagnosis. "
            "Autism can only be assessed appropriately "
            "by qualified healthcare or developmental "
            "professionals."
        ),
    }


@app.get("/api/screenings/history")
def screening_history(
    request: Request,
):
    user = require_roles(
        request,
        "parent",
        "admin",
    )

    with db() as con:
        rows = con.execute(
            """
            SELECT *
            FROM screening_results
            WHERE user_id=?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


# =========================================================
# PROFESSIONAL DIRECTORY
# =========================================================

@app.get("/api/professionals")
def professionals(
    city: str | None = None,
    specialization: str | None = None,
    verified: bool = True,
):
    sql = """
    SELECT *
    FROM professionals
    WHERE 1=1
    """

    params = []

    if verified:
        sql += " AND verified=1"

    if city:
        sql += """
        AND lower(city)=lower(?)
        """
        params.append(city)

    if specialization:
        sql += """
        AND lower(specialization)
        LIKE lower(?)
        """
        params.append(
            "%" + specialization + "%"
        )

    sql += """
    ORDER BY
        verified DESC,
        experience_years DESC
    """

    with db() as con:
        rows = con.execute(
            sql,
            params,
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


# =========================================================
# APPOINTMENTS
# =========================================================

@app.post("/api/appointments")
def appointment(
    payload: AppointmentIn,
    request: Request,
):
    user = current_user(request)

    with db() as con:
        professional = con.execute(
            """
            SELECT 1
            FROM professionals
            WHERE id=?
              AND verified=1
            """,
            (
                payload.professional_id,
            ),
        ).fetchone()

        if not professional:
            raise HTTPException(
                404,
                "Professional not found",
            )

        cur = con.execute(
            """
            INSERT INTO appointments(
                requester_user_id,
                professional_id,
                requested_date,
                mode,
                note
            )
            VALUES(?,?,?,?,?)
            """,
            (
                user["id"],
                payload.professional_id,
                payload.requested_date,
                payload.mode,
                payload.note,
            ),
        )

        aid = cur.lastrowid

    audit(
        user["id"],
        "request",
        "appointment",
        aid,
    )

    return {
        "id": aid,
        "status": "requested",
    }


@app.get("/api/appointments")
def appointments(
    request: Request,
):
    user = current_user(request)

    with db() as con:
        rows = con.execute(
            """
            SELECT
                a.*,
                p.name AS professional_name,
                p.title AS professional_title

            FROM appointments a

            JOIN professionals p
                ON p.id=a.professional_id

            WHERE a.requester_user_id=?

            ORDER BY a.created_at DESC
            """,
            (
                user["id"],
            ),
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


# =========================================================
# NEUROGUIDE AI
# =========================================================

@app.post("/api/chat")
def chat(
    payload: ChatIn,
    request: Request,
):
    user = current_user(
        request,
        False,
    )

    q = payload.message.lower()

    emergency_terms = [
        "suicide",
        "kill myself",
        "not breathing",
        "unconscious",
        "severe injury",
    ]

    if any(
        term in q
        for term in emergency_terms
    ):
        answer = (
            "If there is immediate danger or a medical "
            "emergency, contact local emergency services "
            "or go to the nearest emergency department now. "
            "NeuroGuide AI cannot provide emergency care."
        )

        sources = []

    elif (
        "ear" in q
        or "sound" in q
        or "sensory" in q
    ):
        answer = (
            "Covering the ears can be a way to reduce "
            "uncomfortable sound input. Some autistic people "
            "experience sounds as unusually intense or "
            "unpredictable. Helpful supports may include "
            "reducing background noise, offering a quieter "
            "space, warning before loud sounds, and respecting "
            "safe hearing protection. A qualified professional "
            "can help if sound sensitivity is affecting daily life."
        )

        sources = [
            {
                "name": "NICE CG170",
                "url": (
                    "https://www.nice.org.uk/"
                    "guidance/cg170"
                ),
            },
            {
                "name": "WHO Autism fact sheet",
                "url": (
                    "https://www.who.int/news-room/"
                    "fact-sheets/detail/"
                    "autism-spectrum-disorders"
                ),
            },
        ]

    elif "speech therapy" in q:
        answer = (
            "Speech and language therapy can support "
            "functional communication, understanding, "
            "social communication, speech clarity where "
            "relevant, and use of AAC. Goals should be "
            "individualized and agreed with the person or "
            "family rather than assuming speech is the only "
            "valid form of communication."
        )

        sources = [
            {
                "name": "NICE CG170",
                "url": (
                    "https://www.nice.org.uk/"
                    "guidance/cg170"
                ),
            }
        ]

    else:
        answer = (
            "NeuroGuide AI can provide educational information "
            "about autism, communication, sensory differences, "
            "classroom support, visual schedules, therapies "
            "and family support. This MVP uses a curated "
            "response layer; production deployment should "
            "connect this interface to an approved RAG "
            "knowledge base with clinical-content governance."
        )

        sources = [
            {
                "name": "WHO Autism fact sheet",
                "url": (
                    "https://www.who.int/news-room/"
                    "fact-sheets/detail/"
                    "autism-spectrum-disorders"
                ),
            }
        ]

    if user:
        audit(
            user["id"],
            "chat",
            "ai_conversation",
        )

    return {
        "answer": answer,
        "sources": sources,
        "disclaimer": (
            "Educational support only; not a diagnosis "
            "or substitute for professional care."
        ),
    }


# =========================================================
# ADMIN
# =========================================================

@app.get("/api/admin/summary")
def admin_summary(
    request: Request,
):
    require_roles(
        request,
        "admin",
    )

    tables = {
        "users": "users",
        "children": "child_profiles",
        "screenings": "screening_results",
        "professionals": "professionals",
        "appointments": "appointments",
        "resources": "resources",
    }

    with db() as con:
        return {
            key: con.execute(
                f"SELECT COUNT(*) c FROM {table}"
            ).fetchone()["c"]
            for key, table in tables.items()
        }
