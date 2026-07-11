# Миграција података из HramSP апликације

Овај документ описује процес миграције података из старе HramSP апликације
(DBF фајлови) у нову PostgreSQL базу. Од верзије 2.5.0 пројекат користи
**django-tenants** за изолацију по парохијама — сваки тенант има своју
Postgres шему, а свака се пуни својим скупом података.

## Брзи почетак (свеж увоз)

Сценарио: празна или свежа база, увозимо податке у подразумевани тенант
(`crkva_sv_petke_cukarica`). Цео ток траје око 4 минута.

```bash
# 1) Поставите шеме (public + тенант шеме са свим registar табелама).
python manage.py migrate_schemas

# 2) Цео DBF увоз једном командом.
python manage.py load_data --from dbf-zip:/путања/до/crkva.zip \
    --tenant crkva_sv_petke_cukarica
```

`load_data --from dbf-zip:<путања>` (или `--from dbf-dir:<директоријум>`) је
**фасада** — под задатом шемом покреће редом:

1. `load_dbf` — DBF фајлови → staging табеле (`hsp_*`),
2. `unos_sifarnika` — шифрарници (народности, вероисповести, занимања,
   епархије) + славе,
3. `importuj_dbf` — `migracija_*` + `popravi_*` + `mark_major_feasts`.

`--dry-run` приказује план без извршавања. Свака `migracija_*` команда брише
своје staging табеле (`hsp_*`) одмах по успешном завршетку.

### Ручни ток (нижи ниво)

Појединачни сидери (`unos_*`) и миграциони кораци (`migracija_*`) су
**интерни** — више нису засебне `manage.py` команде (позивају их `load_data`
и `importuj_dbf`). За ручно покретање остају две команде:

```bash
S=crkva_sv_petke_cukarica
python manage.py tenant_command load_dbf --schema=$S --src_zip /путања/до/crkva.zip
python manage.py tenant_command importuj_dbf --schema=$S
```

`importuj_dbf` покреће славе + `migracija_*` + `popravi_*` + обележавање
празника. Пуне шифрарнике сеје само `load_data` (преко `unos_sifarnika`); при
голом `importuj_dbf` шифрарници се допуњавају успут из података. За комплетан
увоз користи `load_data --from dbf-zip:… --tenant $S`.

### Провера бројева

```bash
python manage.py tenant_command shell --schema=crkva_sv_petke_cukarica -c "
from registar.models import Osoba, Krstenje, Vencanje, Domacinstvo, Svestenik
print('osobe       ', Osoba.objects.count())
print('parohijani  ', Osoba.objects.filter(parohijan=True).count())
print('krstenja    ', Krstenje.objects.count())
print('vencanja    ', Vencanje.objects.count())
print('domacinstva ', Domacinstvo.objects.count())
print('svestenici  ', Svestenik.objects.count())
"
```

Очекивани бројеви (за тренутни `crkva.zip`):

| Табела      | Бројeво |
| ---         | --- |
| osobe       | 18.787 |
| parohijani  | 1.850 |
| krstenja    | 3.536 |
| vencanja    | 233 |
| domacinstva | 1.849 |
| svestenici  | 21 |

## Увоз у Docker (стандалон) окружењу

Исти ток као горе, али команде иду кроз контејнер, а `crkva.zip` се прво копира
унутра (контејнер не види фајлове са хоста):

```bash
# 1) копирај архиву у контејнер апликације
docker compose --profile standalone cp crkva.zip app:/tmp/crkva.zip

# 2) цео увоз једном командом (подразумевана шема)
S=crkva_sv_petke_cukarica
docker compose --profile standalone exec app \
  python manage.py load_data --from dbf-zip:/tmp/crkva.zip --tenant $S
```

## Тенант архитектура

**SHARED** шема (`public`) садржи:
- `auth_user`, `auth_group`, `auth_permission` (Django auth)
- `django_session`, `django_admin_log`, `django_content_type`, `django_migrations`
- `tenants_tenant`, `tenants_domain`, `tenants_user_membership`

**TENANT** шеме (`crkva_sv_petke_cukarica`, `crkva_sv_nikole_zaandam`, …) свака садржи:
- `osobe`, `adrese`, `domacinstva`, `ukucani`
- `krstenja`, `vencanja`
- `parohije`, `crkvene_opstine`, `eparhije`, `hramovi`
- `slave`, `narodnosti`, `veroispovesti`, `zanimanja`
- `svestenici`
- Историјске табеле (`registar_historicalosoba`, …)

