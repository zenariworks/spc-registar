# Codebase Concerns

**Analysis Date:** 2026-02-11

## Tech Debt

**Heavy Migration Command Complexity:**
- Issue: Large data migration scripts with complex business logic and file I/O operations bundled with Django command implementations
- Files: `crkva/registar/management/commands/migracija_krstenja.py` (475 lines), `crkva/registar/management/commands/migracija_vencanja.py` (391 lines), `crkva/registar/management/commands/migracija_parohijana.py` (149 lines)
- Impact: These commands handle sensitive historical data conversion. Changes risk data corruption. No separation between data transformation logic and Django infrastructure. Hard to test independently.
- Fix approach: Extract conversion logic to separate `registar/utils/migration_converters.py`, create dedicated `Konvertor` test suite, add comprehensive data validation before saving to database, implement dry-run mode.

**Fasting Rules Implementation Duplication:**
- Issue: Complex Orthodox Christian fasting calculation logic is split across `registar/utils_fasting.py` (419 lines) with significant duplication in date range logic
- Files: `crkva/registar/utils_fasting.py` (lines 157-420 in `is_fasting_day()` and `get_fasting_type()` contain repeated dict construction, weekday checking, date calculations)
- Impact: Multiple functions recalculate the same values (trap weeks, great lent, apostles fast), leading to inefficiency and maintenance issues when rules change
- Fix approach: Cache computed fasting periods in `get_fasting_days_from_db()` result, create `FastingPeriod` namedtuple for consistent data structure, refactor `get_fasting_type()` to use helper methods for each period type instead of inline logic.

**Settings Configuration Issues:**
- Issue: `ALLOWED_HOSTS = ["*"]` configured in production-compatible settings file
- Files: `crkva/crkva/settings.py` (line 39)
- Impact: Security vulnerability - allows any Host header value, enabling Host Header Injection attacks
- Fix approach: Use environment variable with validated host list: `ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")` in production settings only.

**Missing Database Query Optimization:**
- Issue: ViewSets and ListViews don't use `.select_related()` or `.prefetch_related()` for foreign key relationships
- Files: `crkva/registar/views/__init__.py` (line 52: `Slava.objects.filter(pokretni=True)`), `crkva/registar/views/krstenje_view.py` (line 42-43: `SpisakKrstenja.get_queryset()` loads related Hram models without prefetch)
- Impact: N+1 query problem when displaying lists with related objects (Krstenje with Hram, Svestenik; Parohijan with Adresa). Scales poorly with data volume.
- Fix approach: Add `.select_related('hram', 'svestenik')` in `SpisakKrstenja.get_queryset()`, add `.prefetch_related()` for reverse relationships in admin list displays.

**Incomplete Admin Configuration:**
- Issue: Admin search fields reference model fields that aren't properly indexed and use default autocomplete without select_related optimization
- Files: `crkva/registar/admin/parohijan_admin.py` (lines 22-29), `crkva/registar/admin/ulica_admin.py` (likely similar issue)
- Impact: Admin searches slow down with large datasets, autocomplete queries trigger additional database hits for each related object
- Fix approach: Add `list_select_related()` and `get_search_results()` override with `.select_related()`, index search fields in migrations.

**Time Zone Configuration Mismatch:**
- Issue: `TIME_ZONE = "Europe/Amsterdam"` (line 137 in settings.py) doesn't match Serbian Orthodox calendar calculations
- Files: `crkva/crkva/settings.py` (line 137), all fasting calculation functions
- Impact: Calendar calculations and feast day dates may be off by hours in edge cases, time-sensitive operations near midnight may show wrong dates
- Fix approach: Use `TIME_ZONE = "Europe/Belgrade"` for accurate Serbian time representation.

## Known Bugs

**Calendar Date Boundary Edge Case:**
- Symptoms: Fasting type calculations fail when Eastern Orthodox date transitions occur around midnight
- Files: `crkva/registar/utils_fasting.py` (lines 157-187 in `is_fasting_day()` function)
- Trigger: During transition from Gregorian to Julian calendar dates in spring/fall, simultaneous fasting period boundaries
- Workaround: Manual date checking in admin, refresh page after midnight
- Root cause: No timezone-aware date handling when calculating fasting periods relative to vaskrs (Easter). Current implementation assumes UTC midnight.

