# WorkNeuron Project Status

## Project overview

**WorkNeuron** is planned as an AI-assisted skill monetization and task fulfillment marketplace. It will connect clients who publish work with workers who discover, apply for, and complete suitable tasks. The system will provide role-specific workflows for clients, workers, and administrators, with explainable semantic matching and recommendation features.

This repository is currently at the planning/inspection stage. No application functionality has been implemented yet.

## Current repository status

Inspection date: 2026-09-09

- The workspace directory is empty at the start of this planning phase.
- No `frontend/`, `backend/`, `ai_engine/`, `tests/`, or `docs/` directories exist.
- A Django project, DRF configuration, custom user model, initial migration, JWT endpoints, requirements file, environment template, README, and authentication tests now exist.
- No React/Vite frontend or feature-domain modules exist yet; these remain intentionally deferred to later phases.
- A project-local Git repository was initialized. Existing unrelated parent-repository files are outside the project boundary.
- Available development tools detected: Python 3.13.7, Node.js 22.14.0, npm 10.9.2, and Git 2.51.0.
- Django 5.2.17, DRF 3.16.1, SimpleJWT 5.5.1, django-cors-headers 4.9.0, psycopg 3.3.5, and python-dotenv 1.2.3 are declared/installed for the backend.
- The PostgreSQL `psql` client and Windows service were not found. PostgreSQL remains the intended application database, but local PostgreSQL connectivity is not yet verified.

## Final architecture

The planned implementation is a modular Django monolith with a React/Vite client:

```text
React + Vite + JavaScript + Tailwind CSS
        |
        | REST/JSON, JWT, WebSockets
        v
Django + Django REST Framework + Django Channels
        |
        +-- Accounts, profiles, skills, tasks, applications
        +-- Assignments, matching, recommendations, notifications
        +-- Payments, reviews, reputation, complaints, fraud, analytics
        |
        v
PostgreSQL

External integrations:
- Razorpay Test Mode
- SMTP/email provider
- Leaflet + OpenStreetMap
```

The backend will remain a single deployable service. AI matching will be implemented as an internal Python module used by Django services and API endpoints; unnecessary microservices are out of scope.

## Planned folder structure

```text
WorkNeuron/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── utils/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── manage.py
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── profiles/
│   │   ├── skills/
│   │   ├── tasks/
│   │   ├── applications/
│   │   ├── matching/
│   │   ├── recommendations/
│   │   ├── notifications/
│   │   ├── payments/
│   │   ├── reviews/
│   │   ├── reputation/
│   │   ├── complaints/
│   │   ├── fraud/
│   │   └── analytics/
│   ├── requirements.txt
│   └── .env.example
├── ai_engine/
│   ├── embeddings/
│   ├── matching/
│   ├── recommendations/
│   └── utils/
├── tests/
├── docs/
├── README.md
├── PROJECT_STATUS.md
└── .gitignore
```

The structure may be adjusted slightly during implementation if Django app boundaries or testing conventions require it, without changing the mandated technology stack.

## Database entities

The normalized PostgreSQL model will use UUIDs or suitable primary keys, timestamps, foreign keys, indexes, unique constraints, validation, and explicit deletion behavior.

- `User`: authentication identity, role, account status, and common user fields.
- `ClientProfile`: client-specific profile data linked one-to-one to `User`.
- `WorkerProfile`: worker bio, experience, location, availability, and profile metadata linked one-to-one to `User`.
- `Skill`: canonical skill catalog.
- `WorkerSkill`: worker-to-skill relationship, including proficiency/experience metadata where justified.
- `Task`: task owner, content, budget, deadline, location, availability requirements, and lifecycle status.
- `TaskSkill`: task-to-required-skill relationship.
- `Application`: worker application to a task, status, message, and match snapshot/score where appropriate.
- `Assignment`: accepted worker/task relationship, progress, submission, and assignment status.
- `Transaction`: payment intent/order, verification data, amount, and payment status; Razorpay secrets remain in environment variables.
- `Review`: reviewer, reviewed user, assignment/task, rating, text, and uniqueness constraint per review direction and assignment.
- `Notification`: recipient, type, message, read state, and optional related object reference.
- `Complaint`: complainant, subject user/task/application/assignment/payment, status, investigation notes, and resolution.
- `ReputationScore`: worker/client aggregates and formula inputs used for recommendations.
- `FraudAlert`: anomaly type, related entity, score/evidence, status, and admin resolution.

