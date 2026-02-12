# Phase 1: Data Migration Workflow Simplification - Research

**Researched:** 2026-02-11
**Domain:** Django Management Commands, DBF Data Migration, PostgreSQL Staging Tables
**Confidence:** HIGH

## Summary

Phase 1 aims to consolidate a complex multi-step data migration workflow from legacy DBF files into a single unified Django management command. The current system requires 4-5 manual steps with separate commands for each entity type (krstenja, vencanja, parohijana, etc.), totaling ~1,495 lines of migration code across 8 files. The existing architecture already has reusable components (`convert_utils.py` with `Konvertor` class, `base_migration.py` with `MigrationCommand` base class) that can be leveraged, but lacks unified orchestration, dry-run capabilities, and clear separation between dummy development data and real production data from crkva.zip.

**Primary recommendation:** Build on existing `MigrationCommand` base class and `Konvertor` utility; create new `manage.py migrate_data` command that orchestrates all migration steps with `--dummy`/`--real`/`--dry-run` flags; extract reusable logic to `registar/utils/migration_converters.py` module; add progress indicators using `tqdm` or Django's built-in progress output.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 6.0.1 | Web framework and ORM | User constraint, latest stable Django 6.x |
| dbfread | 2.0.7 | DBF file parsing | Already in use, stable library for reading dBASE files |
| psycopg2-binary | 2.9.10 | PostgreSQL adapter | Django PostgreSQL backend requirement |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tqdm | Latest (4.67+) | Progress bars | For long-running migrations with user feedback |
| python-dotenv | Latest (1.0+) | Environment config | If adding environment-based migration configs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dbfread | pandas + pydbf | pandas adds 50MB+ dependency for minimal benefit |
| Custom progress | Django's self.stdout.write | tqdm provides better UX with actual progress bars |
| Separate commands | Single monolith command | Current approach allows granular control but lacks orchestration |

**Installation:**
```bash
# Already installed
django~=6.0.1
dbfread~=2.0.7
psycopg2-binary~=2.9.10

# Optional additions
tqdm~=4.67.0  # For progress bars
```

## Architecture Patterns

### Recommended Project Structure
```
crkva/registar/
├── management/
│   └── commands/
│       ├── migrate_data.py          # NEW: Unified migration command
│       ├── load_dbf.py               # KEEP: DBF loader (already good)
│       ├── base_migration.py         # KEEP: Base class (already exists)
│       ├── convert_utils.py          # KEEP: Konvertor (already exists)
│       └── migracija_*.py            # REFACTOR: Extract logic, keep as fallback
└── utils/
    └── migration_converters.py       # NEW: Extracted conversion logic
```

### Pattern 1: Unified Migration Command with Flags
**What:** Single `manage.py migrate_data` command with mutually exclusive flags for dummy vs real data
**When to use:** When you need to orchestrate multiple migration steps based on data source
**Example:**
```python
# Source: Django best practices for management commands
class Command(BaseCommand):
    help = "Migrate data from legacy DBF files (dummy or real)"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--dummy', action='store_true',
                          help='Load dummy development data')
        group.add_argument('--real', action='store_true',
                          help='Load real data from crkva.zip')

        parser.add_argument('--dry-run', action='store_true',
                           help='Validate without saving to database')
        parser.add_argument('--skip-staging', action='store_true',
                           help='Skip load_dbf step (use existing staging tables)')

    def handle(self, *args, **options):
        if options['dummy']:
            self.load_dummy_data(dry_run=options['dry_run'])
        else:
            self.load_real_data(dry_run=options['dry_run'])
```

### Pattern 2: Two-Phase Migration (Staging → Production)
**What:** Load DBF files into staging tables (`hsp_*`), then migrate to Django models with validation
**When to use:** When data requires transformation and you want rollback capability
**Example:**
```python
# Current architecture (KEEP THIS PATTERN)
# Phase 1: load_dbf.py loads DBF → hsp_* staging tables
# Phase 2: migracija_*.py transforms hsp_* → Django models

# NEW: Orchestrate both phases in migrate_data.py
def handle_migration(self, source, dry_run=False):
    # Phase 1: Load DBF to staging
    if not dry_run:
        call_command('load_dbf', src_zip=source)

    # Phase 2: Migrate staging → models
    self.migrate_krstenja(dry_run=dry_run)
    self.migrate_vencanja(dry_run=dry_run)
    # ... etc
```

