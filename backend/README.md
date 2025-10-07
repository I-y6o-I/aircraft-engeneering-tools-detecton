# Aero Kit Check — Backend

FastAPI service for aircraft tools detection workflow (hackathon prototype).

## How to start - easy way

Запускаем базу данных:

```json
docker compose -f docker-compose.dev.yml up -d db
```

Запускаем backend и frontend:

```json
docker compose -f docker-compose.dev.yml up -d backend frontend
```

Применяем миграции:

```json
docker exec akc\_backend alembic upgrade head
```

## Endpoints

### Prediction endpoints (no auth required)

- **POST `/predict`** — one-off recognition (no auth, no storage).
  Input:

  ```json
  { "image": "<base64-string>", "threshold": 0.98 }
  ```

  Output: classes catalog (11), detections (can be < or > 11; duplicates allowed), `not_found`, `summary`.
- **POST `/predict/adjust`** — accept final annotations after user edits (no auth).
  Rules: exactly **11** annotations, **each class once**, bbox in `[0..1]`.
  Output:

  ```json
  { "ok": true | false, "issues": [ "...optional errors..." ], "count": 11 }
  ```

### Auth endpoints

- **POST `/auth/register`** — register new user (choose role: simple|admin).
  Input:

  ```json
  { "employee_id": "EMP12345", "password": "StrongP@ssw0rd", "role": "simple" }
  ```

  Output:

  ```json
  { "user_id": "uuid", "employee_id": "EMP12345", "role": "simple", "created_at": "2025-09-28T10:20:00Z" }
  ```
- **POST `/auth/login`** — login and receive access JWT.
  Input:

  ```json
  { "employee_id": "EMP12345", "password": "StrongP@ssw0rd" }
  ```

  Output:

  ```json
  { "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "Bearer", "expires_in": 28800 }
  ```
- **GET `/auth/me`** — get profile of current user (requires `Authorization: Bearer <token>`).
  Output:

  ```json
  { "user_id": "uuid", "employee_id": "EMP12345", "role": "simple" }
  ```

### Example auth flow

```bash
# Register user
curl -X POST http://127.0.0.1:8000/auth/register   -H "Content-Type: application/json"   -d '{"employee_id":"EMP12345","password":"StrongP@ssw0rd","role":"simple"}'

# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login   -H "Content-Type: application/json"   -d '{"employee_id":"EMP12345","password":"StrongP@ssw0rd"}' | jq -r .access_token)

# Current profile
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/auth/me
```

### Session Management endpoints (auth required)

- **POST `/sessions/handout`** — create new handout session.
  Input:

  ```json
  { "threshold": 0.95, "notes": "Shift A" }
  ```

  Output:

  ```json
  { "session_id": "uuid", "status": "draft", "threshold_used": 0.95, "created_at": "2025-09-28T10:30:00Z" }
  ```
- **POST `/sessions/{id}/handout/predict`** — run prediction for handout stage.
- **POST `/sessions/{id}/handout/adjust`** — submit final handout annotations.
- **POST `/sessions/{id}/issue`** — mark session as "issued".
- **POST `/sessions/{id}/handover/predict`** — run prediction for handover stage.
- **POST `/sessions/{id}/handover/adjust`** — submit final handover annotations.
- **GET `/sessions/{id}/diff`** — show differences between handout and handover.
- **POST `/sessions/{id}/finalize`** — complete session with "returned" status.
- **GET `/sessions`** — list sessions with role-based access (admins see all, simple users see only their own).
- **GET `/sessions/{id}`** — get detailed session information.

#### Role-based access control:

- **Simple users**: Can only view/manage their own sessions
- **Admin users**: Can view/manage all sessions including other users' sessions

## Health

- **GET `/healthz`** → `{ "status": "ok" }`
- **GET `/version"`** → service name & version

## Quick start (local)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e .
uvicorn src.app:app --reload --port 8000
```

Open Swagger: http://127.0.0.1:8000/docs

### Example request

```bash
curl -X POST http://127.0.0.1:8000/predict   -H "Content-Type: application/json"   -d '{"image":"base64demo","threshold":0.98}' | jq .
```

## Docker

Build & run:

```bash
cd backend
docker build -t aero-kit-check-backend:dev .
# (optional) cp .env.example .env and edit values
docker run --rm -p 8000:8000 --env-file .env aero-kit-check-backend:dev
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

## Environment variables

Service works with defaults; `.env` is optional. Use `.env.example` as a template.

