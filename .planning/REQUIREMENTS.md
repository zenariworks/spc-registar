# Requirements

**Project:** СПЦ Регистар (Serbian Orthodox Church Registry)
**Phase:** Enhancement - Brownfield Improvements
**Priority:** Data Migration Workflow (REQ-001)
**Date:** 2026-02-11

---

## REQ-001: Data Migration Workflow Improvement

**Priority:** P0 (Critical)
**Status:** Active
**Dependencies:** None

### Description
Simplify the data migration workflow from legacy HramSP system (DBF files) to enable easier development cycles and production deployment. Currently requires multiple manual commands and lacks clear separation between dummy development data and real production data.

### Acceptance Criteria
- [ ] Single command to migrate dummy data for development
- [ ] Single command to migrate real data from crkva.zip for production
- [ ] Clear documentation of which command to use when
- [ ] Ability to switch between dummy and real data without manual cleanup
- [ ] Validation step before importing data
- [ ] Rollback capability if migration fails

### Sub-Requirements

#### REQ-001.1: Dummy/Real Data Toggle
**Description:** Implement command-line flag to switch between dummy data generation and real data import
**Acceptance Criteria:**
- [ ] `manage.py migrate_data --dummy` generates test data
- [ ] `manage.py migrate_data --real` imports from crkva.zip
- [ ] Command validates data source before proceeding
- [ ] Clear error messages if crkva.zip is missing
- [ ] Dry-run mode available with `--dry-run` flag

#### REQ-001.2: crkva.zip Import Support
**Description:** Support importing real production data from crkva.zip archive
**Acceptance Criteria:**
- [ ] Accepts path to crkva.zip as command argument
- [ ] Extracts DBF files from ZIP to temporary directory
- [ ] Validates DBF file structure before migration
- [ ] Cleans up temporary files after migration
- [ ] Logs all imported records for audit trail

#### REQ-001.3: Migration Script Consolidation
**Description:** Consolidate separate migration commands into unified workflow
**Acceptance Criteria:**
- [ ] Single entry point replaces `load_dbf`, `migracija_krstenja`, `migracija_vencanja`, `migracija_parohijana`
- [ ] Maintains backward compatibility with existing commands
- [ ] Progress indicators for each migration step
- [ ] Summary report at end showing records imported

### Technical Context
- **Current Pain Points:** (from [CONCERNS.md](CONCERNS.md))
  - `migracija_krstenja.py` is 475 lines - complex and fragile
  - `migracija_vencanja.py` is 391 lines
  - No separation between dummy data (for development) and real data (crkva.zip)
  - Migration workflow requires multiple manual commands

- **Existing Implementation:**
  - `crkva/registar/management/commands/load_dbf.py` - loads DBF to staging tables
  - `crkva/registar/management/commands/migracija_krstenja.py` - baptism migration
  - `crkva/registar/management/commands/migracija_vencanja.py` - wedding migration
  - `crkva/registar/management/commands/unos_krstenja.py` - dummy baptism data
  - `crkva/registar/management/commands/unos_vencanja.py` - dummy wedding data

### Design Considerations
- Extract conversion logic from Django commands to separate utilities (see CONCERNS.md suggestion)
- Implement `Konvertor` test suite for data transformation logic
- Add comprehensive data validation before database saves
- Consider using Django fixtures for dummy data instead of management commands

---

## REQ-002: Slava Celebration Page

**Priority:** P1 (High)
**Status:** Active
**Dependencies:** None

### Description
Create a dedicated page for priests to view upcoming slava celebrations with calendar view, showing which parishioners (parohijani) are celebrating, their addresses for pastoral visits, and whether they need holy water (vodica).

### Acceptance Criteria
- [ ] Calendar view showing slava dates for current month
- [ ] Clickable dates to see details for that day
- [ ] List of celebrating households with names and addresses
- [ ] Indicator showing if household needs vodica
- [ ] Print-friendly view for visit planning
- [ ] Mobile-responsive layout

### Sub-Requirements

#### REQ-002.1: Calendar View Implementation
**Description:** Interactive calendar showing slava celebration dates
**Acceptance Criteria:**
- [ ] Monthly calendar grid with Orthodox dates
- [ ] Slava names displayed on relevant dates
- [ ] Visual distinction between fixed and moveable slavas
- [ ] Navigation between months (prev/next)
- [ ] Current date highlighted
- [ ] Dates with multiple slavas show count indicator