### Pattern 3: Progress Reporting with Summary
**What:** Show progress during migration and summary report at end
**When to use:** For long-running operations where user needs feedback
**Example:**
```python
from tqdm import tqdm

def migrate_records(self, records, dry_run=False):
    created = 0
    skipped = 0
    errors = []

    for record in tqdm(records, desc="Migrating krstenja"):
        try:
            if not dry_run:
                Krstenje.objects.create(**record)
            created += 1
        except ValidationError as e:
            errors.append((record['redni_broj'], str(e)))
            skipped += 1

    return {'created': created, 'skipped': skipped, 'errors': errors}
```

### Pattern 4: Dry-Run Mode with Validation
**What:** Run all migration logic without `save()` to detect issues before committing
**When to use:** Before production migrations to validate data integrity
**Example:**
```python
def _build_krstenje(self, record, dry_run=False):
    # Build object
    data = {...}

    if dry_run:
        # Validate without saving
        obj = Krstenje(**data)
        obj.full_clean()  # Runs model validation
        return None  # Don't save
    else:
        return Krstenje.objects.create(**data)
```

### Anti-Patterns to Avoid
- **N+1 Queries in Migration:** Don't call `get_or_create()` in loop without caching related objects (already present in `migracija_vencanja.py` lines 194-195 - good pattern to replicate)
- **Silent Failures:** Don't skip errors without logging - current commands log to stderr but don't accumulate for summary report
- **Hardcoded Paths:** Don't hardcode `/mnt/c/HramSP/dbf` - use arguments or environment variables (already fixed in `load_dbf.py`)
- **Mixing Concerns:** Don't put business logic (data conversion) in management command - extract to separate module

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ZIP extraction | Custom unzip logic | `zipfile.ZipFile` from stdlib | Already used in `load_dbf.py`, handles edge cases |
| Progress bars | Custom spinner with threads | `tqdm` library | Handles terminal width, nested bars, rate calculation |
| DBF parsing | Custom binary reader | `dbfread.DBF` | Already in use, handles cp1250 encoding, tested |
| Cyrillic conversion | Manual char mapping | Keep existing `Konvertor.string()` | Domain-specific Serbian Latin→Cyrillic, already implemented |
| Django transactions | Manual BEGIN/COMMIT | `@atomic` decorator | Already used in `migracija_vencanja.py:188`, handles rollback |
| Command orchestration | Shell scripts | Django `call_command()` | Keeps everything in Python, easier to test |

**Key insight:** Migration code is deceptively complex - character encoding issues (cp1250), database integrity constraints, transaction management, and data validation edge cases make custom solutions risky. Leverage Django ORM's built-in safeguards.

## Common Pitfalls

### Pitfall 1: DBF Encoding Issues (cp1250)
**What goes wrong:** Serbian characters get mangled if encoding not specified, or if mixed Latin/Cyrillic in source data
**Why it happens:** DBF files from Windows use cp1250 (Central European) encoding, Python defaults to UTF-8
**How to avoid:** Always specify `encoding='cp1250'` when opening DBF files (already done in `load_dbf.py:154`)
**Warning signs:** Seeing `Ã¡` instead of `а`, or UnicodeDecodeError exceptions

### Pitfall 2: Staging Table Collision
**What goes wrong:** Running `load_dbf` multiple times creates duplicate data or fails on existing tables
**Why it happens:** `load_dbf.py` does `DROP TABLE IF EXISTS` (line 175) but migration commands don't coordinate
**How to avoid:** Add `--skip-staging` flag to reuse existing staging tables; add data validation before `DROP TABLE`
**Warning signs:** Migration counts don't match source data counts, duplicate key violations

