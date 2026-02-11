# Codebase Structure

**Analysis Date:** 2026-02-11

## Directory Layout

```
spc-registar/
├── crkva/                          # Django project root (Python package)
│   ├── manage.py                   # Django command-line utility
│   ├── .python-version             # Python version specifier
│   ├── crkva/                      # Project settings package
│   │   ├── __init__.py
│   │   ├── settings.py             # Django configuration
│   │   ├── urls.py                 # Root URL routing
│   │   ├── wsgi.py                 # WSGI application entry point
│   │   └── asgi.py                 # ASGI application entry point
│   ├── registar/                   # Main application (Django app)
│   │   ├── __init__.py
│   │   ├── apps.py                 # App configuration
│   │   ├── models/                 # Data models
│   │   │   ├── __init__.py
│   │   │   ├── parohijan.py        # Parishioner model
│   │   │   ├── krstenje.py         # Baptism model
│   │   │   ├── vencanje.py         # Wedding model
│   │   │   ├── svestenik.py        # Clergy model
│   │   │   ├── slava.py            # Saint's feast day model
│   │   │   ├── adresa.py           # Address model
│   │   │   ├── hram.py             # Church/temple model
│   │   │   ├── parohija.py         # Parish model
│   │   │   ├── eparhija.py         # Diocese model
│   │   │   ├── crkvena_opstina.py  # Church municipality model
│   │   │   ├── mesto.py            # Place model
│   │   │   ├── ulica.py            # Street model
│   │   │   ├── opstina.py          # Municipality model
│   │   │   ├── drzava.py           # Country model
│   │   │   ├── veroispovest.py     # Religion model
│   │   │   ├── narodnost.py        # Ethnicity model
│   │   │   ├── zanimanje.py        # Occupation model
│   │   │   └── ukucanin.py         # Household member model
│   │   ├── views/                  # View controllers
│   │   │   ├── __init__.py         # Imports and exports all views
│   │   │   ├── parohijan_view.py   # Parishioner list/detail/PDF views
│   │   │   ├── krstenje_view.py    # Baptism list/detail/PDF views
│   │   │   ├── vencanje_view.py    # Wedding list/detail/PDF views
│   │   │   ├── svestenik_view.py   # Clergy list/detail/PDF views
│   │   │   ├── kalendar_view.py    # Feast day calendar view
│   │   │   └── view_404.py         # Custom 404 error handler
│   │   ├── admin/                  # Django admin configuration
│   │   │   ├── __init__.py         # Registers all admin classes
│   │   │   ├── parohijan_admin.py  # Admin for parishioners
│   │   │   ├── krstenje_admin.py   # Admin for baptisms
│   │   │   ├── vencanje_admin.py   # Admin for weddings
│   │   │   ├── svestenik_admin.py  # Admin for clergy
│   │   │   ├── slava_admin.py      # Admin for feast days
│   │   │   ├── adresa_admin.py     # Admin for addresses
│   │   │   └── [11 more admin files for other models]
│   │   ├── forms/                  # Form validation and rendering
│   │   │   ├── __init__.py         # Exports all forms
│   │   │   ├── forms.py            # Generic forms (SearchForm)
│   │   │   ├── parohijan_form.py   # Parishioner form
│   │   │   ├── krstenje_form.py    # Baptism form
│   │   │   ├── vencanje_form.py    # Wedding form
│   │   │   └── veroispovest_form.py # Religion form
│   │   ├── filters/                # Django-filter definitions
│   │   │   ├── __init__.py
│   │   │   ├── krstenja_filter.py  # Baptism filtering with search
│   │   │   └── vencanja_filter.py  # Wedding filtering with search
│   │   ├── templates/              # HTML templates
│   │   │   ├── base.html           # Base template with header/sidebar
│   │   │   ├── header.html         # Header component
│   │   │   ├── sidebar.html        # Sidebar navigation component
│   │   │   ├── 404.html            # 404 error page
│   │   │   ├── core/               # Core templates
│   │   │   │   ├── admin/
│   │   │   │   │   └── change_list.html  # Custom admin change list
│   │   │   │   └── category_list.html
│   │   │   └── registar/           # Feature-specific templates
│   │   │       ├── index.html      # Homepage with calendar
│   │   │       ├── kalendar.html   # Feast day calendar view
│   │   │       ├── spisak_parohijana.html  # Parishioner list
│   │   │       ├── info_parohijana.html    # Parishioner detail
│   │   │       ├── pdf_parohijan.html      # Parishioner PDF template
│   │   │       ├── spisak_krstenja.html    # Baptism list
│   │   │       ├── info_krstenje.html      # Baptism detail
│   │   │       ├── pdf_krstenje.html       # Baptism PDF template
│   │   │       ├── pdf_krstenje_stara_krstenica.html  # Legacy certificate format
│   │   │       ├── unos_krstenja.html      # Baptism data entry form
│   │   │       ├── unos_parohijana.html    # Parishioner data entry form
│   │   │       ├── unos_vencanja.html      # Wedding data entry form
│   │   │       ├── search_view.html        # Global search results
│   │   │       └── [more templates for weddings, clergy]
│   │   ├── templatetags/           # Custom Django template filters/tags
│   │   │   ├── __init__.py
│   │   │   ├── julian_dates.py     # Julian calendar date conversion
│   │   │   └── marker_filter.py    # Text highlighting/marking filter
│   │   ├── static/                 # Static assets (images, CSS, JS)
│   │   │   └── registar/
│   │   │       ├── stilovi/        # CSS stylesheets
│   │   │       ├── layout/         # Layout CSS
│   │   │       ├── fontovi/        # Custom fonts
│   │   │       └── utilities/      # Utility CSS classes
│   │   ├── migrations/             # Django database migrations
│   │   │   └── [auto-generated migration files]
│   │   ├── management/             # Django management commands
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       ├── unos_*.py       # Data import commands (unos_mesta, unos_svestenika, etc.)
│   │   │       ├── migracija_*.py  # Data migration commands (migracija_parohijana, etc.)
│   │   │       ├── mark_major_feasts.py    # Mark major Orthodox feasts
│   │   │       ├── fix_moveable_feasts.py  # Compute/fix moveable feast dates
│   │   │       ├── wait_for_db.py         # Health check for Docker startup
│   │   │       ├── convert_utils.py       # Utility conversion functions
│   │   │       ├── random_utils.py        # Random data generation
│   │   │       └── randoms/
│   │   │           └── ulica_random.py    # Random street name generation
│   │   ├── resources/              # Import-export resource definitions
│   │   │   └── [resource definitions for bulk operations]
│   │   ├── tests/                  # Test files
│   │   │   └── [test modules]
│   │   ├── tests.py                # Legacy test module placeholder
│   │   ├── urls.py                 # Registar app URL routing
│   │   ├── utils.py                # Utility functions (Latin-Cyrillic transliteration)
│   │   ├── utils_fasting.py        # Fasting calendar and feast day computations
│   │   └── context_processors.py   # Django context processors (feast days for templates)
│   ├── fixtures/                   # Test and initialization data fixtures
│   │   └── [JSON/JSONL fixture files]
│   └── data/                       # Static data files
│       └── [data initialization files]
├── proxy/                          # Nginx reverse proxy configuration
│   ├── Dockerfile                  # Docker image for proxy
│   ├── default.conf.tpl            # Nginx configuration template
│   ├── run.sh                      # Proxy startup script
│   └── uwsgi_params                # uWSGI parameter forwarding
├── scripts/                        # Deployment and utility scripts
│   └── [shell scripts for deployment]
├── docs/                           # Documentation
│   └── [markdown/documentation files]
├── data/                           # Data directory (Django static/media root in Docker)
│   └── web/
│       ├── static/                 # Collected static files
│       └── media/                  # User-uploaded media files
├── .planning/                      # GSD planning documents (this analysis)
│   └── codebase/
│       ├── ARCHITECTURE.md         # This file's architecture analysis
│       └── STRUCTURE.md            # This file
├── docker-compose.override.yml     # Local Docker development config
├── docker-compose.prod.yml         # Production Docker compose
├── .env                            # Environment variables (secrets - DO NOT COMMIT)
├── .env.dev.example                # Example dev environment variables
├── .env.prod.example               # Example prod environment variables
├── .github/                        # GitHub configuration
│   ├── workflows/                  # CI/CD workflows
│   └── ISSUE_TEMPLATE/             # Issue templates
├── .pre-commit-config.yaml         # Pre-commit hook configuration
├── .pylintrc                       # PyLint configuration
├── .isort.cfg                      # Import sorting configuration
├── .stylelintrc.json               # CSS linting configuration
├── .gitignore                      # Git ignore patterns
├── CLAUDE.md                       # AI agent instructions (Agentic QE v3 config)
└── build.sh                        # Build/deployment script
```

