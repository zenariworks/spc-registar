# Самостални (standalone) Docker

Покретање SPC Регистра у Docker-у, без bare-metal подешавања. Два пута:

- **А) Све-у-једном (bundled)** — апликација + сопствени Postgres у контејнерима.
  Најлакше за локални PC, Windows или један сервер.
- **Б) Слика + спољна база** — само контејнер апликације, ка постојећем Postgres-у.

> Вишекорисничко (django-tenants) и WeasyPrint (PDF) траже Linux окружење и
> Postgres — зато се испоручује Linux контејнер (исти на Windows/mac/Linux).

## Услови

- **Docker Desktop** (Windows/mac, са WSL2) или **Docker Engine + Compose v2** (Linux).
- Команде користе `docker compose` (v2).

## А) Све-у-једном (bundled)

Доноси и Postgres; чува податке у именованим волуменима.

### Windows
Покрените **`start.bat`** (двоклик или из терминала). Подиже стек и исписује адресу.

### Linux / mac
```bash
docker compose -f docker-compose.yml -f docker-compose.standalone.yml up -d --build
```

Апликација: **http://localhost:8000** · прва пријава **admin / admin**.

### Иницијално пуњење (опционо)
Подразумевана парохија се креира аутоматски. Референтне табеле (народности,
вероисповести, занимања, епархије) и календар слава пуне се једном:
```bash
docker compose -f docker-compose.yml -f docker-compose.standalone.yml \
  run --rm app python manage.py seed_lookups --tenant crkva_sv_petke_cukarica
```

### Управљање
```bash
# заустави
docker compose -f docker-compose.yml -f docker-compose.standalone.yml down
# логови
docker compose -f docker-compose.yml -f docker-compose.standalone.yml logs -f app
# ажурирање (после git pull)
docker compose -f docker-compose.yml -f docker-compose.standalone.yml up -d --build
```

### Подаци и бекап
База је у волумену `postgres_data`, статика у `static_data`. Бекап базе:
```bash
docker compose -f docker-compose.yml -f docker-compose.standalone.yml \
  exec db pg_dump -U crkva crkva > backup.sql
```

## Б) Слика + спољна база

За сервер са постојећим/управљаним Postgres-ом.
```bash
cp .env.prod.example .env   # подесите SECRET_KEY, DB_*, ALLOWED_HOSTS
docker compose up -d --build
```
Базни `docker-compose.yml` не доноси базу; повезујете се на спољну преко `.env`.
Иза реверсног проксија (нпр. Caddy) оставите `SECURE_SSL=1` (подразумевано ван
DEBUG-а) и проследите `X-Forwarded-Proto`.

## Напомене

- **Plain HTTP / localhost.** Bundled пут ради преко `http://localhost:8000`
  (`SECURE_SSL=0`), без сертификата — за локалну/LAN употребу.
- **Промените лозинку и кључ.** За било шта изложено промените
  `DJANGO_SUPERUSER_PASSWORD` и `SECRET_KEY` (env или `.env`).
- **LAN приступ.** За приступ са других рачунара додајте IP/име хоста у
  `ALLOWED_HOSTS`, нпр. `ALLOWED_HOSTS=localhost,192.168.1.50`.
- **Без SQLite.** django-tenants захтева Postgres.
