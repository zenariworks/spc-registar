# External Integrations

**Analysis Date:** 2026-02-11

## APIs & External Services

**None Detected**

The application does not currently integrate with external APIs or third-party services. All data operations are internal.

**Note:** django-phonenumber-field is imported but commented out in settings (`INSTALLED_APPS` line 58 of `crkva/settings.py`), indicating no phone number validation integration is active.

## Data Storage

**Databases:**
- PostgreSQL 15+ - Primary relational database
  - Connection: Environment variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`
  - Schema isolation: Custom schema via `DB_SCHEMA` (default: `public`)
  - Client: Django ORM (`django.db`)
  - Adapter: psycopg2-binary 2.9.10

**File Storage:**
- Local filesystem only
  - Static files: `/vol/web/static/`
  - Media files: `/vol/web/media/`
  - In Docker: Volume mount `static_data:/vol/web`

**Caching:**
- None configured (Django cache framework not in use)

## Authentication & Identity

**Auth Provider:**
- Django built-in authentication system
  - Configured in `crkva/settings.py` lines 44-69
  - Middleware: `django.contrib.auth.middleware.AuthenticationMiddleware`
  - User model: Django's default User model
  - Password validators: Four standard validators (similarity, minimum length, common passwords, numeric)

**Access Control:**
- Django admin (`/admin/`) - Requires Django superuser credentials
- No role-based access control (RBAC) or permission system in use
- All authenticated users have same access level to admin panel

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Rollbar, etc.)

**Logs:**
- Standard Python logging to console (StreamHandler)
- Log level: INFO for production, DEBUG for django logger
- Configuration: `crkva/settings.py` lines 178-191
- Structured logging: Not implemented

**Debug:**
- Django debug toolbar available when `DEBUG=True`
- Exception details printed to console in development

## CI/CD & Deployment

**Hosting:**
- Container-based deployment (Docker)
- Deployment target: Any container runtime (Docker Swarm, Kubernetes, ECS, etc.)
- Reverse proxy: Recommended nginx (configured via `proxy/` directory)

**CI Pipeline:**
- None detected (no GitHub Actions, Jenkins, or CI config found)

**Container Registry:**
- Docker image: `zenfiric/app:latest` (per docker-compose.yml line 4)
- Build context: Project root Dockerfile

## Code Quality Tools

**Linting & Formatting:**
- Black 24.4.2 - Python code formatting
- Ruff 0.5.4 - Python linter
- isort 5.13.2 - Import sorting (profile: black)
- Pylint - Static analysis with Django plugin (fail-under threshold: 9)
- Stylelint - CSS linting (enforces BEM naming)

**Pre-commit Hooks:**
- Configured in `.pre-commit-config.yaml`
- Checks: Trailing whitespace, file endings, JSON validation, large files, merge conflicts, requirements.txt ordering
- ruff auto-fixes issues when violations found

**Testing:**
- pytest - Test runner
- Configuration: `pytest.ini`
- Django settings module for tests: `djangodocker.settings.testing` (note: mismatch - actual module is `crkva`)

## Environment Configuration

**Required env vars (production):**
- `SECRET_KEY` - Django secret key (required, no default)
- `DEBUG` - Debug mode (default: 0)
- `DB_HOST` - PostgreSQL hostname (required)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (required)
- `DB_SCHEMA` - PostgreSQL schema (default: public)
- `DB_USER` - Database user (required)
- `DB_PASS` - Database password (required)
- `ALLOWED_HOSTS` - Comma-separated host whitelist (default: *)

**Development env vars (.env.dev.example):**
```
DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
DB_HOST=db
DB_PORT=5432
DB_NAME=devdb
DB_SCHEMA=public
DB_USER=devuser
DB_PASS=changeme
ALLOWED_HOSTS=localhost,127.0.0.1,*
```

**Secrets location:**
- Environment file: `.env` (gitignored, not in repository)
- Docker environment: Passed via environment variables in docker-compose/k8s manifests
- Should use: Docker secrets (Swarm) or Kubernetes secrets (k8s) in production

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Data Import/Export

**Capabilities:**
- django-import-export 4.2.0 - Admin interface supports CSV/Excel import/export
- Location: `crkva/registar/resources/` directory
- Used for bulk operations on church records (baptisms, weddings, clergy, parishioners)

**Management Commands for Data Migration:**
- Custom commands in `crkva/registar/management/commands/`:
  - `unos_*.py` - Data entry scripts for initial population
  - `migracija_*.py` - Data migration scripts from legacy formats
  - `wait_for_db.py` - Database readiness check for Docker startup
  - `mark_major_feasts.py` - Feast day calendar maintenance
  - `fix_moveable_feasts.py` - Easter-dependent feast updates

## Third-Party Static Resources

**CDN Dependencies:**
- Google Fonts: `https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap`
- FontAwesome 6.5.1: `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css`

**Note:** These are loaded in production templates (`crkva/registar/templates/base.html` lines 27-54). Offline alternatives should be considered for air-gapped deployments.

## PDF Generation

**Service:**
- WeasyPrint 62.3 - HTML to PDF rendering
- Used for: Certificate/document printing (routes with `*PDF` classes in views)
- Fonts: Includes system fonts and custom Serbian Orthodox typefaces from `/static/registar/fontovi/`
- Implementation: Views extending WeasyPrint base classes in `crkva/registar/views/` (e.g., `ParohijanPDF`, `KrstenjePDF`, `VencanjePDF`)

---

*Integration audit: 2026-02-11*
