# Миграција података из HramSP апликације

Овај документ описује процес миграције података из старе HramSP апликације (DBF фајлови) у нову PostgreSQL базу података.

## Преглед

Подаци из старе апликације се налазе у DBF (dBASE) фајловима. Процес миграције се одвија у два корака:

1. **Учитавање DBF фајлова у staging табеле** - DBF фајлови се учитавају директно у PostgreSQL staging табеле са `hsp_` префиксом
2. **Миграција у финалне табеле** - Подаци из staging табела се трансформишу и уносе у Django моделе

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

## Команде за миграцију

### 1. Учитавање DBF фајлова (`load_dbf`)

Ова команда чита DBF фајлове и креира staging табеле у PostgreSQL:

```bash
# У Docker окружењу
docker compose run --rm app sh -c "python manage.py load_dbf --src_dir '/путања/до/dbf'"

# Локално (ван Docker-а)
python manage.py load_dbf --src_dir /путања/до/dbf
```

**Параметри:**
- `--src_dir` - Путања до директоријума са DBF фајловима (подразумевано: `/mnt/c/HramSP/dbf`)

**Напомена:** Команда ће пробати и велика и мала слова за имена фајлова (нпр. `HSPKRST.DBF` и `hspkrst.dbf`).

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

## Скрипте за аутоматизацију

### `build.sh` - Комплетна реконструкција базе

Ова скрипта ради комплетну реконструкцију базе података:

```bash
# Реконструкција само базе
./build.sh --db

# Реконструкција само апликације
./build.sh --app

# Обоје (подразумевано ако нема аргумената)
./build.sh
./build.sh --app --db

# За кућну WSL конфигурацију
./build.sh --db --home
```

### `start.sh` - Брзо покретање са миграцијом крштења/венчања

Ова скрипта учитава DBF фајлове, мигрира крштења и венчања, и покреће апликацију:

```bash
# Црквени лаптоп (подразумевано)
./start.sh

# Кућна WSL конфигурација
./start.sh -h
```

## Локације DBF фајлова

Скрипте подржавају две локације:

| Локација | Путања | Опција |
|----------|--------|--------|
| Црквени лаптоп | `/mnt/c/HramSP/dbf` | `-c` (подразумевано) |
| Кућна машина | `/mnt/e/projects/hram-svete-petke/old-app/HramSP/dbf` | `-h` или `--home` |

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

### Грешка: "DBF file not found"

Проверите да ли DBF фајлови постоје на наведеној путањи. Команда тражи фајлове и са великим и малим словима.

### Грешка: "Connection refused" при локалном покретању

Уверите се да је PostgreSQL контејнер покренут:

```bash
docker compose up -d db
```

### Грешка при миграцији (IntegrityError)

Миграционе команде бришу постојеће податке пре уноса нових. Ако добијете грешку, проверите:
- Да ли су претходне миграције (од којих зависи тренутна) успешно завршене
- Да ли staging табеле садрже исправне податке

## Техничке напомене

- DBF фајлови користе `cp1250` енкодинг (Windows Central European)
- Staging табеле користе `TEXT` тип за све колоне (једноставан приступ за staging)
- Свака миграција брише постојеће податке у циљној табели пре уноса
