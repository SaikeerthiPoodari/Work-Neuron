# WorkNeuron

WorkNeuron is an AI-assisted skill monetization and task fulfillment marketplace. The project is being built phase-by-phase as a modular Django monolith with a React/Vite frontend.

## Current status

Phase 14 delivery configuration is complete. WorkNeuron includes the Django/DRF backend and a React/Vite/Tailwind frontend with JWT authentication, role-based dashboards, task/application/assignment workflows, explainable matching, recommendations, reviews, reputation, notifications, WebSockets, Razorpay TEST MODE payments, complaints, anomaly alerts, admin monitoring, analytics, and deployment configuration.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the architecture, phase plan, risks, and current implementation status.

Run the setup commands below from the repository root (the `WorkNeuron` folder containing this README). If your terminal starts in its parent folder (`WorkNeuron_Core_First`), first run `Set-Location .\WorkNeuron`.

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
- `GET/POST/PATCH /api/employers/verification/`
- `POST /api/employers/verification/documents/` (private verification uploads)
- `POST /api/search/voice/` for explainable voice-query intent extraction
- `GET /api/skills/`
- `GET /api/skills/graph/` for authenticated skill co-occurrence discovery
- `GET/POST /api/skills/mine/` for workers
- `DELETE /api/skills/mine/<worker-skill-id>/` for workers
- `POST/PATCH/DELETE /api/skills/<skill-id>/` for administrators
- `GET/POST /api/tasks/`
- `GET /api/tasks/daily-wage/`, `/api/tasks/part-time/`, `/api/tasks/weekend/`, `/api/tasks/event/`, `/api/tasks/festival/`
- Nearby search uses `latitude`, `longitude`, and optional `radius_km` query parameters; results include `distance_km` when coordinates are available.
- `GET/PATCH/DELETE /api/tasks/<task-id>/`
- `POST /api/tasks/<task-id>/transition/`
- `GET /api/tasks/<task-id>/decomposition/` for authorized explainable task steps
- `GET/POST /api/applications/`
- `GET /api/applications/<application-id>/`
- `POST /api/applications/<application-id>/decide/` for task owners/admins
- `POST /api/applications/<application-id>/withdraw/` for the applying worker
- `GET /api/assignments/`
- `GET /api/assignments/<assignment-id>/`
- `POST /api/assignments/<assignment-id>/start/`
- `PATCH /api/assignments/<assignment-id>/progress/`
- `POST /api/assignments/<assignment-id>/submit/`
- `POST /api/assignments/<assignment-id>/complete/`
- `GET /api/matching/tasks/<task-id>/workers/`
- `GET /api/recommendations/workers/?task=<task-id>`
- `GET /api/recommendations/smart-feed/`
- `GET /api/recommendations/jobs/` for personalized explainable job recommendations; supports `job_type`, `category`, `location`, budget, and `verified=true` filters
- `GET/POST /api/reviews/`
- `GET /api/reputation/me/`
- `GET /api/reputation/users/<user-id>/`
- `GET /api/notifications/`
- `POST /api/notifications/<notification-id>/read/`
- `GET /api/payments/`
- `GET /api/payments/employer-dashboard/` for employer earnings, completed jobs and payment history derived from real records
- `POST /api/payments/webhook/` for server-side Razorpay webhook signature verification and idempotent transaction state updates
- `POST /api/payments/create-order/`
- `POST /api/payments/verify/`
- `GET/POST /api/complaints/`
- Job details submit reports through `POST /api/complaints/` with `category=JOB_REPORT` and a `task` reference; duplicate active reports are rejected.
- `GET/PATCH /api/complaints/<complaint-id>/`
- `GET /api/fraud/alerts/` for administrators
- `POST /api/fraud/scan/` for administrators
- `PATCH /api/fraud/alerts/<alert-id>/` for administrators
- `GET /api/admin/users/`
- `PATCH /api/admin/users/<user-id>/`
- `GET /api/admin/tasks/`
- `GET /api/admin/applications/`
- `GET /api/admin/assignments/`
- `GET /api/admin/transactions/`
- `GET /api/admin/complaints/`
- `GET /api/admin/fraud-alerts/`
- `GET /api/admin/verifications/`
- `POST /api/admin/verifications/<id>/action/` with `approve`, `reject`, or `suspend`
- `GET /api/admin/verification-documents/<id>/` for authorized administrators only
- Analytics includes `search_activity.voice_searches` and `search_activity.recommendation_requests`.
- `GET /api/analytics/summary/`
- `GET /health/` for unauthenticated liveness/database readiness checks

