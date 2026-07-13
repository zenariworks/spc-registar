"""
Migracija tabele svestenika iz PostgreSQL staging tabele 'hsp_svestenici' u tabelu 'svestenici'
"""

from django.db import connection
from django.db.utils import IntegrityError
from registar.models import Parohija, Svestenik
from registar.utils.preslovljavanje import Konvertor
from registar.uvoz.osnovno import MigrationCommand


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
        self.zabrani_nad_public()
        dry_run = opts.get("dry_run", False)
        limit = opts.get("limit", 0) or 0

        parsed_data = self._parsiraj()
        if limit:
            parsed_data = parsed_data[:limit]
        created_count = 0

        self.stdout.write(f"Number of parsed_data: {len(parsed_data)}")
        for (
            svestenik_id,
            ime_prezime,
            zvanje,
            parohija_oznaka,
            datum_rodjenja,
        ) in parsed_data:
            # Skip blank priests (uid=0 or empty name)
            if svestenik_id == 0 or not ime_prezime.strip():
                continue

            if dry_run:
                created_count += 1
                continue

            try:
                parohija = None
                broj_parohije = self._konvertuj_rimski(parohija_oznaka)
                if broj_parohije is not None:
                    parohija, _ = Parohija.objects.get_or_create(naziv=broj_parohije)
                elif parohija_oznaka.strip():
                    self.log_warning(
                        f"Непозната парохија '{parohija_oznaka.strip()}' за свештеника "
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
                    parohija=parohija,
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

    def _konvertuj_rimski(self, oznaka):
        """
        Мапира римски број парохије (I/II/III) у "1"/"2"/"3".
        Враћа None за непознату вредност (нпр. "IV") да не бисмо
        креирали парохију назива "0" (#333).
        """
        cifra = {"I": "1", "II": "2", "III": "3", "1": "1", "2": "2", "3": "3"}
        rimski_broj = oznaka.rstrip() if oznaka else ""
        return cifra.get(rimski_broj)

    def _parsiraj(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_svestenici'.
        :return: Lista parsiranih podataka (svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja)
        """
        parsirano = []
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "SV_RBR", "SV_IME", "SV_ZVANJE", "SV_PAROH", "SV_DATROD" FROM hsp_svestenici'
            )
            zapisi = cursor.fetchall()

            for zapis in zapisi:
                svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja = zapis
                parsirano.append(
                    (
                        int(svestenik_id) if svestenik_id else 0,
                        ime_prezime or "",
                        zvanje or "",
                        parohija or "",
                        datum_rodjenja or "",
                    )
                )

        return parsirano
