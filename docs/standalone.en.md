# Standalone Docker

Run SPC Registar in Docker, without a bare-metal setup. Two paths:

- **A) All-in-one (bundled)** — the app + its own Postgres in containers.
  Easiest for a local PC, Windows, or a single server.
- **B) Image + external database** — the app container only, pointed at an existing Postgres.

> Multi-tenancy (django-tenants) and WeasyPrint (PDF) need a Linux environment and
> Postgres — so a Linux container is shipped (the same one on Windows/mac/Linux).

## Requirements

- **Docker Desktop** (Windows/mac, with WSL2) or **Docker Engine + Compose v2** (Linux).
- Commands use `docker compose` (v2).

## A) All-in-one (bundled)

Ships Postgres too; stores data in named volumes.

### Windows
Run **`start.bat`** (double-click or from a terminal). It brings the stack up and prints the address.

### Linux / mac
```bash
docker compose --profile standalone up -d --build
```

App: **http://localhost:8000** · first sign-in **admin / admin**.

### Initial seeding (optional)
The default parish is created automatically. Reference tables (ethnicities,
confessions, occupations, eparchies) and the slava calendar are seeded once:
```bash
docker compose --profile standalone \
  run --rm app python manage.py seed_lookups --tenant crkva_sv_petke_cukarica
```

### Management
```bash
# stop
docker compose --profile standalone down
# logs
docker compose --profile standalone logs -f app
# update (after git pull)
docker compose --profile standalone up -d --build
```

### Data and backup
The database lives in the `postgres_data` volume, static files in `static_data`. Database backup:
```bash
docker compose --profile standalone \
  exec db pg_dump -U crkva crkva > backup.sql
```

## B) Image + external database

For a server with an existing/managed Postgres.
```bash
cp .env.prod.example .env   # set SECRET_KEY, DB_*, ALLOWED_HOSTS
docker compose --profile prod up -d --build
```
The `prod` profile starts no database; connect to an external Postgres via `.env`.
Behind a reverse proxy (e.g. Caddy) keep `SECURE_SSL=1` (the default outside DEBUG) and
forward `X-Forwarded-Proto`.

## Notes

- **Plain HTTP / localhost.** The bundled path runs over `http://localhost:8000`
  (`SECURE_SSL=0`), with no certificate — for local/LAN use.
- **Change the password and key.** For anything exposed, change
  `DJANGO_SUPERUSER_PASSWORD` and `SECRET_KEY` (env or `.env`).
- **LAN access.** To reach it from other machines, add the host IP/name to
  `ALLOWED_HOSTS`, e.g. `ALLOWED_HOSTS=localhost,192.168.1.50`.
- **No SQLite.** django-tenants requires Postgres.
