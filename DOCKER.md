# Dockerizing TimeClock

This repository includes a production-friendly Dockerfile and compose setup to run the app with Postgres.

What’s included:
- Dockerfile (Python 3.13-slim, Pipenv-based, installs latest package versions)
- docker-compose.yml (web + Postgres 15)
- docker-entrypoint.sh (waits for DB, applies migrations, starts Gunicorn)
- .dockerignore (excludes non-runtime files from the image)

## Prereqs
- Docker 24+
- Docker Compose v2 (bundled with recent Docker Desktop)

## Environment
Provide environment via `.env` (not baked into the image). For Docker, set `DATABASE_URL` to the db service host `db` instead of `127.0.0.1`.

Example `.env` (minimal):

```
# Flask
FLASK_ENV=production
SECRET_KEY=change-me

# Postgres (compose will start db service)
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/timeclock

# Optional mail/recaptcha
MAIL_PORT=2500
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
RECAPTCHA_SITE_KEY_V3=
RECAPTCHA_SECRET_KEY_V3=
```

## Build (no cache)
Force fresh dependency resolution and install the latest allowed versions:

```
docker compose build --no-cache
```

Notes:
- The Dockerfile runs `pipenv lock --clear` inside the image to resolve the newest versions compatible with the Pipfile.
- No pip cache is used during install.

## Run

```
docker compose up
```

- App: http://127.0.0.1:8000
- Postgres: port 5432 exposed (for local tooling)

The entrypoint waits for the database and then runs `flask db upgrade`. If you need to seed roles/tags on first run:

```
docker compose exec web flask setup_db
```

## Common tasks
- View logs: `docker compose logs -f web`
- Run a one-off shell: `docker compose exec web bash`
- Run tests: `docker compose exec web flask test`

## Production tips
- Use strong `SECRET_KEY` and mail/recaptcha settings through environment.
- Consider removing the `ports: 5432:5432` mapping on the db service for closed environments.
- Increase Gunicorn workers and add a reverse proxy (nginx/traefik) as needed.
