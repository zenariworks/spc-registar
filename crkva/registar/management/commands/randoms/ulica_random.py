import random

from registar.models import Ulica


def dodaj_ili_dobavi_ulicu(svestenik_id):
    ulice_nazivi = [
        "Булевар Краља Александра",
        "Змаја од Ноћаја",
        "Војводе Степе",
        "Светог Саве",
        "Булевар мира",
        "Господска улица",
        "Титова улица",
        "Ферхадија",
        "Цара Душана",
        "Кнез Михаилова",
        "Маршала Тита",
        "Сарајевска",
        "Његошева",
        "Булевар ослобођења",
        "Булевар Михаила Пупина",
        "Булевар Деспота Стефана",
        "Васе Пелагића",
        "Таковска",
        "Јована Дучића",
        "Андрићева улица",
    ]

    naziv = random.choice(ulice_nazivi)

    ulica, created = Ulica.objects.get_or_create(
        naziv=naziv, defaults={"svestenik": svestenik_id}
    )

    return ulica
