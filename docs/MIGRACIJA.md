# Миграција података из HramSP апликације

Овај документ описује процес миграције података из старе HramSP апликације (DBF фајлови) у нову PostgreSQL базу података.

## Брзи почетак

Миграција података се врши једном командом која аутоматски оркестрира све потребне кораке:

### За развој (тест подаци)

```bash
docker compose run --rm app sh -c "python manage.py migrate_data --dummy"
```

### За продукцију (стварни подаци)

```bash
# Прво покрени валидацију (dry-run)
docker compose run --rm app sh -c "python manage.py migrate_data --real --dry-run"

# Затим покрени стварну миграцију
docker compose run --rm app sh -c "python manage.py migrate_data --real"
```

### За продукцију (из специфичне путање)

```bash
docker compose run --rm app sh -c "python manage.py migrate_data --real /путања/до/crkva.zip"
```

## Преглед

Подаци из старе апликације се налазе у DBF (dBASE) фајловима. Процес миграције се одвија у два корака:

1. **Учитавање DBF фајлова у staging табеле** - DBF фајлови се учитавају директно у PostgreSQL staging табеле са `hsp_` префиксом
2. **Миграција у финалне табеле** - Подаци из staging табела се трансформишу и уносе у Django моделе

**Нова унифицирана команда `migrate_data` аутоматски извршава оба корака.**

## DBF фајлови и staging табеле

| DBF фајл | Staging табела | Опис |
|----------|----------------|------|
| HSPDOMACINI.DBF | hsp_domacini | Домаћини (парохијани) |
| HSPKRST.DBF | hsp_krstenja | Крштења |
| HSPSLAVE.DBF | hsp_slave | Славе |
| HSPSVEST.DBF | hsp_svestenici | Свештеници |
| HSPUKUCANI.DBF | hsp_ukucani | Укућани |
| HSPULICE.DBF | hsp_ulice | Улице |
| HSPVENC.DBF | hsp_vencanja | Венчања |

## Унифицирана команда `migrate_data` (препоручено)

Команда `migrate_data` је једноставан начин за извршавање целокупног процеса миграције. Она аутоматски покреће све потребне кораке у правом редоследу.

### Опције команде

| Опција | Опис |
|--------|------|
| `--dummy` | Генерише тест податке за развој (насумични подаци) |
| `--real [путања]` | Увози стварне податке из crkva.zip архиве. Подразумевана путања: `./crkva.zip` |
| `--dry-run` | Проверава податке без уписа у базу (валидација) |
| `--skip-staging` | Прескаче учитавање DBF фајлова (користи постојеће staging табеле) |
| `--keep-staging` | Не брише staging табеле након миграције (за инспекцију) |

**Напомена:** Морате навести или `--dummy` или `--real` (међусобно искључиве опције).

### Редослед миграције

#### За `--dummy` режим (развојни подаци):

1. `unosi` - Референтни подаци (вероисповести, родни односи, итд.)
2. `unos_drzava` - Генерисање држава
3. `unos_mesta` - Генерисање места
4. `unos_ulica` - Генерисање улица
5. `unos_adresa` - Генерисање адреса
6. `unos_svestenika` - Генерисање свештеника
7. `unos_krstenja` - Генерисање крштења
8. `unos_vencanja` - Генерисање венчања

#### За `--real` режим (продукциони подаци):

1. `load_dbf` - Учитавање DBF фајлова у staging табеле
2. `unosi` - Референтни подаци
3. `unos_drzava` - Увоз држава
4. `unos_mesta` - Увоз места
5. `migracija_slava` - Миграција слава
6. `migracija_ulica` - Миграција улица
7. `migracija_svestenika` - Миграција свештеника
8. `migracija_parohijana` - Миграција парохијана (домаћини)
9. `migracija_ukucana` - Миграција укућана
10. `migracija_ukucana_parohijana` - Миграција веза укућани-парохијани
11. `migracija_krstenja` - Миграција крштења
12. `migracija_vencanja` - Миграција венчања

**Важно:** Команда извршава кораке у овом редоследу јер постоје зависности између табела (нпр. крштења зависе од свештеника).

### Примери употребе