Сваки HTTP захтев пролази кроз `SessionTenantMiddleware`:
1. Резолвира тренутног тенанта (из сесије / чланства / подразумеваног).
2. Поставља `search_path` на `crkva_<...>, public`.
3. Враћа `search_path` на `public` на крају захтева.

Тиме сваки упит ка `Osoba` или `Krstenje` аутоматски иде у тенант шему.

## Креирање новог тенанта

**Конвенција имена шеме:** `crkva_sv_<заштитник>_<место>` — на пример
`crkva_sv_petke_cukarica` (Парохија Чукарица, храм Свете Петке) или
`crkva_sv_nikole_zaandam` (Парохија Амстердам, храм Светог Николаја).
Само ASCII слова, цифре и доње црте — Postgres шеме не дозвољавају
ћирилицу, размаке или цртице. `naziv` је кориснички приказ (ћирилица).

```bash
python manage.py shell -c "
from tenants.models import Tenant
t = Tenant(
    schema_name='crkva_sv_save_vracar',
    naziv='Парохија Врачар',
    parohija_naziv='Парохија Врачар',
    is_active=True,
)
t.save()  # auto_create_schema=True → шема се креира + све миграције се покрећу
"
```

Затим пунте податке у нову шему истим током
(`load_data --from dbf-zip:<путања> --tenant crkva_sv_save_vracar`).

## DBF фајлови → staging → финалне табеле

| DBF фајл        | Staging табела   | Команда која пуни модел       |
| ---             | ---              | ---                             |
| HSPSVEST.DBF    | hsp_svestenici   | `migracija_svestenika`         |
| HSPDOMACINI.DBF | hsp_domacini     | `migracija_ukucana_parohijana` |
| HSPUKUCANI.DBF  | hsp_ukucani      | `migracija_ukucana_parohijana` |
| HSPULICE.DBF    | hsp_ulice        | `migracija_ulice_svestenik` (#26) |
| HSPKRST.DBF     | hsp_krstenja     | `migracija_krstenja`           |
| HSPVENC.DBF     | hsp_vencanja     | `migracija_vencanja`           |

Славе не долазе из DBF-а — сеју се из `fixtures/slave.jsonl` командом
`unos_slava` (коју покреће `importuj_dbf`). Шифрарници (народности,
вероисповести, занимања, епархије) долазе из `fixtures/*.csv|jsonl` командом
`unos_sifarnika`.

## Поправка пре поновног увоза

Ако треба да направите свежи увоз преко постојеће базе:

```bash
# 1) Backup пре било чега.
PGPASSWORD=postgres pg_dump -h localhost -U postgres -d crkva_db \
    --no-owner --no-privileges \
    | gzip > /root/backups/pre_reimport_$(date +%Y%m%d_%H%M%S).sql.gz

# 2) Drop + recreate базу. (Деструктивно — обриши тренутне податке!)
PGPASSWORD=postgres dropdb -h localhost -U postgres crkva_db
PGPASSWORD=postgres createdb -h localhost -U postgres crkva_db

# 3) Покрените брзи почетак (1-2 кораке) изнад.
```

## Брисање тенанта

```bash
python manage.py shell -c "
from tenants.models import Tenant
t = Tenant.objects.get(schema_name='tenant_xxx')
# auto_drop_schema = False на моделу — мора експлицитно
from django_tenants.utils import schema_exists
from django.db import connection
if schema_exists('tenant_xxx'):
    with connection.cursor() as c:
        c.execute('DROP SCHEMA tenant_xxx CASCADE')
t.delete()
"
```

## Развојни подаци (mock / dummy)

За насумичне развојне податке (не из `crkva.zip`) користите `load_data
--from mock`:

```bash
python manage.py load_data --from mock --tenant crkva_sv_petke_cukarica --count 100
```

Ово сеје шифрарнике + адресе + свештенике + парохијане + домаћинства +
крштења + венчања (реалистичним mock генераторима). За само један тип
користи `--only` (нпр. `load_data --from mock --only unos_svestenika
--tenant <šema>`). Ако вам је потребно празно стање, само креирајте нови
тенант (видети горе) без покретања увоза.
