# NeuroConnect 360 — Phase 1 MVP

A runnable full-stack MVP for **NeuroConnect 360: An AI-Driven Multilingual Ecosystem for Autism Awareness, Early Screening, Personalized Support, Education, Professional Collaboration, and Research**.

## Implemented in this MVP

- Premium responsive public landing page
- English / Urdu / Roman Urdu UI switcher
- Registration, login, logout, secure cookie sessions
- Role-aware onboarding foundations (Parent/Caregiver, Professional, Teacher, Researcher)
- Parent dashboard with multiple child profiles
- Developmental milestone tracker
- Autism awareness/resource library with filtering
- Screening-support workflow with consent, non-diagnostic result language, history and safety disclaimer
- Verified professional directory
- Appointment request workflow
- NeuroGuide AI evidence-grounded **demo shell** with safety rules and source citations
- Admin-ready content/resource APIs
- Audit logging foundation
- SQLite local database for zero-friction development
- OpenAPI/Swagger at `/docs`

## Important medical-safety note

This implementation is an educational/support MVP. It does **not** diagnose autism, recommend prescription medication, or replace qualified healthcare/developmental professionals. The included screening demonstration is intentionally **not a copyrighted standardized instrument** and does not reproduce M-CHAT-R/F, AQ, CAST, ASSQ, or other restricted instruments.

## Run locally

Requires Python 3.11+ with FastAPI and Uvicorn.

```bash
cd neuroconnect360
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open: http://127.0.0.1:8000

Swagger: http://127.0.0.1:8000/docs

### Demo accounts

- Parent: `parent@neuroconnect.local` / `DemoParent123!`
- Professional: `therapist@neuroconnect.local` / `DemoProfessional123!`
- Admin: `admin@neuroconnect.local` / `DemoAdmin123!`

## Project structure

```text
neuroconnect360/
├── app/
│   ├── auth.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   └── seed.py
├── static/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── data/
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── tests/
│   └── smoke_test.py
└── README.md
```

## Production hardening before real deployment

Replace SQLite with PostgreSQL, use managed object storage, add email verification/MFA, CSRF tokens for state-changing cookie-auth requests, Redis-backed rate limiting, malware scanning for uploads, managed secrets, independent clinical/content governance, legal/licensing review for any standardized screening instrument, consent/version policies, security testing, observability, backups, data retention policies, and jurisdiction-specific privacy/child-safeguarding review.

## Deploy to Vercel

This package includes a root `app.py` FastAPI entrypoint for Vercel's zero-configuration Python/FastAPI runtime.

### GitHub + Vercel dashboard

1. Create a new GitHub repository, for example `neuroconnect360`.
2. Push the contents of this folder (the folder containing `app.py`) to the repository root.
3. In Vercel choose **Add New → Project**, import the GitHub repository, and deploy.
4. Vercel should detect **FastAPI** automatically. Do not set a Node.js build command.
5. After deployment verify `/`, `/api/health`, and `/docs`.

### Vercel CLI

```bash
npm install -g vercel
vercel login
vercel
vercel --prod
```

### Important database note

The included Vercel demo uses SQLite in `/tmp`, which is **ephemeral** on serverless infrastructure. It is suitable only for a demonstration deployment. Registrations and other writes can disappear when the function instance is recycled. Before using NeuroConnect 360 with real users, migrate the database to managed PostgreSQL (for example Neon/Vercel Postgres) and store secrets in Vercel Environment Variables.