```bash
# Генерисање тест података за развој
docker compose run --rm app sh -c "python manage.py migrate_data --dummy"

# Провера тест података без уписа (dry-run)
docker compose run --rm app sh -c "python manage.py migrate_data --dummy --dry-run"

# Валидација продукционих података пре миграције
docker compose run --rm app sh -c "python manage.py migrate_data --real --dry-run"

# Стварна миграција из подразумеване путање (./crkva.zip)
docker compose run --rm app sh -c "python manage.py migrate_data --real"

# Миграција из специфичне путање
docker compose run --rm app sh -c "python manage.py migrate_data --real /path/to/crkva.zip"

# Поновно покретање миграције (користи постојеће staging табеле)
docker compose run --rm app sh -c "python manage.py migrate_data --real --skip-staging"

# Миграција са чувањем staging табела за инспекцију
docker compose run --rm app sh -c "python manage.py migrate_data --real --keep-staging"
```

### Извештај о миграцији

Команда приказује детаљан извештај након завршетка:

- Укупан број корака
- Статус сваког корака (✓ Успешно, ✗ Грешка, ⚠ Упозорење)
- Укупно време извршавања
- Детаљи о грешкама (ако их има)

---

## Напредне команде (за напредне кориснике)

**Напомена:** Команда `migrate_data` је препоручен начин за извршавање миграције. Појединачне команде испод су доступне за напредне кориснике који желе фину контролу над процесом или дебаговање специфичних корака.

Ако вам је потребна фина контрола над процесом миграције, можете користити појединачне команде:

### 1. Учитавање DBF фајлова (`load_dbf`)

Ова команда чита DBF фајлове и креира staging табеле у PostgreSQL. Подржава читање из директоријума или директно из ZIP архиве.

```bash
# Из директоријума (Docker)
docker compose run --rm app sh -c "python manage.py load_dbf --src_dir '/путања/до/dbf'"

# Из ZIP архиве (Docker)
docker compose run --rm app sh -c "python manage.py load_dbf --src_zip '/путања/до/crkva.zip'"

# Локално (ван Docker-а)
python manage.py load_dbf --src_dir /путања/до/dbf
python manage.py load_dbf --src_zip /путања/до/crkva.zip
```

**Параметри:**
- `--src_dir` - Путања до директоријума са DBF фајловима
- `--src_zip` - Путања до ZIP архиве са DBF фајловима

**Напомене:**
- Ако није наведен ни један параметар, подразумевана путања је `/mnt/c/HramSP/dbf`
- Команда ће пробати и велика и мала слова за имена фајлова (нпр. `HSPKRST.DBF` и `hspkrst.dbf`)
- ZIP архива може имати DBF фајлове у поддиректоријуму

### 2. Миграција појединачних табела

Након учитавања DBF фајлова, покрените миграционе команде редоследом:

```bash
# Основни подаци (потребно покренути прво)
python manage.py unosi
python manage.py unos_meseci
python manage.py unos_drzava

# Миграција из staging табела
python manage.py migracija_slava
python manage.py migracija_svestenika
python manage.py migracija_ulica
python manage.py migracija_parohijana
python manage.py migracija_ukucana
python manage.py migracija_krstenja
python manage.py migracija_vencanja
```

**Важно:** Редослед је битан јер неке табеле зависе од других (нпр. `migracija_krstenja` зависи од `migracija_svestenika`).

## Скрипта за аутоматизацију (`start.sh`)

Скрипта `start.sh` комбинује изградњу апликације, базе и покретање у једну команду:

```bash
./start.sh [--app] [--db] [--run] [--home] [--zip <путања>]
```

### Опције

| Опција | Опис |
|--------|------|
| `--app` | Rebuild app контејнера |
| `--db` | Rebuild базе (миграције + load_dbf + миграција података) |
| `--run` | Брзо покретање (load_dbf + krstenja/vencanja + up) |
| `--home` | Користи home WSL путању за DBF фајлове |
| `--zip <путања>` | Користи ZIP архиву за DBF фајлове |

Ако не наведете ниједну опцију, покреће се комплетна изградња (`--app --db --run`).

### Примери

```bash
# Комплетна изградња (app + db + run)
./start.sh

# Само rebuild app контејнера
./start.sh --app

# Само rebuild базе (миграције + load_dbf + миграција података)
./start.sh --db

# Брзо покретање (само load_dbf + krstenja/vencanja + up)
./start.sh --run

# За кућну WSL конфигурацију
./start.sh --home
./start.sh --db --home

# Коришћење ZIP архиве за DBF фајлове
./start.sh --zip /путања/до/crkva.zip
```

