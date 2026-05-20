# Архитектура

## Кратак преглед

Django 6.0 апликација иза gunicorn-а и nginx-а, PostgreSQL као једина база, [django-tenants](https://django-tenants.readthedocs.io/) за изолацију података по парохији. Frontend је server-rendered (Django templates + ванилла CSS/JS), без SPA framework-а. PDF сертификати се генеришу WeasyPrint-ом.

![Структура пројекта](structure.png)

## Структура репозиторијума

```
spc-registar/
├── crkva/                      # Django пројекат (име: crkva)
│   ├── crkva/                  # Сетинзи + root URLConf + WSGI
│   │   ├── settings.py
│   │   ├── urls.py             # /healthz, /readyz, /admin, /parohija, /
│   │   └── wsgi.py
│   ├── registar/               # Главна апликација (регистри)
│   │   ├── models/             # Osoba, Domacinstvo, Krstenje, Vencanje, Svestenik, Adresa...
│   │   ├── views/              # CBV + FBV; сви имају LoginRequiredMixin / @login_required
│   │   ├── forms/              # ModelForms + TenantPhoneField
│   │   ├── templates/registar/ # Детаљни шаблони (krstenje.html, parohijan.html...)
│   │   ├── static/registar/    # CSS (BEM, дизајн-токени), JS (ванилла)
│   │   ├── management/commands/# DBF import, миграциони one-shots
│   │   ├── migrations/         # Django миграције за registar шему
│   │   └── tests/              # 570+ unit + интеграционих тестова
│   ├── tenants/                # django-tenants апликација (Tenant, Domain, Role, UserMembership)
│   │   ├── models.py
│   │   ├── permissions.py      # tenant_role_required, tenant_admin_required, can_edit
│   │   └── migrations/         # Миграције за public шему
│   ├── kalendar/               # Slava модел + покретне славе
│   └── manage.py
├── scripts/
│   ├── gunicorn.conf.py        # gunicorn config (порт 9000)
│   ├── backup.sh               # pg_dump целе базе
│   └── migration/              # помоћни скриптови за migracija_*
├── docs/                       # Ова документација
├── biome.json                  # CSS/JS линт правила
├── .pre-commit-config.yaml     # ruff, ruff-format, isort, autoflake, pylint, biome, djlint
├── pyproject.toml
└── docker-compose*.yml         # 3 фајла: base + override (dev) + prod
```

## Django-tenants: изолација по парохији

Свака парохија је засебна **Postgres шема** у истој бази:

```
postgres-db: crkva
├── public                          ← дељене табеле (Tenant, Domain, UserMembership, auth_user)
├── crkva_sv_petke_cukarica         ← парохија "Свете Петке у Чукарици"
│   ├── osobe, domacinstva, krstenja, vencanja, svestenici, hramovi, adrese...
├── crkva_sv_nikole_zaandam         ← парохија "Светог Николе у Зандаму"
│   └── (исте табеле, потпуно одвојени подаци)
└── test_tenant                     ← коришћен за тестове
```

- **Дељене (SHARED_APPS)** — `django.contrib.*`, `tenants`, `django_select2` → у public шеми
- **Тенант-специфичне (TENANT_APPS)** — `registar`, `kalendar`, `simple_history` → копија у свакој шеми

### Како се рутира тенант

Захтев долази на хост типа `cukarica.localhost` или `registar.parohija.example`. `django-tenants` middleware проверава Domain табелу у public шеми, налази тенанта, и постави `connection.tenant` + `connection.schema_name`. Сви upit-и у том request-у иду само у ту шему.

### Креирање нове парохије

```bash
python manage.py shell
>>> from tenants.models import Tenant, Domain
>>> t = Tenant.objects.create(
...     schema_name="crkva_sv_jovana_nis",
...     name="Свети Јован Богослов, Ниш",
...     default_phone_region="RS",
... )
>>> Domain.objects.create(domain="nis.parohija.example", tenant=t, is_primary=True)
```

`migrate_schemas` ће следећи пут аутоматски креирати све табеле у новој шеми.

## Ауторизација

Сви request-ови захтевају пријаву (`@login_required` / `LoginRequiredMixin`); анонимни саобраћај иде на `/prijava/?next=<rutu>`. Писање је уско по улози.

### Улоге (`tenants.models.Role`)

| Улога | Шта може да пише | Где |
|---|---|---|
| `Админ` | Све у тенанту | `osoba`, `domacinstvo`, `krstenje`, `vencanje`, `svestenik` |
| `Канцеларија` | Парохијане, домаћинства, крштења, венчања | (изузев `svestenik`) |
| `Свештенство` | Свештеници | само `svestenik` |
| `Преглед` | Ништа — само чита | — |

Дефинисано у `crkva/tenants/permissions.py:WRITE_BY_ROLE`. Superuser заобилази проверу. Декоратор `@tenant_role_required("osoba")` се ставља изнад view-a који пише.

### Шема ауторизације

- **Anonymous** → `/prijava/` (login)
- **Authenticated** → све `Spisak*`, `Prikaz*`, `*PDF` view-ове, `index`, `kalendar`, `search`, `search_autocomplete`
- **Role check (`can_edit`)** → `unos_*`, `izmena_*`, `brzi_*`, `calibrate_*`
- **Tenant admin** → корисничко управљање (`tenants/views.py`)

## Кључне компоненте

### Модели

- **`Osoba`** (`registar.models.parohijan`) — једина "person" табела; `parohijan=True` означава парохијане. Алиаси: `Parohijan = Osoba` (за читљивост).
- **`Domacinstvo`** — домаћинство; везано преко `domacin` (FK на Osoba) и `adresa` (FK на Adresa); чланови преко `Ukucanin` join модела.
- **`Krstenje`, `Vencanje`** — записи са FK на учеснике (отац/мајка/кум; зеник/невеста/кум/стари сват). Обоје имају `uid` (UUID) као primary ID за URL-ове.
- **`Svestenik`** — свештеници, посебан скуп људи (не унакрсно са Osoba).
- **`Slava`** (`kalendar.models`) — фиксне и покретне славе; помоћи метод `get_datum(year)` за покретне.

Сви модели користе [`simple_history`](https://django-simple-history.readthedocs.io/) за audit лог промена.

### Forms

- **`TenantPhoneField`** (`registar/forms/phone.py`) — телефонско поље које регион чита из `connection.tenant.default_phone_region` (RS, NL, DE, ...) тако да парохија ван Србије може да користи свој позивни број.
- Сви ModelForm-ови наслеђују `Meta.fields` експлицитно (не `__all__`) ради безбедности.

### Темплате-tag-ови

- **`info_components`** (`registar/templatetags/`) — пружа `{% info_row %}`, `{% info_section %}`, `{% info_row_bool %}` за DRY рендерирање детаљних страница.
- **`marker_filter`** — означава претражене речи (са HTML escape пре `mark_safe`).
- **`form_errors_extras`** — конвертује `form.errors` у `{field: [str]}` JSON, користи се са `json_script` за inline error UX.

### Frontend архитектура

- CSS токени у `static/registar/base/tokens.css` — све боје преко `var(--color-*)`, тема (`light`, `sepia`, `tamna`) се ради преко override-a у `themes/*.css`
- BEM конвенција за класе (`.info-row__icon`, `.tab-group--with-panels`)
- JS је ванилла + jQuery (за django-select2), нема билд корака за апликациони код
- [Biome](https://biomejs.dev/) линтер за CSS/JS (`biome.json`)

### URL шема

```
/healthz                     liveness probe (без auth)
/readyz                      readiness probe (DB ping; без auth)
/admin/                      Django admin
/parohija/                   тенант UI (tenants app)
/prijava/                    login
/odjava/                     logout
/                            home (slava календар)
/parohijani/                 списак парохијана
/parohijan/<uid>/            детаљи парохијана
/parohijan/print/<uid>/      PDF
/krstenja/, /krstenje/<uid>/, /krstenje/print/<uid>/
/vencanja/, /vencanje/<uid>/, /vencanje/print/<uid>/
/domacinstva/, /domacinstvo/<uid>/
/svestenici/, /svestenik/<uid>/, /svestenik/print/<uid>/
/slava-kalendar/             календар слава
/search/                     претрага
/unos/<resurs>/              нови запис
/izmena/<resurs>/<uid>/      измена записа
/api/brzi-unos-osobe/        AJAX за брзо креирање особе
/api/brzi-izmena-adrese/<uid>/ AJAX за измену адресе
```

## База података

Шему и FK-ове можете видети на [dbdiagram.io/d/65319d89ffbf5169f00f803f](https://dbdiagram.io/d/65319d89ffbf5169f00f803f).

## Settings

| Окружење | Извор |
|---|---|
| Локални развој | `.env.dev.example` → копирати у `.env` |
| Производња | `.env.prod.example` → копирати у `.env` са продукционим вредностима |

Кључне променљиве — види `crkva/crkva/settings.py:36+`:

- `DEBUG` — мора бити `0` у продукцији
- `SECRET_KEY` — никад не оставити вредност из примера
- `DB_*` — host, port, name, user, pass
- `ALLOWED_HOSTS` — листа домена; никад `*` у продукцији

## CI / аутоматизација

`.github/workflows/`:

| Workflow | Шта ради |
|---|---|
| `pylint.yml` | Pylint на Python кôду при сваком push-у |
| `hadolint.yml` | Линт Dockerfile-а |
| `docker-build.yml` | Изградња + push на Docker Hub при merge-у у main |
| `auto-tag.yml` | Подиже семвер тег при merge-у (feature → minor, fix → patch) |
