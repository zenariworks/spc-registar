# Architecture

**Analysis Date:** 2026-02-11

## Pattern Overview

**Overall:** Django MVT (Model-View-Template) monolithic application with domain-driven organization around Orthodox Church registry concepts (parishes, clergy, baptisms, weddings, saints' feasts).

**Key Characteristics:**
- Layered architecture: Models → Admin Interface → Views → Templates
- Domain-driven entity organization around church/registry concepts
- Admin-first interface (Django admin) with public-facing web views
- Dual search capability: Latin-Cyrillic transliteration support with database query variants
- Calendar/temporal computation layer for Orthodox feast days (fixed and moveable)

## Layers

**Data Layer (Models):**
- Purpose: Define domain entities for Orthodox Church registry (parishioners, clergy, baptisms, weddings, churches, addresses)
- Location: `crkva/registar/models/`
- Contains: 20+ model files (parohijan.py, krstenje.py, vencanje.py, svestenik.py, slava.py, etc.)
- Depends on: Django ORM, PostgreSQL database
- Used by: Admin interface, views, management commands

**Admin Layer (Backend Interface):**
- Purpose: Provide admin users CRUD operations with import/export capabilities for all registry entities
- Location: `crkva/registar/admin/`
- Contains: Admin class definitions for each model (e.g., `parohijan_admin.py`, `krstenje_admin.py`) using Django admin + import_export
- Depends on: Django admin framework, import_export library
- Used by: Admin staff for data management

**View Layer (Public Interface):**
- Purpose: Render public-facing web pages for viewing registry data, entering new records, generating PDFs
- Location: `crkva/registar/views/`
- Contains: Function-based views (search_view, index, unos_*) and class-based views (ListView, DetailView for lists/detail, PDF generation)
- Depends on: Django template rendering, WeasyPrint for PDF generation, models
- Used by: HTTP clients accessing public web interface

**Template Layer (Presentation):**
- Purpose: Render HTML pages for public interface and PDF documents
- Location: `crkva/registar/templates/`
- Contains: HTML templates organized by feature (registar/spisak_parohijana.html, registar/pdf_krstenje.html, etc.)
- Depends on: Django template engine, CSS/static files
- Used by: Views layer for rendering responses

**Utility Layer:**
- Purpose: Provide cross-cutting concerns and helpers
- Location: `crkva/registar/utils.py`, `crkva/registar/utils_fasting.py`, `crkva/registar/context_processors.py`
- Contains: Latin-Cyrillic transliteration, feast day computation, fasting calendar logic, template context processors
- Depends on: Python standard library, Django utilities
- Used by: Views, models, templates

**Management/Initialization Layer:**
- Purpose: Data import, initialization, and one-time setup tasks
- Location: `crkva/registar/management/commands/`
- Contains: Django management commands for data ingestion (unos_*.py), migration scripts (migracija_*.py), utility helpers (convert_utils.py, random_utils.py)
- Depends on: Django management framework, models
- Used by: Deployment scripts and administrators

**Configuration Layer:**
- Purpose: Application configuration, database settings, middleware setup
- Location: `crkva/settings.py`, `crkva/urls.py`, `crkva/wsgi.py`
- Contains: Django settings (database, installed apps, middleware, templates), URL routing
- Depends on: Environment variables, Django framework
- Used by: WSGI server, request routing

## Data Flow

**Public Registry View Flow:**

1. HTTP request → `crkva/urls.py` routes to appropriate view
2. View (e.g., `SpisakParohijana` in `registar/views/parohijan_view.py`) executes `get_queryset()`
3. Query variants generated via `get_query_variants()` from `utils.py` (Latin-Cyrillic support)
4. ORM filters `Parohijan` model records matching search criteria
5. Template context with queryset and search form passed to `registar/templates/registar/spisak_parohijana.html`
6. Template renders HTML response with pagination (10 items per page)
7. HTTP response returned to client

**PDF Generation Flow:**

1. Request to `/parohijan/print/<uid>/` → `ParohijanPDF.render_to_response()`
2. Model instance fetched via `get_object()`
3. Template `registar/pdf_parohijan.html` rendered to HTML string
4. WeasyPrint converts HTML → PDF binary
5. HTTP response with `application/pdf` content-type returned

**Data Entry Flow:**

1. GET request to `/unos/parohijana/` → render form template
2. POST with form data → Django form validation via `ParohijanForm`
3. If valid: form.save() → model instance created → redirect to list view
4. If invalid: template re-rendered with error messages

**Calendar/Feast Day Flow:**

1. Context processor `processor_narednih_slava()` called on every page request
2. Fetches fixed feasts from `Slava` table (where mesec/dan match current date)
3. Fetches moveable feasts via `Slava.get_datum(year)` for Gauss algorithm computed Easter dates
4. Groups by date and includes fasting day information
5. Variables passed to all templates: `hoje_slave`, `dandas_slave`, `narednih_slave`, fasting flags

**State Management:**

- No client-side state management (Django ORM manages state)
- Session state via Django middleware (`SessionMiddleware`) for admin authentication
- Template context variables passed per-request (stateless)
- Database is source of truth for all domain data

## Key Abstractions

**Parohijan (Parishioner):**
- Purpose: Central entity representing individual parishioner with name, address, birth date, religion, feast day
- Examples: `crkva/registar/models/parohijan.py`
- Pattern: Django Model with relationships to Adresa and Slava; `__str__` method for admin display

**Krstenje (Baptism):**
- Purpose: Record of a baptism event with details about child, parents, godparents, church, date
- Examples: `crkva/registar/models/krstenje.py`
- Pattern: UUID-based primary key (vs AutoField for parishioners), foreignkey to Hram (church/temple)

**Slava (Saint's Feast Day):**
- Purpose: Define fixed and moveable Orthodox feast days with names, dates, fasting levels
- Examples: `crkva/registar/models/slava.py`
- Pattern: Supports both fixed (mesec/dan) and moveable (offset from Easter) feast dates

**Vencanje (Wedding):**
- Purpose: Record of a wedding event with bride/groom details and church information
- Examples: `crkva/registar/models/vencanje.py`
- Pattern: Similar structure to Krstenje with UUID primary key

**Svestenik (Clergy):**
- Purpose: Record of a priest/clergy member with position and church assignment
- Examples: `crkva/registar/models/svestenik.py`
- Pattern: Linked to Hram and Parohija via foreign keys

**SearchForm + KrstenjeFilter:**
- Purpose: Provide unified search interface across domain entities with transliteration support
- Examples: `crkva/registar/forms/forms.py`, `crkva/registar/filters/krstenja_filter.py`
- Pattern: Use `get_query_variants()` to convert Latin/Cyrillic and generate variant-based queries

## Entry Points

**Web Server Entry Point:**
- Location: `crkva/wsgi.py`
- Triggers: WSGI server (uWSGI in Docker) loads and calls `application`
- Responsibilities: Initialize Django application context for request handling

**Main Router:**
- Location: `crkva/urls.py`
- Triggers: Every HTTP request
- Responsibilities: Route requests to registar app or Django admin; serve static files in DEBUG mode

**Registar URL Dispatcher:**
- Location: `crkva/registar/urls.py`
- Triggers: All non-admin requests
- Responsibilities: Map URL patterns to view functions/classes (index, calendars, lists, detail views, PDF generation, data entry)

**Management Command Entry Points:**
- Location: `crkva/registar/management/commands/*.py`
- Triggers: `python manage.py <command_name>`
- Responsibilities: Data initialization (unos_*), migration (migracija_*), and setup tasks

**Admin Interface:**
- Location: Django admin at `/admin/` via `djangocontrib.admin`
- Triggers: Authenticated staff access
- Responsibilities: CRUD operations for all models with import/export

## Error Handling

**Strategy:** Minimal explicit error handling; relies on Django defaults + custom 404 handler

**Patterns:**
- Custom 404 handler: `crkva/registar/views/view_404.py` renders custom `404.html` template
- Form validation errors: Rendered in templates via `{{ form.errors }}` constructs
- Database errors: Propagated as HTTP 500 responses (Django default)
- PDF generation errors (WeasyPrint): Caught at view level in `ParohijanPDF.render_to_response()`
- Missing objects: `get_object_or_404()` raises 404 if model instance not found

## Cross-Cutting Concerns

**Logging:**
- Approach: Django logging configuration in `settings.py` (console handler at INFO level for Django ORM)
- No application-level log statements currently visible; relies on Django/database logging

**Validation:**
- Approach: Django model-level validation via `verbose_name` fields, form-level validation via `Form.is_valid()`
- Transliteration awareness: `ParohijanForm`, `KrstenjaForm` use `get_query_variants()` for flexible name matching during search

**Authentication:**
- Approach: Django's built-in auth middleware (`AuthenticationMiddleware`) for session-based admin access
- No custom authentication; admin interface protected by Django's default staff/superuser checks
- Public views (parishioner lists, calendars) have no authentication requirement

**Database Transactions:**
- Approach: PostgreSQL connection with schema isolation (SCHEMA environment variable sets search_path)
- Encoding: UTF8 for Cyrillic support
- Auto-commit mode for single-statement operations; no explicit transaction management observed

---

*Architecture analysis: 2026-02-11*