### Pitfall 3: Transaction Isolation Failures
**What goes wrong:** Partial migrations leave database in inconsistent state (some tables migrated, others not)
**Why it happens:** Each migration command runs in separate transaction, no overall coordination
**How to avoid:** Wrap entire migration workflow in `@atomic` decorator at orchestration level
**Warning signs:** Database has krstenja but no related svestenici or hramovi

### Pitfall 4: Memory Exhaustion on Large Datasets
**What goes wrong:** Loading all records into memory before processing causes OOM on large DBF files
**Why it happens:** `list(self._fetch_records())` in `migracija_krstenja.py:99` loads entire table
**How to avoid:** Use generators and process in batches (already done with `BATCH_SIZE` in some commands)
**Warning signs:** Process killed by OS, slow startup before processing begins

### Pitfall 5: Missing Foreign Key Data
**What goes wrong:** Creating Krstenje before migrating Svestenik causes ForeignKey constraint violation
**Why it happens:** Migration order matters - some models reference others
**How to avoid:** Document and enforce migration order (already documented in MIGRACIJA.md lines 56-69)
**Warning signs:** IntegrityError exceptions about missing referenced row

### Pitfall 6: Silent Data Loss in Conversion
**What goes wrong:** `Konvertor.string()` strips whitespace, `Konvertor.int()` returns default on error (lines 8-14 convert_utils.py)
**Why it happens:** Defensive programming that swallows errors
**How to avoid:** Log all conversion warnings, add validation mode that fails loudly
**Warning signs:** Imported records have missing or default values that were present in source

## Code Examples

Verified patterns from official sources and existing codebase:

### Orchestrating Multiple Commands
```python
# Source: Django documentation - management/commands best practices
from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Call existing commands programmatically
        call_command('load_dbf', src_zip='/path/to/crkva.zip', verbosity=options['verbosity'])
        call_command('migracija_krstenja', verbosity=options['verbosity'])
        call_command('migracija_vencanja', verbosity=options['verbosity'])
```

### Temporary File Handling for ZIP Extraction
```python
# Source: crkva/registar/management/commands/load_dbf.py:109-120
import tempfile
import zipfile

with zipfile.ZipFile(src_zip) as zf:
    with zf.open(archive_name) as dbf_file:
        with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
            tmp.write(dbf_file.read())
            tmp_path = Path(tmp.name)

        try:
            count = self._load_dbf_file(tmp_path, table_name)
        finally:
            tmp_path.unlink(missing_ok=True)
```

### Progress Reporting with Summary
```python
# Pattern from Django admin actions - accumulate results and display summary
def handle(self, *args, **options):
    results = {
        'krstenja': {'created': 0, 'skipped': 0, 'errors': []},
        'vencanja': {'created': 0, 'skipped': 0, 'errors': []},
    }

    results['krstenja'] = self.migrate_krstenja(dry_run=options['dry_run'])
    results['vencanja'] = self.migrate_vencanja(dry_run=options['dry_run'])

    # Summary report
    self.stdout.write(self.style.SUCCESS('\n=== MIGRATION SUMMARY ==='))
    for entity, stats in results.items():
        self.stdout.write(f"{entity}: {stats['created']} created, {stats['skipped']} skipped")
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"  Errors: {len(stats['errors'])}"))
```

### Dry-Run with Validation
```python
# Source: Django best practices for data migrations
from django.core.exceptions import ValidationError

def migrate_entity(self, records, dry_run=False):
    for record in records:
        try:
            obj = Krstenje(**record)
            obj.full_clean()  # Validate without saving

            if not dry_run:
                obj.save()
        except ValidationError as e:
            self.log_error(f"Validation failed: {e}")
```

