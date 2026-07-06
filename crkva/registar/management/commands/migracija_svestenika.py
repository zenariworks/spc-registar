"""
Migracija tabele svestenika iz PostgreSQL staging tabele 'hsp_svestenici' u tabelu 'svestenici'
"""

from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.base_migration import MigrationCommand
from registar.models import Parohija, Svestenik
from registar.utils.konvertori import Konvertor


class Command(MigrationCommand):
    """
    Класа Ђанго команде за попуњавање табеле svestenika

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_svestenika"
    """

    help = "Migracija tabele svestenika iz PostgreSQL staging tabele 'hsp_svestenici'"
    staging_table = "hsp_svestenici"
    target_model = Svestenik

    def handle(self, *args, **opts):
        dry_run = opts.get("dry_run", False)
        limit = opts.get("limit", 0) or 0

        parsed_data = self._parse_data()
        if limit:
            parsed_data = parsed_data[:limit]
        created_count = 0

        self.stdout.write(f"Number of parsed_data: {len(parsed_data)}")
        for svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja in parsed_data:
            # Skip blank priests (uid=0 or empty name)
            if svestenik_id == 0 or not ime_prezime.strip():
                continue

            if dry_run:
                created_count += 1
                continue

            try:
                parohija_instance = None
                broj_parohije = self._convert_roman_to_integer(parohija)
                if broj_parohije is not None:
                    parohija_instance, _ = Parohija.objects.get_or_create(
                        naziv=broj_parohije
                    )
                elif parohija.strip():
                    self.log_warning(
                        f"Непозната парохија '{parohija.strip()}' за свештеника "
                        f"{ime_prezime.strip()} — уписујем без парохије."
                    )

                ime, prezime = (ime_prezime.strip().split(" ", 1) + [""])[:2]
                svestenik = Svestenik(
                    uid=svestenik_id,
                    ime=Konvertor.string(ime),
                    prezime=Konvertor.string(prezime),
                    mesto_rodjenja="",
                    datum_rodjenja=datum_rodjenja if datum_rodjenja else None,
                    zvanje=self._normalize_zvanje(Konvertor.string(zvanje)),
                    parohija=parohija_instance,
                )
                svestenik.save()

                created_count += 1

            except IntegrityError as e:
                self.log_error(e)

        self.log_success(created_count, "свештеници")

        if dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
            return

        # #333: свештеници се убацују са експлицитним uid (SV_RBR), па PK
        # секвенца остаје иза MAX(uid); накнадни унос (брзи додатак, форма)
        # би иначе пуцао на duplicate key. Поравнавамо секвенцу пре брисања
        # staging табеле.
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('svestenici', 'uid'), "
                "(SELECT COALESCE(MAX(uid), 1) FROM svestenici))"
            )
        self.stdout.write("Ресетован аутоинкремент за свештенике.")

        # Drop staging table after successful migration
        self.drop_staging_table()

    def _normalize_zvanje(self, raw: str) -> str:
        """Map a legacy DBF zvanje string to the canonical choice value.

        Source DBF stores zvanje in mixed case/spacing (e.g. "протонамесник",
        "протојереј - ставрофор"); the model choices are TitleCase with no
        spaces around the hyphen. We collapse spaces, drop letter-casing,
        and match against the choices in a case-insensitive way.
        """
        from registar.models.svestenik import zvanja

        if not raw:
            return raw or ""
        # Normalize whitespace, including around hyphens.
        norm = (
            " ".join(raw.split())
            .replace(" - ", "-")
            .replace(" -", "-")
            .replace("- ", "-")
        )
        target = norm.casefold()
        for key, _label in zvanja:
            if key.casefold() == target:
                return key
        return norm  # fallback: store the cleaned-up but unrecognized string

    def _convert_roman_to_integer(self, parohija):
        # Мапира римски број парохије (I/II/III) у "1"/"2"/"3".
        # Враћа None за непознату вредност (нпр. "IV") да не бисмо
        # креирали парохију назива "0" (#333).
        roman_to_int = {"I": "1", "II": "2", "III": "3", "1": "1", "2": "2", "3": "3"}
        parohija = parohija.rstrip() if parohija else ""
        return roman_to_int.get(parohija)

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_svestenici'.
        :return: Lista parsiranih podataka (svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja)
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "SV_RBR", "SV_IME", "SV_ZVANJE", "SV_PAROH", "SV_DATROD" FROM hsp_svestenici'
            )
            rows = cursor.fetchall()

            for row in rows:
                svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja = row
                parsed_data.append(
                    (
                        int(svestenik_id) if svestenik_id else 0,
                        ime_prezime or "",
                        zvanje or "",
                        parohija or "",
                        datum_rodjenja or "",
                    )
                )

        return parsed_data