## Directory Purposes

**`crkva/`:**
- Purpose: Django project root containing configuration, WSGI/ASGI entry points, and the registar app
- Contains: Project settings, URL routing, WSGI/ASGI applications
- Key files: `manage.py` (command runner), `settings.py` (config), `urls.py` (routing)

**`crkva/registar/`:**
- Purpose: Main Django application implementing the church registry domain
- Contains: Models, views, admin interfaces, forms, templates, utility functions
- Key files: `models/` (data definitions), `views/` (handlers), `admin/` (backend UI), `templates/` (frontend)

**`crkva/registar/models/`:**
- Purpose: Domain entities for Orthodox Church registry system
- Contains: 20 model definition files representing parishioners, events (baptisms, weddings), clergy, locations, feast days
- Key files: `parohijan.py` (central entity), `slava.py` (feast day calendar), `krstenje.py` (baptisms), `vencanje.py` (weddings)

**`crkva/registar/views/`:**
- Purpose: HTTP request handlers and view logic for public registry interface
- Contains: Function-based views (search, data entry), class-based views (lists, detail, PDF generation)
- Key files: `parohijan_view.py`, `krstenje_view.py`, `vencanje_view.py` (CRUD + PDF views)

**`crkva/registar/admin/`:**
- Purpose: Backend staff interface for managing all registry entities
- Contains: Django admin ModelAdmin subclasses with import/export capabilities for each model
- Key files: `*_admin.py` for each model (e.g., `parohijan_admin.py`)

