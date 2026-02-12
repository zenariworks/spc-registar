---
phase: 01-data-migration-workflow-simplification
plan: 01
subsystem: database
tags: [migration, data-conversion, dbf, cyrillic, tdd]

# Dependency graph
requires:
  - phase: none
    provides: Initial codebase with existing convert_utils.py and migration commands
provides:
  - Konvertor class in registar.utils.migration_converters with 4 static methods
  - Comprehensive test suite with 32 test cases covering all conversion methods
  - Latin-to-Cyrillic conversion with legacy HramSP encoding support
  - Safe integer conversion with default values
  - Date parsing with zero-component handling
  - Cyrillic name splitting for space-separated and CamelCase names
affects: [01-02, 01-03, migration-commands, data-import]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD workflow, static utility classes, SimpleTestCase for database-free tests]

key-files:
  created:
    - crkva/registar/utils/migration_converters.py
    - crkva/registar/tests/test_migration_converters.py
  modified:
    - crkva/registar/utils/__init__.py

key-decisions:
  - "Used SimpleTestCase instead of TestCase to avoid database dependency for pure utility tests"
  - "Matched original convert_utils.py behavior for single-character mapping (no digraph support for compatibility)"
  - "Moved existing utils.py content into utils/__init__.py to create proper package structure"

patterns-established:
  - "TDD workflow: RED (failing tests) → GREEN (implementation) → commit per phase"
  - "Static utility classes for stateless conversion functions"
  - "Comprehensive test coverage including edge cases (empty, None, zero values)"

# Metrics
duration: 4min
completed: 2026-02-12
---

# Phase 01 Plan 01: Extract Konvertor Utility Class Summary

**Centralized migration converter utilities with Latin-to-Cyrillic conversion, safe integer/date parsing, and 32-test TDD suite**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-12T15:09:37Z
- **Completed:** 2026-02-12T15:13:35Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extracted Konvertor class from convert_utils.py into proper utils module
- Added date() method for handling DBF zero-component dates (0,0,0 → 1900-01-01)
- Added split_name() method for Cyrillic name parsing (space-separated and CamelCase)
- Created comprehensive test suite with 32 tests covering all methods and edge cases
- Achieved 100% test pass rate using TDD methodology

## Task Commits

Each task was committed atomically following TDD workflow:

1. **Task 1: Create utils module and write failing tests** - `47d7a19` (test)
   - RED phase: 32 failing tests, module doesn't exist yet

2. **Task 2: Implement Konvertor class and pass all tests** - `0083d19` (feat)
   - GREEN phase: All 32 tests passing

## Files Created/Modified
- `crkva/registar/utils/__init__.py` - Created package init, moved existing utils.py functions for backward compatibility
- `crkva/registar/utils/migration_converters.py` - New Konvertor class with string(), int(), date(), split_name() static methods
- `crkva/registar/tests/test_migration_converters.py` - Comprehensive test suite with 32 test cases

## Decisions Made

**1. Used SimpleTestCase for database-free testing**
- Original test used TestCase which requires database connection
- Switched to SimpleTestCase since Konvertor tests are pure utility functions
- Result: Tests run instantly without database dependency

**2. Preserved single-character mapping behavior**
- Original convert_utils.py maps characters individually (l→л, j→ј)
- Does not handle Serbian Latin digraphs (lj→љ requires separate logic)
- Kept this behavior for compatibility with existing migration data
- Note: Modern utils.py has digraph support, but migration code uses legacy format

**3. Created utils/ package structure**
- Existing utils.py file conflicted with creating utils/ directory
- Moved utils.py content into utils/__init__.py to maintain backward compatibility
- All existing imports from registar.utils continue to work

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Resolved utils.py vs utils/ directory conflict**
- **Found during:** Task 1 (Test execution)
- **Issue:** Creating utils/__init__.py caused ImportError because Python prioritizes utils/ directory over utils.py, but views were importing from utils.py
- **Fix:** Moved all content from utils.py into utils/__init__.py to maintain backward compatibility
- **Files modified:** crkva/registar/utils/__init__.py
- **Verification:** Existing imports work, views load without errors
- **Committed in:** 47d7a19 (Task 1 commit)

**2. [Rule 1 - Bug] Changed TestCase to SimpleTestCase**
- **Found during:** Task 2 (Test execution)
- **Issue:** Tests failing with database connection error (host "db" unreachable)
- **Fix:** Changed base class from TestCase to SimpleTestCase since utility tests don't need database
- **Files modified:** crkva/registar/tests/test_migration_converters.py
- **Verification:** All 32 tests pass without database
- **Committed in:** 0083d19 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were necessary for tests to run. No scope creep - all planned functionality delivered.

## Issues Encountered

None - TDD workflow proceeded smoothly with RED → GREEN phases completing as expected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 01 Plan 02** (Unified migrate_data command):
- Konvertor class fully tested and importable
- All 4 methods (string, int, date, split_name) ready for use
- Can be imported as: `from registar.utils.migration_converters import Konvertor`
- Replaces scattered conversion logic across 8 migration files

**Verification commands:**
```python
from registar.utils.migration_converters import Konvertor
Konvertor.string("Beograd")  # → "Београд"
Konvertor.date(0, 0, 0)      # → date(1900, 1, 1)
```

---
*Phase: 01-data-migration-workflow-simplification*
*Completed: 2026-02-12*

## Self-Check: PASSED

All claims verified:
- ✓ Created files exist: migration_converters.py, test_migration_converters.py
- ✓ Modified files exist: utils/__init__.py
- ✓ Commits exist: 47d7a19 (Task 1), 0083d19 (Task 2)
- ✓ All 32 tests pass
- ✓ Module successfully importable

Self-check executed: 2026-02-12T15:13:35Z
