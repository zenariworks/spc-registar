# Производна поставка

Апликација подржава два пута за продукцију. Тренутна жива поставка користи bare-metal (gunicorn + systemd + Caddy); Docker је алтернатива.

- [Bare-metal (gunicorn + systemd + nginx)](#bare-metal)
- [Docker (production compose)](#docker)
- [Након поставке](#након-поставке-обавезно)

---

## Bare-metal

Тренутна продукциона топологија: Python 3.13 преко pyenv, gunicorn као WSGI сервер иза nginx прокси-ја, systemd unit за управљање процесом.

### 1. Подешавање сервера

Линукс сервер (Ubuntu 22.04+) са:

```bash
sudo apt install -y postgresql-16 nginx git build-essential \
    libpq-dev libffi-dev libcairo2 libpango-1.0-0 libgdk-pixbuf-2.0-0 \
    libjpeg-dev zlib1g-dev nodejs npm

# pyenv
curl https://pyenv.run | bash
# Додајте у ~/.bashrc / ~/.zshrc — види https://github.com/pyenv/pyenv#installation
pyenv install 3.13.8
pyenv virtualenv 3.13.8 crkva
```

### 2. Клонирање и инсталација

```bash
sudo mkdir -p /root/projects
cd /root/projects
git clone git@github.com:zenariworks/spc-registar.git
cd spc-registar
pyenv local crkva
pip install -r requirements.txt
npm install
```

### 3. Производни `.env`

```bash
cp .env.prod.example .env
# Подесите:
#   DEBUG=0
#   SECRET_KEY=<генеришите>   (нпр. python -c "import secrets; print(secrets.token_urlsafe(64))")
#   ALLOWED_HOSTS=registar.parohija.example
#   DB_PASS=<јака лозинка>
#   DB_HOST=localhost (или адреса спољне базе)
```

> ⚠ Никада не коммитуј `.env` — у `.gitignore` је. Не дели вредности у chat/issue trackerу.

### 4. База + миграције

```bash
sudo -u postgres createuser crkva --pwprompt
sudo -u postgres createdb crkva -O crkva

cd crkva
python manage.py migrate_schemas      # public + сви тенанти
python manage.py collectstatic --noinput
python manage.py compress --force
python manage.py createsuperuser
```

### 5. Gunicorn конфигурација

Конфиг је у `scripts/gunicorn.conf.py`. Подразумевани listen порт је 9000.

### 6. Systemd unit

```ini
# /etc/systemd/system/spc-registar.service
[Unit]
Description=SPC Registar Django App (gunicorn)
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/projects/spc-registar/crkva
Environment="PYENV_VERSION=crkva"
Environment="PATH=/root/.pyenv/shims:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=/root/.pyenv/versions/crkva/bin/gunicorn crkva.wsgi:application \
    -c /root/projects/spc-registar/scripts/gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now spc-registar
sudo systemctl status spc-registar
```

### 7. Caddy (reverse proxy + аутоматски HTTPS)

Едж је **Caddy** — терминира TLS и аутоматски прибавља/обнавља Let's Encrypt
сертификат. Статику служи whitenoise из саме апликације, па Caddy само
прослеђује све ка gunicorn-у. Пример `/etc/caddy/Caddyfile`:

```
registar.parohija.example {
    reverse_proxy 127.0.0.1:9000
}
```

```bash
sudo systemctl reload caddy
```

Подешавање `SECURE_PROXY_SSL_HEADER` у settings прихвата `X-Forwarded-Proto`
који Caddy шаље, па `request.is_secure()`, CSRF и secure колачићи раде преко
HTTPS хоста.

### 8. Деплој (стандардни ток после `git push origin main`)

```bash
ssh root@<server>
cd ~/projects/spc-registar
git checkout main && git pull --ff-only
cd crkva
python manage.py collectstatic --noinput
python manage.py compress --force
python manage.py migrate_schemas       # ако има нових миграција
sudo systemctl restart spc-registar
curl -I http://localhost:9000/healthz   # должно бити 200
```

---

## Docker

Алтернативни пут — продукција у Docker контејнерима преко `docker-compose.yml + docker-compose.prod.yml`.

### 1. Подесите `.env.prod`

```bash
cp .env.prod.example .env.prod
# Поставите производне вредности (SECRET_KEY, DB_PASS, ALLOWED_HOSTS итд.)
```

### 2. Изградња + покретање

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
# или
make prod-up
```

Унутрашњи gunicorn слуша на 8000, изложен је порт 80 кроз proxy сервис (види `docker-compose.prod.yml`).

### 3. Иницијалне команде

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm app \
    python manage.py createsuperuser
```

### 4. Логови и управљање

```bash
make prod-logs          # tail логова
make prod-migrate       # покрени миграције
make prod-down          # заустави
```

---

## Након поставке (обавезно)

### Здравствене провере

Апликација излаже две probe-руте без аутентификације:

| Рута | Шта проверава | Употреба |
|---|---|---|
| `/healthz` | Процес ради (без DB упита) | Liveness probe за load balancer |
| `/readyz` | `SELECT 1` ка бази успева | Readiness probe / monitoring |

### Безбедносна листа

- [ ] `DEBUG=0` у `.env`
- [ ] `SECRET_KEY` је јединствен и није `dev-secret-key-...`
- [ ] `ALLOWED_HOSTS` је уско ограничен (не `*`)
- [ ] `DB_PASS` је јак и није `postgres` / `changeme`
- [ ] HTTPS је постављен (Certbot)
- [ ] Backup стратегија за Postgres (cron + `pg_dump`)
- [ ] systemd unit има `Restart=always`
- [ ] nginx access/error логови ротирају

### Backup-и

Скрипта `scripts/backup.sh` ради `pg_dump` целе базе са свим тенант шемама. Поставите у cron, нпр. дневно у 03:00:

```cron
0 3 * * * /root/projects/spc-registar/scripts/backup.sh >> /var/log/spc-registar-backup.log 2>&1
```

### Monitoring

Уколико желите Sentry или сличан error reporting, додајте `sentry-sdk` у `requirements.txt` и иницијализујте у `crkva/settings.py`. Тренутно само console logging.

### Креирање нове парохије (тенанта)

После првог пуштања, нову парохију направите кроз Django admin (`/admin/`) — модел `Tenant` (apps: tenants). Шема ће се аутоматски креирати по принципу django-tenants. Више о моделу: [architecture.md](architecture.md).