#### REQ-002.2: Visit Planner
**Description:** Detailed view showing households celebrating on selected date
**Acceptance Criteria:**
- [ ] Household name (презиме породице)
- [ ] Full address from Adresa model
- [ ] Contact phone number if available
- [ ] Slava name being celebrated
- [ ] Vodica requirement indicator (да/не)
- [ ] Sortable by address for efficient route planning
- [ ] Export to PDF for printing

#### REQ-002.3: Vodica Needs Tracking
**Description:** Track and display holy water requirements for each household
**Acceptance Criteria:**
- [ ] Boolean field on Parohijan or Slava model for vodica needs
- [ ] Admin interface to update vodica requirements
- [ ] Summary count of vodica bottles needed for the month
- [ ] Visual indicator (icon) on calendar and detail views

### Technical Context
- **Existing Models:**
  - `Slava` model with `pokretni` (moveable) flag and date calculation
  - `Parohijan` model linked to `Slava` via foreign key
  - `Adresa` model with street, number, postal code

- **Existing Views:**
  - Home page (`index()` in `crkva/registar/views/__init__.py`) shows 7-day calendar
  - Template at `crkva/registar/templates/registar/index.html`

- **Orthodox Calendar Integration:**
  - `utils_fasting.py` contains date calculation logic
  - Moveable slavas calculated relative to Vaskrs (Easter)
  - Gauss algorithm for Easter date calculation

### Design Considerations
- Extend existing home page or create separate `/slava/mesec/<YYYY-MM>` route?
- Use existing calendar logic from `index()` view as foundation
- Consider using Django template tags for calendar rendering
- Mobile-first responsive design for tablet use during visits

---

## REQ-003: Serbian Cyrillic Documentation

**Priority:** P1 (High)
**Status:** Active
**Dependencies:** None

### Description
Create comprehensive documentation in Serbian Cyrillic for installation, user guide, and data migration procedures. Current README.md is in Cyrillic but lacks depth.

### Acceptance Criteria
- [ ] Installation guide (INSTALACIJA.md) in Serbian Cyrillic
- [ ] User guide (UPUTSTVO.md) for priests and assistants
- [ ] Enhanced data migration guide (docs/MIGRACIJA.md) in Cyrillic
- [ ] Troubleshooting section for common issues
- [ ] Screenshots and examples where helpful
- [ ] All documentation accessible from README.md

### Sub-Requirements

#### REQ-003.1: Installation Guide
**Description:** Step-by-step setup instructions
**Acceptance Criteria:**
- [ ] Prerequisites (Docker, Docker Compose)
- [ ] Environment setup (.env configuration)
- [ ] First-time database initialization
- [ ] Creating superuser account
- [ ] Accessing admin interface
- [ ] Production deployment considerations

#### REQ-003.2: User Guide
**Description:** Operational guide for daily use
**Acceptance Criteria:**
- [ ] How to search for parishioners
- [ ] Adding baptism records (крштења)
- [ ] Adding wedding records (венчања)
- [ ] Printing certificates (крштенице, венчанице)
- [ ] Managing slava records
- [ ] Using the calendar view
- [ ] Backing up data

#### REQ-003.3: Data Migration Guide Enhancement
**Description:** Detailed migration procedures
**Acceptance Criteria:**
- [ ] Translate existing docs/MIGRACIJA.md to Cyrillic
- [ ] Add troubleshooting section
- [ ] Document crkva.zip import workflow (once REQ-001.2 implemented)
- [ ] Include data validation steps
- [ ] Add rollback procedures

### Technical Context
- **Existing Documentation:**
  - README.md (Serbian Cyrillic, comprehensive)
  - docs/MIGRACIJA.md (Serbian Cyrillic, focused on migration)
  - CONTRIBUTING.md (referenced but needs enhancement)

### Design Considerations
- Keep README.md as main entry point with links to detailed guides
- Use consistent terminology matching the codebase (парохијани, крштења, венчања)
- Include code examples with actual commands
- Consider adding video tutorials for common workflows

---

## REQ-004: Reusable HTML Components

**Priority:** P2 (Medium)
**Status:** Active
**Dependencies:** None

### Description
Refactor Django templates to use reusable components, reducing HTML duplication and improving maintainability. Current templates have significant duplication.

### Acceptance Criteria
- [ ] Component library created in `registar/templates/components/`
- [ ] Common UI patterns extracted (forms, tables, buttons, navigation)
- [ ] All templates refactored to use components
- [ ] Documentation for component usage
- [ ] No visual regressions in existing pages

### Sub-Requirements

