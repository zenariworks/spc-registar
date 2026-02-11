# Roadmap

**Project:** СПЦ Регистар - Brownfield Improvements
**Milestone:** v1.0 Enhancement Delivery
**Start Date:** 2026-02-11
**Target Completion:** TBD

---

## Milestone Overview

This milestone focuses on improving the developer experience and user workflows for the Serbian Orthodox Church Registry system. Priority is on simplifying data migration (critical for development and final delivery), adding useful features for priests' pastoral work, and improving maintainability.

### Success Criteria
- [ ] Data migration reduced from multiple manual steps to single command
- [ ] crkva.zip can be imported seamlessly for production deployment
- [ ] Priests can efficiently plan slava visits using calendar view
- [ ] Comprehensive Serbian Cyrillic documentation enables independent setup
- [ ] Template duplication reduced by 50%+ through component reuse
- [ ] User authentication foundation in place for future multi-user deployment

---

## Phase Breakdown

### Phase 1: Data Migration Workflow Simplification
**REQ Coverage:** REQ-001 (all sub-requirements)
**Priority:** P0 (Critical)
**Estimated Effort:** 3-5 days
**Status:** Planned

#### Goal
Consolidate complex, multi-step data migration process into a single unified command that supports both dummy development data and real production data from crkva.zip.

#### Deliverables
1. `manage.py migrate_data` command with `--dummy` and `--real` flags
2. Automatic crkva.zip extraction and validation
3. Dry-run mode for safe testing
4. Consolidated migration logic from separate commands
5. Progress indicators and summary reporting
6. Updated MIGRACIJA.md documentation

#### Tasks
- [ ] Extract conversion logic from existing migration commands to `registar/utils/migration_converters.py`
- [ ] Create `Konvertor` utility class with data transformation methods
- [ ] Implement `manage.py migrate_data` command with argument parser
- [ ] Add ZIP archive extraction and temporary file handling
- [ ] Add DBF file structure validation
- [ ] Implement `--dry-run` mode that validates without saving
- [ ] Add progress bars for long-running migrations
- [ ] Generate summary report showing records imported/skipped
- [ ] Write unit tests for `Konvertor` class
- [ ] Write integration tests with sample DBF data
- [ ] Update docs/MIGRACIJA.md with new workflow

#### Success Metrics
- Single command replaces 4-5 manual steps
- crkva.zip import works without manual file extraction
- Dry-run mode catches data errors before database writes
- Migration time reduced by 40%+ through optimized queries
- 80%+ test coverage on conversion logic

#### Dependencies
- None (foundational phase)

#### Risks
- Existing migration commands must remain backward compatible
- DBF file format variations from different HramSP versions
- Large crkva.zip files may cause memory issues during extraction

---

### Phase 2: Slava Celebration Calendar Page
**REQ Coverage:** REQ-002 (all sub-requirements)
**Priority:** P1 (High)
**Estimated Effort:** 4-6 days
**Status:** Planned

#### Goal
Create an interactive calendar view showing upcoming slava celebrations with household details, addresses, and vodica requirements to help priests efficiently plan pastoral visits.

#### Deliverables
1. Monthly calendar view with slava dates highlighted
2. Detail page showing households celebrating on selected date
3. Vodica (holy water) requirement tracking
4. Print-friendly layout for visit planning
5. Mobile-responsive design for tablet use

#### Tasks
- [ ] Add `vodica_potrebna` BooleanField to Parohijan model
- [ ] Create migration for new field
- [ ] Create `/slava/mesec/<YYYY-MM>/` URL route
- [ ] Implement `SlavaMesecView` view class extending existing calendar logic
- [ ] Create `slava_calendar.html` template with monthly grid
- [ ] Add JavaScript for date selection and navigation
- [ ] Create `slava_detalji.html` template for household list
- [ ] Implement sorting by address for efficient routing
- [ ] Add print stylesheet for visit planning
- [ ] Update admin to allow vodica requirement editing
- [ ] Add icon indicators for vodica in templates
- [ ] Write view tests for calendar rendering
- [ ] Write integration tests for date filtering

#### Success Metrics
- Calendar displays all slavas (fixed and moveable) correctly
- Household addresses displayed in route-optimized order
- Print view fits on single page for typical day (5-10 households)
- Page loads in <500ms for typical month
- Mobile responsive on tablets (iPad/Android)

