"""Табеларни приказ спискова (#378).

Подразумевани приказ остаје картице; `?prikaz=tabela` рендерује класичну
табелу (једно поље по колони) са заглављем колона по типу записа. AJAX захтев
(бесконачни скрол) враћа само редове (`<tr class="stavka-red">`), без оквира.
"""

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Hram, Krstenje, Osoba, Vencanje

User = get_user_model()
AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

KOLONE = {
    "parohijani": ["Име", "Презиме", "Пол", "Датум рођења", "Адреса"],
    "domacinstva": [
        "Домаћин",
        "Адреса",
        "Тел. фиксни",
        "Тел. мобилни",
        "Слава",
        "Бр. укућана",
    ],
    "vencanja": ["Датум", "Женик", "Невеста", "Презиме женика", "Храм"],
    "krstenja": ["Датум", "Име детета", "Презиме оца", "Отац", "Мајка", "Храм"],
}


class PrikazTabelaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hram = Hram.objects.create(naziv="Тест Храм")
        cls.dete = Osoba.objects.create(ime="Лука", prezime="Лукић", parohijan=True)
        cls.otac = Osoba.objects.create(ime="Марко", prezime="Лукић")
        cls.majka = Osoba.objects.create(ime="Мара", prezime="Марић")
        cls.zenik = Osoba.objects.create(ime="Ђорђе", prezime="Ђурић")
        cls.nevesta = Osoba.objects.create(ime="Јана", prezime="Јанић")
        cls.domacin = Osoba.objects.create(ime="Ана", prezime="Анић", parohijan=True)
        Domacinstvo.objects.create(domacin=cls.domacin)
        Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            hram=cls.hram,
            dete=cls.dete,
            otac=cls.otac,
            majka=cls.majka,
        )
        Vencanje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 6, 1),
            hram=cls.hram,
            zenik=cls.zenik,
            nevesta=cls.nevesta,
        )

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_default_prikaz_is_cards(self):
        """Без параметра prikaz — картице, без табеле."""
        for name in KOLONE:
            body = self.client.get(reverse(name)).content.decode()
            self.assertIn('<ul class="spisak"', body, msg=name)
            self.assertNotIn("spisak-tabela", body, msg=name)

    def test_tabela_renders_table_with_headers(self):
        """prikaz=tabela рендерује табелу са тачним заглављима колона и редовима."""
        for name, kolone in KOLONE.items():
            body = self.client.get(reverse(name) + "?prikaz=tabela").content.decode()
            self.assertIn('<table class="spisak-tabela"', body, msg=name)
            self.assertIn('<tr class="stavka-red"', body, msg=name)
            for kolona in kolone:
                self.assertIn(
                    f'<th scope="col">{kolona}</th>', body, msg=f"{name}:{kolona}"
                )

    def test_toggle_present_with_active_table_state(self):
        """Прекидач приказа постоји; у режиму табеле „Табела" је активна опција."""
        body = self.client.get(
            reverse("parohijani") + "?prikaz=tabela"
        ).content.decode()
        self.assertIn("prikaz-prekidac", body)
        self.assertRegex(
            body, r"prikaz-prekidac__dugme is-active[^>]*>[^<]*<i[^>]*></i>\s*Табела"
        )

    def test_toggle_preserves_search_query(self):
        """Хреф прекидача чува претрагу (search) уместо да је одбаци."""
        body = self.client.get(
            reverse("parohijani") + "?prikaz=tabela&search=Лук"
        ).content.decode()
        self.assertIn("search=%D0%9B", body)

    def test_ajax_tabela_returns_rows_only(self):
        """AJAX + prikaz=tabela враћа само редове — без <table>/<ul> оквира."""
        body = self.client.get(
            reverse("parohijani") + "?prikaz=tabela", **AJAX
        ).content.decode()
        self.assertIn('<tr class="stavka-red"', body)
        self.assertNotIn("<table", body)
        self.assertNotIn("<ul", body)

    def test_ajax_cards_returns_li_not_rows(self):
        """AJAX без табеле враћа картице (<li class="stavka">), без редова табеле."""
        body = self.client.get(reverse("parohijani"), **AJAX).content.decode()
        self.assertIn('<li class="stavka"', body)
        self.assertNotIn("stavka-red", body)