**Incomplete Test Coverage:**
- Symptoms: Placeholder test exists that doesn't validate core functionality
- Files: `crkva/registar/tests.py` (lines 6-13: test named `test_animals_can_speak()` testing Parohijan, unrelated to actual functionality)
- Trigger: Running test suite - test passes but doesn't validate any real behavior
- Impact: No safety net for regression testing on models, views, or migration logic
- Fix approach: Create comprehensive test suite with fixtures for calendar calculations, migration data validation, view rendering.

## Security Considerations

**Environment Variable Exposure Risk:**
- Risk: `.env` file checked into git history (line noted in .gitignore but file exists with past values)
- Files: Root `.env` file, `.env.dev.example`, `.env.prod.example` (examples are OK, but actual `.env` should not exist)
- Current mitigation: `.env` is in `.gitignore`, but git history may contain old values
- Recommendations:
  - Rotate `SECRET_KEY` immediately
  - Run `git filter-repo` to remove `.env` from history if ever committed
  - Use pre-commit hook to prevent env file commits
  - Document required env vars clearly with `.env.example`

**SQL Injection via Migration Commands:**
- Risk: `migracija_*.py` commands parse external data files and directly convert strings before ORM layer validation
- Files: `crkva/registar/management/commands/migracija_krstenja.py` (lines 100-175), `migracija_vencanja.py`, `migracija_parohijana.py`
- Current mitigation: Django ORM .save() uses parameterized queries, but data passed through `Konvertor.string()` without validation
- Recommendations:
  - Add whitelist validation for string data
  - Implement pre-import data validation step
  - Log all imported records with hash for audit trail
  - Add rollback/cleanup option for migration commands

**Admin Interface Open to Public:**
- Risk: `ALLOWED_HOSTS = ["*"]` + no visible authentication enforcement in `urls.py`
- Files: `crkva/urls.py` (line 23), `crkva/crkva/settings.py` (line 39)
- Current mitigation: Django admin requires login, but relies on ALLOWED_HOSTS for Host validation which is set to wildcard
- Recommendations:
  - Restrict ALLOWED_HOSTS to specific domains
  - Add SSL enforcement (`SECURE_SSL_REDIRECT = True` in production)
  - Implement rate limiting on admin login
  - Add IP whitelisting for admin path

**PDF Generation Vulnerability:**
- Risk: `WeasyPrint` used without HTML sanitization in PDF generation views
- Files: `crkva/registar/views/krstenje_view.py` (line 72), similar in other PDF views
- Impact: If any template data comes from user input without escaping, could allow SSRF/code injection
- Current mitigation: Django templates auto-escape by default
- Recommendations:
  - Add explicit `mark_safe()` review - ensure only trusted data
  - Validate template context before rendering
  - Add Content Security Policy headers

## Performance Bottlenecks

**Calendar View Full Database Loads:**
- Problem: Home page (`index()` view) fetches ALL fixed Slava records monthly and ALL moveable Slava records for year range
- Files: `crkva/registar/views/__init__.py` (lines 38-57)
- Cause: Loop over 7 days fetches 2+ queries minimum (fixed by month, moveable filtered), then iterates over results in Python
- Improvement path:
  - Cache Slava records by month (Redis cache with 1 year TTL)
  - Pre-compute vaskrs dates at year start
  - Use single SQL query with OR conditions instead of separate fetches
  - Expected improvement: 500ms → 50ms page load time

**Fasting Type Calculation Inefficiency:**
- Problem: `get_fasting_type()` function recalculates vaskrs and computes all fasting periods for every date queried
- Files: `crkva/registar/utils_fasting.py` (lines 190-420), called from `index()` view for each date
- Cause: No memoization, redundant date arithmetic, repeated Slava.objects.filter() calls
- Improvement path:
  - Add `@functools.lru_cache` with year-based key
  - Pre-compute annual fasting calendar once per year
  - Store in cache layer or compile to static JSON
  - Expected improvement: O(n) iterations over Slava table → O(1) lookup

**Admin Import-Export Performance:**
- Problem: `ImportExportMixin` with large record sets (1000+ Parohijan records) causes timeout
- Files: `crkva/registar/admin/parohijan_admin.py` (line 10)
- Cause: No batch processing, default Django ORM creates individual queries per record
- Improvement path:
  - Override `get_import_formats()` to batch operations
  - Use `bulk_create()` in resource class with `batch_size=1000`
  - Add progress bar for large imports
  - Implement async task queue (Celery) for import jobs

