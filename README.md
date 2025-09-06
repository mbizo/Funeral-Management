# Funeral Assurance Management System

A minimal, production-ready Flask application for managing funeral assurance policies, agents, commissions, payments, and member coverage — with PDF policy document generation.

## Features

- **Agents** with configurable commission rates; automatic commission entries on each premium payment.
- **Policyholders & Policies** with **auto-generated policy numbers**.
- **Covered Members** per policy (name, relationship, DOB, ID).
- **Benefits** stored on each policy (cash payout, description).
- **Status Tracking:** Active vs Lapsed (based on overdue days). Manual override supported.
- **Reports:**
  - New policies in a date range.
  - Active policies.
  - Lapsed policies.
  - Agent commissions by date range.
- **Payments:** record premiums; automatically updates policy status & agent commission.
- **PDF:** Generate a policy document for the policyholder listing all covered members and benefits.
- **Auth:** Simple admin password via environment variable.
- **SQLite** via SQLAlchemy. Ready to move to PostgreSQL later.

## Quick Start (Local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
export FLASK_APP=run.py
export ADMIN_PASSWORD=admin123   # change in .env or CI secrets
flask run
```

Open http://127.0.0.1:5000

## GitHub Actions (CI)

This repo includes a workflow that:
1. Installs dependencies
2. Runs tests
3. Builds a **release artifact** (a zip containing the app) for download

Configure a repository secret **ADMIN_PASSWORD** (or the workflow will default to "admin123" for CI only).

## Default Login

The app uses a single admin login: `admin` with password from env `ADMIN_PASSWORD`.
- Locally: set `ADMIN_PASSWORD` before running.
- CI: workflow sets a fallback for tests only.

## Policy Number Format

`POL-YYYY-XXXXXX` (sequential per database).

## Lapse Rules

A policy is **Active** if the most recent payment is within the policy's `grace_days` window; otherwise **Lapsed**. Default `grace_days=30` for new policies. You can manually set status from the Edit screen.

## Tech

- Python 3.11
- Flask, SQLAlchemy
- ReportLab for PDFs
- Bootstrap 5 (CDN)

## Project Structure

```
funeral_assurance_system/
├─ app/
│  ├─ __init__.py
│  ├─ models.py
│  ├─ routes.py
│  ├─ pdf.py
│  ├─ utils.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ login.html
│  │  ├─ dashboard.html
│  │  ├─ agents.html
│  │  ├─ agent_detail.html
│  │  ├─ policies.html
│  │  ├─ policy_form.html
│  │  ├─ policy_detail.html
│  │  ├─ payments.html
│  │  ├─ reports.html
│  └─ static/
│     └─ styles.css
├─ tests/
│  └─ test_smoke.py
├─ run.py
├─ requirements.txt
├─ .env.example
└─ .github/workflows/ci.yml
```

## Deploy Notes

For a single-box deployment, set `FLASK_ENV=production` behind a reverse proxy (nginx). Use `gunicorn` if desired.

## License

MIT