### Batch Processing with Cache
```python
# Source: crkva/registar/management/commands/migracija_vencanja.py:194-196
# Cache foreign key lookups to avoid N+1 queries
svestenici = {s.uid: s for s in Svestenik.objects.all()}
hramovi = {}

for record in records:
    svestenik = svestenici.get(record.svestenik_id)
    hram = self._get_or_create_hram(record.hram_naziv, hramovi)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate shell script orchestration | Django call_command() | Django 1.0+ (2008) | Better testability, error handling |
| Manual transaction management | @atomic decorator | Django 1.6 (2013) | Automatic rollback on exceptions |
| print() statements | self.stdout.write() | Django management command best practice | Respects --verbosity flag |
| load_dbf requires directory | Supports ZIP archives | Recent (2024) per codebase | Simpler deployment workflow |
| Individual migrations only | Need unified orchestration | Not yet implemented | Gap to fill in Phase 1 |

**Deprecated/outdated:**
- **Django 5.1.2 in current environment:** requirements.txt shows `django~=6.0.1` but environment shows Django 5.1.2 installed (output from pip list) - needs upgrade or version mismatch
- **psycopg2-binary in production:** Should use `psycopg2` (not binary) for production per best practices

## Open Questions

1. **Dummy Data Source**
   - What we know: Current workflow uses `unos_krstenja` and `unos_vencanja` commands to generate random data
   - What's unclear: Should `--dummy` flag call these commands, or create fixture files?
   - Recommendation: Call existing `unos_*` commands for now, consider fixture files in future phase

2. **Staging Table Persistence**
   - What we know: Migration commands drop staging tables after successful migration (line 107 in `migracija_parohijana.py`)
   - What's unclear: Should `--dry-run` mode preserve staging tables for inspection?
   - Recommendation: Add `--keep-staging` flag to preserve tables for debugging

3. **Rollback Strategy**
   - What we know: `@atomic` decorator handles transaction rollback on exception
   - What's unclear: How to rollback after successful migration if user discovers data issues?
   - Recommendation: Document backup/restore procedure, consider adding `--backup` flag that creates database dump before migration

4. **Migration Order Dependencies**
   - What we know: Order matters (unosi → unos_meseci → unos_drzava → migracija_slava → etc.)
   - What's unclear: Should dependencies be explicitly declared or just documented?
   - Recommendation: Document in help text and MIGRACIJA.md, add dependency check at runtime

5. **crkva.zip Location**
   - What we know: ZIP file exists at `/Users/milan.jelisavcic/Projects/spc-registar/crkva.zip` (747934 bytes)
   - What's unclear: Should path be hardcoded, environment variable, or always require `--real <path>` argument?
   - Recommendation: Default to `./crkva.zip` in project root, allow override with argument

## Sources

### Primary (HIGH confidence)
- **Django 6.0 Documentation** - Management commands: https://docs.djangoproject.com/en/6.0/howto/custom-management-commands/
- **Existing Codebase** - `crkva/registar/management/commands/`:
  - `load_dbf.py` (198 lines) - DBF loading with ZIP support
  - `base_migration.py` (143 lines) - Base class with common migration logic
  - `convert_utils.py` (95 lines) - Konvertor class for Latin→Cyrillic
  - `migracija_krstenja.py` (391 lines) - Complex migration with person relationships
  - `migracija_vencanja.py` (372 lines) - Uses bulk_create and caching pattern
- **docs/MIGRACIJA.md** - Current migration documentation (171 lines)
- **requirements.txt** - Confirmed versions: Django 6.0.1, dbfread 2.0.7

### Secondary (MEDIUM confidence)
- **dbfread documentation** - https://dbfread.readthedocs.io/ - Verified DBF encoding handling
- **tqdm documentation** - https://tqdm.github.io/ - Progress bar library, widely used in Django projects

### Tertiary (LOW confidence)
- None - all research based on official docs and codebase analysis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, versions confirmed in requirements.txt and working code
- Architecture: HIGH - Based on existing working patterns in codebase, Django official best practices
- Pitfalls: HIGH - Observed in existing code comments, CONCERNS.md analysis, and common Django migration issues

**Research date:** 2026-02-11
**Valid until:** 2026-04-11 (60 days - stable Django ecosystem, no fast-moving dependencies)
