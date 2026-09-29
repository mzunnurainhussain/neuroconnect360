# NeuroConnect 360 — Architecture

## Phase-1 runtime

```mermaid
flowchart TD
  U[Users] --> W[Responsive Web UI]
  W --> API[FastAPI REST API]
  API --> A[Secure Cookie Authentication + RBAC]
  API --> US[User & Child Profile Service]
  API --> RS[Resource Service]
  API --> SS[Screening Support Service]
  API --> MS[Milestone Service]
  API --> PS[Professional Directory]
  API --> AS[Appointment Service]
  API --> AI[NeuroGuide AI Safety Layer]
  US & RS & SS & MS & PS & AS --> DB[(SQLite local / PostgreSQL production)]
  API --> AUD[Audit Log]
```

## Target production architecture

```mermaid
flowchart TD
  C[Web / Future Mobile Clients] --> CDN[CDN / WAF]
  CDN --> G[API Gateway]
  G --> AUTH[Identity, MFA, RBAC]
  G --> CORE[Modular Core API]
  G --> AIS[AI Service]
  CORE --> PG[(PostgreSQL)]
  CORE --> REDIS[(Redis)]
  CORE --> OBJ[(Encrypted Object Storage)]
  AIS --> SAFE[Safety & Policy Layer]
  SAFE --> RET[Retrieval Service]
  RET --> VDB[(pgvector / Vector DB)]
  VDB --> KB[Approved Knowledge Base]
  SAFE --> LLM[LLM Provider / Model]
  CORE --> OBS[Logs, Metrics, Alerts, Audit]
```

## Safety boundary

NeuroGuide AI and screening-support features are deliberately separated from diagnosis. Any production AI response pipeline should implement approved-source retrieval, citation generation, uncertainty communication, emergency escalation, medical-safety validation, user feedback, and professional governance.

## RBAC

Initial roles: Parent/Caregiver, Professional, Teacher, Researcher, Administrator. The schema is intentionally extensible toward granular Roles/Permissions tables in the full implementation.
