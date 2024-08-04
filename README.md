# СПЦ Регистар

[![Pylint](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml)

## Опис пројекта

СПЦ Регистар је дигитални систем за вођење евиденције Српске Православне Цркве. Омогућава ефикасно управљање црквеним записима, укључујући крштења, венчања и друге важне догађаје.

## Садржај

- [Предуслови](#предуслови)
- [Први кораци](#први-кораци)
- [Производно окружење](#производно-окружење)
- [Развој и тестирање](#развој-и-тестирање)
- [Додатне белешке](#додатне-белешке)

## Предуслови

Пре него што започнете, потребно је да имате следеће софтвере инсталиране на вашем систему:

- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

Пратите упутства за инсталацију на званичним вебсајтовима.

## Први кораци

### 1. Инсталација и подешавање

   ```bash
   docker compose build
   ```

   У случају проблема са дозволама, погледајте [додатне белешке](#додатне-белешке).

### 2. Миграције базе података и учитавање тест података

- Креирање и примена миграција:

   ```bash
   docker compose run --rm app sh -c "python manage.py makemigrations && python manage.py migrate"
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

### 3. Креирање суперкорисника и покретање апликације

- Креирајте суперкорисника:

   ```bash
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

- Покретање апликације:

   ```bash
   docker compose up
   ```

   Сада можете приступити регистру на [localhost:8000](http://localhost:8000), а админ панелу на [localhost:8000/admin](http://localhost:8000/admin).

## Производно окружење

### 1. Подешавање конфигурационог фајла

   ```bash
   mv .example.env .acc.env
   ```

   Ажурирајте вредности променљивих у `.acc.env`.

### 2. Изградња и покретање апликације

   ```bash
   docker compose -f docker-compose-acc.yml build
   docker compose -f docker-compose-acc.yml up
   ```

   Приступите админ панелу на [127.0.0.1/admin](http://127.0.0.1/admin).

### 3. Креирање суперкорисника

   ```bash
   docker compose -f docker-compose-acc.yml run --rm app sh -c "python manage.py createsuperuser"
   ```

## Развој и тестирање

### Покретање тестова

   ```bash
   docker compose run --rm app sh -c "python manage.py test"
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
