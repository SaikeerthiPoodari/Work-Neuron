# WorkNeuron Client/Employer Portal Status

## Enhancement update — 2026-10-01

The client portal now includes a protected worker directory (`GET /api/employers/workers/`), client hiring analytics (`GET /api/analytics/client/`), account detail/password settings, payment detail access, mark-all notification read support, private job drafts with publish transitions, and job-scoped messaging/interview API routes under `/api/messaging/`. New client routes include `/client/workers`, `/client/analytics`, `/client/messages`, and `/client/settings`.

Review date: 2026-09-30

This status reflects the checked-in code and backend API contracts, not the full future portal specification. The existing shared WorkNeuron application, authentication, and `CLIENT` role are retained; there is no second client app or login. Client login and registration use `/login` and `/register`, and the authenticated role selects the client dashboard at `/`.

Status meanings: `IMPLEMENTED` = current UI calls a real backend capability; `PARTIALLY IMPLEMENTED` = only part of the requested UX/data contract exists; `BLOCKED BY BACKEND` = required endpoint/data model is not present; `BLOCKED EXTERNALLY` = requires deployed services or physical/browser verification.

| Feature | Status | Page | API | Notes |
|---|---|---|---|---|
| Existing client login and registration | IMPLEMENTED | `/login`, `/register` | `POST /api/auth/login/`, `POST /api/auth/register/`, `GET /api/auth/me/` | One shared JWT flow. Client stays on the role-aware root dashboard; admin and worker roles remain separate. |
| Client route protection | IMPLEMENTED | Shared protected layout; client applications route | JWT identity and role from auth context | Applications page is client-only; other APIs enforce role/ownership server-side. |
| Client dashboard | IMPLEMENTED | `/` | `/api/tasks/`, `/api/assignments/`, `/api/notifications/?unread=true`, `/api/payments/employer-dashboard/`, `/api/applications/`, `/api/reviews/`, `/api/recommendations/workers/` | KPIs, recent records, notifications, quick actions, and per-job worker recommendations use server data. Average rating is derived from reviews returned for the signed-in user. |
| Client navigation | IMPLEMENTED | Shared desktop sidebar and mobile navigation | N/A | Client-specific links; mobile navigation can scroll horizontally to all client sections. |
| Client profile | PARTIALLY IMPLEMENTED | `/profile` | `GET/PATCH /api/profiles/me/` | Employer-specific editor supports organization name, bio, phone, location, website and controlled employer type. Account name/email, logo upload, structured client address/city/area/state, and separate contact fields are not in this profile API. |
| Employer verification | PARTIALLY IMPLEMENTED | `/verification` | `GET/POST/PATCH /api/employers/verification/`, `POST /api/employers/verification/documents/` | Real statuses, submission and resubmission, private upload, backend-confirmed verified badge, and rejection remarks are supported. UI does not expose document download (admin-only by design) and does not show every review timestamp/remark state. Not government verification. |
| Create job/task | PARTIALLY IMPLEMENTED | `/tasks?create=1` | `GET /api/skills/`, `POST /api/tasks/` | Multi-step form now covers supported details, skills, requirements, category, job/salary type, dates, location, coordinates and work mode. API stores one `budget`, not min/max salary. Draft state is not supported; publishing creates an OPEN job immediately. |
| Edit job/task | IMPLEMENTED | `/tasks` | `PATCH /api/tasks/{id}/` | Edit is offered for open/application-received tasks and uses the existing owner-scoped endpoint. |
| My jobs, filtering, close, delete | IMPLEMENTED | `/tasks` | `GET/DELETE /api/tasks/{id}/`, `POST /api/tasks/{id}/transition/` | Status tabs, application counts and owner-only actions use API data. Close uses the supported `CANCELLED` transition. Delete is offered only for OPEN jobs with no applications; backend protection failures remain visible. There is no DRAFT state. |
| Client job details | PARTIALLY IMPLEMENTED | `/tasks/{id}` | `GET/PATCH /api/tasks/{id}/` | Shared detail page has real task data and client application actions; the new applications route provides applicant review/decision. No separate client-only detail page. |
| Applications received | IMPLEMENTED | `/applications`, `/tasks/{id}` | `GET /api/applications/`, `GET /api/applications/tasks/{task_id}/comparison/` | Dedicated client route reuses the existing applicant comparison component and displays actual worker profile snippets and backend match scores. |
| Application decision / worker selection | IMPLEMENTED | `/applications` | `POST /api/applications/{id}/decide/` | Accept/reject are backend-validated; accepting creates an assignment. |
| Dedicated application detail/profile route | PARTIALLY IMPLEMENTED | `/applications` | `GET /api/applications/{id}/`, comparison endpoint | Applicant profile, skills, rating, experience and match factors are shown in the application card. There is no dedicated `/applications/{id}` frontend route; API detail alone returns a limited serializer. |
| AI recommended workers | IMPLEMENTED | `/`, `/recommendations` | `GET /api/recommendations/workers/?task={owned_task_id}` | Scores and explanations come from the backend matcher. User must choose a task they own. |
| General worker directory/search | BLOCKED BY BACKEND | Not present | No client-scoped worker search/list endpoint | Current API only returns recommendations for a particular owned task. No name/category/location/availability/rating directory filters or general worker profile endpoint exist. |
| Worker profile visibility | PARTIALLY IMPLEMENTED | `/applications` applicant cards | Owned-task comparison endpoint | Displays permitted comparison response fields. There is no general profile endpoint or client-side profile route; exact private worker coordinates are not returned here. |
| Selected workers and task tracking | IMPLEMENTED | `/assignments` | `GET /api/assignments/`, assignment level/review endpoints | Existing lifecycle and stage workflow is retained. Assignment records expose worker email and progress; selected-workforce filters and full schedule details are limited. |
| Payments and payment detail | PARTIALLY IMPLEMENTED | `/payments` | `GET /api/payments/`, `GET /api/payments/employer-dashboard/`, payment create/verify endpoints | History, summary and test checkout use real transactions. There is no transaction detail endpoint/page. Backend statuses are CREATED, VERIFIED, FAILED and REFUNDED; it does not expose a distinct AUTHORIZED state. |
| Ratings and reviews | IMPLEMENTED | `/reviews` | `GET/POST /api/reviews/` | Reviews are tied to completed assignments and duplicate submissions are rejected by the backend. |
| Notifications | PARTIALLY IMPLEMENTED | `/notifications` and dashboard | `GET /api/notifications/`, `POST /api/notifications/{id}/read/`, authenticated WebSocket | Per-user list/read and WebSocket connection exist. No mark-all-read endpoint; production broker behavior is external. |
| Reports / report-a-job | PARTIALLY IMPLEMENTED | `/complaints`; worker job detail | `GET/POST /api/complaints/` | Client can file a complaint against one of their returned jobs/applications/assignments/payments. Client cannot file a JOB_REPORT against their own job; client job list does not expose other employers' jobs. Job reporting is a worker-facing flow. |
| Client complaints/disputes | IMPLEMENTED | `/complaints` | `GET/POST /api/complaints/`, `GET /api/complaints/{id}/` | Client form now associates each submission with an owned task, application, assignment, or payment and shows status/resolution notes. Full dispute conversation/thread is not modeled. |
| Client settings and preferences | BLOCKED BY BACKEND | Not present | No account-settings/password/preferences API | No password change, notification preferences, visibility controls, or client default job/location preferences are exposed. No fake controls were added. |
| Location-aware job posting | IMPLEMENTED | `/tasks?create=1` | `POST/PATCH /api/tasks/`, profile endpoint for its supported fields | Remote/on-site/hybrid, structured task address/city/area/state, coordinates, current one-shot browser location and manual fallback. On-site address/city are validated by backend. Client profile itself has only a free-form location field. |
| Client map and job-location view | PARTIALLY IMPLEMENTED | Shared job/map surfaces | Task list/detail APIs | Leaflet exists in the application, but a dedicated client job-detail map and client map search are not implemented. |
| Responsive and accessible UI | PARTIALLY IMPLEMENTED | Client pages/shared components | N/A | Responsive layouts, labels, loading/error/empty states and scrollable mobile navigation are present. This environment has no configured frontend test/lint/browser automation; device, keyboard and screen-reader checks remain unverified. |
| Frontend build and automated tests | PARTIALLY IMPLEMENTED | Full SPA | N/A | Production Vite build verified in this session. `package.json` has no test or lint script. Backend regression is run separately. |