**`crkva/registar/forms/`:**
- Purpose: Form definitions for data validation and user input handling
- Contains: Django Form subclasses for search, data entry (parishioners, baptisms, weddings)
- Key files: `parohijan_form.py`, `krstenje_form.py`, `vencanje_form.py`, `forms.py` (generic SearchForm)

**`crkva/registar/filters/`:**
- Purpose: Search/filter logic for Django ListView filtering
- Contains: django_filters FilterSet definitions with multi-field search
- Key files: `krstenja_filter.py`, `vencanja_filter.py` (support Latin-Cyrillic query variants)

**`crkva/registar/templates/`:**
- Purpose: HTML presentation layer for rendering web pages and PDF documents
- Contains: Django template files organized by feature
- Key files: `base.html` (layout), `registar/index.html` (homepage), `registar/pdf_*.html` (PDF templates), `registar/unos_*.html` (data entry forms)

**`crkva/registar/templatetags/`:**
- Purpose: Custom Django template filters and tags
- Contains: Python modules extending template language (date conversions, text highlighting)
- Key files: `julian_dates.py` (Orthodox calendar date filtering), `marker_filter.py` (search result highlighting)

**`crkva/registar/management/commands/`:**
- Purpose: One-time setup, data import, and maintenance tasks
- Contains: Django management commands for database initialization, data migration, utility operations
- Key files: `unos_*.py` (load reference data), `migracija_*.py` (migrate from legacy systems), `wait_for_db.py` (Docker health check)