Core integrity rules will include one application per worker/task, one active assignment per task, one review per reviewer/reviewed direction per completed assignment, ownership checks, and valid task state transitions.

## API structure

The planned REST API namespaces are:

```text
/api/auth/
/api/users/
/api/profiles/
/api/skills/
/api/tasks/
/api/applications/
/api/assignments/
/api/matching/
/api/recommendations/
/api/notifications/
/api/payments/
/api/reviews/
/api/reputation/
/api/complaints/
/api/admin/
/api/analytics/
```

Each implemented endpoint will have real serializers, validation, authentication, object-level authorization, meaningful HTTP methods/status codes, consistent errors, and pagination/filtering where applicable. Endpoints will not be added merely to make an unfinished UI appear complete.

## Task and application workflows

The task state machine will support:

```text
OPEN -> APPLICATIONS_RECEIVED -> ASSIGNED -> IN_PROGRESS -> SUBMITTED -> COMPLETED
  \----------------------------------------------------------------> CANCELLED
```

The transition service will enforce allowed transitions and actor permissions. In particular, workers may update only their own assignment, clients may approve their own task submission, and administrators may intervene according to explicit policy.

Applications will enforce that a worker cannot apply to their own task, apply twice, or apply to a non-open/closed task. Only the task owner can accept or reject an application, and accepting one will create the assignment transactionally while preventing duplicate active assignments.

## AI matching architecture

The initial AI implementation will be explainable semantic matching, not a claimed deep neural network trained for this project:

1. Build normalized text from task title, description, and required skills; build normalized text from worker bio, skills, experience, and relevant history.
2. Generate sentence embeddings with a documented Sentence Transformers model selected during Phase 5.
3. Calculate cosine similarity for the semantic skill/task component.
4. Calculate structured components for skill coverage, experience, rating, availability, location, reputation, and relevant task history.
5. Combine components using configuration-driven weights and normalize the result to a 0-100 score.
6. Return component scores and a human-readable explanation so the result can be inspected in a viva and in the client UI.

The recommendation engine will rank tasks for workers and workers for clients using matching scores plus freshness, preferences, budget/deadline fit, interaction history, and platform safety constraints. Smart Task Feed ranking will reuse the same service rather than duplicate scoring logic. Model choice, weighting, fallback behavior, and limitations will be recorded in implementation documentation once built.

## Development phases

1. **Phase 0 — Inspection and planning:** repository baseline, architecture, schema, API plan, risks, and status document.
2. **Phase 1 — Foundation:** Django/DRF setup, PostgreSQL configuration, environment handling, JWT authentication, base project checks.
3. **Phase 2 — Profiles and skills:** client/worker profiles and skill management.
4. **Phase 3 — Tasks:** task CRUD, publishing, search/filtering, and validated lifecycle.
5. **Phase 4 — Workflows:** applications, assignments, authorization, progress tracking, and submissions.
6. **Phase 5 — Intelligence:** embeddings, explainable matching, recommendations, and Smart Task Feed.
7. **Phase 6 — Trust:** reviews, ratings, and transparent reputation calculations.
8. **Phase 7 — Communication:** notifications, email, Channels, and WebSocket delivery.
9. **Phase 8 — Payments:** Razorpay Test Mode order/verification integration and transaction records.
10. **Phase 9 — Safety:** complaints and academic-level anomaly/fraud detection with documented limitations.
11. **Phase 10 — Administration:** admin workflows, monitoring, dashboards, and analytics.
12. **Phase 11 — Frontend integration/refinement:** complete role-based React screens, states, validation, and API integration.
13. **Phase 12 — Advanced features:** only individually selected after core stability; no advanced feature will be allowed to destabilize the core flow.
14. **Phase 13 — Quality/security/performance:** unit/API/integration tests, security review, and performance review.
15. **Phase 14 — Delivery:** deployment configuration, documentation synchronization, demo workflow, and final verification.

## Current phase

**Phase 11 — Frontend integration and refinement (complete).**

Implemented scope across Phases 1–11:

- Django 5.2 modular backend with ASGI/WSGI configuration.
- Django REST Framework with JSON rendering and JWT authentication.
- PostgreSQL environment configuration through `backend/.env`; SQLite is used only as a local fallback when `DB_ENGINE` is unset so foundation tests can run without a PostgreSQL service.
- Custom email-based `User` model with `CLIENT`, `WORKER`, and protected `ADMIN` roles.
- Registration, login, refresh, and authenticated current-user endpoints.
- JWT role/email claims and CORS configuration.
- Initial migration, admin registration, project-local `.gitignore`, and setup README.
- Automated authentication tests.
- Client and worker profile models linked one-to-one with the existing user model.
- Authenticated profile read/update endpoint with role-specific serializer fields.
- Canonical skill catalog and worker-skill relationship with proficiency and experience metadata.
- Admin-only skill catalog creation/update/deactivation/deletion permissions.
- Worker-only add/list/remove skill endpoints with duplicate and inactive-skill validation.
- Profile and skill API tests.
- Task and task-required-skill models with ownership, indexes, constraints, and lifecycle status.
- Client task creation, retrieval, update, deletion, and authenticated visibility rules.
- Worker task discovery limited to open/application-received tasks.
- Search and filtering by text, budget, location, skill, deadline, and administrator status.
- Validated task transition service and transition API.
- Task API tests covering creation, authorization, filtering, lifecycle validation, and closed-task visibility.
- Worker applications with duplicate prevention, self-task prevention, withdrawal, and task status updates.
- Client/admin application decisions with transactional assignment creation and rejection of competing submissions.
- Assignment visibility by worker/client/admin role.
- Worker assignment start, progress updates, and work submission.
- Client/admin submission approval and completion recording.
- Assignment-specific authorization and workflow tests.
- Sentence Transformer embedding service using the configured `all-MiniLM-L6-v2` model by default.
- Cosine similarity and structured skill, experience, rating, availability, location, and reputation components.
- Configuration-driven matching weights with 0-100 explainable output and human-readable explanation.
- Client worker-match endpoint and worker recommendation endpoint.
- Worker Smart Task Feed with match ranking and skill/location/budget filters.
- Deterministic embedding-injected tests that do not falsely claim model inference.
- Client-to-worker and worker-to-client reviews after completed assignments.
- Duplicate review prevention per assignment and direction.
- Transparent reputation score records with average rating, completion rate, response rate, complaint health, and score components.
- Reputation recalculation after each received review and public authenticated reputation lookup.
- Persisted notification records with unread filtering and read-state updates.
- Notification service with WebSocket group delivery and optional email delivery.
- JWT-authenticated Django Channels consumer at `/ws/notifications/`.
- Notification events wired to applications, assignments, and reviews.
- ASGI `ProtocolTypeRouter` and in-memory channel layer for local development/tests.
- Razorpay TEST MODE order creation with server-side credentials.
- Transaction records with created, verified, failed, and refunded states.
- Server-side payment signature verification and authorization.
- Payment verification notification to the assigned worker.
- Complaint submission for users, tasks, applications, assignments, and payments.
- Admin complaint review, resolution notes, and resolved-by tracking.
- Academic anomaly alerts for high application activity, repeated complaints, unusual transactions, and suspicious rating patterns.
- Admin-only fraud scan, alert list, and alert status management.
- Admin-only user monitoring and account activation management.
- Admin monitoring endpoints for tasks, applications, assignments, transactions, complaints, and fraud alerts.
- Live analytics summary for user roles, task statuses, applications, assignments, transactions, reviews, complaints, and alerts.
- React/Vite/JavaScript/Tailwind frontend with protected JWT routes and role-based navigation.
- Client, worker, and admin dashboards connected to real backend APIs.
- Task, profile, skills, application, assignment, recommendation, review, payment, complaint, notification, and admin screens.
- JWT notification WebSocket subscription and Razorpay TEST MODE checkout callback.
- Loading, error, empty, validation, and responsive layout states.

## Next action

Next: verify/configure a local PostgreSQL instance and pre-download the configured embedding model, then begin **Phase 13 — Quality, security, and performance review**. Phase 12 advanced features are intentionally deferred until the core application is reviewed.

## Phase 2 completion report

