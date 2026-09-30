# WorkNeuron deployment checklist

This is the deployment checklist for the Django ASGI backend and Vite frontend. A real deployment has not been performed from this workspace; provider credentials and hosting access are required for manual verification.

## Backend

1. Create PostgreSQL and set `DATABASE_URL` (or the `DB_*` variables). Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
2. Set a long random `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` to the real HTTPS origins.
3. Serve ASGI with Daphne: `daphne -b 0.0.0.0 -p $PORT config.asgi:application`.
4. Set `SECURE_SSL_REDIRECT=True`, secure cookies, HSTS, and HTTPS proxy headers in the hosting environment.
5. Configure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` only for Razorpay TEST MODE until live credentials and payment review are available.
6. Use private object storage for verification documents. Do not expose `MEDIA_ROOT` through a public static route; serve documents only through the authenticated admin endpoint. The local filesystem backend is development-only.
7. Configure a production Channels layer if WebSockets run across multiple instances. The current in-memory channel layer is not a multi-instance production broker.
8. Confirm the embedding model can load within the service memory limit. Matching returns an explicit error when unavailable.
9. Configure `API_ANON_RATE`, `API_USER_RATE`, and `API_SENSITIVE_RATE`; the latter protects voice, reports, verification uploads, and payment endpoints through DRF throttling. Use a shared cache such as Redis for multi-instance rate-limit consistency.
10. Configure a hosting health probe at `GET /health/`; it checks database connectivity and returns 503 when the database is unavailable.

## Frontend

```powershell
cd frontend
npm ci
npm run build
```

Deploy `frontend/dist` as an SPA. Set `VITE_API_URL=https://<backend>/api` and `VITE_WS_URL=wss://<backend>/ws/notifications/`. Configure SPA rewrites to `index.html`.

## Verification checklist

- `python manage.py check --deploy`
- `python manage.py migrate --plan`
- `python manage.py test`
- `npm run build`
- JWT login/refresh and role authorization
- PostgreSQL migrations and rollback procedure
- Razorpay TEST order/signature verification
- Razorpay webhook URL: `https://<backend>/api/payments/webhook/`; configure the provider webhook secret as `RAZORPAY_WEBHOOK_SECRET` and subscribe to captured/authorized/failed payment events.
- Private verification document access as employer and admin
- WebSocket notification delivery over `wss://`
- Leaflet tiles and HTTPS mixed-content policy
- Static/media storage and backup policy

External credentials/manual deployment verification is still required for PostgreSQL hosting, Razorpay, object storage, HTTPS certificates, and production WebSockets.

## Backup and recovery

Use the managed PostgreSQL provider's encrypted automated backups and point-in-time recovery where available. Before launch, document retention, restore ownership, recovery-point objective, recovery-time objective, and perform a non-production restore rehearsal. Local SQLite and local media are development-only and are not a recovery strategy.

## Browser verification boundary

This workspace verifies backend APIs and the Vite build, but does not include a configured Playwright/Cypress runner. Browser microphone permission, keyboard/screen-reader behavior, mobile breakpoints, Leaflet tile loading, WebSocket reconnection, and hosted HTTPS must be manually verified in the target browser/hosting environment.
