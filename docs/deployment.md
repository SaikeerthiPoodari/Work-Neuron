# WorkNeuron deployment

## Backend on Render

The repository includes `render.yaml` for a Render web service and PostgreSQL database.

1. Create a Render Blueprint from the GitHub repository.
2. Set the secret/synchronization values requested by the blueprint:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_ALLOWED_HOSTS` with the Render backend hostname
   - `CORS_ALLOWED_ORIGINS` with the Vercel frontend origin
   - `CSRF_TRUSTED_ORIGINS` with the Vercel frontend origin
   - Razorpay TEST MODE keys if payments are demonstrated
3. Deploy. The build runs migrations and collects static files; Daphne serves the ASGI application.
4. Pre-download or warm the configured Sentence Transformer model during deployment if the host has sufficient disk/RAM. Matching returns `503` when the model cannot load rather than fabricating scores.

Railway can use the same `backend/requirements.txt`, `python manage.py migrate`, `python manage.py collectstatic --noinput`, and `daphne -b 0.0.0.0 -p $PORT config.asgi:application` commands with a PostgreSQL `DATABASE_URL`.

## Frontend on Vercel

1. Import the repository into Vercel and set the project root to `frontend`.
2. Use `npm run build` as the build command and `dist` as the output directory.
3. Set:
   - `VITE_API_URL=https://<backend-host>/api`
   - `VITE_WS_URL=wss://<backend-host>/ws/notifications/`
4. `frontend/vercel.json` provides SPA rewrites for React Router.

## Secrets and test integrations

Never commit `.env` files or credentials. Razorpay remains TEST MODE only. Email, database, JWT, and embedding configuration must be supplied through environment variables. After deployment, verify JWT login, task creation, application acceptance, assignment completion, notification WebSockets, and mocked/test payment verification from the frontend.

