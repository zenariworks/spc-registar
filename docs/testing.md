# Тестирање и контрола квалитета

Стек: Django тест runner + pre-commit куке (ruff, pylint, biome, djlint, autoflake, isort, plус custom inline-script guard).

## Покретање тестова

```bash
# bare-metal:
cd crkva
python manage.py test registar tenants --keepdb --parallel auto

# Docker:
docker compose run --rm app python manage.py test registar tenants --keepdb
```

Заставице:
- `--keepdb` — поново користи тест базу (брже на 2. покретању)
- `--parallel auto` — користи све CPU језгре
- `--verbosity=2` — детаљан испис теста по теста
- `registar.tests.test_views` — само један модул
- `registar.tests.test_views.SpisakKrstenjaViewTestCase.test_spisak_krstenja_returns_200` — само један тест

### Тренутно стање

572+ теста. Baseline ~5 failures + 15 errors су унапред постојеће CWD-релативне путање и pre-existing template attribute audit (види `docs/testing.md#познати-проблеми`).

### Покривеност

```bash
pip install coverage
coverage run --source=. manage.py test
coverage report
coverage html       # отвори htmlcov/index.html
```

## Pre-commit куке

Једном поставите:

```bash
pre-commit install
```

После тога свака `git commit` команда ће покренути куке на staged фајловима. Конфигурација је у `.pre-commit-config.yaml`.

### Шта се покреће

| Кука | На чему | Шта проверава |
|---|---|---|
| `trailing-whitespace`, `end-of-file-fixer` | сви фајлови | стандардна хигијена |
| `check-json`, `check-merge-conflict` | сви фајлови | формат + git конфликти |
| `ruff` | `*.py` | Python линт + аутоматска исправка |
| `ruff-format` | `*.py` | Python форматирање (черне-style) |
| `isort` | `*.py` | сортирање import-ова (Black profile) |
| `autoflake` | `*.py` | уклони неискоришћене import-ове + променљиве |
| `pylint` | `*.py` (изузев migrations + scripts/gunicorn.conf.py) | дубинска Python провера |
| `django-tests` | `*.py` | покреће `manage.py test` (може бити прескочена; види ниже) |
| `biome` | `*.css`, `*.js` | CSS/JS линт (parse, dupes, dead overrides, console.log) |
| `djlint-django` | `*.html` | Django темплате линт (H021 = inline style) |
| `no-inline-script-debug` | `*.html` | бранимо `console.log` / `debugger` у inline `<script>` блоковима |
| `conventional-pre-commit` | commit поруке | проверава префикс (`feat:`, `fix:`, `refactor:`, итд.) |

### Ручно покретање

```bash
# Само на тренутно измењеним фајловима:
pre-commit run

# На свим фајловима:
pre-commit run --all-files

# Само једна кука:
pre-commit run ruff --all-files
pre-commit run biome --files crkva/registar/static/registar/components/tabovi.css
```

### Прескакање одређених кука

Када је кука позната-сломљена и поправка иде у засебном PR-у:

```bash
SKIP=django-tests git commit -m "..."
```

> **Никада** не користите `--no-verify` без експлицитног разлога — то прескаче СВЕ куке и често крије проблеме. Уместо тога користите `SKIP=<кука>` са поименичним именом.

## Biome (CSS + JS)

Свеж сетап:

```bash
npm install                # инсталира @biomejs/biome у node_modules/
./node_modules/.bin/biome lint crkva/registar/static/registar/
```

Конфигурација је у `biome.json`. Подразумевано:

- Лне укључени: `noConsoleLog`, `noDebugger`, `noVar` (warn), unused vars (warn), CSS parse, duplicate selectors, dead overrides
- Искључени (превише шумни за постојећи кôд): `useArrowFunction`, `noForEach`, `useTemplate`

Аутоматска исправка:

```bash
./node_modules/.bin/biome lint --apply crkva/registar/static/registar/  # сигурне исправке
./node_modules/.bin/biome lint --apply-unsafe crkva/registar/static/registar/  # ризичне (нпр. var → const)
```

## Pylint

Конфигурација у `.pylintrc`. Тренутно баш не примењује стриктна правила; служи као мрежа за грубе грешке (unreached code, неучитани симболи).

```bash
pylint crkva/registar/                                      # цео registar
pylint crkva/registar/views/parohijan_view.py               # један фајл
```

## Djlint (Django темплате)

Хвата inline стилове (H021), неискоришћене темплате тагове, итд.

```bash
djlint crkva/registar/templates/registar/
```

Конфигурација у `pyproject.toml`.

## Како писати тестове

### Пут до базе (тенант контекст)

Сви интеграциони тестови иду кроз тенант шему. Стандардни шаблон:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class MojIntTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="t", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_renders(self):
        r = self.client.get("/parohijani/")
        self.assertEqual(r.status_code, 200)
```

### Како тестирати write-view (треба роль)

- Створите `User` + `UserMembership` са `Role.KANCELARIJA` или другом одговарајућом
- ИЛИ направите `create_superuser` (заобилази проверу)

### Како тестирати анонимни захтев

```python
def test_redirects_anonymous(self):
    self.client.logout()
    r = self.client.get("/parohijani/")
    self.assertEqual(r.status_code, 302)
    self.assertIn("/prijava/", r["Location"])
```

## Познати проблеми

| Проблем | Узрок | Заобилажење |
|---|---|---|
| `django-tests` pre-commit кука пада са pickle грешком | Постоји проблем са `--parallel` runner-ом када су тест шеме у нестабилном стању | `SKIP=django-tests git commit ...` |
| Тестови `test_select2_unified_chrome`, `test_gunicorn_conf` итд. падају са FileNotFoundError | Релативне путање из тестова не разрешују се правилно из `crkva/` директоријума | Покретати из root-а: `cd / && python crkva/manage.py test ...` или фиксирати путање у тестовима |
| `test_no_hard_findings_remain` пада на `domacinstvo.zivi_clanovi` | View поставља атрибут динамички, а audit команда не зна за то | Знано-погрешно, безбедно је игнорисати |

## Аутоматска контрола приликом merge-а

GitHub Actions покреће:
- `pylint` workflow (`.github/workflows/pylint.yml`) на сваком push-у
- `hadolint` workflow — линт Dockerfile-а
- `docker-build` workflow — изградња + push при merge-у у main
- `auto-tag` workflow — подиже семвер тег при merge-у (feature → minor, fix → patch)

CI не покреће `pre-commit` (то се ради локално); али сви хук-ови су поновљиви и могу се додати у CI ако треба.
