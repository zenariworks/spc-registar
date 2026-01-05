# СПЦ Регистар

[![Pylint](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml)

## Опис пројекта

СПЦ Регистар је дигитални систем за вођење евиденције Српске Православне Цркве. Омогућава ефикасно управљање црквеним записима, укључујући крштења, венчања и друге важне догађаје.

## Садржај

- [Предуслови](#предуслови)
- [Први кораци](#први-кораци)
- [Производно окружење](#производно-окружење)
- [Развој и тестирање](#развој-и-тестирање)
- [Миграција података из HramSP](#миграција-података-из-hramsp)
- [Додатне белешке](#додатне-белешке)

## Предуслови

Пре него што започнете, потребно је да имате следеће софтвере инсталиране на вашем систему:

- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

Пратите упутства за инсталацију на званичним вебсајтовима.

## Први кораци

### 1. Подешавање окружења

Копирајте template фајл за развојно окружење:

   ```bash
   cp .env.dev.example .env
   ```

Ажурирајте вредности у `.env` по потреби (опционално).

### 2. Инсталација и подешавање

   ```bash
   docker compose build
   # или
   make build
   ```

   У случају проблема са дозволама, погледајте [додатне белешке](#додатне-белешке).

### 3. Миграције базе података и учитавање тест података

- Креирање и примена миграција:

   ```bash
   docker compose run --rm app sh -c "python manage.py makemigrations && python manage.py migrate"
   # или
   make dev-makemigrations
   make dev-migrate
   ```

- Унос основних података у базу:

   ```bash
   docker compose run --rm app sh -c "python manage.py unosi"
   ```

- Унос случајних (демо) података у базу:

    ```bash
    docker compose run --rm app sh -c "python manage.py unos_krstenja"
    docker compose run --rm app sh -c "python manage.py unos_vencanja"
    ```

   Након овог корака, у базу је унет пример података.
   Након покретања, могућ је и приказ ових података на [localhost:8000/](http://localhost:8000/).

### 4. Креирање суперкорисника и покретање апликације

- Креирајте суперкорисника:

   ```bash
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

- Покретање апликације:

   ```bash
   docker compose up
   # или
   make dev-up
   ```

- Преглед логова:

   ```bash
   make dev-logs
   ```

- Заустављање апликације:

   ```bash
   make dev-down
   ```

   Сада можете приступити регистру на [localhost:8000](http://localhost:8000), а админ панелу на [localhost:8000/admin](http://localhost:8000/admin).

## Производно окружење

### 1. Подешавање конфигурационог фајла

   ```bash
   cp .env.prod.example .env.prod
   ```

   Ажурирајте вредности променљивих у `.env.prod` (SECRET_KEY, DB_HOST, DB_PASS, ALLOWED_HOSTS, итд.).

### 2. Изградња и покретање апликације

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml build
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   # или
   make prod-up
   ```

   Приступите апликацији на [http://localhost](http://localhost) или [http://127.0.0.1](http://127.0.0.1).

### 3. Креирање суперкорисника

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm app sh -c "python manage.py createsuperuser"
   ```

### 4. Преглед логова и управљање

   ```bash
   # Преглед логова
   make prod-logs

   # Покретање миграција
   make prod-migrate

   # Заустављање апликације
   make prod-down
   ```

## Docker конфигурација

Пројекат користи модуларну Docker Compose конфигурацију која олакшава пребацивање између развојног и производног окружења:

- **docker-compose.yml** - Основна конфигурација (дељена између окружења)
- **docker-compose.override.yml** - Развојно окружење (аутоматски се учитава)
- **docker-compose.prod.yml** - Производно окружење (експлицитно се учитава)

### Makefile команде

За брзо управљање окружењима користите `make` команде:

```bash
# Помоћ
make help

# Развојно окружење
make dev-up              # Покретање развојног окружења
make dev-down            # Заустављање развојног окружења
make dev-logs            # Преглед логова
make dev-shell           # Приступ Django shell-у
make dev-migrate         # Покретање миграција
make dev-makemigrations  # Креирање нових миграција

# Производно окружење
make prod-up             # Покретање производног окружења
make prod-down           # Заустављање производног окружења
make prod-logs           # Преглед логова
make prod-migrate        # Покретање миграција

# Опште
make build               # Изградња Docker слика
make clean               # Уклањање свих контејнера, волумена и слика
```

### Разлике између окружења

**Развојно:**
- Django development server (`runserver`)
- DEBUG режим укључен
- Изворни код монтиран као volume (live reload)
- Локална PostgreSQL база података
- Порт 8000 директно изложен

**Производно:**
- Gunicorn WSGI server
- DEBUG режим искључен
- Користи екстерну базу података
- Nginx proxy
- Порт 80 изложен кроз proxy
- Аутоматско рестартовање
- Оптимизовано за перформансе и безбедност

## Развој и тестирање

### Покретање тестова

   ```bash
   docker compose run --rm app sh -c "python manage.py test"
   ```

## Миграција података из HramSP

За миграцију података из старе HramSP апликације (DBF фајлови) у нову базу података, погледајте детаљну документацију: **[docs/MIGRACIJA.md](docs/MIGRACIJA.md)**

Кратак преглед:

```bash
# Учитавање DBF фајлова у PostgreSQL staging табеле (из директоријума или ZIP архиве)
docker compose run --rm app sh -c "python manage.py load_dbf --src_dir '/mnt/c/HramSP/dbf'"
docker compose run --rm app sh -c "python manage.py load_dbf --src_zip '/путања/до/crkva.zip'"

# Миграција крштења и венчања
docker compose run --rm app sh -c "python manage.py migracija_krstenja"
docker compose run --rm app sh -c "python manage.py migracija_vencanja"
```

Или користите скрипту за аутоматску миграцију:

```bash
./start.sh                    # Комплетна изградња (app + db + run)
./start.sh --app              # Само rebuild app контејнера
./start.sh --db               # Само rebuild базе (миграције + load_dbf + миграција података)
./start.sh --run              # Брзо покретање (load_dbf + krstenja/vencanja + up)
./start.sh --home             # Користи home WSL путању за DBF фајлове
./start.sh --zip /путања.zip  # Користи ZIP архиву за DBF фајлове
```

## Додатне белешке

### Проблем са дозволама код Докера

1. Коришћење Docker-а као не-root корисник:

   ```bash
   sudo groupadd docker
   sudo usermod -aG docker $USER
   ```

   Одјавите се и поново пријавите.

2. Подешавање дозвола за `docker.sock`:

   ```bash
   sudo chmod a+rw /var/run/docker.sock
   ```

### Структура пројекта

![Структура пројекта](docs/structure.png)

### Структура базе података

- [Дијаграм базе](https://dbdiagram.io/d/65319d89ffbf5169f00f803f)

## Доприноси

Молимо вас да прочитате наше [Смернице за доприносе](CONTRIBUTING.md) за детаље о нашем кодексу понашања и процесу подношења захтева за измене.

## Лиценца

Овај пројекат је лиценциран под [МИТ Лиценцом](LICENSE.md).

## Подршка

Ако наиђете на било какве проблеме или имате питања, молимо вас да [отворите питање](https://github.com/zenariworks/crkva/issues) на нашем GitHub репозиторијуму.


## Инсталација и покретанје програма у WSL-u

1. Инсталација апликације у WSL-у и свих потребних алата:

   ```bash
   # wsl - instalira default Ubuntu 24.04 distribuciju
   wsl --install
   wsl -l -v

   # python
   sudo apt update
   sudo apt upgrade -y
   sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   sudo apt update
   sudo apt install docker-ce -y
   sudo service docker start
   docker --version
   sudo groupadd docker
   sudo usermod -aG docker $USER
   sudo service docker restart

   # git
   sudo apt install git
   git --version

   # python virtual environment
   cd /home/sasa
   sudo apt install python3 -y
   sudo apt install python3-pip -y
   python3 --version
   pip3 --version
   sudo apt install python3-dev -y

   # kreiranje virtual environment-a u folderu '/home/sasa' i aktivacija
   sudo apt install python3.12-venv
   python3 -m venv .python_venv

   # paketi
   pip install pandas dbfread
   pip install --upgrade -r requirements.txt


   ```
2. Клоне пројекта и избор праве верзије тј. таг-а:

   ```bash
   cd /home/sasa
   git clone git@github.com:zenariworks/spc-registar.git crkva
   git checkout feature/hsp_v1.0

   ```

3. Креирање контејнера и покретанје апликације:

   ```bash
   cd /home/sasa/crkva

   # rebuild kontejnera aplikacije (samo ako je nesto menjano)
   ~/crkva$ ./start.sh --app

   # rebuild kontejnera baze
   ~/crkva$ ./start.sh --db

   # kompletna izgradnja (app + db + run)
   ~/crkva$ ./start.sh
   ~/crkva$ ./start.sh --app --db --run

   # brzo pokretanje (samo load_dbf + krstenja/vencanja + up)
   ~/crkva$ ./start.sh --run

   # korišćenje home WSL putanje za DBF fajlove
   ~/crkva$ ./start.sh --home

   # korišćenje ZIP arhive za DBF fajlove
   ~/crkva$ ./start.sh --zip /putanja/do/crkva.zip

   # za slucaj da app kontejner ne moze da se podigne, staticki web fajlovi se nalaze u 'data'
   # sudo chown sasa:sasa data -R

   # pokretanje aplikacije iz terminala na windows-u
   ./start-registar.bat

   ```
