# Expense Analyzer

Expense tracking web application with a **FastAPI** JSON backend and a **vanilla HTML/CSS/JS** frontend. Both apps live in this repo and are served from one process for same-origin cookie sessions.

**License:** GNU General Public License v3.0

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Browser (frontend/*.html + js/)        │
│  fetch(..., { credentials: "include" }) │
└──────────────────┬──────────────────────┘
                   │ HTTP + session cookie
                   ▼
┌─────────────────────────────────────────┐
│  FastAPI (backend/app)                  │
│  /api/auth  /api/expenses  /api/reports │
│  SessionMiddleware (HttpOnly cookie)    │
│  StaticFiles → frontend/ at /           │
└──────────┬──────────────────┬───────────┘
           │                  │
           ▼                  ▼
     MySQL user_details   AWS DynamoDB expense_table
```

| Store | Purpose |
|-------|---------|
| **MySQL** | User metastore (`user_details`) — auth, profile |
| **AWS DynamoDB** | Expense transactions (`expense_table`) |

---

## Repository layout

```
expense_analyzer/
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .env.example
│   └── app/
│       ├── main.py              # FastAPI app, session, CORS, static mount
│       ├── config.py            # Settings from env
│       ├── database.py          # SQLAlchemy engine / sessions
│       ├── deps.py              # get_current_user from session
│       ├── models/user.py
│       ├── schemas/
│       ├── routers/             # auth, expenses, reports
│       └── services/            # auth, password, dynamodb, analytics
├── frontend/
│   ├── index.html               # Dashboard / landing
│   ├── login.html
│   ├── signup.html
│   ├── report.html
│   ├── css/
│   ├── js/
│   └── images/
├── LICENSE
└── README.md
```

---

## Features

- User signup / login / logout with **bcrypt** passwords and **signed session cookies** (1-day lifetime)
- Same credential validation rules as the previous Flask app (including `admin` / `1234` bypass)
- Manual expense entry into DynamoDB (scoped by username)
- Bill file upload stub (accepts `.jpg` / `.pdf`; parsing not implemented)
- Monthly quick reports (last 3 months) and custom date-range reports
- Server-side matplotlib charts returned as base64 PNGs

---

## API surface

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | Public | Set session cookie |
| POST | `/api/auth/signup` | Public | Create user |
| POST | `/api/auth/logout` | Required | Clear session |
| GET | `/api/auth/me` | Optional | Auth status + months list |
| POST | `/api/expenses` | Required | Add expense |
| POST | `/api/expenses/upload` | Required | Upload bill (stub) |
| GET | `/api/reports/months` | Required | Last three month labels |
| POST | `/api/reports/by-month` | Required | Report for a calendar month |
| POST | `/api/reports/by-date-range` | Required | Report for date range |
| GET | `/api/health` | Public | Health check |

Interactive docs: `http://127.0.0.1:8000/docs` (when the API is running and not shadowed — use `/api` routes; OpenAPI is at `/docs` if registered before the static mount).

---

## Authentication

- Starlette `SessionMiddleware` stores `user_id` in a signed **HttpOnly** cookie (`expense_session` by default).
- Cookie: `SameSite=lax`, max age **1 day**.
- Protected routes use `Depends(get_current_user)`; unauthenticated calls return **401**.
- Frontend always calls the API with `credentials: "include"`.

Set a stable `SESSION_SECRET_KEY` in production (do not rely on a weak default).

---

## Configuration

Copy [`backend/.env.example`](backend/.env.example) to `backend/.env` and fill in values:

| Variable | Purpose |
|----------|---------|
| `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | MySQL metastore |
| `AWS_ACCESS_KEY` / `AWS_SECRET_KEY` | DynamoDB credentials |
| `DB_REGION` | AWS region (default `ap-south-1`) |
| `TABLE_NAME` | DynamoDB table (default `expense_table`) |
| `SESSION_SECRET_KEY` | Session cookie signing key |
| `CORS_ORIGINS` | Comma-separated origins for credentialed CORS |

---

## Setup & run

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- MySQL with `user_details` (created via `init_db` on startup when reachable)
- DynamoDB table `expense_table` in the configured region

### Local development

Backend dependencies are declared in `backend/pyproject.toml` and locked in `backend/uv.lock`. Install and run with **uv** (not pip):

```bash
cd backend
uv sync
cp .env.example .env        # then edit secrets

uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` — the frontend is served from the same origin so session cookies work.

### WSGI / production note

This app is ASGI (FastAPI/uvicorn), not Flask WSGI. Deploy with uvicorn/gunicorn+uvicorn workers, or an ASGI-compatible host.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Data model (unchanged)

### MySQL — `user_details`

`u_key`, `uid`, `username`, `password` (bcrypt), `first_name`, `last_name`, `email`, `family_size`, `create_date`, `end_date`, `active`

### DynamoDB — `expense_table`

`Pid`, `year_month`, `byr_name`, `CommodityName`, `Price`, `Purchase_date`, `CommodityType`

---

## Usage

1. Open `/` → Login or Signup  
2. Add an expense or upload a bill file (upload is a stub)  
3. Open a month report or search a date range  
4. Review table + charts on `/report.html`  
5. Logout from the menu  

---

## Migration notes

- Replaced Flask + Jinja + Flask-Login with FastAPI + cookie sessions + static frontend.
- React SPA migration is intentionally deferred; the API is already JSON so a React client can be added later without changing DynamoDB/MySQL logic.
