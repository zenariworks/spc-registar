# Дизајн: самостални (standalone) / портабилни Docker деплој

- **Статус:** Предлог (дизајн-запис за сагласност — још без измена кода)
- **Issue:** #7 (Како покретати самостални (standalone) Docker)
- **Датум:** 2026-06-13

## Контекст

Апликација тренутно ради на **једном Linux серверу, bare-metal**:
pyenv (Python 3.13) → `gunicorn` на `:9000` → **Caddy** терминира TLS на `:443`
(Let's Encrypt) → reverse-proxy ка gunicorn-у; Postgres на `localhost`; процес
води `spc-registar` systemd unit.

> Напомена: `docs/deployment.md` описује **nginx + certbot** едж. Живи едж је
> заправо **Caddy** (`/etc/caddy/Caddyfile`). То неслагање документације
> исправљамо у склопу овог рада.

Issue #7 тражи документован начин да се апликација покрене **самостално преко
Docker-а**. Иако постоје `docker-compose.yml` / `*.override.yml` / `*.prod.yml`,
`Dockerfile` и `scripts/run.sh`, голи `docker run` слике **не ради** данас (види
Дефекти), а нема ни упутства корак-по-корак.

## Силе (шта одређује дизајн)

1. **WeasyPrint** (PDF мотор) тражи нативне библиотеке (Cairo, Pango, GDK-PixBuf,
   fontconfig, фонтови). Тривијално на Linux-у, мучно на Windows/macOS bare-metal.
   → Испорука **Linux контејнера** је кључ портабилности.
2. **Postgres + django-tenants** — мулти-тенант по шеми; **нема SQLite пута**.
   Свака инсталација тражи прави Postgres → спаковати га за самосталан рад.
3. **Публика** — парохијске канцеларије (често **Windows**), локални рачунари и
   сервери, често нетехнички корисници. Лакоћа инсталације је пресудна.
4. **TLS** — Caddy већ доказује HTTPS без подешавања за јавни сервер; LAN/PC
   инсталације немају јавни домен.

## Одлуке

| # | Одлука | Образложење |
|---|--------|-------------|
| O1 | **Docker је примарна портабилна дистрибуција.** Bare-metal остаје документован као „тренутни/напредни“ серверски пут. | WeasyPrint + Postgres + pyenv на Windows-у је кркљав; контејнери су репродуктивни. |
| O2 | **Windows = Docker Desktop** (WSL2) + једна compose команда (умотана у `start.bat`). | Нема инсталера за одржавање; иста слика свуда. |
| O3 | **Две документоване топологије:** (а) bundled све-у-једном (подразумевано), (б) слика + спољна база (сервери). | Покрива локал/PC и серверске потребе. |
| O4 | **LAN/PC инсталације служе plain HTTP на `localhost`** уз `DEBUG=0`. | Најједноставније за офлајн/једнокутијски рад; без сертификата. |
| O5 | Увести **`SECURE_SSL` env флег** који раздваја HTTPS учвршћивање од `DEBUG`. | Неопходно да `DEBUG=0` ради безбедно преко plain HTTP (види ниже). |
| O6 | Задржати **django-tenants** (један подразумевани тенант на локалним инсталацијама). | Уграђено је; миграција подразумеваног тенанта га већ креира. |

## Архитектура

**Једна Linux слика, слојевити Compose.**

- `docker-compose.yml` — базни `app` сервис (build/image), разуман подразумевани `CMD`.
- `docker-compose.override.yml` — развој (mount изворног кода, `runserver`, уграђени `db`).
- `docker-compose.standalone.yml` — **НОВО**, подразумевани самосталан: `app`
  (gunicorn, plain HTTP) + `db` (postgres:16) + именовани волумени (`pgdata`,
  `static`, `media`) + `restart: unless-stopped`; излаже `8000:8000` →
  `http://localhost:8000`.
- `docker-compose.prod.yml` — спољна база + едж прокси (сервер).

| Циљ | Команда | Стек |
|-----|---------|------|
| Windows / локални PC | `start.bat` → `docker compose -f docker-compose.yml -f docker-compose.standalone.yml up -d` | app + уграђени Postgres, plain HTTP localhost |
| Један сервер | иста standalone compose | све-у-једном, `restart: unless-stopped` |
| Скалирани сервер | слика + спољни управљани Postgres + едж Caddy | тренутни модел |
| Bare-metal | pyenv + gunicorn + systemd + Caddy | тренутна жива кутија (задржано, документовано као напредно) |

### Улазна тачка слике (замењује `scripts/run.sh`)

Прави `entrypoint.sh`, **идемпотентан**, који подиже свежу базу:

```
wait_for_db
migrate_schemas              # НЕ `migrate` (django-tenants)
collectstatic --noinput
seed_lookups                 # народности/вероисповести/...
unos_slava                   # календар (славе) — само ако је празно
createsuperuser --noinput    # из DJANGO_SUPERUSER_* env, ако не постоји
exec gunicorn crkva.wsgi:application -c scripts/gunicorn.conf.py
```

Миграција подразумеваног тенанта (`tenants/0002_create_default_tenant`) већ
креира подразумевану парохију и чини staff кориснике администраторима, па први
`up` даје функционалну пријаву.

### Измена подешавања (O5)

Данас (`crkva/crkva/settings.py`):

```python
if not DEBUG and not _RUNNING_TESTS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    ...
```

HTTPS учвршћивање је везано за `DEBUG`, па `DEBUG=0` форсира SSL редирекцију +
secure колачиће → `http://localhost` пуца. Предлог: условити учвршћивање
експлицитним env флегом, подразумевано чувајући тренутно понашање:

```python
SECURE_SSL = os.environ.get("SECURE_SSL", "0" if DEBUG else "1") == "1"
if SECURE_SSL and not _RUNNING_TESTS:
    SECURE_SSL_REDIRECT = True
    ...
```

Самосталан поставља `DEBUG=0 SECURE_SSL=0` → безбедно (без debug страница, прави
`ALLOWED_HOSTS`) али plain HTTP. Јавни сервер задржава `SECURE_SSL=1` (подразумевано).

## Дефекти за исправку (предуслови)

1. **`scripts/run.sh`** учитава 7 fixtures који не постоје у овом репозиторијуму
   (`import_auth/codetables/metadata/measures/filters/topicsets/spatialdimensions`
   — остаци из другог template пројекта). Уз `set -e` контејнер пуца при старту →
   замењено горњом улазном тачком.
2. **`docker-compose.prod.yml`** покреће `gunicorn app.wsgi:application` — погрешан
   модул; треба `crkva.wsgi`. (`deployment.md:183` документује баг уместо да га исправи.)
3. Compose ауто-команде користе `migrate` (треба `migrate_schemas`).
4. Документација користи `docker compose` (v2) док Makefile/хост користе
   `docker-compose` (v1) — изабрати једно (v2) и ускладити обоје.
5. `docs/deployment.md` описује nginx + certbot; стварност је **Caddy**.

## Шта НИЈЕ циљ (non-goals)

- Без нативног Windows инсталера / без уграђеног мотора (Docker Desktop је пут).
- Без SQLite / једнофајловног режима (django-tenants тражи Postgres).
- Не уклањамо bare-metal — остаје тренутни продукциони пут, документован као напредан.

## Предложена испорука (2 PR-а)

1. `fix(docker)` — преписана улазна тачка, prod `app.wsgi`→`crkva.wsgi`, `SECURE_SSL`
   флег. Проверљиво подизањем стека. *Чини да самосталан стварно ради.*
2. `feat(docker)` + `docs` — `docker-compose.standalone.yml`, `start.bat`, упутство
   (обе топологије), исправке `deployment.md`/README. *Затвара #7.*

## Отворена питања / ризици

- Миграција подразумеваног тенанта тврдо кодира „Парохија Чукарица“. За другу
  парохију оператер је преименује кроз admin/UI; опционо касније учинити име
  env-управљаним.
- `seed`/`unos_*` команде треба потврдити као идемпотентне + tenant-свесне пре
  везивања у first-run bootstrap.
- Docker Desktop на Windows-у тражи WSL2 + admin инсталацију (прихваћено по O2).
