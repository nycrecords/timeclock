# TimeClock Quick Start

## Prerequisites

- Python 3.13 (verify with `python3 --version`)
- Pipenv (`python3 -m pip install --user pipenv`)
- PostgreSQL 15+ with `psql` on PATH (Windows installers or Homebrew work fine)
- Docker Desktop 4.29+ (includes Docker Compose v2)
- On macOS: ensure `$(python3 -m site --user-base)/bin` is on PATH for Pipenv

## 1) Configure Environment

- Copy the example env file: `cp .env.example .env`
- Set your local database URL in `.env` if you plan to run outside Docker, for example:
  - `DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/timeclock`
- Optional: set Flask env vars
  - `FLASK_APP=timeclock.py`
  - `FLASK_ENV=development`

## 2) Pipenv Workflow

1. Create the virtual environment and install dependencies:
   - `pipenv --python 3.13`
   - `pipenv sync --dev`
2. Keep dependencies fresh when needed:
   - `pipenv run pip list --outdated`
   - `pipenv lock --clear && pipenv sync --dev`
3. Database setup on your host Postgres:
   - `pipenv run flask db upgrade`
   - `pipenv run flask setup_db`
4. Run the development server:
   - `pipenv run flask run`
   - Visit http://127.0.0.1:5000
5. Production-style runner for local testing:
   - `pipenv run gunicorn -w 2 -b 127.0.0.1:5000 timeclock:app`

## 3) Docker Workflow

### Docker Quick Steps (Windows, PowerShell)

Use these copy/paste steps for a clean, simple setup.

1) Install Docker Desktop
- Download and install from docker.com. Enable WSL 2 when prompted.
- Start Docker Desktop and wait for "Engine running".

2) Open a PowerShell in the project folder
- `cd "C:\\Users\\Leonardo Lopez\\Desktop\\timeclock"`
- Verify Docker: `docker --version` and `docker compose version`

3) Build and start containers
- Build fresh: `docker compose build --no-cache`
- Start stack: `docker compose up -d`
- App URL: http://127.0.0.1:5000

4) Initialize database (choose ONE option)
- Option A — Migrations only (fresh schema):
  - `docker compose exec web flask db upgrade`
  - `docker compose exec web flask setup_db`
- Option B — Restore provided dump `timeclock_20250404.sql`:
  - Drop/recreate DB:
    - `docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS timeclock WITH (FORCE);"`
    - `docker compose exec -T db psql -U postgres -d postgres -c "CREATE DATABASE timeclock WITH TEMPLATE template0 ENCODING 'UTF8';"`
  - Ensure legacy role exists:
    - `docker compose exec -T db psql -U postgres -d postgres -c "CREATE ROLE timeclock_db;"`
  - Import dump:
    - `Get-Content timeclock_20250404.sql | docker compose exec -T db psql -U postgres -d timeclock`
  - Align Alembic version:
    - `docker compose exec -T db psql -U postgres -d timeclock -c "UPDATE alembic_version SET version_num='8408e175c444';"`
  - Seed app data:
    - `docker compose exec web flask setup_db`

5) Create admin user (admin@example.com / password)
- `docker compose exec web python -c "from app import create_app, db; from app.models import User, Role, Tag; app=create_app('default'); ctx=app.app_context(); ctx.push(); role=Role.query.filter_by(name='Administrator').first(); tag=Tag.query.filter_by(name='Employee').first(); user=User(email='admin@example.com', first_name='Admin', last_name='User', division='Administration', role=role, tag=tag, is_supervisor=True, validated=True); user.password='password'; user.password_list.update(user.password_hash); db.session.add(user); db.session.commit(); print('Created admin user with id', user.id)"`

6) Verify
- Users count: `docker compose exec -T db psql -U postgres -d timeclock -c "SELECT COUNT(*) FROM users;"`
- App logs: `docker compose logs -f web`
- Login at http://127.0.0.1:5000 with `admin@example.com` / `password`.

### Build & Run Containers

1. Build images from the locked dependency set:
   - `docker compose build --no-cache`
2. Start the stack (web + Postgres 15):
   - `docker compose up -d`
   - App: http://127.0.0.1:5000
   - Postgres exposed on host port 5438 (`db` service listens on 5432 internally)

### Restore the Seed Database Dump (PowerShell examples)

1. Drop and recreate the database inside the container:
   - `docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS timeclock WITH (FORCE);"`
   - `docker compose exec -T db psql -U postgres -d postgres -c "CREATE DATABASE timeclock WITH TEMPLATE template0 ENCODING 'UTF8';"`
2. Ensure the legacy owner role exists (ignore "role already exists" warnings if it is already present):
   - `docker compose exec -T db psql -U postgres -d postgres -c "CREATE ROLE timeclock_db;"`
3. Stream the dump into Postgres (PowerShell):
   - `Get-Content timeclock_20250404.sql | docker compose exec -T db psql -U postgres -d timeclock`
4. Align Alembic with the current migrations head:
   - `docker compose exec -T db psql -U postgres -d timeclock -c "UPDATE alembic_version SET version_num='8408e175c444';"`
5. Seed roles/tags inside the app container:
   - `docker compose exec web flask setup_db`

### Insert an Administrator Account

Create `admin@example.com` with password `password` (Administrator role, supervisor, validated):

```
docker compose exec web python -c "from app import create_app, db; from app.models import User, Role, Tag; app=create_app('default'); ctx=app.app_context(); ctx.push(); role=Role.query.filter_by(name='Administrator').first(); tag=Tag.query.filter_by(name='Employee').first(); user=User(email='admin@example.com', first_name='Admin', last_name='User', division='Administration', role=role, tag=tag, is_supervisor=True, validated=True); user.password='password'; user.password_list.update(user.password_hash); db.session.add(user); db.session.commit(); print('Created admin user with id', user.id)"
```

Repeat the same command (after removing `print`) if you ever need to reset the account in a fresh database.

### Common Docker Tasks

- View logs: `docker compose logs -f web`
- Run a one-off shell: `docker compose exec web bash`
- Run the unit tests: `docker compose exec web flask test`
- Stop the stack: `docker compose down`
- Remove stack + data volume: `docker compose down -v`

## 4) Verify the Database

- Application-level check:
  - `pipenv run python scripts/verify_db.py` (or `--json`)
- Post-restore smoke tests:
  - `docker compose exec -T db psql -U postgres -d timeclock -c "SELECT COUNT(*) FROM users;"`

## Troubleshooting

- Pipenv not found: add `$(python3 -m site --user-base)/bin` to PATH and open a new terminal.
- psql/pgAdmin connection failures: ensure Postgres is running (`brew services start postgresql@15` on macOS) and DATABASE_URL matches the correct host/port.
- Role/database errors during restores: create any missing roles (for example `CREATE ROLE timeclock_db;`) and recreate the `timeclock` database before re-importing.
- After editing migrations locally, rerun `pipenv run flask db upgrade` or `docker compose exec web flask db upgrade` to keep schema in sync.
- For login issues immediately after restoring a dump, reset the admin user with the command in the Administrator section above.

## Email, ReCAPTCHA, and Sessions

- For password reset email testing, set mail vars in `.env` or plug in a local mail catcher.
- ReCAPTCHA keys (v2/v3) are optional in local dev; set them in `.env` to exercise verification paths.
- Sessions use Flask-Session with filesystem storage by default; no Redis is required locally.

## Password Hashing Notes

- Password hashes use PBKDF2-SHA256 so they fit in the current `users.password_hash` (VARCHAR(128)). If you widen the column, you can swap to a stronger hash method.
