# Подешавање развојног окружења

Имате два начина да покренете апликацију локално. Изаберите онај који вам одговара.

- [Bare-metal (pyenv + локални Postgres)](#bare-metal)
- [Docker Compose](#docker)
- [Шта да радите после](#први-кораци-после-инсталације)

---

## Bare-metal

За локални развој на Linux/macOS-у директно са pyenv-ом и локалним Postgres-ом.

### 1. Захтеви

| Алат | Верзија |
|---|---|
| Python | 3.13.x |
| PostgreSQL | 16.x |
| Node.js | 20.x+ (за biome линтер) |
| pyenv | најновија (опционо али препоручено) |

### 2. Клонирајте репозиторијум

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar
```

### 3. Креирајте Python окружење

```bash
pyenv install 3.13.8         # ако није већ инсталиран
pyenv virtualenv 3.13.8 crkva
pyenv local crkva            # везује директоријум за окружење
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Инсталирајте Node алате (biome линтер)

```bash
npm install     # инсталира @biomejs/biome у node_modules/
```

### 5. Подесите окружење

```bash
cp .env.dev.example .env
# Уредите .env ако треба (DEBUG, ALLOWED_HOSTS, итд.) — детаље види [docs/architecture.md](architecture.md)
```

### 6. Покрените Postgres и креирајте базу

```bash
sudo systemctl start postgresql
sudo -u postgres createuser devuser --pwprompt          # лозинку упишите у .env
sudo -u postgres createdb devdb -O devuser
```

### 7. Миграције + тенант

```bash
cd crkva
python manage.py migrate_schemas       # креира public шему + тенантe
python manage.py createsuperuser
```

### 8. Pre-commit куке

```bash
pre-commit install
```

### 9. Покрените сервер

```bash
python manage.py runserver
# Отворите http://localhost:8000/, пријавите се на /prijava/
```

---

## Docker

За изоловано развојно окружење преко Docker Compose-а.

### 1. Захтеви

- [Docker](https://www.docker.com/products/docker-desktop) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2

### 2. Клонирајте и подесите

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar
cp .env.dev.example .env
```

### 3. Изградња

```bash
docker compose --profile dev build
# или
make build
```

### 4. Покретање

```bash
docker compose --profile dev up -d   # развојно окружење (са live reload-ом)
# или
make dev-up
```

Сервер слуша на [http://localhost:8000/](http://localhost:8000/). Постгрес је изложен на порту 8001 (мапа из контејнера 5432).

### 5. Миграције + суперкорисник

```bash
docker compose --profile dev run --rm app-dev python manage.py migrate_schemas
docker compose --profile dev run --rm app-dev python manage.py createsuperuser
```

### 6. Дневне команде

| Команда | Шта ради |
|---|---|
| `make dev-up` | Покреће контејнере |
| `make dev-down` | Зауставља контејнере |
| `make dev-logs` | Прати логове |
| `make dev-shell` | Django shell унутар контејнера |
| `make dev-migrate` | Покреће миграције |
| `make dev-makemigrations` | Креира нове миграције |

---

## Први кораци после инсталације

### Учитавање демо података (опционо)

Ако желите тест парохијане/крштења/венчања пре него што започнете рад:

```bash
# bare-metal:
python manage.py unos_krstenja
python manage.py unos_vencanja

# Docker:
docker compose --profile dev run --rm app-dev python manage.py unos_krstenja
docker compose --profile dev run --rm app-dev python manage.py unos_vencanja
```

### Учитавање стварних података из HramSP-а

Ако мигрирате из старе HramSP апликације: види [MIGRACIJA.md](MIGRACIJA.md).

### Креирање нове парохије (тенанта)

Свака парохија је засебна Postgres шема. Креирање нове иде преко Django admin-а или скрипте — детаље види [architecture.md](architecture.md).

---

## Решавање проблема

**`relation "..." does not exist`** — нисте покренули `migrate_schemas` за тенант. Покрените још једном.

**Pre-commit куке падају на `django-tests`** — постоји познат проблем са парalel runner-ом; заобиђите са `SKIP=django-tests git commit ...` за тренутни commit.

**`Permission denied` на Docker сокету** — додајте корисника у `docker` групу: `sudo usermod -aG docker $USER`, па се одјавите и пријавите.

**Biome не може да се покрене** — нисте покренули `npm install`. Pre-commit куки `biome` јој је потребан.