The notification WebSocket endpoint is `ws://localhost:8000/ws/notifications/?token=<access-token>`. The token is validated server-side; unauthenticated sockets are closed.

Payments are TEST MODE only. Configure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `backend/.env`; secrets are never returned or committed. The backend returns a clear configuration error when credentials are absent.

Fraud/anomaly detection is an academic rule-based/statistical module. It creates reviewable alerts from activity thresholds and suspicious patterns; it is not a production financial fraud system.

The Skill Graph is an explainable co-occurrence graph: skills are nodes and an edge connects two skills when at least one worker has selected both. Edge weight is the number of distinct workers sharing the pair; it does not imply causal relationships.

Task decomposition uses sentence-based NLP and phrase matching against the task's required skill catalog. It is an academic explainable assistant, not a generative language model or a claim of deep neural task planning.

## Frontend setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_URL` and `VITE_WS_URL` when the backend is not running locally. The production bundle is generated with `npm run build`.

## Presentation demo data

After migrations, create repeatable local-only presentation data:

```powershell
cd backend
python manage.py seed_demo
```

This command is idempotent and never runs automatically. It creates sample client, worker, and administrator accounts, skills, tasks at different lifecycle stages, applications, assignments, reviews, a Razorpay TEST transaction record, notifications, a complaint, and a fraud alert.

Use these local demo accounts with the default password `DemoPass123!`:

- `demo.client@workneuron.local`
- `demo.worker@workneuron.local`
- `demo.admin@workneuron.local`

## Quality checks

```powershell
cd backend
python manage.py check --deploy
python manage.py test
python -m pip check

cd ..\frontend
npm audit --omit=dev
npm run build
```

## Deployment

Deployment configuration is included in `render.yaml`, `frontend/vercel.json`, and [docs/deployment.md](docs/deployment.md). The backend runs as an ASGI service with Daphne and PostgreSQL `DATABASE_URL`; the frontend is a Vercel SPA. Configure all secrets in the hosting provider environment, never in Git.

Task list query parameters currently include `search`, `min_budget`, `max_budget`, `location`, `location_city`, `location_area`, `location_state`, `latitude`, `longitude`, `radius_km`, `sort`, `skill`, `job_type`, `category`, `salary_type`, `education`, `experience`, `working_hours`, `employer_type`, `verified`, `work_mode`, `deadline_before`, and `deadline_after`. Tasks now also support controlled job types (`FULL_TIME`, `PART_TIME`, `DAILY_WAGE`, `WEEKEND`, `EVENT`, `FESTIVAL`, `CONTRACT`, `FREELANCE`, `TEMPORARY`, `INTERNSHIP`) and salary modes (`MONTHLY`, `DAILY`, `HOURLY`, `FIXED`, `NEGOTIABLE`). Workers receive only open or application-received tasks; clients receive their own tasks.

## AI matching methodology

WorkNeuron uses the Sentence Transformers model configured by `EMBEDDING_MODEL`, defaulting to `sentence-transformers/all-MiniLM-L6-v2`, to encode task and worker text. Scikit-learn cosine similarity produces the semantic component. Structured components cover skill overlap, experience, availability, location, and neutral cold-start rating/reputation values. Components are combined with `MATCHING_WEIGHTS_JSON`, normalized to a 0–100 score, and returned with an explanation. This is an explainable embedding-based scoring system, not a newly trained deep neural network.

If the embedding model cannot be loaded, matching endpoints return `503 Service Unavailable`; the backend does not silently substitute fabricated AI scores.

No secrets belong in Git. Use `backend/.env.example` as the configuration template.
