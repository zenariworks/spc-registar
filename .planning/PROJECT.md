# СПЦ Регистар (Serbian Orthodox Church Registry)

## What This Is

A Django-based church registry system for Serbian Orthodox parishes to manage sacramental records (baptisms, weddings), parishioner information, clergy data, and Orthodox liturgical calendar. Used by priests and parish assistants to maintain historical church records and plan pastoral visits.

## Core Value

Church records must be accurate, accessible, and preserved. If everything else fails, the ability to retrieve and print sacramental certificates (крштенице, венчанице) must work.

## Requirements

### Validated

<!-- Shipped and confirmed valuable — existing functionality -->

- ✓ Parishioner management (парохијани) with addresses and contact info — existing
- ✓ Baptism records (крштења) with certificate printing — existing
- ✓ Wedding records (венчања) with certificate printing — existing
- ✓ Clergy management (свештеници) with parish assignments — existing
- ✓ Slava tracking (славе) linked to households — existing
- ✓ Orthodox calendar with fixed and moveable feast days — existing
- ✓ Fasting rules calculation (пост) for Orthodox calendar — existing
- ✓ Admin interface with CRUD operations for all entities — existing
- ✓ Import/export functionality via django-import-export — existing
- ✓ Latin-to-Cyrillic transliteration in search — existing
- ✓ Print baptism certificates (крштенице) — existing
- ✓ Print wedding certificates (венчанице) — existing
- ✓ Data migration from legacy HramSP database (DBF files) — existing
- ✓ Docker deployment with PostgreSQL 16 — existing

### Active

<!-- Current scope — building toward these -->

- [ ] Simplified data migration workflow with dummy/real data toggle
- [ ] Support crkva.zip import for real production data
- [ ] Slava celebration page with calendar view (clickable dates)
- [ ] Slava visit planner showing addresses and vodica needs
- [ ] Serbian Cyrillic documentation (installation, user guide, data migration)
- [ ] Reusable HTML template components to reduce duplication
- [ ] Login management with user authentication (lower priority)
- [ ] Role-based access control for priests vs assistants (lower priority)

### Out of Scope

- Standalone distribution packaging — deferred until features mature
- Mobile app — web-first approach sufficient for now
- Audit logging — can add later if governance requires it
- Automated backups — handled at infrastructure level initially
- Real-time notifications — not needed for current workflow
- Multi-parish federation — single parish deployment only

## Context

**Technical Environment:**
- Migrated from legacy HramSP system (DBF database files)
- Python 3.12 + Django 6.0.1 + PostgreSQL 16
- Docker Compose deployment
- Currently runs on Docker locally, needs better data seeding workflow

**Users:**
- Primary: Parish priests (full access to all records)
- Secondary: Parish assistants (data entry, limited access)

**Known Issues:**
- Heavy migration command complexity (475-line scripts, hard to maintain)
- N+1 query problems in list views (needs select_related optimization)
- Migration workflow requires multiple manual commands
- Time zone mismatch (Europe/Amsterdam instead of Europe/Belgrade)
- No clear separation between dummy data (for development) and real data (crkva.zip)

**Domain Expertise:**
- Orthodox Christian liturgical calendar calculations (moveable feasts)
- Gauss algorithm for Easter date calculation
- Serbian Orthodox sacramental record keeping practices
- Cyrillic and Latin script transliteration

## Constraints

- **Tech Stack**: Django 6.0+ with PostgreSQL 16+ (no SQLite, no MySQL)
- **Language**: Serbian language with Cyrillic script primary, Latin transliteration for search
- **Code Style**: Pythonic Python 3.12+ code (type hints, dataclasses, modern syntax)
- **Data Integrity**: Historical sacramental records are immutable once created
- **Performance**: Must handle 10,000+ parishioner records with responsive search
- **Deployment**: Docker Compose for local development, future production hosting TBD

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Upgrade to Django 6.0 + Python 3.12 + PostgreSQL 16 | Modern Django requires Python 3.12+, PostgreSQL 16 for Django 6.0 compatibility | ✓ Good — completed during setup |
| Rebase feature/final onto main after bc7a47c | Clean git history, eliminate duplicate commits from parallel development | ✓ Good — 33 commits rebased successfully |
| Prioritize data migration workflow over other features | Critical for development cycle and final delivery | — Pending |
| Calendar view for slava celebration page | Most intuitive UX for priests planning visits | — Pending |
| Defer standalone distribution | Focus on core features first | — Pending |

---
*Last updated: 2026-02-11 after initialization*
