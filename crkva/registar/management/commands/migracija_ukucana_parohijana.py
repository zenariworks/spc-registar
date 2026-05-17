"""Миграција домаћинстава и укућана из hsp_domacini + hsp_ukucani.

Креира Osoba (домаћин), Adresa, Domacinstvo, и Ukucanin записе. За разлику
од miграcija_vencanja/krstenja, овде имамо два изворна table-а; код је
донекле линеаран, али сада дели исте помоћнике из `registar.migracija`.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

from typing import Dict, Iterable

from django.db import connection
from registar.management.commands.base_migration import MigrationCommand
from registar.migracija.address import find_or_create_adresa, warm_adresa_cache
from registar.migracija.helpers import cyr, extract_maiden
from registar.migracija.osoba_repo import (
    cache_osoba,
    find_or_create_osoba,
    lookup_osoba,
    warm_osoba_cache,
)
from registar.models import Domacinstvo, Osoba, Slava, Ukucanin


class Command(MigrationCommand):
    help = "Миграција домаћинстава и укућана из hsp_domacini и hsp_ukucani"

    staging_tables = ["hsp_domacini", "hsp_ukucani"]
    target_model = Ukucanin

    def handle(self, *args, **opts) -> None:
        self._dry_run = opts.get("dry_run", False)
        limit: int = opts.get("limit", 0) or 0

        if not self._dry_run:
            self.stdout.write("Чишћење постојећих података...")
            Ukucanin.objects.all().delete()
            Domacinstvo.objects.all().delete()

        # Warm in-memory caches so the hot loop hits dicts, not the DB.
        n_adr = warm_adresa_cache()
        n_os = warm_osoba_cache()
        self.stdout.write(f"Загрејано: {n_adr} адреса, {n_os} особа у кешу.")

        self.stdout.write("Учитавам називе улица из hsp_ulice...")
        self.ulice_cache = self._build_ulice_cache()
        self.stdout.write(f"Учитано {len(self.ulice_cache)} улица.")

        self.stdout.write("Креирам парохијане и домаћинства...")
        self._create_parohijani_and_domacinstva(limit=limit)

        if not self._dry_run:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT setval(pg_get_serial_sequence('osobe', 'uid'), "
                    "(SELECT COALESCE(MAX(uid), 1) FROM osobe))"
                )
            self.stdout.write("Ресетован аутоинкремент за осoбе.")

        self.stdout.write("Креирам укућане...")
        records = self.take(self._prepare_ukucanin_records(), limit)
        created = self.migrate_in_batches(
            records, batch_size=1000, dry_run=self._dry_run
        )
        self.log_success(created, table_name="укућана")
        if self._dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
        else:
            self._drop_staging_tables()

    # ---------------- Ulice cache ----------------

    def _build_ulice_cache(self) -> Dict[int, str]:
        cache: Dict[int, str] = {}
        with connection.cursor() as cursor:
            cursor.execute('SELECT "UL_SIFRA", "UL_NAZIV" FROM hsp_ulice')
            for sifra_raw, naziv_raw in cursor.fetchall():
                sifra = int(sifra_raw) if sifra_raw else 0
                naziv = cyr(naziv_raw or "")
                if sifra and naziv:
                    cache[sifra] = naziv
        return cache

    # ---------------- Domaćin pass ----------------

    def _create_parohijani_and_domacinstva(self, limit: int = 0) -> None:
        created_parohijani = 0
        created_domacinstva = 0
        self._dbf_uid_to_osoba_uid: Dict[int, int] = {}

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
            rows = cursor.fetchall()

        if limit:
            rows = rows[:limit]

        for row in rows:
            (
                uid_raw,
                puno_ime,
                ulica_uid_raw,
                broj_ulice,
                _oznaka_ulice,
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

                puno_ime = cyr(puno_ime)
                if not puno_ime:
                    continue

                ime, prezime_raw = (puno_ime.split(" ", 1) + [""])[:2]
                married_prezime, devojacko_prezime = extract_maiden(prezime_raw)
                # Domaćin records with only a "р.<maiden>" surname can't
                # be created without a married surname — fall back to the
                # maiden value so the row isn't lost, and the cleanup
                # command (popravi_devojacka) can re-split it later.
                prezime = married_prezime or devojacko_prezime
                if not ime or not prezime:
                    self.log_skip(
                        f"Парохијан UID {parohijan_uid}: непотпуно име '{puno_ime}'"
                    )
                    continue

                if self._dry_run:
                    created_parohijani += 1
                    created_domacinstva += 1
                    continue

                ulica_naziv = self.ulice_cache.get(ulica_uid, "") if ulica_uid else ""
                adresa = find_or_create_adresa(
                    ulica=ulica_naziv,
                    broj=cyr(str(broj_ulice or "")),
                    broj_stana=cyr(str(broj_stana or "")),
                    mesto="Чукарица",
                    sprat="",
                    primedba=cyr(napomena or ""),
                )

                slava = None
                if slava_uid:
                    slava = Slava.objects.filter(uid=slava_uid).first()

                tel_f = (telefon_fiksni or "").strip() or None
                tel_m = (telefon_mobilni or "").strip() or None

                # Name-based dedup: if an Osoba with this (ime, prezime) already
                # exists AND shares a safety signal (same canonical Adresa,
                # tel_fiksni, or tel_mobilni), reuse it instead of creating a
                # second row with a different uid.
                cached = lookup_osoba(ime, prezime)
                safe_to_merge = bool(cached) and (
                    (adresa is not None and cached.adresa_id == adresa.uid)
                    or (tel_f and cached.tel_fiksni and str(cached.tel_fiksni) == tel_f)
                    or (
                        tel_m
                        and cached.tel_mobilni
                        and str(cached.tel_mobilni) == tel_m
                    )
                )

                if safe_to_merge:
                    osoba = cached
                    updates = {}
                    if not osoba.parohijan:
                        updates["parohijan"] = True
                    if not osoba.adresa_id and adresa is not None:
                        updates["adresa"] = adresa
                    if not osoba.tel_fiksni and tel_f:
                        updates["tel_fiksni"] = tel_f
                    if not osoba.tel_mobilni and tel_m:
                        updates["tel_mobilni"] = tel_m
                    if not osoba.devojacko_prezime and devojacko_prezime:
                        updates["devojacko_prezime"] = devojacko_prezime
                    if updates:
                        Osoba.objects.filter(pk=osoba.pk).update(**updates)
                        osoba.refresh_from_db()
                else:
                    osoba, p_created = Osoba.objects.get_or_create(
                        uid=parohijan_uid,
                        defaults={
                            "ime": ime,
                            "prezime": prezime,
                            "devojacko_prezime": devojacko_prezime or None,
                            "parohijan": True,
                            "adresa": adresa,
                            "tel_fiksni": tel_f,
                            "tel_mobilni": tel_m,
                        },
                    )
                    if p_created:
                        created_parohijani += 1
                        # Only cache the FIRST occurrence of this name. If the
                        # cache already holds an Osoba with this name (cached
                        # was non-None above but we landed here because the
                        # safety check failed), keep the original cache entry.
                        if not lookup_osoba(ime, prezime):
                            cache_osoba(osoba)

                # Track DBF UID -> canonical Osoba so the ukucani pass can resolve
                # UK_RBRDOM even when we deduped onto an Osoba with a different uid.
                self._dbf_uid_to_osoba_uid[parohijan_uid] = osoba.uid

                _, d_created = Domacinstvo.objects.get_or_create(
                    domacin=osoba,
                    defaults={
                        "adresa": adresa,
                        "slava": slava,
                        "tel_fiksni": tel_f,
                        "tel_mobilni": tel_m,
                        "slavska_vodica": slavska_vodica
                        and slavska_vodica.strip() == "D",
                        "vaskrsnja_vodica": uskrsnja_vodica
                        and uskrsnja_vodica.strip() == "D",
                        "napomena": cyr(napomena or ""),
                    },
                )
                if d_created:
                    created_domacinstva += 1

            except Exception as e:  # pylint: disable=broad-except
                self.log_error(f"Грешка за домаћина UID {uid_raw}: {e}")
                continue

        self.stdout.write(
            f"Креирано {created_parohijani} парохијана и {created_domacinstva} домаћинстава."
        )

    # ---------------- Ukucanin pass ----------------

    def _prepare_ukucanin_records(self) -> Iterable[dict | None]:
        # Resolve via dbf-uid -> osoba-uid -> domacinstvo so deduped parohijani
        # still match their ukucani.
        osoba_to_dom: Dict[int, Domacinstvo] = {
            d.domacin.uid: d for d in Domacinstvo.objects.select_related("domacin")
        }
        domacinstva_cache: Dict[int, Domacinstvo] = {}
        for dbf_uid, osoba_uid in self._dbf_uid_to_osoba_uid.items():
            dom = osoba_to_dom.get(osoba_uid)
            if dom is not None:
                domacinstva_cache[dbf_uid] = dom

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "UK_RBRDOM", "UK_IME" FROM hsp_ukucani ORDER BY "UK_RBRDOM"'
            )
            for uid_raw, ime_raw in cursor.fetchall():
                uid = int(uid_raw) if uid_raw else 0
                raw_ime = cyr(ime_raw or "")

                if uid == 0 or uid not in domacinstva_cache or not raw_ime:
                    yield None
                    continue

                domacinstvo = domacinstva_cache[uid]
                prezime = domacinstvo.domacin.prezime

                preminuo = raw_ime.startswith("+")
                ime = raw_ime[1:].strip() if preminuo else raw_ime

                osoba = find_or_create_osoba(ime, prezime, parohijan=False)
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

    # ---------------- Cleanup ----------------

    def _drop_staging_tables(self) -> None:
        with connection.cursor() as cursor:
            for table in self.staging_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                self.stdout.write(
                    self.style.SUCCESS(f"Обрисана staging табела '{table}'.")
                )
