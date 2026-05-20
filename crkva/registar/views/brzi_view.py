"""AJAX endpoints за брзе акције из модала (особа + адреса)."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from registar.models import Adresa, Osoba
from tenants.permissions import tenant_role_required


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

    osoba = Osoba.objects.create(
        ime=ime, prezime=prezime, pol=pol or None, parohijan=True
    )
    return JsonResponse({"id": osoba.uid, "text": str(osoba)})


@tenant_role_required("domacinstvo")
def brzi_izmena_adrese(request, uid):
    """AJAX endpoint за брзу измену постојеће адресе из модалног дијалога.

    Updates the address row identified by ``uid`` in place so that every
    Domacinstvo currently pointing at that row sees the fresh values
    without re-linking.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    adresa = get_object_or_404(Adresa, uid=uid)
    adresa.ulica = request.POST.get("ulica", "").strip()
    adresa.broj = request.POST.get("broj", "").strip()
    adresa.broj_stana = request.POST.get("broj_stana", "").strip()
    adresa.mesto = request.POST.get("mesto", "").strip()
    try:
        adresa.save()
    except Exception as exc:  # pragma: no cover - DB constraint surface
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"id": str(adresa.uid), "text": str(adresa)})