**`proxy/`:**
- Purpose: Nginx reverse proxy configuration for production deployment
- Contains: Docker image definition, Nginx config template, startup script
- Key files: `Dockerfile` (builds Nginx image), `default.conf.tpl` (Nginx configuration)

**`scripts/`:**
- Purpose: Deployment and operational scripts
- Contains: Shell scripts for building, deploying, and managing the application

**`data/web/static/`:**
- Purpose: Collected static files (CSS, JS, fonts) served by web server
- Contains: Django admin static files, custom application stylesheets, fonts
- Generated: Yes (created by `python manage.py collectstatic`)
- Committed: No (generated during deployment)

## Key File Locations

**Entry Points:**
- `crkva/wsgi.py`: WSGI application (loaded by uWSGI server)
- `crkva/urls.py`: Root URL dispatcher (routes /admin/ to admin, everything else to registar app)
- `crkva/registar/urls.py`: Registar app URL dispatcher (routes to views)

**Configuration:**
- `crkva/settings.py`: Django settings (database, apps, middleware, templates)
- `.env`: Environment variables (SECRET_KEY, DB_HOST, DEBUG, etc.) — **never commit**
- `docker-compose.override.yml`: Local Docker development setup
- `docker-compose.prod.yml`: Production Docker deployment

**Core Logic:**
- `crkva/registar/models/parohijan.py`: Central Parishioner model (primary domain entity)
- `crkva/registar/models/slava.py`: Feast day model with fixed/moveable support
- `crkva/registar/utils.py`: Latin-Cyrillic transliteration utilities
- `crkva/registar/utils_fasting.py`: Orthodox fasting calendar computation
- `crkva/registar/context_processors.py`: Template context providers (upcoming feast days)

**Views/Handlers:**
- `crkva/registar/views/parohijan_view.py`: Parishioner list/detail/PDF views and data entry
- `crkva/registar/views/krstenje_view.py`: Baptism list/detail/PDF views and data entry
- `crkva/registar/views/vencanje_view.py`: Wedding list/detail/PDF views and data entry
- `crkva/registar/views/__init__.py`: Central view import aggregator (index, calendar, search)

**Testing:**
- `crkva/registar/tests/`: Directory for test modules (if present)
- `crkva/registar/tests.py`: Legacy test placeholder
- `crkva/fixtures/`: Test data fixtures in JSON/JSONL format

## Naming Conventions

**Files:**
- Models: Singular lowercase entity name with `.py` (e.g., `parohijan.py`, `krstenje.py`)
- Admin classes: `{entity}_admin.py` (e.g., `parohijan_admin.py`)
- View modules: `{entity}_view.py` (e.g., `parohijan_view.py`)
- Forms: `{entity}_form.py` (e.g., `parohijan_form.py`)
- Templates: kebab-case descriptive names with `.html` (e.g., `spisak_parohijana.html`, `pdf_krstenje.html`)
- Management commands: verb/action name underscore-separated (e.g., `mark_major_feasts.py`, `migracija_parohijana.py`)

**Directories:**
- Plural names for Django convention: `models/`, `views/`, `admin/`, `forms/`, `filters/`, `templates/`, `migrations/`, `management/`
- Nested by feature: `templates/registar/` for app-specific templates
- Feature-based organization: `management/commands/` groups all commands

**Database Tables:**
- Plural lowercase: `parohijani`, `krstenja`, `vencanja` (Serbian language plurals)
- Defined via Django `Meta.db_table` in each model

**Python Classes:**
- Models: PascalCase entity name (e.g., `Parohijan`, `Krstenje`)
- Admin classes: `{Model}Admin` (e.g., `ParohijanAdmin`)
- View classes: Action + Entity (e.g., `SpisakParohijana` = Parishioner List, `PrikazParohijana` = Parishioner Detail, `ParohijanPDF` = PDF generator)
- Form classes: `{Entity}Form` (e.g., `ParohijanForm`)
- Filter classes: `{Entity}Filter` (e.g., `KrstenjeFilter`)

