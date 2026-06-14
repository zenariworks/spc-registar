# Setup & running

Pick a path based on what you need. All Docker paths use a single
`docker-compose.yml` with profiles (`dev` / `standalone` / `prod`).

| Path | For whom | Command |
|---|---|---|
| **Standalone (Docker)** | local PC, Windows laptop, single server | `start.bat` / `./start.sh` → _below_ |
| **Development** | contributing to the code | `make dev-up` or a pyenv venv → _below_ |
| **Production** | server with a domain/HTTPS | [Deployment](deployment.md) |

> django-tenants (multi-tenant) and WeasyPrint (PDF) require Linux + Postgres —
> so a Linux container is shipped (the same on Windows/macOS/Linux); SQLite is
> not supported.

---

## Standalone (Docker, all-in-one)

App + its own Postgres in containers — the easiest path for a local machine or a
single server. Data is stored in the named volume `postgres_data`.

### Requirements
- **Docker Desktop** (Windows/macOS, with WSL2) or **Docker Engine + Compose v2** (Linux).

### Run

=== "Windows"
    Run **`start.bat`** (double-click or from a terminal).

=== "Linux / macOS"
    Run **`./start.sh`**.

=== "Directly (compose)"
    ```bash
    docker compose --profile standalone up -d --build
    ```

App: **http://localhost:8000** · first sign-in **admin / admin**.

### Manage
```bash
docker compose --profile standalone down          # stop
docker compose --profile standalone logs -f app   # logs
docker compose --profile standalone up -d --build # update (after git pull)
```

### Initial data
The default parish (`crkva_sv_petke_cukarica`) is created automatically.
Reference tables and the feast calendar are seeded once:
```bash
docker compose --profile standalone \
  run --rm app python manage.py seed_lookups --tenant crkva_sv_petke_cukarica
```
To import real data from the legacy HramSP app (`crkva.zip`) see
[Data migration](MIGRACIJA.md).

### Data & backup
```bash
docker compose --profile standalone exec db pg_dump -U crkva crkva > backup.sql
```

### Notes
- **Plain HTTP / localhost** (`SECURE_SSL=0`) — for local/LAN use, no certificates.
- **Change the password and key** for anything exposed: `DJANGO_SUPERUSER_PASSWORD` and `SECRET_KEY`.
- **LAN access:** add the host IP/name to `ALLOWED_HOSTS` (e.g. `localhost,192.168.1.50`).

---

## Development

For working on the code itself — two options: bare-metal (pyenv) or the Docker `dev` profile.

### Option A — bare-metal (pyenv + local Postgres)

Requirements: Python 3.13.x, PostgreSQL 16.x, Node.js 20.x+ (biome linter), pyenv (recommended).

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar

pyenv install 3.13.8            # if not already installed
pyenv virtualenv 3.13.8 crkva
pyenv local crkva
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

npm install                    # biome linter into node_modules/
cp .env.dev.example .env       # edit as needed (see architecture.md)

# Postgres + database
sudo systemctl start postgresql
sudo -u postgres createuser devuser --pwprompt   # put the password in .env
sudo -u postgres createdb devdb -O devuser

cd crkva
python manage.py migrate_schemas               # public schema + tenants
python manage.py createsuperuser
cd .. && pre-commit install
cd crkva && python manage.py runserver         # http://localhost:8000/
```

### Option B — Docker (`dev` profile)

```bash
cp .env.dev.example .env
docker compose --profile dev up -d --build     # runserver + live reload, bundled Postgres
docker compose --profile dev run --rm app-dev python manage.py createsuperuser
```

Daily commands (Makefile): `make dev-up` · `make dev-down` · `make dev-logs` ·
`make dev-shell` · `make dev-migrate` · `make dev-makemigrations`.

### Demo data (optional)
```bash
# bare-metal:
python manage.py unos_krstenja
python manage.py unos_vencanja
# Docker:
docker compose --profile dev run --rm app-dev python manage.py unos_krstenja
```

---

## Production

Production runs either **bare-metal** (gunicorn + systemd + Caddy — the current live
setup) or **Docker** (`--profile prod`: gunicorn + Caddy, external database). Full
procedure: [Deployment](deployment.md).

---

## Troubleshooting

**`relation "..." does not exist`** — you haven't run `migrate_schemas` for the tenant. Run it again.

**Pre-commit hooks fail on `django-tests`** — skip for the current commit: `SKIP=django-tests git commit ...`.

**`Permission denied` on the Docker socket** — add your user to the `docker` group: `sudo usermod -aG docker $USER`, then log out and back in.

**Biome won't start** — you haven't run `npm install`.
