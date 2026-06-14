# Постављање и покретање

Изаберите пут према томе шта вам треба. Сви Docker путеви користе један
`docker-compose.yml` са профилима (`dev` / `standalone` / `prod`).

| Пут | За кога | Команда |
|---|---|---|
| **Стандалон (Docker)** | локални PC, Windows лаптоп, један сервер | `start.bat` / `./start.sh` → _ниже_ |
| **Развојно окружење** | допринос коду | `make dev-up` или pyenv venv → _ниже_ |
| **Производња** | сервер са доменом/HTTPS | [Производња](deployment.md) |

> django-tenants (вишекорисничко) и WeasyPrint (PDF) траже Linux + Postgres —
> зато се испоручује Linux контејнер (исти на Windows/macOS/Linux); SQLite није
> подржан.

---

## Стандалон (Docker, све-у-једном)

Апликација + сопствени Postgres у контејнерима — најлакши пут за локални рачунар
или један сервер. Подаци се чувају у именованом волумену `postgres_data`.

### Услови
- **Docker Desktop** (Windows/macOS, са WSL2) или **Docker Engine + Compose v2** (Linux).

### Покретање
- **Windows:** покрените **`start.bat`** (двоклик или из терминала).
- **Linux / macOS:** покрените **`./start.sh`**.
- Или директно:
  ```bash
  docker compose --profile standalone up -d --build
  ```

Апликација: **http://localhost:8000** · прва пријава **admin / admin**.

### Управљање
```bash
docker compose --profile standalone down          # заустави
docker compose --profile standalone logs -f app   # логови
docker compose --profile standalone up -d --build # ажурирање (после git pull)
```

### Иницијално пуњење
Подразумевана парохија (`crkva_sv_petke_cukarica`) се креира аутоматски.
Референтне табеле и календар слава пуне се једном:
```bash
docker compose --profile standalone \
  run --rm app python manage.py seed_lookups --tenant crkva_sv_petke_cukarica
```
За увоз стварних података из старе HramSP апликације (`crkva.zip`) види
[Миграцију података](MIGRACIJA.md).

### Подаци и бекап
```bash
docker compose --profile standalone exec db pg_dump -U crkva crkva > backup.sql
```

### Напомене
- **Plain HTTP / localhost** (`SECURE_SSL=0`) — за локалну/LAN употребу, без сертификата.
- **Промените лозинку и кључ** за било шта изложено: `DJANGO_SUPERUSER_PASSWORD` и `SECRET_KEY`.
- **LAN приступ:** додајте IP/име хоста у `ALLOWED_HOSTS` (нпр. `localhost,192.168.1.50`).

---

## Развојно окружење

За рад на самом коду — две опције: bare-metal (pyenv) или Docker `dev` профил.

### Опција А — bare-metal (pyenv + локални Postgres)

Захтеви: Python 3.13.x, PostgreSQL 16.x, Node.js 20.x+ (biome линтер), pyenv (препоручено).

```bash
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar

pyenv install 3.13.8            # ако није већ инсталиран
pyenv virtualenv 3.13.8 crkva
pyenv local crkva
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

npm install                    # biome линтер у node_modules/
cp .env.dev.example .env       # уредите по потреби (види architecture.md)

# Postgres + база
sudo systemctl start postgresql
sudo -u postgres createuser devuser --pwprompt   # лозинку упишите у .env
sudo -u postgres createdb devdb -O devuser

cd crkva
python manage.py migrate_schemas               # public шема + тенанти
python manage.py createsuperuser
cd .. && pre-commit install
cd crkva && python manage.py runserver         # http://localhost:8000/
```

### Опција Б — Docker (`dev` профил)

```bash
cp .env.dev.example .env
docker compose --profile dev up -d --build     # runserver + live reload, уграђени Postgres
docker compose --profile dev run --rm app-dev python manage.py createsuperuser
```

Дневне команде (Makefile): `make dev-up` · `make dev-down` · `make dev-logs` ·
`make dev-shell` · `make dev-migrate` · `make dev-makemigrations`.

### Демо подаци (опционо)
```bash
# bare-metal:
python manage.py unos_krstenja
python manage.py unos_vencanja
# Docker:
docker compose --profile dev run --rm app-dev python manage.py unos_krstenja
```

---

## Производња

Продукција иде или **bare-metal** (gunicorn + systemd + Caddy — тренутна жива
поставка) или **Docker** (`--profile prod`: gunicorn + Caddy, спољашња база). Пун
поступак: [Производња](deployment.md).

---

## Решавање проблема

**`relation "..." does not exist`** — нисте покренули `migrate_schemas` за тенант. Покрените још једном.

**Pre-commit куке падају на `django-tests`** — заобиђите за тренутни commit: `SKIP=django-tests git commit ...`.

**`Permission denied` на Docker сокету** — додајте корисника у `docker` групу: `sudo usermod -aG docker $USER`, па се одјавите и пријавите.

**Biome не може да се покрене** — нисте покренули `npm install`.
