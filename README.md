# WorkNeuron

WorkNeuron is an AI-assisted skill monetization and task fulfillment marketplace. The project is being built phase-by-phase as a modular Django monolith with a React/Vite frontend.

## Current status

Phase 2 is complete. The backend contains the Django/DRF foundation, a custom role-aware user model, JWT register/login/refresh/me endpoints, client and worker profiles, canonical skills, worker skill metadata, role-based permissions, and automated tests. Tasks, matching, recommendations, payments, and the frontend are intentionally not implemented yet.

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
- `GET/PATCH /api/profiles/me/`
- `GET /api/skills/`
- `GET/POST /api/skills/mine/` for workers
- `DELETE /api/skills/mine/<worker-skill-id>/` for workers
- `POST/PATCH/DELETE /api/skills/<skill-id>/` for administrators

No secrets belong in Git. Use `backend/.env.example` as the configuration template.
