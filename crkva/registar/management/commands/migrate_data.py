"""
Унифицирана команда за миграцију података.

Оркестрира целокупан процес миграције података кроз:
- --dummy: Генерише насумичне развојне податке
- --real: Увози из crkva.zip архиве
- --dry-run: Валидира без чувања у базу
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    """
    Унифицирана команда за миграцију података.
    """

    help = "Оркестрира миграцију података (--dummy или --real)"

    def add_arguments(self, parser):
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument(
            "--dummy",
            action="store_true",
            help="Генериши насумичне развојне податке",
        )
        mode_group.add_argument(
            "--real",
            nargs="?",
            const="crkva.zip",
            default=None,
            metavar="PATH",
            help="Увези из crkva.zip архиве (подразумевана путања: ./crkva.zip)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Валидирај без чувања у базу",
        )
        parser.add_argument(
            "--skip-staging",
            action="store_true",
            help="Прескочи load_dbf корак (користи постојеће staging табеле)",
        )
        parser.add_argument(
            "--keep-staging",
            action="store_true",
            help="Не брише staging табеле након миграције",
        )

    def handle(self, *args, **options):
        self.start_time = time.time()
        self.dry_run = options["dry_run"]

        # Валидација: тачно једна од --dummy или --real
        if options["dummy"]:
            mode = "dummy"
            self.stdout.write(
                self.style.NOTICE("\n" + "═" * 50)
            )
            self.stdout.write(
                self.style.NOTICE("  МИГРАЦИЈА ПОДАТАКА - РЕЖИМ: РАЗВОЈНИ (DUMMY)")
            )
            if self.dry_run:
                self.stdout.write(
                    self.style.WARNING("  (DRY-RUN: Без уписа у базу)")
                )
            self.stdout.write(
                self.style.NOTICE("═" * 50 + "\n")
            )
            results = self._migrate_dummy()

        elif options["real"]:
            mode = "real"
            zip_path = Path(options["real"])

            # Подразумевана путања је релативна према пројектном корену
            if not zip_path.is_absolute():
                # Претпоставка: crkva/ је у пројектном корену
                project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
                zip_path = project_root / zip_path

            # Провери постојање фајла
            if not zip_path.exists():
                raise CommandError(
                    f"Фајл није пронађен: {zip_path}\n"
                    f"Молимо обезбедите crkva.zip на путањи или користите: "
                    f"--real /путања/до/crkva.zip"
                )

            self.stdout.write(
                self.style.NOTICE("\n" + "═" * 50)
            )
            self.stdout.write(
                self.style.NOTICE("  МИГРАЦИЈА ПОДАТАКА - РЕЖИМ: ПРОДУКЦИОНИ (REAL)")
            )
            self.stdout.write(
                self.style.NOTICE(f"  Извор: {zip_path}")
            )
            if self.dry_run:
                self.stdout.write(
                    self.style.WARNING("  (DRY-RUN: Валидација без уписа)")
                )
            self.stdout.write(
                self.style.NOTICE("═" * 50 + "\n")
            )

            results = self._migrate_real(
                zip_path,
                skip_staging=options["skip_staging"],
                keep_staging=options["keep_staging"],
            )
        else:
            raise CommandError(
                "Морате навести један режим: --dummy или --real"
            )

        # Штампај извештај
        self._print_summary(results, mode)

        # Ако било какве грешке, подигни изузетак
        error_count = sum(1 for r in results if r["status"] == "error")
        if error_count > 0:
            raise CommandError(
                f"Миграција завршена са {error_count} грешком/ама."
            )

    def _migrate_real(
        self, zip_path: Path, skip_staging: bool, keep_staging: bool
    ) -> List[Dict]:
        """
        Миграција продукционих података из crkva.zip.
        """
        results = []

        # Укупно 12 корака (или 11 ако --skip-staging)
        total_steps = 11 if skip_staging else 12
        current_step = 0

        # Корак 1: load_dbf (осим ако --skip-staging)
        if not skip_staging:
            current_step += 1
            result = self._run_step(
                current_step,
                total_steps,
                "Учитавање DBF фајлова",
                "load_dbf",
                {"src_zip": zip_path},
            )
            results.append(result)

            # Ако load_dbf не успе, не настављај
            if result["status"] == "error":
                self.stdout.write(
                    self.style.ERROR(
                        "\n[ГРЕШКА] load_dbf није успео. Миграција се прекида."
                    )
                )
                return results

        # За --dry-run, само валидирај staging табеле
        if self.dry_run:
            return self._validate_staging_tables(results, skip_staging)

        # Корак 2: unosi (референтни подаци)
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Референтни подаци", "unosi", {}
            )
        )

        # Корак 3: unos_drzava
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Увоз држава", "unos_drzava", {}
            )
        )

        # Корак 4: unos_mesta
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Увоз места", "unos_mesta", {}
            )
        )

        # Корак 5: migracija_slava
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Миграција слава", "migracija_slava", {}
            )
        )

        # Корак 6: migracija_ulica
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Миграција улица", "migracija_ulica", {}
            )
        )

        # Корак 7: migracija_svestenika
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција свештеника",
                "migracija_svestenika",
                {},
            )
        )

        # Корак 8: migracija_parohijana
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција парохијана",
                "migracija_parohijana",
                {},
            )
        )

        # Корак 9: migracija_ukucana
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција укућана",
                "migracija_ukucana",
                {},
            )
        )

        # Корак 10: migracija_ukucana_parohijana
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција веза укућани-парохијани",
                "migracija_ukucana_parohijana",
                {},
            )
        )

        # Корак 11: migracija_krstenja
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција крштења",
                "migracija_krstenja",
                {},
            )
        )

        # Корак 12: migracija_vencanja
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Миграција венчања",
                "migracija_vencanja",
                {},
            )
        )

        # Обриши staging табеле ако није --keep-staging
        if not keep_staging:
            self._drop_staging_tables()

        return results

    def _validate_staging_tables(
        self, results: List[Dict], skip_staging: bool
    ) -> List[Dict]:
        """
        Валидација staging табела за --dry-run режим.
        """
        staging_tables = [
            "hsp_domacini",
            "hsp_krstenja",
            "hsp_slave",
            "hsp_svestenici",
            "hsp_ukucani",
            "hsp_ulice",
            "hsp_vencanja",
        ]

        self.stdout.write(
            self.style.WARNING("\n[DRY-RUN] Провера staging табела...\n")
        )

        with connection.cursor() as cursor:
            for table in staging_tables:
                cursor.execute(
                    f"SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_name = '{table}'"
                )
                exists = cursor.fetchone()[0] > 0

                if exists:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {table}: {row_count} редова"
                        )
                    )
                    results.append(
                        {
                            "step": f"Валидација: {table}",
                            "status": "ok",
                            "message": f"{row_count} редова",
                        }
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {table}: Не постоји"
                        )
                    )
                    results.append(
                        {
                            "step": f"Валидација: {table}",
                            "status": "warning",
                            "message": "Табела не постоји",
                        }
                    )

        self.stdout.write(
            self.style.WARNING(
                "\n[DRY-RUN] Миграција се не извршава. Подаци остају непромењени.\n"
            )
        )

        return results

    def _migrate_dummy(self) -> List[Dict]:
        """
        Генерисање развојних података.
        """
        results = []

        if self.dry_run:
            # За dry-run само листај команде
            steps = [
                "unosi - Референтни подаци",
                "unos_drzava - Генерисање држава",
                "unos_mesta - Генерисање места",
                "unos_ulica - Генерисање улица",
                "unos_adresa - Генерисање адреса",
                "unos_svestenika - Генерисање свештеника",
                "unos_krstenja - Генерисање крштења",
                "unos_vencanja - Генерисање венчања",
            ]

            self.stdout.write(
                self.style.WARNING("\n[DRY-RUN] Команде које би биле извршене:\n")
            )

            for i, step in enumerate(steps, 1):
                self.stdout.write(f"  {i}. {step}")
                results.append(
                    {
                        "step": step,
                        "status": "skipped",
                        "message": "Dry-run режим",
                    }
                )

            self.stdout.write(
                self.style.WARNING(
                    "\n[DRY-RUN] Подаци неће бити генерисани.\n"
                )
            )
            return results

        # Стварна генерација
        total_steps = 8
        current_step = 0

        # Корак 1: unosi
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Референтни подаци", "unosi", {}
            )
        )

        # Корак 2: unos_drzava
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање држава", "unos_drzava", {}
            )
        )

        # Корак 3: unos_mesta
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање места", "unos_mesta", {}
            )
        )

        # Корак 4: unos_ulica
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање улица", "unos_ulica", {}
            )
        )

        # Корак 5: unos_adresa
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање адреса", "unos_adresa", {}
            )
        )

        # Корак 6: unos_svestenika
        current_step += 1
        results.append(
            self._run_step(
                current_step,
                total_steps,
                "Генерисање свештеника",
                "unos_svestenika",
                {"broj": 5},  # Generate 5 random clergy members
            )
        )

        # Корак 7: unos_krstenja
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање крштења", "unos_krstenja", {}
            )
        )

        # Корак 8: unos_vencanja
        current_step += 1
        results.append(
            self._run_step(
                current_step, total_steps, "Генерисање венчања", "unos_vencanja", {}
            )
        )

        return results

    def _run_step(
        self,
        current: int,
        total: int,
        name: str,
        command: str,
        kwargs: Dict,
    ) -> Dict:
        """
        Извршава један корак миграције.
        """
        self.stdout.write(
            self.style.NOTICE(f"\n[{current}/{total}] {name}...")
        )

        try:
            call_command(command, **kwargs)
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ {name} - Успешно")
            )
            return {
                "step": name,
                "status": "ok",
                "message": "Успешно",
            }
        except CommandError as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ {name} - Грешка: {e}")
            )
            return {
                "step": name,
                "status": "error",
                "message": str(e),
            }
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ {name} - Непозната грешка: {e}")
            )
            return {
                "step": name,
                "status": "error",
                "message": str(e),
            }

    def _drop_staging_tables(self):
        """
        Брише staging табеле (hsp_*).
        """
        staging_tables = [
            "hsp_domacini",
            "hsp_krstenja",
            "hsp_slave",
            "hsp_svestenici",
            "hsp_ukucani",
            "hsp_ulice",
            "hsp_vencanja",
        ]

        self.stdout.write(
            self.style.NOTICE("\nБрисање staging табела...")
        )

        with connection.cursor() as cursor:
            for table in staging_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Обрисано: {table}")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Не могу обрисати {table}: {e}"
                        )
                    )

    def _print_summary(self, results: List[Dict], mode: str):
        """
        Штампа извештај о миграцији.
        """
        duration = time.time() - self.start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        self.stdout.write("\n")
        self.stdout.write("═" * 60)
        self.stdout.write(
            self.style.NOTICE("\n  ИЗВЕШТАЈ О МИГРАЦИЈИ\n")
        )
        self.stdout.write("═" * 60)

        # Статистика по статусу
        success_count = sum(1 for r in results if r["status"] == "ok")
        error_count = sum(1 for r in results if r["status"] == "error")
        warning_count = sum(1 for r in results if r["status"] == "warning")
        skipped_count = sum(1 for r in results if r["status"] == "skipped")

        self.stdout.write(f"\nРежим: {mode.upper()}")
        if self.dry_run:
            self.stdout.write(" (DRY-RUN)")
        self.stdout.write(f"\nУкупно корака: {len(results)}")
        self.stdout.write(f"\n  ✓ Успешно: {success_count}")
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"\n  ✗ Грешке: {error_count}")
            )
        if warning_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n  ⚠ Упозорења: {warning_count}")
            )
        if skipped_count > 0:
            self.stdout.write(f"\n  ○ Прескочено: {skipped_count}")

        self.stdout.write("\n\n" + "─" * 60)
        self.stdout.write(f"\n{'Корак':<40} {'Статус':<20}")
        self.stdout.write("\n" + "─" * 60)

        for i, result in enumerate(results, 1):
            step_name = result["step"]
            status = result["status"]

            if status == "ok":
                status_str = self.style.SUCCESS("✓ Успешно")
            elif status == "error":
                status_str = self.style.ERROR("✗ Грешка")
            elif status == "warning":
                status_str = self.style.WARNING("⚠ Упозорење")
            else:
                status_str = "○ Прескочено"

            self.stdout.write(f"\n{i}. {step_name:<37} {status_str}")

            # Прикажи поруке о грешкама
            if status in ("error", "warning") and result.get("message"):
                self.stdout.write(f"\n   └─ {result['message']}")

        self.stdout.write("\n" + "═" * 60)
        self.stdout.write(
            f"\nУкупно време: {minutes}m {seconds}s"
        )
        self.stdout.write("\n" + "═" * 60 + "\n")

        # Завршна порука
        if error_count == 0:
            if self.dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ Валидација успешна! Миграција се може покренути без --dry-run.\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✓ Миграција успешно завршена!\n"
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Миграција завршена са {error_count} грешком/ама.\n"
                )
            )
