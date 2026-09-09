# WorkNeuron

WorkNeuron is an AI-assisted skill monetization and task fulfillment marketplace. The project is being built phase-by-phase as a modular Django monolith with a React/Vite frontend.

## Current status

Phase 1 foundation is complete. The backend contains Django/DRF configuration, a custom role-aware user model, JWT register/login/refresh/me endpoints, environment-based settings, and authentication tests. Profiles, tasks, matching, recommendations, payments, and the frontend are intentionally not implemented yet.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the architecture, phase plan, risks, and current implementation status.

## Phase 1 setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py test
python manage.py runserver
```

The intended database is PostgreSQL. For a first foundation check only, if `DB_ENGINE` is not set, Django uses a local SQLite file; configure the PostgreSQL values in `backend/.env` before normal development.

Authentication endpoints:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/` with `Authorization: Bearer <access-token>`

No secrets belong in Git. Use `backend/.env.example` as the configuration template.
