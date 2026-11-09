# WorkNeuron deployment on a separate PythonAnywhere account

This guide prepares WorkNeuron only. Use a separate PythonAnywhere account/email
from Finova. No deployment has been performed; explicit approval is required
before using the provider dashboard.

## Compatibility

- Django 5.2 requires Python 3.10+. Use Python 3.12 if available and keep the
  same version in the virtualenv and Web tab.
- PythonAnywhere web apps are WSGI. `docs/pythonanywhere_wsgi.py` uses the
  explicit `config.settings_production` module for HTTP/API requests.
- Channels/WebSockets remain in the codebase. The WSGI web app does not provide
  the ASGI WebSocket endpoint, so live push notifications will not work there.
  Keep existing polling behavior or host ASGI/Daphne on a WebSocket-capable
  service and set `VITE_WS_URL` to it.
- PostgreSQL requires a paid PythonAnywhere plan (and the PostgreSQL add-on for
  a PythonAnywhere-hosted database). SQLite is not a production substitute.
- Free accounts have restricted outbound access and limited CPU, disk, and
  workers. AI calls, Razorpay, email, map/tile services, and the
  sentence-transformers model may need allowlisting, a paid plan, or an
  external service.
- Profile/network images and employer verification documents use local disk.
  This is single-instance/POS-only; use private object storage and backups
  before production. Never publicly map private verification files.

## Files prepared

- `backend/config/settings_development.py`: explicit local settings.
- `backend/config/settings_production.py`: required secrets, strict hosts and
  origins, HTTPS security, and PostgreSQL configuration.
- `docs/pythonanywhere_wsgi.py`: WSGI template.
- `backend/.env.example`: local and production variable examples.
- Existing `frontend/src/services/api.js` already reads `VITE_API_URL`;
  `frontend/.env.example` documents the build-time API/WS URLs.
- `backend/config/settings.py` remains the backwards-compatible local module.

## Setup commands

In the new account's Bash console:

```bash
cd ~
git clone https://github.com/SaikeerthiPoodari/Work-Neuron.git
cd ~/Work-Neuron
python3.12 -m venv ~/.virtualenvs/workneuron-312
source ~/.virtualenvs/workneuron-312/bin/activate
python -m pip install --upgrade pip
cd ~/Work-Neuron/backend
pip install -r requirements.txt
```

Create `~/Work-Neuron/backend/.env` (ignored by Git). Generate a secret with:

```bash
python -c 'from secrets import token_urlsafe; print(token_urlsafe(64))'
```

Set these values with real, uncommitted values:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings_production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generated-value>
DJANGO_ALLOWED_HOSTS=<new-username>.pythonanywhere.com
CORS_ALLOWED_ORIGINS=https://<frontend-origin>
CSRF_TRUSTED_ORIGINS=https://<frontend-origin>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<database-name>
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_HOST=<postgres-host>
DB_PORT=5432
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
MEDIA_ROOT=/home/<new-username>/Work-Neuron/backend/media
```

Use the exact HTTPS frontend origin for CORS/CSRF; do not use `*`, HTTP, a
trailing path, or the Finova domain. Add Razorpay/AI/email/storage secrets only
after separately provisioning those services.

## Database migration

Create the PostgreSQL database in the paid account's Databases tab and copy its
connection values into `.env`. Then run:

```bash
cd ~/Work-Neuron/backend
source ~/.virtualenvs/workneuron-312/bin/activate
python manage.py check --deploy --settings=config.settings_production
python manage.py migrate --plan --settings=config.settings_production
python manage.py migrate --settings=config.settings_production
python manage.py collectstatic --noinput --settings=config.settings_production
python manage.py createsuperuser --settings=config.settings_production
```

Back up the database before migration. Do not run `makemigrations` on the host;
commit reviewed migrations from development.

## Web tab and WSGI

1. Add a Manual configuration web app using the same Python version.
2. Set virtualenv to
   `/home/<new-username>/.virtualenvs/workneuron-312`.
3. Paste `docs/pythonanywhere_wsgi.py` into the WSGI file and replace the
   username/path placeholder. It must use `config.settings_production`.
4. Add static mapping `/static/` to
   `/home/<new-username>/Work-Neuron/backend/staticfiles`.
5. Do not publicly map `/media/` while private verification documents are
   stored there. Reload and inspect the error log.

## Frontend

Vite substitutes `VITE_API_URL` at build time. Create
`frontend/.env.production` with the public backend URL and an empty
`VITE_WS_URL` for WSGI-only hosting, then run:

```bash
cd ~/Work-Neuron/frontend
npm ci
npm run build
```

Host `frontend/dist` as a static site with an SPA fallback to
`index.html`, either through another web app if the plan permits or an
external static host. If a separate ASGI service is later used, set
`VITE_WS_URL=wss://<websocket-origin>/ws/notifications/` before rebuilding.

## Unsupported features and alternatives

| Feature | Limitation | Alternative |
|---|---|---|
| PostgreSQL | Paid plan/add-on required | Paid PythonAnywhere or external managed PostgreSQL |
| WebSockets | Not supplied by normal WSGI app | External ASGI/Daphne; keep polling |
| Redis | External access needs paid/unrestricted networking | Paid plan + managed Redis; fallback only for testing |
| AI/model download | Free allowlist and CPU/memory limits | Paid/allowlisted host or external AI worker |
| Payments/email | External credentials and outbound access required | Configure secrets and verify webhooks publicly |
| Background workers | No always-on worker in normal web app | Scheduled jobs or external queue/worker |
| Media uploads | Local disk is not durable/private storage | Private object storage and authenticated downloads |

No unsupported feature has been removed or silently replaced.

## Verification after approval

```bash
cd ~/Work-Neuron/backend
python manage.py check --deploy --settings=config.settings_production
python manage.py test --settings=config.settings_production
curl -i https://<backend-origin>/health/
```

Then test JWT login/refresh, all role dashboards and authorization, uploads,
password reset email, Razorpay test flows/webhooks, AI fallback/provider,
frontend routes, and static assets. Live deployment is successful only after
the live API and frontend pass these checks; this preparation is not deployment.