## Changes in this continuation

- Added a client-specific job-management view to the existing `/tasks` route, with supported multi-step posting, editing, API-backed status tabs, close action, and one-shot geolocation.
- Added client-only `/applications`, protected by the existing CLIENT role, reusing the existing comparison component with backend select/reject actions.
- Added a client dashboard with real records and backend-provided recommendations; worker/admin dashboard rendering remains unchanged.
- Added client-specific mobile navigation links and a controlled business-type profile editor.
- Fixed the client complaints form so submissions include a backend-owned record reference instead of sending a request that fails required reference validation.
- Added visible initial dashboard API error handling and deletion for open jobs with no applications.
- Added the missing notification-kind migration for existing report and verification notification choices; no new backend models or endpoints were needed for the portal work.

## Verification performed

- Frontend dependency restore from `frontend/package-lock.json`: `npm ci` passed; 0 vulnerabilities reported during install.
- Frontend production build: passed (Vite transformed 117 modules). Vite emitted a >500 kB chunk-size advisory.
- Backend regression: 99 tests passed.
- Django system check: passed; `makemigrations --check --dry-run` reported no changes; migration chain applied successfully to local SQLite.
- Python dependency check: `pip check` passed. `npm audit --omit=dev` reported 0 vulnerabilities.
- Integrated browser smoke test: client login opened the client dashboard; dashboard APIs returned HTTP 200; applications loaded the seeded job and actual backend score; the six-step job form reached Preview without publishing; client profile and complaints rendered; unauthenticated applications redirected to login; Worker applications access redirected to the worker dashboard.
- ASGI/WebSocket smoke test: Daphne served the existing ASGI application; the client notification socket reached `WSCONNECT`.
- Razorpay checkout was not browser-verified: the integrated browser blocked an internal remote checkout asset. Test-mode API/signature behavior remains covered by backend tests.
- Added `backend/private/` to `.gitignore` so private verification uploads and test upload fixtures are not staged accidentally.
- No frontend test or lint script is configured in `frontend/package.json`; browser/device accessibility and physical responsive matrix remain unverified.

## Remaining boundaries

General worker directory/profile search, client settings/password/preferences, draft jobs, salary ranges, application/payment detail pages, client job-reporting for other employers' jobs, mark-all notification support, and some client profile fields require backend contracts or additional product design. Hosted Razorpay, private cloud storage, shared WebSocket delivery, and physical browser/accessibility verification remain external to local implementation.
