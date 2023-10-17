# Црква св. Петке

[![Pylint](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/zenariworks/crkva/actions/workflows/pylint.yml)

## Садржај

- [Предуслови](#предуслови)
- [Први кораци](#први-кораци)
- [Производно окружење](#производно-окружење)
- [Развој и тестирање](#развој-и-тестирање)

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

- Учитавање тест података:

   ```bash
   docker compose run --rm app sh -c "python manage.py loaddata import_svestenik"
   ```

   Након овог корака, у базу је унет пример података о свештенику.
   Након покретања, могућ је и приказ ових података.

### 3. Креирање суперкорисника и покретање апликације

- Креирајте суперкорисника:

   ```bash
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

- Покретање апликације:

   ```bash
   docker compose up
   ```

   Админ панелу сада можете приступити на [localhost:8000/admin](localhost:8000/admin).
   Ако желите да видите учитан тест податак из корака 2, приступите [localhost:8000/svestenik/1](localhost:8000/svestenik/1).

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

   Приступите админ панелу на [127.0.0.1/admin](127.0.0.1/admin).

### 3. Креирање суперкорисника

   ```bash
   docker compose -f docker-compose-acc.yml run --rm app sh -c "python manage.py createsuperuser"
   ```

## Развој и тестирање

### 1. Покретање тестова

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
![Alt text](docs/structure.png)