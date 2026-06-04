"""AJAX endpoints за брзе акције из модала (особа + адреса)."""

import logging

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from registar.models import Adresa, Hram, Osoba
from tenants.permissions import tenant_role_required

logger = logging.getLogger(__name__)


@tenant_role_required("osoba")
def brzi_unos_osobe(request):
    """AJAX endpoint за брзо креирање особе из модалног дијалога."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    ime = request.POST.get("ime", "").strip()
    prezime = request.POST.get("prezime", "").strip()
    pol = request.POST.get("pol", "").strip()

    if not ime or not prezime:
        return JsonResponse({"error": "Име и презиме су обавезни"}, status=400)

    # Validate pol against the field's declared choices so a hand-crafted
    # POST cannot store arbitrary single-character values that the UI later
    # treats as "unknown".
    valid_pol = {choice[0] for choice in Osoba._meta.get_field("pol").choices}
    if pol and pol not in valid_pol:
        return JsonResponse({"error": "Неважећа вредност за пол"}, status=400)

    # The parohijan flag comes from the modal's “парохијан” toggle, defaulted
    # per role (off for a kum / venčanje in-law usually from another parish, on
    # for дете/отац/мајка/женик/невеста). Absent → parishioner, for
    # backward compatibility. This lets an external kum be added with just
    # име+презиме and stay selectable in select2 without polluting the
    # parish roster.
    parohijan = (
        request.POST.get("parohijan", "1").strip().lower() in ("1", "true", "on", "да")
    )
    osoba = Osoba.objects.create(
        ime=ime, prezime=prezime, pol=pol or None, parohijan=parohijan
    )
    return JsonResponse({"id": osoba.uid, "text": str(osoba)})


@tenant_role_required("domacinstvo")
def brzi_izmena_adrese(request, uid):
    """AJAX endpoint за брзу измену постојеће адресе из модалног дијалога.

    Updates the address row identified by ``uid`` in place so that every
    Domacinstvo currently pointing at that row sees the fresh values
    without re-linking.
    """
    adresa = get_object_or_404(Adresa, uid=uid)
    # GET = pre-fill payload for the dropdown-pencil edit flow.
    if request.method == "GET":
        return JsonResponse(
            {
                "id": str(adresa.uid),
                "text": str(adresa),
                "ulica": adresa.ulica or "",
                "broj": adresa.broj or "",
                "broj_stana": adresa.broj_stana or "",
                "mesto": adresa.mesto or "",
            }
        )
    if request.method != "POST":
        return JsonResponse({"error": "GET or POST only"}, status=405)

    adresa.ulica = request.POST.get("ulica", "").strip()
    adresa.broj = request.POST.get("broj", "").strip()
    adresa.broj_stana = request.POST.get("broj_stana", "").strip()
    adresa.mesto = request.POST.get("mesto", "").strip()
    try:
        adresa.full_clean()
        adresa.save()
    except ValidationError as exc:
        return JsonResponse(
            {"error": "Невалидни подаци адресе.", "detail": exc.message_dict},
            status=400,
        )
    except IntegrityError:
        logger.exception("IntegrityError saving Adresa uid=%s", uid)
        return JsonResponse(
            {"error": "Адреса се не може сачувати због конфликта података."}, status=400
        )
    except DatabaseError:
        logger.exception("DatabaseError saving Adresa uid=%s", uid)
        return JsonResponse({"error": "Грешка у бази података."}, status=500)
    return JsonResponse({"id": str(adresa.uid), "text": str(adresa)})


@tenant_role_required("krstenje")
def brzi_unos_hrama(request):
    """AJAX endpoint за брзо креирање храма из модалног дијалога."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    naziv = request.POST.get("naziv", "").strip()
    mesto = request.POST.get("mesto", "").strip()
    if not naziv:
        return JsonResponse({"error": "Назив храма је обавезан"}, status=400)

    # get_or_create on (naziv, mesto) so repeated quick-adds of the same temple
    # return the existing row instead of piling up duplicates.
    hram, _ = Hram.objects.get_or_create(naziv=naziv, mesto=mesto)
    return JsonResponse({"id": str(hram.uid), "text": str(hram)})


@tenant_role_required("domacinstvo")
def brzi_unos_adrese(request):
    """AJAX endpoint за брзо креирање нове адресе из модалног дијалога.

    Permission mirrors brzi_izmena_adrese ("domacinstvo"). Адреса се дели
    међу особама/домаћинствима, па се исти нормализовани унос не дуплира —
    ако постоји, враћа се постојећи ред.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    ulica = request.POST.get("ulica", "").strip()
    broj = request.POST.get("broj", "").strip()
    broj_stana = request.POST.get("broj_stana", "").strip()
    mesto = request.POST.get("mesto", "").strip()
    if not ulica and not mesto:
        return JsonResponse({"error": "Унесите бар улицу или место."}, status=400)

    # Match the unique_adresa_normalized constraint columns case-insensitively
    # and reuse an existing row instead of erroring on a duplicate.
    existing = Adresa.objects.filter(
        ulica__iexact=ulica,
        broj__iexact=broj,
        broj_stana__iexact=broj_stana,
        mesto__iexact=mesto,
    ).first()
    if existing:
        return JsonResponse({"id": str(existing.uid), "text": str(existing)})

    adresa = Adresa(ulica=ulica, broj=broj, broj_stana=broj_stana, mesto=mesto)
    try:
        adresa.full_clean()
        adresa.save()
    except ValidationError as exc:
        return JsonResponse(
            {"error": "Невалидни подаци адресе.", "detail": exc.message_dict},
            status=400,
        )
    except IntegrityError:
        logger.exception("IntegrityError creating Adresa")
        return JsonResponse(
            {"error": "Адреса се не може сачувати због конфликта."}, status=400
        )
    return JsonResponse({"id": str(adresa.uid), "text": str(adresa)})
