# WorkNeuron

WorkNeuron is an AI-assisted skill monetization and task fulfillment marketplace. The project is being built phase-by-phase as a modular Django monolith with a React/Vite frontend.

## Current status

Phase 9 is complete. The backend contains the Django/DRF foundation, JWT authentication, profiles, skills, task workflows, applications, assignments, explainable Sentence Transformer matching, recommendations, Smart Task Feed ranking, two-way reviews, reputation scoring, persisted notifications, optional email, Django Channels WebSockets, Razorpay TEST MODE payments, complaints, and academic anomaly alerts. The frontend is intentionally not implemented yet.

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
- `GET/POST /api/tasks/`
- `GET/PATCH/DELETE /api/tasks/<task-id>/`
- `POST /api/tasks/<task-id>/transition/`
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
- `GET/POST /api/reviews/`
- `GET /api/reputation/me/`
- `GET /api/reputation/users/<user-id>/`
- `GET /api/notifications/`
- `POST /api/notifications/<notification-id>/read/`
- `GET /api/payments/`
- `POST /api/payments/create-order/`
- `POST /api/payments/verify/`
- `GET/POST /api/complaints/`
- `GET/PATCH /api/complaints/<complaint-id>/`
- `GET /api/fraud/alerts/` for administrators
- `POST /api/fraud/scan/` for administrators
- `PATCH /api/fraud/alerts/<alert-id>/` for administrators

The notification WebSocket endpoint is `ws://localhost:8000/ws/notifications/?token=<access-token>`. The token is validated server-side; unauthenticated sockets are closed.

Payments are TEST MODE only. Configure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `backend/.env`; secrets are never returned or committed. The backend returns a clear configuration error when credentials are absent.

Fraud/anomaly detection is an academic rule-based/statistical module. It creates reviewable alerts from activity thresholds and suspicious patterns; it is not a production financial fraud system.

Task list query parameters currently include `search`, `min_budget`, `max_budget`, `location`, `skill`, `deadline_before`, and `deadline_after`. Workers receive only open or application-received tasks; clients receive their own tasks.

## AI matching methodology

WorkNeuron uses the Sentence Transformers model configured by `EMBEDDING_MODEL`, defaulting to `sentence-transformers/all-MiniLM-L6-v2`, to encode task and worker text. Scikit-learn cosine similarity produces the semantic component. Structured components cover skill overlap, experience, availability, location, and neutral cold-start rating/reputation values. Components are combined with `MATCHING_WEIGHTS_JSON`, normalized to a 0–100 score, and returned with an explanation. This is an explainable embedding-based scoring system, not a newly trained deep neural network.

If the embedding model cannot be loaded, matching endpoints return `503 Service Unavailable`; the backend does not silently substitute fabricated AI scores.

No secrets belong in Git. Use `backend/.env.example` as the configuration template.
