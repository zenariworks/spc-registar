"""
Миграција домаћинстава и укућана из hsp_domacini + hsp_ukucani.
Креира Domacinstvo за сваког парохијана и Ukucanin за све чланове (преко Osoba).
Опција А: сваки укућанин има Osoba запис (чак и преминули).
"""

import re
from typing import Dict, Iterable

from django.db import connection
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Adresa, Domacinstvo, Osoba, Slava, Ukucanin, Ulica


class Command(MigrationCommand):
    help = "Миграција домаћинстава и укућана из hsp_domacini и hsp_ukucani"

    staging_tables = ["hsp_domacini", "hsp_ukucani"]
    target_model = Ukucanin  # за логовање

    def handle(self, *args, **kwargs) -> None:
        self.stdout.write("Чишћење постојећих података...")
        Ukucanin.objects.all().delete()
        Domacinstvo.objects.all().delete()

        # Не бришемо све Osobe, само оне које су биле креиране као укућани
        # Задржавамо Osobe из Krstenja/Vencanja
        self.stdout.write("Учитавам податке о домаћинима и укућанима...")

        # 1. Прво креирамо Parohijane (Osobe) и Domacinstva
        self._create_parohijani_and_domacinstva()

        # 2. Онда мигрирамо укућане
        records = self._prepare_ukucanin_records()
        created_count = self.migrate_in_batches(records, batch_size=1000)

        self.log_success(created_count, table_name="укућана")
        self._drop_staging_tables()

    def _clean_prezime(self, prezime: str) -> str:
        """Очисти презиме од префикса као што су 'р.', 'r.', 'рођена'."""
        if not prezime:
            return prezime
        prezime = re.sub(r"^р\.?\s*", "", prezime, flags=re.IGNORECASE).strip()
        prezime = re.sub(r"^r\.?\s*", "", prezime, flags=re.IGNORECASE).strip()
        prezime = re.sub(r"^рођена\s+", "", prezime, flags=re.IGNORECASE).strip()
        return prezime

    def _create_parohijani_and_domacinstva(self) -> None:
        """Креира Parohijan (Osoba) + Adresa + Domacinstvo за сваког домаћина."""
        created_parohijani = 0
        created_domacinstva = 0

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT "DOM_RBR", "DOM_IME", "DOM_RBRUL", "DOM_BROJ", "DOM_OZNAKA",
                       "DOM_STAN", "DOM_TELDIR", "DOM_TELMOB", "DOM_RBRSL",
                       "DOM_SLAVOD", "DOM_USKVOD", "DOM_NAPOM"
                FROM hsp_domacini
                WHERE "DOM_RBR" IS NOT NULL AND "DOM_IME" IS NOT NULL
                ORDER BY "DOM_RBR"
                """
            )

            for row in cursor.fetchall():
                (
                    uid_raw,
                    puno_ime,
                    ulica_uid_raw,
                    broj_ulice,
                    oznaka_ulice,
                    broj_stana,
                    telefon_fiksni,
                    telefon_mobilni,
                    slava_uid_raw,
                    slavska_vodica,
                    uskrsnja_vodica,
                    napomena,
                ) = row

                try:
                    parohijan_uid = int(uid_raw)
                    ulica_uid = int(ulica_uid_raw) if ulica_uid_raw else None
                    slava_uid = int(slava_uid_raw) if slava_uid_raw else None

                    if not ulica_uid:
                        self.log_skip(f"Парохијан UID {parohijan_uid}: нема улицу")
                        continue

                    # Parse full name
                    puno_ime = Konvertor.string(puno_ime).strip()
                    if not puno_ime:
                        continue

                    ime, prezime = (puno_ime.split(" ", 1) + [""])[:2]
                    prezime = self._clean_prezime(prezime)

                    if not ime or not prezime:
                        self.log_skip(
                            f"Парохијан UID {parohijan_uid}: непотпуно име '{puno_ime}'"
                        )
                        continue

                    # Create Adresa
                    try:
                        ulica = Ulica.objects.get(uid=ulica_uid)
                    except Ulica.DoesNotExist:
                        self.log_skip(
                            f"Парохијан UID {parohijan_uid}: улица {ulica_uid} не постоји"
                        )
                        continue

                    adresa = Adresa.objects.create(
                        broj=Konvertor.string(broj_ulice or ""),
                        sprat=None,
                        broj_stana=Konvertor.string(broj_stana or ""),
                        dodatak=Konvertor.string(oznaka_ulice or ""),
                        postkod=None,
                        primedba=Konvertor.string(napomena or ""),
                        ulica=ulica,
                    )

                    # Get or create Slava
                    slava = None
                    if slava_uid:
                        try:
                            slava = Slava.objects.get(uid=slava_uid)
                        except Slava.DoesNotExist:
                            pass

                    # Create or get Parohijan (Osoba)
                    osoba, created = Osoba.objects.get_or_create(
                        uid=parohijan_uid,
                        defaults={
                            "ime": ime,
                            "prezime": prezime,
                            "parohijan": True,
                            "adresa": adresa,
                            "slava": slava,
                            "tel_fiksni": Konvertor.string(telefon_fiksni or ""),
                            "tel_mobilni": Konvertor.string(telefon_mobilni or ""),
                            "slavska_vodica": slavska_vodica
                            and slavska_vodica.strip() == "D",
                            "uskrsnja_vodica": uskrsnja_vodica
                            and uskrsnja_vodica.strip() == "D",
                        },
                    )

                    if created:
                        created_parohijani += 1

                    # Create Domacinstvo
                    domacinstvo, created = Domacinstvo.objects.get_or_create(
                        domacin=osoba,
                        defaults={
                            "adresa": adresa,
                            "slava": slava,
                            "tel_fiksni": Konvertor.string(telefon_fiksni or ""),
                            "tel_mobilni": Konvertor.string(telefon_mobilni or ""),
                            "slavska_vodica": slavska_vodica
                            and slavska_vodica.strip() == "D",
                            "vaskrsnja_vodica": uskrsnja_vodica
                            and uskrsnja_vodica.strip() == "D",
                            "napomena": Konvertor.string(napomena or ""),
                        },
                    )

                    if created:
                        created_domacinstva += 1

                except Exception as e:
                    self.log_error(f"Грешка за домаћина UID {uid_raw}: {e}")
                    continue

        self.stdout.write(
            f"Креирано {created_parohijani} парохијана и {created_domacinstva} домаћинстава."
        )

    def _prepare_ukucanin_records(self) -> Iterable[dict | None]:
        """Припрема записе за Ukucanin (bulk_create)."""
        # Кеш: domacinstvo по uid парохијана
        domacinstva_cache: Dict[int, Domacinstvo] = {
            d.domacin.uid: d for d in Domacinstvo.objects.select_related("domacin")
        }

        query = 'SELECT "UK_RBRDOM", "UK_IME" FROM hsp_ukucani ORDER BY "UK_RBRDOM"'

        with connection.cursor() as cursor:
            cursor.execute(query)
            for uid_raw, ime_raw in cursor.fetchall():
                uid = int(uid_raw) if uid_raw else 0
                raw_ime = Konvertor.string(ime_raw or "").strip()

                if uid == 0 or uid not in domacinstva_cache:
                    # Skip orphaned records
                    yield None
                    continue

                if not raw_ime:
                    # Skip empty names
                    yield None
                    continue

                domacinstvo = domacinstva_cache[uid]
                prezime = domacinstvo.domacin.prezime

                preminuo = raw_ime.startswith("+")
                ime = raw_ime[1:].strip() if preminuo else raw_ime

                # Проналазимо или креирамо Osoba using base_migration helper
                osoba = self.get_or_create_osoba(ime, prezime, parohijan=False)

                if not osoba:
                    self.log_skip(f"Не могу креирати особу: {ime} {prezime}")
                    yield None
                    continue

                yield {
                    "domacinstvo": domacinstvo,
                    "osoba": osoba,
                    "ime_ukucana": ime,
                    "preminuo": preminuo,
                }

    def _drop_staging_tables(self):
        """Брише све staging табеле."""
        with connection.cursor() as cursor:
            for table in self.staging_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                self.stdout.write(
                    self.style.SUCCESS(f"Обрисана staging табела '{table}'.")
                )