## Локације DBF фајлова

Скрипта подржава две локације:

| Локација | Путања | Опција |
|----------|--------|--------|
| Црквени лаптоп | `/mnt/c/HramSP/dbf` | (подразумевано) |
| Кућна машина | `/mnt/e/projects/hram-svete-petke/old-app/HramSP/dbf` | `--home` |

## Покретање миграције локално (ван Docker-а)

Ако желите да покренете миграцију локално (нпр. за дебаговање):

```bash
# Активирајте Python virtual environment
source .python_venv/bin/activate

# Инсталирајте зависности
pip install -r requirements.txt

# Учитајте DBF фајлове
python manage.py load_dbf --src_dir /путања/до/dbf

# Покрените миграције
python manage.py migracija_krstenja
python manage.py migracija_vencanja
```

**Напомена:** База података мора бити доступна (Docker контејнер `crkva-db-1` мора бити покренут).

## Решавање проблема

### Грешка: "Фајл није пронађен" (crkva.zip not found)

**Узрок:** Команда `migrate_data --real` не може да пронађе crkva.zip архиву.

**Решење:**
```bash
# Наведите пуну путању до архиве
docker compose run --rm app sh -c "python manage.py migrate_data --real /пуна/путања/до/crkva.zip"

# Или копирајте архиву у пројектни корен
cp /путања/до/crkva.zip ./crkva.zip
docker compose run --rm app sh -c "python manage.py migrate_data --real"
```

### Грешка: "DBF file not found" (load_dbf)

**Узрок:** DBF фајлови не постоје на наведеној путањи или немају очекивана имена.

**Решење:**
- Проверите да ли DBF фајлови постоје на наведеној путањи
- Команда тражи фајлове и са великим и малим словима (нпр. `HSPKRST.DBF` и `hspkrst.dbf`)
- Уверите се да ZIP архива садржи све потребне фајлове

### Грешка: "Connection refused" при локалном покретању

**Узрок:** PostgreSQL контејнер није покренут.

**Решење:**
```bash
docker compose up -d db
```

### Грешка при миграцији (IntegrityError)

**Узрок:** Постоји конфликт спољних кључева или дупликати података.

**Решење:**

- Проверите да ли су претходне миграције (од којих зависи тренутна) успешно завршене
- Проверите да ли staging табеле садрже исправне податке
- Покрените команду са `--dry-run` да валидирате податке пре миграције

### Колизија staging табела

**Узрок:** Staging табеле (hsp_*) већ постоје из претходне миграције.

**Решење:**
```bash
# Користи постојеће staging табеле (ако су исправне)
docker compose run --rm app sh -c "python manage.py migrate_data --real --skip-staging"

# Или ручно обриши staging табеле и покрени поново
docker compose run --rm app sh -c "python manage.py dbshell"
# У psql: DROP TABLE hsp_domacini, hsp_krstenja, hsp_slave, hsp_svestenici, hsp_ukucani, hsp_ulice, hsp_vencanja;
```

### Проблеми са енкодингом (српска ћирилица)

**Узрок:** DBF фајлови користе cp1250 енкодинг који можда није правилно конфигурисан.

**Решење:**
- Команда `migrate_data` аутоматски користи cp1250 енкодинг за DBF фајлове
- Ако видите чудне карактере, проверите да ли је исправна верзија dbfread библиотеке инсталирана

### Делимична миграција након грешке

**Узрок:** Миграција се прекинула током извршавања, неке табеле су увезене а друге нису.

**Решење:**
```bash
# 1. Провери staging табеле (да видиш да ли су учитане)
docker compose run --rm app sh -c "python manage.py migrate_data --real --dry-run"

# 2. Ако staging табеле постоје, прескочи load_dbf корак
docker compose run --rm app sh -c "python manage.py migrate_data --real --skip-staging"

# 3. Ако staging табеле не постоје или су некомплетне, покрени поново
docker compose run --rm app sh -c "python manage.py migrate_data --real"
```

## Техничке напомене

- DBF фајлови користе `cp1250` енкодинг (Windows Central European)
- Staging табеле користе `TEXT` тип за све колоне (једноставан приступ за staging)
- Свака миграција брише постојеће податке у циљној табели пре уноса
