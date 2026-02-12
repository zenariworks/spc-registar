# Technology Stack

**Analysis Date:** 2026-02-11

## Languages

**Primary:**
- Python 3.10 - Backend application and data processing logic
- HTML/Django Templates - Server-side rendered views and components
- CSS3 - Styling with BEM methodology
- JavaScript - Client-side interactivity (minimal, primarily localStorage for theme persistence)

**Secondary:**
- SQL - PostgreSQL schema and queries

## Runtime

**Environment:**
- Python 3.10 (Alpine 3.13 in Docker)
- WSGI Server: uWSGI (production) via gunicorn
- Django 5.1.2 framework

**Package Manager:**
- pip
- Lockfile: requirements.txt (pinned versions with ~= constraints)

## Frameworks

**Core:**
- Django 5.1.2 - Web framework and ORM
- Django REST Framework 3.15.2 - REST API framework (installed but limited usage)

**Admin & Data Management:**
- django-import-export 4.2.0 - Import/export functionality for admin
- django-select2 8.2.1 - Enhanced select dropdowns with search
- django-admin-searchable-dropdown 1.2 - Searchable admin dropdowns
- django-filter 24.3 - Queryset filtering and filtering UI
- django-extensions 3.2.3 - Additional Django management commands

**Assets & Compression:**
- django-compressor 4.4 - CSS/JS compression and offline compilation

**Utilities:**
- python-dateutil 2.8.2 - Date/time utilities for Easter and feast calculations
- django-environ 0.11.0 - Environment variable management

**PDF Generation:**
- WeasyPrint 62.3 - HTML to PDF conversion for certificates/reports
- Pillow 12.0.0 - Image processing and manipulation
- rcssmin 1.1.0 - CSS minimization for WeasyPrint

## Key Dependencies

**Critical:**
- Django 5.1.2 - MVC framework, ORM, admin, templating, security middleware
- psycopg2-binary 2.9.10 - PostgreSQL database adapter

**Database:**
- PostgreSQL 15+ (external, configured via environment variables)

**Infrastructure:**
- uWSGI 2.0.19+ - WSGI application server for production
- Django compressor - Asset optimization during build

## Configuration

**Environment:**
- Configured via `.env` file (read by django-environ)
- Critical vars: `SECRET_KEY`, `DEBUG`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_SCHEMA`, `DB_USER`, `DB_PASS`, `ALLOWED_HOSTS`
- Example configs: `.env.dev.example`, `.env.prod.example`

**Database:**
- PostgreSQL with schema isolation via `search_path={SCHEMA}`
- Connection pool managed by Django ORM
- Migrations via Django's migration framework

**Build:**
- Dockerfile: Multi-layer Alpine-based image for size efficiency
- docker-compose.yml: Development orchestration with PostgreSQL service
- docker-compose.prod.yml: Production overrides (external DB, gunicorn workers)

**Settings Module:**
- Primary: `crkva.settings` (Base Django settings file)
- Database configured in `crkva/settings.py` lines 96-110
- Compressor settings: `COMPRESS_ENABLED=True`, `COMPRESS_OFFLINE=False` (offline mode for production builds)

## Platform Requirements

**Development:**
- Python 3.10 (via .python-version)
- Docker & Docker Compose
- PostgreSQL 15+ (via docker-compose service or external)
- 2GB+ RAM for PDF rendering with WeasyPrint

**Production:**
- Container runtime (Docker/Kubernetes/ECS)
- External PostgreSQL 15+ database
- Minimum 512MB RAM
- WSGI-compatible reverse proxy (nginx recommended)
- Static file serving capability (CDN or volume mount at `/vol/web/static/`)

## Build Process

**Development:**
```bash
docker-compose up -d
```

**Production:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Entry Command:**
- Development: Django dev server via `python manage.py runserver 0.0.0.0:8000`
- Production: Gunicorn with 4 workers: `gunicorn --bind 0.0.0.0:8000 --workers 4 app.wsgi:application`

## Frontend Stack

**CSS:**
- Plain CSS3 with BEM naming convention (enforced by stylelint)
- Compressed via django-compressor
- Fonts: Google Fonts (Source Sans Pro) + local TTF fonts for Serbian Orthodox characters
- Theme system: Light/dark mode via data-theme attribute (localStorage persistence)

**JavaScript:**
- Minimal custom JavaScript
- FontAwesome 6.5.1 via CDN for icons
- Django Select2 for enhanced dropdowns
- No build tool (CSS/JS compression handled by django-compressor)

**Static Files:**
- Served from `/vol/web/static/` volume mount
- Media files served from `/vol/web/media/`
- Compressed offline for production via `python manage.py compress`

---

*Stack analysis: 2026-02-11*