#### Dependencies
- Phase 1 (for test data generation)

#### Risks
- Performance with large number of slavas per day
- Complex Orthodox calendar calculations may have edge cases
- Mobile UX for priests accustomed to paper lists

---

### Phase 3: Serbian Cyrillic Documentation
**REQ Coverage:** REQ-003 (all sub-requirements)
**Priority:** P1 (High)
**Estimated Effort:** 2-3 days
**Status:** Planned

#### Goal
Create comprehensive documentation in Serbian Cyrillic covering installation, daily usage, and data migration to enable independent setup and operation by parish staff.

#### Deliverables
1. `docs/INSTALACIJA.md` - Setup and deployment guide
2. `docs/UPUTSTVO.md` - User guide for daily operations
3. Enhanced `docs/MIGRACIJA.md` - Migration procedures
4. Updated `README.md` with links to all documentation

#### Tasks
- [ ] Write INSTALACIJA.md covering Docker setup, .env configuration, first-time initialization
- [ ] Add production deployment section with security considerations
- [ ] Write UPUTSTVO.md covering parishioner search, adding records, printing certificates
- [ ] Document slava calendar usage (from Phase 2)
- [ ] Add troubleshooting section for common Docker issues
- [ ] Enhance MIGRACIJA.md with crkva.zip workflow (from Phase 1)
- [ ] Add data validation and rollback procedures
- [ ] Include screenshots for key workflows
- [ ] Add backup/restore procedures
- [ ] Update README.md with documentation links
- [ ] Review with Serbian language native speaker for clarity

#### Success Metrics
- Non-technical parish staff can follow installation guide successfully
- User guide covers 90%+ of daily tasks
- Troubleshooting section addresses common Docker/database issues
- Documentation follows consistent Serbian Cyrillic terminology

#### Dependencies
- Phase 1 (for updated migration documentation)
- Phase 2 (for slava calendar documentation)

#### Risks
- Technical terminology translation may lose precision
- Screenshots need updating when UI changes
- Maintaining documentation in sync with code changes

---

### Phase 4: Reusable HTML Components
**REQ Coverage:** REQ-004 (all sub-requirements)
**Priority:** P2 (Medium)
**Estimated Effort:** 3-4 days
**Status:** Planned

#### Goal
Refactor Django templates to extract common UI patterns into reusable components, reducing duplication and improving maintainability.

#### Deliverables
1. Component library in `registar/templates/components/`
2. Refactored templates using components via `{% include %}`
3. Component usage documentation
4. No visual regressions on existing pages

#### Tasks
- [ ] Audit existing templates for duplication patterns
- [ ] Create `components/` directory structure
- [ ] Implement form field component with error handling
- [ ] Implement table component with sorting/pagination
- [ ] Implement button components (primary/secondary/danger)
- [ ] Implement card/panel component
- [ ] Implement navigation component
- [ ] Implement alert/message component
- [ ] Refactor baptism templates to use components
- [ ] Refactor wedding templates to use components
- [ ] Refactor parishioner templates to use components
- [ ] Refactor calendar templates to use components
- [ ] Create `docs/KOMPONENTE.md` documenting component API
- [ ] Write template rendering tests
- [ ] Perform visual regression testing on all pages

#### Success Metrics
- HTML line count reduced by 30%+ through component reuse
- No visual differences in before/after screenshots
- Component usage documented with examples
- All existing pages render correctly with components

#### Dependencies
- Phase 2 (to avoid refactoring calendar templates twice)

#### Risks
- Component abstraction may reduce template readability
- Over-engineering components for one-off use cases
- Maintaining component API stability as needs evolve

---

### Phase 5: Login Management and Role-Based Access
**REQ Coverage:** REQ-005 (all sub-requirements)
**Priority:** P3 (Lower)
**Estimated Effort:** 4-5 days
**Status:** Backlog

#### Goal
Implement user authentication and differentiate access levels between priests (full access) and assistants (limited access) to support multi-user parish deployments.

#### Deliverables
1. Login/logout functionality
2. Role-based permissions (priest vs assistant)
3. User management in admin interface
4. Password reset functionality
5. Audit logging of user actions

