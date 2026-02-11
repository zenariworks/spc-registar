# Testing Patterns

**Analysis Date:** 2026-02-11

## Test Framework

**Runner:**
- pytest (via `pytest` command)
- Configuration: `pytest.ini` at project root
- Django integration: DJANGO_SETTINGS_MODULE = djangodocker.settings.testing

**Assertion Library:**
- Django TestCase built-in assertions (not pytest assertions)

**Run Commands:**
```bash
pytest                        # Run all tests
pytest -v                     # Verbose output
pytest --cov                  # Coverage report
pytest -k test_name           # Run specific test
```

**Test Configuration (pytest.ini):**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = djangodocker.settings.testing

python_files = tests.py test_*.py *_tests.py
```

## Test File Organization

**Location:**
- Django TestCase pattern: tests co-located with app code
- Primary test file: `registar/tests.py` (single file)
- Test directory structure: `registar/tests/` directory exists but is empty (.gitkeep only)
- Structure suggests migration from tests.py to tests/ directory is incomplete

**Naming:**
- Main test file: `registar/tests.py`
- Pattern expects: `test_*.py` (e.g., `test_models.py`, `test_views.py`)
- Alternative pattern: `*_tests.py` (e.g., `models_tests.py`)

**Current Structure:**
```
registar/
├── tests.py               # Existing test file (minimal)
├── tests/                 # Empty directory (not yet migrated)
│   └── .gitkeep
├── models/
├── views/
├── forms/
└── admin/
```

## Test Structure

**Suite Organization:**
```python
from django.test import TestCase

from .models import Parohijan


class UnitTestCase(TestCase):
    def setUp(self):
        Parohijan.objects.create(uid=2023)

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        godina = Parohijan.objects.get(uid=2023)
        self.assertEqual(str(godina), 2023)
```

**Patterns:**
- Setup method: `setUp(self)` creates test data (Django standard)
- Teardown: No explicit teardown observed (Django TestCase handles database cleanup)
- Test method naming: `test_{feature_being_tested}(self)` starting with "test_"
- Docstring: Brief description of what test validates
- Assertion: `self.assertEqual()` (Django TestCase assertion)

## Mocking

**Framework:** Not configured/observed in codebase
- No unittest.mock imports detected
- No @patch decorators
- No mock fixtures

**Patterns:**
- Direct database creation in setUp using ORM: `Parohijan.objects.create(...)`
- No external API mocking (no API integrations in current code)
- No patching of system calls

**What to Mock:**
- External API calls (if added in future)
- File I/O operations (if added)
- Time-dependent functions (e.g., `dt.date.today()`)

**What NOT to Mock:**
- Django ORM operations (use TestCase database)
- Model methods (test actual behavior)
- Utility functions (use real implementation)

## Fixtures and Factories

**Test Data:**
No dedicated fixture framework (no pytest-factoryboy, no factory_boy).

Fixture pattern observed:
```python
def setUp(self):
    Parohijan.objects.create(
        uid=2023,
        ime="Јован",
        prezime="Јовановић"
    )
```

**Location:**
- Data creation happens inline in setUp methods
- Migrations provide initial data (e.g., `unos_slava.py`, `unos_eparhija.py` management commands)
- No separate fixtures directory

## Coverage

**Requirements:** Not specified in configuration
- No coverage.rc file
- No coverage thresholds enforced
- Current coverage: minimal (only 1 test file with 1 test case)

**View Coverage:**
```bash
pytest --cov=registar --cov-report=html    # Generate HTML coverage report
pytest --cov=registar --cov-report=term    # Terminal coverage report
```

## Test Types

**Unit Tests:**
- Scope: Test individual model methods and utility functions
- Approach: Direct instantiation and assertion
- Location: `registar/tests.py`
- Example: `test_animals_can_speak()` tests model string representation

**Integration Tests:**
- Scope: Not yet implemented
- Would test: Form validation, view responses, ORM queries
- Needed for: Form processing, view business logic, filter operations

**E2E Tests:**
- Framework: Not used
- Alternative: Django test client in views tests (not yet implemented)
- Could use: Playwright for browser automation if added

## Common Patterns

**Async Testing:**
- Not applicable (Django request/response is synchronous)
- Async support available in Django 4.1+ but not used

**Error Testing:**
No error-testing patterns observed.

**Recommended Pattern:**
```python
def test_invalid_parohijan_uid(self):
    """Test that invalid UIDs raise DoesNotExist"""
    with self.assertRaises(Parohijan.DoesNotExist):
        Parohijan.objects.get(uid=99999)
```

## Test Data Management

**Database:**
- TestCase provides transaction-wrapped database access
- Each test runs in a transaction rolled back after completion
- Initial data: populated via Django migrations + management command scripts
- Fixtures: None currently defined (could use Django fixtures or factory_boy)

## Missing Test Coverage

**Untested Areas:**
- View functions: `unos_parohijana()`, `SpisakParohijana`, `ParohijanPDF` - no tests
- Form validation: `ParohijanForm`, `VencanjeForm`, `KrstenjeForm` - no tests
- Filters: `KrstenjeFilter`, `VencanjeFilter` - no tests
- Template tags: `markiraj()`, `gregorian_to_julian()` - no tests
- Management commands: Migration commands, data import commands - no tests
- Model methods: `Slava.calc_vaskrs()`, `Slava.get_datum()` - no tests
- Utility functions: `latin_to_cyrillic()`, `get_query_variants()` - no tests
- Admin interface: All admin classes - no tests

**Risk Areas:**
- Calendar/date calculations (Orthodox Easter algorithm in `Slava.calc_vaskrs()`)
- Fasting period calculations in `utils_fasting.py`
- Serbian text conversion (transliteration)
- Form validation and ORM relationships

## Best Practices (Not Yet Implemented)

**Django TestCase Features:**
- `setUpClass()` for expensive one-time setup (not used)
- `setUpTestData()` for data shared across test methods (not used)
- `client` attribute for testing HTTP responses (not used)
- Transaction testing with `TransactionTestCase` (not used)

**Testing Utilities:**
- `override_settings` decorator for testing different configurations
- `Client()` for testing views without live server
- `RequestFactory()` for testing view functions directly

---

*Testing analysis: 2026-02-11*
