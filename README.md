# Expense Analyzer

A Flask WSGI web application for tracking personal expenses, generating analytics reports, and managing user accounts. Expenses are stored in AWS DynamoDB; user credentials and profiles live in MySQL. The app is designed to run as a WSGI service (e.g. on PythonAnywhere).

**License:** GNU General Public License v3.0

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Repository Structure](#repository-structure)
4. [Technology Stack](#technology-stack)
5. [Features](#features)
6. [Data Model](#data-model)
7. [Application Routes](#application-routes)
8. [Module Reference](#module-reference)
9. [Configuration](#configuration)
10. [Authentication & Security](#authentication--security)
11. [Analytics & Reporting](#analytics--reporting)
12. [Setup & Deployment](#setup--deployment)
13. [Usage Guide](#usage-guide)

---

## Overview

Expense Analyzer lets registered users:

- Add expenses manually (date, product, type, price)
- Upload bill images/PDFs (UI present; parsing not fully implemented)
- View reports for the last three months or a custom date range
- See pie charts and trend graphs for spending patterns
- Register, log in, and log out with bcrypt-hashed passwords

The application uses a dual-database design:

| Store | Purpose |
|-------|---------|
| **MySQL** | User metastore (`user_details`) — auth, profile, password history |
| **AWS DynamoDB** | Expense transactions (`expense_table`) — purchases, credits, analytics |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Client (Browser)                             │
│         Templates: main_page | login | signup | month_report            │
│         Static: CSS + background image                                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP (GET/POST)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Flask WSGI Application (main.py)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Flask-Login  │  │ Flask-       │  │ Flask-       │  │ Jinja2      │  │
│  │ LoginManager │  │ Bootstrap    │  │ SQLAlchemy   │  │ Templates   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                                         │
│  Routes: /  /login  /signup  /logout                                    │
│          /add_expense/submit  /add_expense/submit_file                  │
│          /view_expense/<month>  /view_expense/date_range                │
└──────────┬───────────────────────────────┬──────────────────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────┐     ┌────────────────────────────────────────────┐
│   frontend/          │     │              scripts/                      │
│  ┌────────────────┐  │     │  ┌─────────────────┐  ┌─────────────────┐  │
│  │ login.py       │  │     │  │ aws_functions.py│  │ analytics_      │  │
│  │ authenticate   │  │     │  │ query/push      │  │ functions.py    │  │
│  │ create_user    │  │     │  │ DynamoDB        │  │ generate_graphs │  │
│  │ update_password│  │     │  └────────┬────────┘  └────────┬────────┘  │
│  └───────┬────────┘  │     │           │                    │           │
│  ┌───────▼────────┐  │     │  ┌────────▼────────┐  ┌────────▼────────┐  │
│  │ user.py        │  │     │  │ passwordhash.py │  │ matplotlib      │  │
│  │ User model     │  │     │  │ bcrypt hashing  │  │ base64 PNG      │  │
│  │ SQLAlchemy db  │  │     │  └─────────────────┘  └─────────────────┘  │
│  └───────┬────────┘  │     └───────────┬────────────────────────────────┘
│  ┌───────▼────────┐  │                 │
│  │ validation.py  │  │                 │
│  │ form regex     │  │                 │
│  └────────────────┘  │                 │
└──────────┬───────────┘                 │
           │                             │
           ▼                             ▼
┌──────────────────────┐     ┌──────────────────────┐
│   MySQL (metastore)  │     │  AWS DynamoDB        │
│  user_details table  │     │  expense_table       │
│  Host: PythonAnywhere│     │  Region: ap-south-1  │
└──────────────────────┘     └──────────────────────┘

                    configs/keys.py
         (MySQL creds, AWS keys, graph categories, secrets)
```

### Request flow (add expense)

```
Browser form POST /add_expense/submit
        → @login_required
        → push_to_dynamodb(form_data, username)
        → DynamoDB put_item
        → flash success → redirect /
```

### Request flow (view report)

```
Browser POST /view_expense/<month>  or  /view_expense/date_range
        → @login_required
        → query_dynamodb(...)
        → pandas DataFrame (debits/credits/net outstanding)
        → generate_graphs(...) → base64 PNG charts
        → render month_report.html
```

---

## Repository Structure

```
expense_analyzer/
├── main.py                 # Flask app entry point, routes, LoginManager setup
├── configs/
│   ├── __init__.py
│   └── keys.py             # DB credentials, AWS keys, graph category lists
├── frontend/
│   ├── __init__.py
│   ├── user.py             # User SQLAlchemy model + db instance
│   ├── login.py            # Auth: authenticate, create_user, update_password
│   └── validation.py       # Login form username/password regex validation
├── scripts/
│   ├── __init__.py
│   ├── aws_functions.py    # DynamoDB query/push, month helpers
│   ├── analytics_functions.py  # Chart generation (pie + bar)
│   └── passwordhash.py     # bcrypt PasswordHasher utility
├── templates/
│   ├── main_page.html      # Dashboard: add expense + view reports
│   ├── login_page.html
│   ├── signup_page.html
│   └── month_report.html   # Table + charts report view
├── static/
│   ├── main_page.css
│   ├── login_page.css
│   ├── month_report.css
│   └── images/
│       └── pexels-rdne-7947716.jpg
├── maintenance/
│   └── temp.py             # One-off CSS responsive enhancement utility
├── LICENSE                 # GPLv3
└── README.md
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Web framework | Flask (WSGI) |
| UI | Flask-Bootstrap, Jinja2 templates, custom CSS |
| Auth | Flask-Login, bcrypt |
| ORM | Flask-SQLAlchemy / SQLAlchemy |
| User DB | MySQL |
| Expense DB | AWS DynamoDB (boto3) |
| Analytics | pandas, numpy, matplotlib |
| Hosting target | PythonAnywhere-style WSGI deployment |

### Implied Python dependencies

```
flask
flask-bootstrap
flask-login
flask-sqlalchemy
sqlalchemy
boto3
bcrypt
pandas
numpy
matplotlib
pymysql   # or another MySQL driver compatible with SQLAlchemy
```

> There is no `requirements.txt` in the repo yet; the list above is inferred from imports.

---

## Features

### Implemented

- User registration (username, email, name, password, family size)
- Login / logout with session management (1-day login duration)
- Form validation (username ≥ 8 alphanumeric/underscore; strong password rules)
- Manual expense entry with commodity type dropdown
- Expense storage in DynamoDB scoped by username (`byr_name`)
- Monthly quick-view buttons (last 3 calendar months)
- Custom date-range expense search
- Report table with Debits, Credits, and running Net Outstanding
- Three analytics charts embedded as base64 PNGs
- Flash messages for success/error feedback

### Partial / planned

- Bill file upload UI (`/add_expense/submit_file`) accepts `.jpg`/`.pdf` but does not yet parse or persist file contents
- Password update/history logic exists in `frontend/login.py` (`update_password`) but is not exposed via a route
- Menu bar links on the main page are placeholders and not wired correctly

---

## Data Model

### MySQL — `user_details`

| Column | Type | Notes |
|--------|------|-------|
| `u_key` | String(100) PK | Secure random token |
| `uid` | Integer | Logical user id (used by Flask-Login `get_id`) |
| `username` | String(100) | Login name |
| `password` | String(100) | bcrypt hash |
| `first_name` | String(100) | |
| `last_name` | String(100) | |
| `email` | String(100) | |
| `family_size` | Integer | |
| `create_date` | String(30) | Timestamp string |
| `end_date` | String(30) | Soft-delete / version end (`9999-12-31` when active) |
| `active` | String(1) | `'Y'` / `'N'` — supports password history versioning |

### DynamoDB — `expense_table`

| Attribute | Type | Notes |
|-----------|------|-------|
| `Pid` | String | Per-month sequential id (zero-padded) |
| `year_month` | String | `YYYYMM` partition-style filter key |
| `byr_name` | String | Username who owns the expense |
| `CommodityName` | String | Product/item name |
| `Price` | Number | Amount |
| `Purchase_date` | String | `YYYY-MM-DD` |
| `CommodityType` | String | Category (Food, Bills, Salary, etc.) |

**Commodity types (UI):** Salary, Credits, Food, Transportation, Entertainment, Grocery, Green-Grocery, Clothes, Bills, House-rent, Other-rents, Miscellaneous

**Graph groupings (`configs/keys.py`):**

- Graph 1 (high-level): Bills, Rents, Transportation, Others  
  (`House-rent` / `Other-rents` → Rents)
- Graph 2 (detail): Grocery, Green-Grocery, Food, Entertainment, Clothes, Miscellaneous

---

## Application Routes

| Method | Path | Auth | Handler | Description |
|--------|------|------|---------|-------------|
| GET | `/` | Optional | `index` | Landing/dashboard; months list if logged in |
| GET/POST | `/login` | Public | `login` | Authenticate and start session |
| GET/POST | `/signup` | Public | `signup` | Create user account |
| GET/POST | `/logout` | Required | `logout` | End session |
| POST | `/add_expense/submit` | Required | `add_expense_to_file` | Persist expense to DynamoDB |
| POST | `/add_expense/submit_file` | Required | `parse_file` | File upload stub |
| POST | `/view_expense/<month>` | Required | `get_report` | Monthly report + charts |
| POST | `/view_expense/date_range` | Required | `get_expense` | Date-range report + charts |

Unauthenticated access to protected routes redirects to `/login`.

---

## Module Reference

### `main.py`

Application factory/setup and all HTTP routes. Initializes:

- SQLAlchemy with MySQL URI from `configs.keys`
- Flask-Login (`LoginManager`, `user_loader` by `uid`)
- Flask-Bootstrap
- Random `SECRET_KEY` per process start via `SECRET_KEY_GEN()`

Run locally: `python main.py` (Flask development server).

### `frontend/user.py`

Defines `db = SQLAlchemy()` and the `User` model (`UserMixin`). `get_id()` returns `str(uid)` for session identity.

### `frontend/login.py`

- `check_user` — active user existence check  
- `authenticate` — bcrypt verify against active user  
- `create_user` — insert new `user_details` row  
- `update_password` — versioned password history (expiry + max history from config); not routed yet  

### `frontend/validation.py`

Regex rules for login forms; special-case bypass for `admin` / `1234`.

### `scripts/aws_functions.py`

- `query_dynamodb(data, user)` — scan by month string or date-range dict; builds debit/credit/net columns  
- `push_to_dynamodb(data, user)` — allocate next `Pid` for `year_month`, `put_item`  
- `get_last_three_months()` — labels for dashboard quick buttons  
- `add_attribute()` — maintenance helper to backfill `byr_name`  

### `scripts/analytics_functions.py`

- `generate_graphs(df, dates_range)` → `(expense_pie, small_expense_pie, trend_bar)` as base64 PNG  
- Filters out Salary/Credits from spend charts  
- Fills missing dates for continuous trend bars  

### `scripts/passwordhash.py`

`PasswordHasher`: bcrypt (12 rounds), verify, secure token generation.

### `maintenance/temp.py`

Utility to inject responsive CSS media queries into files under `static/`.

---

## Configuration

All runtime secrets and environment constants live in `configs/keys.py`:

| Variable | Purpose |
|----------|---------|
| `MYSQL_HOST` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | MySQL metastore connection |
| `AWS_ACCESS_KEY` / `AWS_SECRET_KEY` | DynamoDB credentials |
| `DB_REGION` | AWS region (default `ap-south-1`) |
| `TABLE_NAME` | DynamoDB table (`expense_table`) |
| `PASS_EXPIRY` | Password age limit in days (30) |
| `MAX_PASS_HISTORY` | Retained password versions (3) |
| `SECRET_KEY_GEN` | Lambda generating Flask secret key |
| `GRAPH1_COMM_TYPES` / `GRAPH2_COMM_TYPES` | Chart category buckets |

**Important:** AWS and MySQL secrets are currently empty placeholders in source (keys were removed from git history). Populate them via environment-specific config before running; do not commit real credentials.

---

## Authentication & Security

1. Passwords hashed with **bcrypt** (12 rounds); plaintext never stored  
2. Sessions via **Flask-Login**; login duration set to 1 day  
3. Protected routes use `@login_required`  
4. Login input validated with regex (length, complexity)  
5. User rows support soft versioning (`active`, `end_date`) for password history  
6. Flask `SECRET_KEY` regenerated on each process start  

**Caveats to be aware of when hardening:**

- Credentials and AWS keys are stored in a Python module (prefer env vars / secret manager)  
- `admin`/`1234` bypass in validation is a development convenience  
- DynamoDB access uses `scan` + filter (fine for small datasets; consider keys/indexes at scale)  
- No CSRF tokens on forms beyond Flask session secret  

---

## Analytics & Reporting

For a successful query, the report page shows:

1. **Transaction table** — Purchase date, commodity, type, Debits, Credits, Net Outstanding (running balance). Final row is a totals summary.  
2. **Expense Distribution (pie)** — High-level categories (Bills / Rents / Transportation / Others)  
3. **Small Expense Distribution (pie)** — Grocery, Food, Entertainment, etc.  
4. **Trend Analysis (bar)** — Daily total expense vs. transaction count across the period  

Charts are rendered server-side with matplotlib and embedded as `data:image/png;base64,...` in `month_report.html`.

---

## Setup & Deployment

### Prerequisites

- Python 3.8+  
- MySQL database with `user_details` table (auto-created via `db.create_all()` on startup if permissions allow)  
- AWS account with DynamoDB table `expense_table` in the configured region  
- Network access from the host to MySQL and AWS  

### Local development

```bash
# 1. Clone
git clone <repo-url>
cd expense_analyzer

# 2. Create and activate a virtualenv, then install dependencies
pip install flask flask-bootstrap flask-login flask-sqlalchemy sqlalchemy \
            boto3 bcrypt pandas numpy matplotlib pymysql

# 3. Configure configs/keys.py with MySQL + AWS credentials

# 4. Ensure DynamoDB table exists with expected attributes

# 5. Run
python main.py
```

### WSGI deployment (e.g. PythonAnywhere)

Point the WSGI entry to the Flask `app` object in `main.py`:

```python
# typical WSGI file pattern
import sys
path = '/home/<user>/expense_analyzer'
if path not in sys.path:
    sys.path.append(path)

from main import app as application
```

Ensure the host can reach MySQL and that AWS credentials for DynamoDB are configured.

---

## Usage Guide

1. Open `/` — guests see the landing view; click through to login/signup  
2. **Sign up** at `/signup` with username, email, names, password, family size  
3. **Log in** at `/login`  
4. On the dashboard:  
   - Enter an expense (date, name, type, price) → Submit  
   - Or upload a bill file (UI only for now)  
   - Click a recent month button, or pick a From/To date range → Search  
5. Review the table and charts on the monthly report page  
6. **Logout** via the menu link  

---

## Related Branches

| Branch | Notes |
|--------|-------|
| `main` | Current stable |
| `feature/login_page` | Login/signup UI work |
| `feature/imagereader` | Related to bill/image reading (in progress) |
| `feature/initial_commit_20250328` | Early bootstrap history |