**Python Functions:**
- View functions: verb + noun pattern (e.g., `unos_parohijana()`, `search_view()`, `custom_404()`)
- Utility functions: descriptive snake_case (e.g., `get_query_variants()`, `latin_to_cyrillic()`, `is_fasting_day()`)

**URL Patterns:**
- Kebab-case paths: `parohijani/`, `krstenja/`, `vencanja/`
- Named routes with underscores: `parohijani`, `parohijan_detail`, `parohijan_pdf`
- RESTful pattern: `/resource/` (list), `/resource/<id>/` (detail), `/resource/print/<id>/` (PDF)

## Where to Add New Code

**New Model/Entity:**
1. Create model file: `crkva/registar/models/{entity_name}.py`
2. Import in: `crkva/registar/models/__init__.py`
3. Create admin: `crkva/registar/admin/{entity_name}_admin.py`
4. Import in: `crkva/registar/admin/__init__.py`
5. Create migration: `python manage.py makemigrations`
6. Add to INSTALLED_APPS if new Django app (unlikely - most are in registar app)

**New View/Page:**
1. Create view function/class in: `crkva/registar/views/{entity_name}_view.py` or in `__init__.py`
2. Export from: `crkva/registar/views/__init__.py`
3. Add URL pattern: `crkva/registar/urls.py`
4. Create template: `crkva/registar/templates/registar/{view_name}.html`
5. If public form data entry, create form: `crkva/registar/forms/{entity_name}_form.py`

**New Utility Function:**
- Cross-cutting concern: `crkva/registar/utils.py` (transliteration, text processing)
- Calendar/feast logic: `crkva/registar/utils_fasting.py` (Orthodox calendar computations)
- Template context: `crkva/registar/context_processors.py` (make data available to all templates)

**New Data Import:**
- Create command: `crkva/registar/management/commands/{action}_{entity}.py` (e.g., `unos_zanimanja.py`)
- Follow existing pattern: Load CSV/JSON, create model instances
- Commands are run with: `python manage.py {action}_{entity}`

**New Template:**
- Location: `crkva/registar/templates/registar/` (feature-specific)
- Inherit from: `base.html` for common layout
- Include: `header.html`, `sidebar.html` for navigation components
- Use custom tags: `{% load julian_dates marker_filter %}` for custom filtering

**New Test:**
- Location: `crkva/registar/tests/{test_module}.py` (organized by entity/feature)
- Class-based structure: `TestParohijanModel`, `TestParohijanView`
- Follow Django testing conventions: Use `TestCase`, `Client` for integration tests

## Special Directories

**`crkva/registar/migrations/`:**
- Purpose: Store Django ORM migration files tracking database schema changes
- Generated: Yes (created by `python manage.py makemigrations`)
- Committed: Yes (must commit to version control)
- How to use: Create with `python manage.py makemigrations`, apply with `python manage.py migrate`

**`data/web/static/`:**
- Purpose: Collected static assets served by web server (CSS, JS, fonts, images)
- Generated: Yes (created by `python manage.py collectstatic`)
- Committed: No (generated during Docker build)
- Volume mount in Docker: `/vol/web/static/` in production

**`data/web/media/`:**
- Purpose: User-uploaded files and generated documents (PDFs)
- Generated: Yes (runtime uploads and PDF generation)
- Committed: No (runtime data)
- Volume mount in Docker: `/vol/web/media/` in production

**`.claude/`:**
- Purpose: Claude Code IDE configuration and extensions
- Generated: Yes (by Claude Code)
- Committed: No (.gitignore excludes)

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents (this analysis)
- Generated: Yes (by GSD mapping commands)
- Committed: Yes (consumed by `/gsd:plan-phase` and `/gsd:execute-phase`)

---

*Structure analysis: 2026-02-11*