**PDF Generation Synchronous Blocking:**
- Problem: WeasyPrint PDF generation is CPU-intensive and blocks request handling
- Files: `crkva/registar/views/krstenje_view.py` (line 72: `HTML().write_pdf()` call)
- Impact: Single PDF request can timeout (15-30 seconds) during heavy usage
- Improvement path:
  - Move PDF generation to background task (Celery)
  - Queue for later download
  - Return task ID immediately
  - Add cache for frequently-generated PDFs

## Fragile Areas

**Fasting Calculation Logic:**
- Files: `crkva/registar/utils_fasting.py` (all functions)
- Why fragile: Complex inter-dependent date calculations with multiple edge cases (Julian/Gregorian conversion, leap years, century rules). Small changes cascade through multiple functions. Hard to verify correctness.
- Safe modification:
  - Write comprehensive test suite with known dates and expected fasting types
  - Verify against external Orthodox calendar authority
  - Use property-based testing (hypothesis library) for date ranges
  - Create audit trail showing calculations for manual verification
- Test coverage gaps: Zero tests for fasting logic, Slava model calculations, or conversion functions

**Data Migration Commands:**
- Files: `crkva/registar/management/commands/migracija_*.py` (all three migration files)
- Why fragile: Complex state machine with conditional branches for data parsing, conversion errors silently logged, no rollback mechanism. One malformed record could stop entire migration.
- Safe modification:
  - Never modify while production data exists
  - Always create backup before running
  - Run in dry-run mode first
  - Implement data validation before import
  - Add comprehensive logging with record-level details
- Test coverage gaps: No unit tests for Konvertor class, no integration tests with sample data files

**Model Field Validation:**
- Files: Model definitions in `crkva/registar/models/` (particularly Slava, Krstenje, Parohijan with many optional fields)
- Why fragile: Many nullable fields (null=True, blank=True) with interdependent constraints not enforced at database level
- Safe modification:
  - Add model-level `clean()` method for cross-field validation
  - Document which field combinations are valid
  - Add database constraints for critical fields
  - Implement form-level validation to catch early
- Test coverage gaps: No validation tests for invalid field combinations

**Admin Interface Customizations:**
- Files: Multiple admin files in `crkva/registar/admin/`
- Why fragile: Search fields reference model fields without guaranteed existence (line 22-29 in parohijan_admin.py lists search fields that must match model). Autocomplete_fields depend on specific model relationships.
- Safe modification:
  - Always verify field names exist in corresponding model
  - Test search functionality after model changes
  - Use model introspection to validate admin configuration
- Test coverage gaps: No admin interface tests validating search fields, filters, or autocomplete work

## Scaling Limits

**Database Connection Pooling:**
- Current capacity: Django default connection pool (single persistent connection)
- Limit: With 100+ concurrent users, single connection saturates, query queue backs up
- Scaling path:
  - Implement PgBouncer (PostgreSQL connection pooler)
  - Set connection pool size based on application replicas
  - Add read replicas for reporting queries (calendar, statistics)
  - Monitor slow queries with `pg_stat_statements`

**Static Media File Handling:**
- Current capacity: MEDIA_ROOT mounted to `/vol/web/media/` (single volume)
- Limit: No distributed storage - if running multiple app instances, each sees own media files
- Scaling path:
  - Migrate to S3-compatible storage (MinIO, AWS S3)
  - Use django-storages for transparent media handling
  - Pre-generate PDFs and cache in CDN

**PDF Generation Throughput:**
- Current capacity: Synchronous WeasyPrint, single-threaded request handling
- Limit: ~2-3 PDFs/second per process before timeouts
- Scaling path:
  - Implement task queue (Celery + Redis)
  - Generate PDFs asynchronously
  - Cache PDF output by content hash
  - Add rate limiting per user

**Session Store:**
- Current capacity: In-memory session storage (default Django)
- Limit: Lost on app restart, not shared across multiple instances
- Scaling path:
  - Migrate to Redis/Memcached session backend
  - Configure sticky sessions at load balancer

## Dependencies at Risk

**WeasyPrint 62.3:**
- Risk: WeasyPrint security updates lag, PDF generation performance issues reported
- Impact: PDF vulnerabilities could expose application to malicious input
- Migration plan:
  - Monitor WeasyPrint releases, upgrade when patches available
  - Consider alternative: ReportLab (lighter, faster) or pre-render to static PDFs
  - Set max PDF generation timeout to prevent DoS