#### REQ-004.1: Component Library Creation
**Description:** Create reusable Django template components
**Acceptance Criteria:**
- [ ] Form field component with error handling
- [ ] Table component with sorting and pagination
- [ ] Button components (primary, secondary, danger)
- [ ] Navigation/menu component
- [ ] Card/panel component for content grouping
- [ ] Alert/message component
- [ ] Modal dialog component

#### REQ-004.2: Template Refactoring
**Description:** Update existing templates to use components
**Acceptance Criteria:**
- [ ] Identify duplicate HTML patterns across templates
- [ ] Replace with `{% include "components/..." %}` tags
- [ ] Pass data via template context variables
- [ ] Maintain existing CSS class names for styling
- [ ] Test all pages for visual consistency

### Technical Context
- **Current Template Structure:** (from [STRUCTURE.md](STRUCTURE.md))
  - Templates in `crkva/registar/templates/registar/`
  - Bootstrap-based styling
  - Base template with blocks for content

- **Django Template Features to Use:**
  - `{% include %}` for component inclusion
  - Template tags for complex logic
  - Template inheritance for layout structure

### Design Considerations
- Use Django inclusion tags for components with logic
- Consider adding Tailwind CSS or Alpine.js for modern component patterns
- Maintain backward compatibility with existing custom CSS
- Document component API (required/optional parameters)

---

## REQ-005: Login Management

**Priority:** P3 (Lower)
**Status:** Backlog
**Dependencies:** None

### Description
Implement user authentication and role-based access control to differentiate between priests (full access) and assistants (limited access). Currently no authentication layer.

### Acceptance Criteria
- [ ] User login/logout functionality
- [ ] Session management
- [ ] Role-based permissions (priest, assistant)
- [ ] Admin can manage user accounts
- [ ] Password reset functionality
- [ ] Audit log of user actions

### Sub-Requirements

#### REQ-005.1: User Authentication
**Description:** Basic login/logout with Django auth
**Acceptance Criteria:**
- [ ] Login page with username/password
- [ ] Session-based authentication
- [ ] Logout functionality
- [ ] "Remember me" option
- [ ] Account lockout after failed attempts
- [ ] Password strength requirements

#### REQ-005.2: Role-Based Access Control
**Description:** Differentiate access levels
**Acceptance Criteria:**
- [ ] Priest role: full access to all records
- [ ] Assistant role: limited to data entry, no deletion
- [ ] Role assignment via Django admin
- [ ] Permission checks on views and templates
- [ ] Graceful handling of unauthorized access

### Technical Context
- **Django Auth Framework:**
  - Built-in `django.contrib.auth`
  - User, Group, Permission models available
  - Login/logout views provided

- **Current State:**
  - No authentication layer (admin interface uses Django default)
  - All views are publicly accessible

### Design Considerations
- Use Django's built-in authentication system
- Consider django-guardian for object-level permissions
- Add middleware to require authentication on all views except login
- Implement audit logging with django-auditlog
- Design permissions model: should assistants see all parishioners or only their assigned ones?

---

## Cross-Cutting Concerns

### Code Quality
- **Constraint:** Python 3.12+ Pythonic code style
  - Use type hints for all function signatures
  - Use dataclasses where appropriate
  - Follow PEP 8 naming conventions
  - Modern Python syntax (match/case, walrus operator where clear)

### Performance
- **From [CONCERNS.md](CONCERNS.md):**
  - Add `.select_related()` and `.prefetch_related()` to avoid N+1 queries
  - Index search fields in database migrations
  - Cache calendar calculations (fasting types, moveable dates)

### Security
- **From [CONCERNS.md](CONCERNS.md):**
  - Change `ALLOWED_HOSTS = ["*"]` to environment-based list
  - Rotate `SECRET_KEY` and remove from git history
  - Add pre-commit hook to prevent env file commits
  - Implement rate limiting on admin login (when REQ-005 implemented)

### Testing
- **From [TESTING.md](TESTING.md):**
  - Current test coverage is minimal (placeholder test exists)
  - Add unit tests for data conversion logic (Konvertor class)
  - Add integration tests for migration commands
  - Add view tests for calendar and PDF generation
  - Property-based testing for Orthodox calendar calculations

---

## Out of Scope

The following are explicitly NOT in scope for this phase:

- Standalone distribution packaging (deferred until features mature)
- Mobile app (web-first approach sufficient)
- Audit logging (can add later if governance requires)
- Automated backups (handled at infrastructure level)
- Real-time notifications (not needed for current workflow)
- Multi-parish federation (single parish deployment only)
- REST API (Django admin and templates sufficient for now)

---

*Requirements defined: 2026-02-11*