```
APP_NAME=Aero Kit Check Backend
HOST=0.0.0.0
PORT=8000

# Use JSON list or "*" (CSV in .env is not supported)
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
# or
# CORS_ORIGINS="*"

# Security (dev placeholder — replace in prod)
JWT_SECRET=dev-secret-please-change

# External ML service (optional; we use local stub for now)
# ML_ENDPOINT=http://ml:9000/infer

# Database (required for /sessions/* endpoints)
DATABASE_URL=postgresql+asyncpg://akc:akc@localhost:5432/akc

# Optional override for classes catalog (JSON or CSV)
# CLASSES=["screwdriver_plus","wrench_adjustable","offset_cross","ring_wrench_3_4","nippers","brace","lock_pliers","pliers","shernitsa","screwdriver_minus","oil_can_opener"]
```

> Tip: for dev you can set `CORS_ORIGINS` to `"*"`. If you use cookies/credentials, set an explicit list of origins.

## Docker Compose (optional)

If you want to run Postgres together with the backend, create `docker-compose.dev.yml` and run:

```bash
docker compose -f docker-compose.dev.yml up --build
```

- API: http://127.0.0.1:8000
- DB exposed on `localhost:5432` (user/db/pass: `akc`/`akc`/`akc`)

Apply migrations (once you add SQLAlchemy/Alembic deps):

```bash
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

## Project structure

```
backend/
├─ src/
│  ├─ app.py                 # FastAPI app entrypoint
│  ├─ core/                  # settings, logging, db, auth, security
│  ├─ models/                # SQLAlchemy models (User, Session)
│  ├─ services/              # business logic services
│  └─ api/
│     ├─ routers/            # endpoints (/predict, /auth/*, /sessions/*)
│     └─ schemas/            # Pydantic models (requests/responses)
├─ tests/                    # comprehensive test suite (55 tests)
│  ├─ conftest.py            # pytest configuration and fixtures
│  ├─ test_predict.py        # prediction endpoints tests
│  ├─ test_auth.py           # authentication tests
│  ├─ test_sessions.py       # session management tests
│  ├─ test_validation.py     # input validation tests
│  ├─ test_security.py       # security and authorization tests
│  ├─ test_integration.py    # integration workflow tests
│  ├─ test_config.py         # configuration tests
│  └─ test_simplified.py     # simplified test suite
├─ alembic/                  # database migrations
├─ Dockerfile                # containerized backend
├─ .dockerignore             # build context exclusions
├─ .env.example              # template for local env
└─ pyproject.toml            # deps & setuptools (src/ layout)
```

## Tests

The project includes comprehensive test coverage with 55 tests across multiple categories:

### Install test dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### Run tests

#### All tests (requires database connection):

```bash
# Set DATABASE_URL for tests that require database
DATABASE_URL="postgresql+asyncpg://akc:akc@localhost:5432/akc" pytest -v
```

#### Tests without database dependency:

```bash
# Run core functionality tests (16 tests pass reliably)
pytest tests/test_predict.py tests/test_validation.py::test_predict_validation tests/test_validation.py::test_predict_adjust_validation_errors tests/test_validation.py::test_edge_cases tests/test_validation.py::test_cors_and_options tests/test_validation.py::test_content_type_validation tests/test_config.py::test_app_configuration tests/test_config.py::test_error_handling tests/test_config.py::test_response_formats tests/test_simplified.py::test_predict_endpoints tests/test_simplified.py::test_error_handling tests/test_simplified.py::test_app_health -v
```

### Test categories

- **`test_predict.py`** — Prediction endpoints testing
- **`test_validation.py`** — Input validation and edge cases
- **`test_auth.py`** — Authentication flow testing
- **`test_sessions.py`** — Session management endpoints
- **`test_security.py`** — Security and authorization tests
- **`test_integration.py`** — Full workflow integration tests
- **`test_config.py`** — Application configuration tests
- **`test_simplified.py`** — Simplified test suite for CI/CD

## Database Setup

For session management endpoints, you need PostgreSQL running:

```bash
# Using Docker Compose (recommended for development)
docker compose -f docker-compose.dev.yml up -d

# Run migrations
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

Or set up PostgreSQL manually and configure `DATABASE_URL` in your `.env` file.

## Session Workflow Example

```bash
# Register admin user
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"ADMIN001","password":"admin123","role":"admin"}'

# Login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"ADMIN001","password":"admin123"}' | jq -r .access_token)

# Create handout session
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8000/sessions/handout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"threshold":0.95,"notes":"Test session"}' | jq -r .session_id)

# Run handout prediction
curl -X POST http://127.0.0.1:8000/sessions/$SESSION_ID/handout/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image":"base64_test_image","threshold":0.95}'

# List sessions (role-based access)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/sessions
```

## Notes

- `/predict` may return fewer or more than 11 detections and may contain duplicates of the same class — this is expected.
- `/predict/adjust` must receive exactly 11 annotations, one per class; server validates and rejects duplicates/missing/invalid bboxes.
- `/auth` endpoints manage users with role = simple|admin.
- **Database is required** for `/sessions/*` endpoints.
- Session management implements role-based access control (RBAC).