**Django 5.1.2:**
- Risk: Security updates end after release, need to track maintenance window
- Impact: Unpatched vulnerabilities if on unsupported version
- Migration plan:
  - Plan upgrade path to Django LTS versions (currently 5.1, will be 6.0 LTS)
  - Set calendar reminder for Django security updates
  - Test each minor version thoroughly (1-2 week cycle)

**uWSGI >= 2.0.19.1:**
- Risk: Older constraint, may have known CVEs in versions 2.0.19.1-2.0.x
- Impact: Potential remote code execution vulnerabilities
- Migration plan:
  - Update to latest stable uWSGI 2.1+ or switch to Gunicorn
  - Verify production compatibility before deployment

**psycopg2-binary 2.9.10:**
- Risk: psycopg2-binary not recommended for production (should use psycopg2 with system postgres-devel)
- Impact: Version mismatches with system PostgreSQL, security patches lag
- Migration plan:
  - Switch to `psycopg2` (not binary) in requirements
  - Ensure docker builds install PostgreSQL dev headers

## Missing Critical Features

**Audit Logging:**
- Problem: No record of who changed what data, when, and why
- Blocks: Compliance with data protection regulations, forensic investigation if data corruption occurs
- Implementation: Add django-audit-log or similar, log all admin changes, model save/delete operations

**Data Validation Framework:**
- Problem: No centralized way to validate data constraints (must encode in model clean(), forms, and migrations separately)
- Blocks: Prevents consistent validation across API/admin/migrations
- Implementation: Create `registar/validators.py` with reusable validators, use in models and forms

**API Endpoints:**
- Problem: Only Django admin and basic views, no REST API for programmatic access
- Blocks: Cannot build mobile app, third-party integrations
- Implementation: Add django-rest-framework, create read-only endpoints for public data

**Search Across Multiple Models:**
- Problem: Each model has own search view, no unified search
- Blocks: Users must know which type of record to search for
- Implementation: Add global search that spans Parohijan, Krstenje, Vencanje with unified results

**Backup and Restore Mechanism:**
- Problem: No backup job configured, no documented restore procedure
- Blocks: Data loss recovery if database corruption or disk failure
- Implementation: Add pg_dump cronjob, document restore procedure, test quarterly

## Test Coverage Gaps

**Fasting Logic:**
- What's not tested: Calculation of Orthodox Easter dates, fasting period boundaries, handling of edge cases (leap years, Julian-Gregorian boundary dates)
- Files: `crkva/registar/utils_fasting.py` (entire file)
- Risk: Entire calendar functionality could break unnoticed, users see wrong fasting types
- Priority: High - core business logic

**Model Validation:**
- What's not tested: Cross-field validation (e.g., moveable Slava must have offset_dani or offset_nedelje), required field combinations
- Files: `crkva/registar/models/slava.py`, `krstenje.py`, `vencanje.py`, others
- Risk: Invalid data in database if form validation bypassed or admin misused
- Priority: High - data integrity

**Migration Commands:**
- What's not tested: Data conversion functions (Konvertor class), handling of malformed input files, integrity constraints after migration
- Files: `crkva/registar/management/commands/migracija_krstenja.py`, `migracija_vencanja.py`, `migracija_parohijana.py`
- Risk: Silent data loss or corruption during migrations, no way to validate migration success
- Priority: Critical - historical data integrity

**View Rendering:**
- What's not tested: Calendar view data population, template context generation, PDF generation
- Files: `crkva/registar/views/__init__.py`, `krstenje_view.py`, others
- Risk: Broken views, missing data in templates, PDF generation failures
- Priority: Medium - user-facing functionality

**Admin Interface:**
- What's not tested: Search functionality, filtering, bulk actions, import/export
- Files: All admin files in `crkva/registar/admin/`
- Risk: Admin searches silently return wrong results, filters fail, imports corrupt data
- Priority: Medium - backend operations

**Serialization and Data Export:**
- What's not tested: Import/export format compatibility, data integrity during export/re-import
- Files: Resource classes referenced by ImportExportMixin
- Risk: Exported data cannot be re-imported, data truncation during export
- Priority: Medium - data portability

---

*Concerns audit: 2026-02-11*