#### Tasks
- [ ] Enable Django authentication middleware
- [ ] Create login/logout views and templates
- [ ] Design permission model (priest vs assistant roles)
- [ ] Create Django groups for each role
- [ ] Add permission decorators to views
- [ ] Implement object-level permissions for sensitive actions
- [ ] Add user management to admin interface
- [ ] Implement password reset via email
- [ ] Add django-auditlog for action tracking
- [ ] Create audit log viewing interface
- [ ] Add account lockout after failed login attempts
- [ ] Write authentication flow tests
- [ ] Write permission enforcement tests
- [ ] Update documentation with user management procedures

#### Success Metrics
- All views require authentication except login page
- Priests have full CRUD access to all records
- Assistants can create/edit but not delete records
- Audit log captures all sensitive operations (create, update, delete)
- Failed login attempts lock account after 5 tries

#### Dependencies
- Phase 3 (for documentation updates)

#### Risks
- Permission model may need refinement after user feedback
- Audit logging may impact performance on high-volume operations
- Password reset requires email configuration (SMTP)

---

## Phase Dependencies Graph

```
Phase 1 (Data Migration)
   ↓
Phase 2 (Slava Calendar) ─────→ Phase 3 (Documentation)
   ↓                                  ↓
Phase 4 (HTML Components) ────────→ Phase 5 (Login Management)
```

**Critical Path:** Phase 1 → Phase 2 → Phase 3 → Phase 5

---

## Risk Management

### High Risk Items
1. **Data Migration Compatibility** (Phase 1)
   - Risk: crkva.zip format variations may break import
   - Mitigation: Extensive testing with multiple crkva.zip samples, comprehensive validation

2. **Orthodox Calendar Edge Cases** (Phase 2)
   - Risk: Moveable feast calculations may have bugs in edge cases
   - Mitigation: Property-based testing, verification against external authority

### Medium Risk Items
1. **Component Abstraction Balance** (Phase 4)
   - Risk: Over-abstraction reduces template readability
   - Mitigation: Keep components simple, document clearly, iterate based on usage

2. **Performance at Scale** (Phase 2, Phase 5)
   - Risk: Calendar queries and audit logging may slow down with 10,000+ records
   - Mitigation: Add database indexes, use select_related, implement query optimization

### Low Risk Items
1. **Documentation Maintenance** (Phase 3)
   - Risk: Documentation drifts out of sync with code
   - Mitigation: Review docs during code review, update as part of feature delivery

---

## Resource Allocation

### Development Priorities
1. **Phase 1:** Solo developer, focus on correctness and backward compatibility
2. **Phase 2:** Consider UX feedback from actual priests early
3. **Phase 3:** Native Serbian speaker for documentation review
4. **Phase 4:** Template refactoring can be done incrementally
5. **Phase 5:** Security review before deployment

### Testing Strategy
- **Unit Tests:** Focus on data conversion (Phase 1), calendar calculations (Phase 2)
- **Integration Tests:** End-to-end migration workflows (Phase 1), view rendering (Phase 2)
- **Visual Regression:** Before/after component refactoring (Phase 4)
- **Security Tests:** Authentication flows, permission enforcement (Phase 5)

---

## Success Criteria for Milestone v1.0

### Must Have (Required for Delivery)
- ✅ Phase 1 complete: Single-command data migration with crkva.zip support
- ✅ Phase 2 complete: Slava calendar page with vodica tracking
- ✅ Phase 3 complete: Serbian Cyrillic documentation suite

### Should Have (High Value, Include if Possible)
- ✅ Phase 4 complete: Component library reduces template duplication

### Nice to Have (Lower Priority, Deferrable)
- ⚠️ Phase 5 complete: Login management (can defer to v1.1 if needed)

### Quality Gates
- [ ] 80%+ test coverage on new code
- [ ] All existing features still work (no regressions)
- [ ] Documentation reviewed by Serbian speaker
- [ ] Performance benchmarks met (<500ms page loads)
- [ ] Security review passed (if Phase 5 included)

---

## Timeline Estimate

**Optimistic:** 16-23 days (3-4 weeks)
**Realistic:** 20-28 days (4-5 weeks)
**Pessimistic:** 30-40 days (6-8 weeks)

### Assumptions
- Single developer working full-time
- No major blockers or requirement changes
- Test data (crkva.zip samples) available
- Development environment already set up

---

*Roadmap created: 2026-02-11*
