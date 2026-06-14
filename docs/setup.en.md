# Development setup

There are two ways to run the app locally. Pick whichever suits you.

- [Bare-metal (pyenv + local Postgres)](#bare-metal)
- [Docker Compose](#docker)
- [What to do next](#first-steps-after-install)

---

## Bare-metal

For local development on Linux/macOS directly with pyenv and a local Postgres.

### 1. Requirements

| Tool | Version |
|---|---|
| Python | 3.13.x |
| PostgreSQL | 16.x |
| Node.js | 20.x+ (for the biome linter) |
| pyenv | latest (optional but recommended) |

### 2. Clone the repository

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar
```

### 3. Create the Python environment

```bash
pyenv install 3.13.8         # if not already installed
pyenv virtualenv 3.13.8 crkva
pyenv local crkva            # binds the directory to the environment
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Install Node tooling (biome linter)

```bash
npm install     # installs @biomejs/biome into node_modules/
```

### 5. Configure the environment

```bash
cp .env.dev.example .env
# Edit .env if needed (DEBUG, ALLOWED_HOSTS, ...) — see architecture.md for details
```

### 6. Start Postgres and create the database

```bash
sudo systemctl start postgresql
sudo -u postgres createuser devuser --pwprompt          # put the password in .env
sudo -u postgres createdb devdb -O devuser
```

### 7. Migrations + tenant

```bash
cd crkva
python manage.py migrate_schemas       # creates the public schema + tenants
python manage.py createsuperuser
```

### 8. Pre-commit hooks

```bash
pre-commit install
```

### 9. Run the server

```bash
python manage.py runserver
# Open http://localhost:8000/ and sign in at /prijava/
```

---

## Docker

For an isolated development environment via Docker Compose.

### 1. Requirements

- [Docker](https://www.docker.com/products/docker-desktop) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2

### 2. Clone and configure

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar
cp .env.dev.example .env
```

### 3. Build

```bash
docker compose --profile dev build
# or
make build
```

### 4. Run

```bash
docker compose --profile dev up -d   # dev environment (with live reload)
# or
make dev-up
```

The server listens on [http://localhost:8000/](http://localhost:8000/). Postgres is exposed on port 8001 (mapped from 5432 in the container).

### 5. Migrations + superuser

```bash
docker compose --profile dev run --rm app-dev python manage.py migrate_schemas
docker compose --profile dev run --rm app-dev python manage.py createsuperuser
```

### 6. Everyday commands

| Command | What it does |
|---|---|
| `make dev-up` | Starts the containers |
| `make dev-down` | Stops the containers |
| `make dev-logs` | Tails the logs |
| `make dev-shell` | Django shell inside the container |
| `make dev-migrate` | Runs migrations |
| `make dev-makemigrations` | Creates new migrations |

---

## First steps after install

### Load demo data (optional)

If you want test parishioners/baptisms/weddings before you start:

```bash
# bare-metal:
python manage.py unos_krstenja
python manage.py unos_vencanja

# Docker:
docker compose --profile dev run --rm app-dev python manage.py unos_krstenja
docker compose --profile dev run --rm app-dev python manage.py unos_vencanja
```

### Load real data from HramSP

If migrating from the legacy HramSP app: see [MIGRACIJA.md](MIGRACIJA.md).

### Create a new parish (tenant)

Each parish is a separate Postgres schema. Creating one is done via the Django admin or a script — see [architecture.md](architecture.md).

---

## Troubleshooting

**`relation "..." does not exist`** — you didn't run `migrate_schemas` for the tenant. Run it again.

**Pre-commit hooks fail on `django-tests`** — a known issue with the parallel runner; bypass for the current commit with `SKIP=django-tests git commit ...`.

**`Permission denied` on the Docker socket** — add your user to the `docker` group: `sudo usermod -aG docker $USER`, then log out and back in.

**Biome won't run** — you didn't run `npm install`. The `biome` pre-commit hook needs it.
