# Миграција података из HramSP апликације

Овај документ описује процес миграције података из старе HramSP апликације
(DBF фајлови) у нову PostgreSQL базу. Од верзије 2.5.0 пројекат користи
**django-tenants** за изолацију по парохијама — сваки тенант има своју
Postgres шему, а свака се пуни својим скупом података.

## Брзи почетак (свеж увоз)

Сценарио: празна или свежа база, желимо да увеземо податке у подразумевани
тенант (`crkva_sv_petke_cukarica`). Цео ток траје око 4 минута.

```bash
# 1) Поставите шему и креирајте подразумеваног тенанта.
#    Креира public шему + crkva_sv_petke_cukarica шему са свим registar табелама.
python manage.py migrate_schemas

# 2) Учитајте DBF фајлове у staging табеле унутар тенант шеме.
python manage.py tenant_command load_dbf --schema=crkva_sv_petke_cukarica \
    --src_zip /путања/до/crkva.zip

# 3) Сејте lookup табеле (народности, вероисповести, занимања, епархије, славе).
python manage.py tenant_command unos_narodnosti      --schema=crkva_sv_petke_cukarica
python manage.py tenant_command unos_veroispovesti   --schema=crkva_sv_petke_cukarica
python manage.py tenant_command unos_zanimanja       --schema=crkva_sv_petke_cukarica
python manage.py tenant_command unos_eparhija        --schema=crkva_sv_petke_cukarica
python manage.py tenant_command unos_slava           --schema=crkva_sv_petke_cukarica

# 4) Покрените миграције за сваки модел.
python manage.py tenant_command migracija_svestenika        --schema=crkva_sv_petke_cukarica
python manage.py tenant_command migracija_ukucana_parohijana --schema=crkva_sv_petke_cukarica
python manage.py tenant_command migracija_krstenja          --schema=crkva_sv_petke_cukarica
python manage.py tenant_command migracija_vencanja          --schema=crkva_sv_petke_cukarica
```

После корак 4) сваки `migracija_*` команда брише своје staging табеле
(`hsp_*`) одмах по успешном завршетку.

### Проверa бројева

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

# 2) staging + lookup табеле + миграција (подразумевана шема)
S=crkva_sv_petke_cukarica
docker compose --profile standalone exec app \
  python manage.py tenant_command load_dbf --schema=$S --src_zip /tmp/crkva.zip
for c in unos_narodnosti unos_veroispovesti unos_zanimanja unos_eparhija; do
  docker compose --profile standalone exec app \
    python manage.py tenant_command $c --schema=$S
done
docker compose --profile standalone exec app \
  python manage.py tenant_command importuj_dbf --schema=$S
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

Затим пунте податке у нову шему истим током (`tenant_command ... --schema=crkva_sv_save_vracar`).

## DBF фајлови → staging → финалне табеле

| DBF фајл        | Staging табела   | Команда која пуни модел       |
| ---             | ---              | ---                             |
| HSPSVEST.DBF    | hsp_svestenici   | `migracija_svestenika`         |
| HSPDOMACINI.DBF | hsp_domacini     | `migracija_ukucana_parohijana` |
| HSPUKUCANI.DBF  | hsp_ukucani      | `migracija_ukucana_parohijana` |
| HSPULICE.DBF    | hsp_ulice        | (тренутно се не користи)       |
| HSPKRST.DBF     | hsp_krstenja     | `migracija_krstenja`           |
| HSPVENC.DBF     | hsp_vencanja     | `migracija_vencanja`           |
| HSPSLAVE.DBF    | hsp_slave        | `unos_slava`                    |

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

# 3) Покрените брзи почетак (1-4 кораке) изнад.
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

## Развојни подаци (dummy)

Команда `migrate_data --dummy` за насумичне развојне податке више не
постоји — њена функционалност је замењена реалним поновним увозом из
`crkva.zip`. Ако вам је потребно празно стање, само креирајте нови
тенант (видети горе) без покретања `tenant_command ... migracija_*`.