- **Completed features:** client/worker profiles, canonical skills, worker skill metadata, role-based permissions, duplicate prevention, and profile/skill administration.
- **Files changed:** `backend/apps/profiles/`, `backend/apps/skills/`, `backend/config/settings.py`, `backend/config/urls.py`, generated migrations, `README.md`, and this status document.
- **Tests performed:** Django system check and automated API/unit tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 9 tests.
- **Known issues:** PostgreSQL service/connectivity is still not available locally, so automated tests use the documented SQLite fallback. Frontend integration is deferred to the frontend refinement phase.
  - **Next recommended phase:** Phase 3 — task CRUD, publishing, search/filtering, and validated task lifecycle.

## Phase 3 completion report

- **Completed features:** task CRUD, normalized required skills, client ownership, worker task discovery, search/filtering, pagination-compatible list API, and validated task transitions.
- **Files changed:** `backend/apps/tasks/`, `backend/config/settings.py`, `backend/config/urls.py`, generated task migration, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, and automated API/unit tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 15 tests.
- **Known issues:** PostgreSQL service/connectivity is still not available locally, so automated tests use the documented SQLite fallback. Assignment-specific actor checks will be completed in Phase 4 when assignments exist.
  - **Next recommended phase:** Phase 4 — applications and assignments.

## Phase 4 completion report

- **Completed features:** worker applications, transactional client decisions, assignment creation, application withdrawal/rejection, progress tracking, work submission, and client completion approval.
- **Files changed:** `backend/apps/applications/`, `backend/apps/assignments/`, `backend/config/settings.py`, `backend/config/urls.py`, generated migrations, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, and automated API/integration tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 21 tests.
- **Known issues:** PostgreSQL service/connectivity is still not available locally, so automated tests use the documented SQLite fallback. Notifications, payments, reviews, and AI scoring are intentionally deferred to later phases.
- **Next recommended phase:** Phase 5 — explainable AI matching, recommendations, and Smart Task Feed.

## Phase 5 completion report

- **Completed features:** explainable semantic matching, configurable structured scoring, client worker recommendations, worker task recommendations, and Smart Task Feed ranking.
- **Files changed:** `ai_engine/`, `backend/apps/matching/`, `backend/apps/recommendations/`, AI dependencies/configuration, `README.md`, and this status document.
- **Tests performed:** Django system check and automated engine/API tests with a deterministic injected embedding provider.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 27 tests.
- **Known issues:** first real matching use requires downloading the configured Sentence Transformer model. Until the model is available, matching endpoints return HTTP 503 rather than fabricating scores. Rating and reputation components are neutral 50-point cold-start values until Phase 6.
- **Next recommended phase:** Phase 6 — reviews, ratings, and reputation.

## Phase 6 completion report

- **Completed features:** two-way reviews, completed-assignment validation, duplicate prevention, reputation calculation, reputation API, and reputation updates after reviews.
- **Files changed:** `backend/apps/reviews/`, `backend/apps/reputation/`, `backend/config/settings.py`, `backend/config/urls.py`, generated migrations, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, and automated review/reputation API tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 31 tests.
- **Known issues:** response rate and complaint health are provisional 100-point values until response instrumentation and complaints are implemented. PostgreSQL service/connectivity remains unverified locally.
- **Next recommended phase:** Phase 7 — notifications, email, Django Channels, and WebSockets.

## Phase 7 completion report

- **Completed features:** persisted notifications, unread/read API, optional email hook, Channels consumer, JWT WebSocket authentication, and event integration for applications, assignments, and reviews.
- **Files changed:** `backend/apps/notifications/`, `backend/config/asgi.py`, `backend/config/routing.py`, `backend/config/settings.py`, notification integrations, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, API/service tests, and ASGI import verification.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 33 tests; ASGI application loaded as `ProtocolTypeRouter`.
- **Known issues:** local development uses an in-memory channel layer; production deployment should use a shared channel backend suitable for the selected host. PostgreSQL service/connectivity remains unverified locally.
- **Next recommended phase:** Phase 8 — Razorpay Test Mode payments.

## Phase 8 completion report

- **Completed features:** Razorpay TEST MODE order creation, transaction persistence, signature verification, authorization, failure handling, and payment notifications.
- **Files changed:** `backend/apps/payments/`, Razorpay requirements/environment settings, notification integration, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, and mocked Razorpay API/integration tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 37 tests.
- **Known issues:** Razorpay credentials are required for real test checkout and remain environment-only. No real-money settlement or live-mode behavior is implemented. PostgreSQL service/connectivity remains unverified locally.
- **Next recommended phase:** Phase 9 — complaints and academic-level fraud/anomaly detection.

## Phase 9 completion report

- **Completed features:** complaint intake, complaint authorization, admin resolution, academic anomaly scan, alert persistence, admin alert review, and alert status management.
- **Files changed:** `backend/apps/complaints/`, `backend/apps/fraud/`, `backend/config/settings.py`, `backend/config/urls.py`, generated migrations, `README.md`, and this status document.
- **Tests performed:** Django system check, migrations, complaint API tests, and anomaly detection tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 41 tests.
- **Known issues:** anomaly detection is threshold/statistics-based academic functionality, not production-grade fraud detection. Thresholds are currently code-level defaults and should be made configurable before deployment. PostgreSQL service/connectivity remains unverified locally.
- **Next recommended phase:** Phase 10 — admin dashboard and analytics.

## Phase 10 completion report

- **Completed features:** role-protected admin monitoring APIs, user activation management, live analytics summary, and admin tests.
- **Files changed:** `backend/apps/administration/`, `backend/apps/analytics/`, `backend/config/settings.py`, `backend/config/urls.py`, `README.md`, and this status document.
- **Tests performed:** Django system check and automated admin/analytics API tests.
- **Test results:** `python manage.py check` passed; `python manage.py test` passed with 44 tests.
- **Known issues:** no frontend exists yet; admin API coverage is ready for the React dashboard. PostgreSQL service/connectivity remains unverified locally.
- **Next recommended phase:** Phase 11 — React/Vite frontend integration and refinement.

## Phase 11 completion report

- **Completed features:** React/Vite/Tailwind frontend foundation, JWT auth flows, protected role routes, dashboards, task/application/assignment workflows, profiles/skills, recommendations, reviews, payments, complaints, notifications, admin monitor, WebSocket updates, and Razorpay checkout callback.
- **Files changed:** `frontend/`, `README.md`, and this status document.
- **Tests performed:** `npm install`, `npm audit` during installation, and production Vite build.
- **Test results:** dependencies installed with 0 vulnerabilities reported; `npm run build` passed with 56 modules transformed.
- **Known issues:** frontend currently assumes the backend is available at `http://localhost:8000` unless `VITE_API_URL`/`VITE_WS_URL` is configured. PostgreSQL service/connectivity remains unverified locally. Browser-level E2E tests are still pending.
- **Next recommended phase:** Phase 13 — security, performance, and end-to-end quality review. Phase 12 optional advanced features remain deferred.

## Technical risks

- PostgreSQL server/client availability and local development configuration are not yet verified; Phase 1 tests currently use SQLite fallback.
- Python 3.13 and dependency compatibility must be checked when selecting supported Django, DRF, Channels, ML, and database-driver versions.
- Sentence Transformer models add download size, startup cost, and deployment resource requirements; a documented fallback strategy may be needed for constrained environments.
- WebSocket deployment requires ASGI configuration and a hosting setup compatible with Django Channels.
- Razorpay verification requires test credentials and careful server-side signature validation; no secrets may enter Git.
- Location matching should avoid exposing unnecessary precise location data and should define a simple academic distance policy.
- Recommendation quality will depend on sparse early-user/task data; cold-start behavior must use content-based signals and transparent defaults.
- Fraud detection will be academic anomaly detection, not production-grade financial fraud prevention.
- The broad parent Git repository is not a safe project boundary for commits; a local repository should be initialized in the workspace before feature commits.

## Assumptions

- The requested technology stack is binding: React/Vite/JavaScript/Tailwind, Django/DRF, PostgreSQL, JWT, Django Channels, Sentence Transformers, scikit-learn, Razorpay Test Mode, and Leaflet/OpenStreetMap.
- The application is a modular monolith for a final-year project; microservices are out of scope.
- Admin users are represented by the Django user model and protected admin/API permissions, not by an independently duplicated identity table.
- Payments are test-mode records and demonstration flows only; real-money settlement is out of scope.
- A task has one primary assigned worker in the initial core workflow. Team tasks, voice, multilingual, dynamic pricing, blockchain, and other advanced features remain deferred.
- A completed assignment supports one client-to-worker review and one worker-to-client review.
- Email provider credentials, Razorpay credentials, database credentials, and JWT secrets will be supplied through environment variables when needed.
- Phase completion will be reported with changed files, tests, results, known issues, and the next recommended phase.
