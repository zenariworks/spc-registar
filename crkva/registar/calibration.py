"""Конфигурација алата за калибрацију позиција поља на штампаним обрасцима.

Једно место истине за оба обрасца (крштеница/венчаница) — приказ дели
``registar/calibrate.html``, а поглед ``render_calibrate`` бира врсту преко
``CALIBRATIONS``. Вредности ``top/left/width/height`` су у милиметрима и служе
само као почетне; алат их синхронизује са живим ``--{prefix}-*`` из CSS-а.
"""
# pylint: disable=line-too-long

KRSTENJE_FIELDS = [
    {"id": "knjiga", "label": "Књига", "value": "1", "top": 14, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "strana", "label": "Страна", "value": "2", "top": 22, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "broj", "label": "Текући број", "value": "11", "top": 30, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "eparhija", "label": "Епархије", "value": "БЕОГРАДСКО-КАРЛОВАЧКЕ", "top": 46, "left": 26, "width": 80, "height": 6, "group": "header"},
    {"id": "hram", "label": "храма", "value": "Храм Свете Петке", "top": 54, "left": 26, "width": 75, "height": 6, "group": "header"},
    {"id": "mesto", "label": "у", "value": "Београду", "top": 54, "left": 110, "width": 45, "height": 6, "group": "header"},
    {"id": "godina", "label": "год", "value": "25", "top": 54, "left": 165, "width": 15, "height": 6, "group": "header"},
    {"id": "field1", "label": "1. Рођење датум", "value": "2025, јануар 15/2, 14ч", "top": 82, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field2", "label": "2. Место рођења", "value": "Београд", "top": 91, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field3", "label": "3. Крштење датум", "value": "2025, фебруар 10/јануар 28", "top": 104, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field4", "label": "4. Место крштења", "value": "Београд, Храм Св. Петке", "top": 119, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field5", "label": "5. Име и пол", "value": "МАРКО, мушко", "top": 129, "left": 99, "width": 100, "height": 6, "group": "table"},
    {"id": "field6", "label": "6. Родитељи", "value": "Петар Петровић, инж.\nМарија Петровић\nБеоград, Кн. Милоша 10\nправославна", "top": 135, "left": 99, "width": 100, "height": 30, "group": "table"},
    {"id": "field7", "label": "7. Дете по реду", "value": "прво", "top": 168, "left": 118, "width": 80, "height": 8, "group": "table"},
    {"id": "field8", "label": "8. Брачно", "value": "јесте", "top": 177, "left": 118, "width": 80, "height": 8, "group": "table"},
    {"id": "field9", "label": "9. Близанац", "value": "није", "top": 186, "left": 118, "width": 80, "height": 8, "group": "table"},
    {"id": "field10", "label": "10. Телесна мана", "value": "није", "top": 195, "left": 118, "width": 80, "height": 8, "group": "table"},
    {"id": "field11", "label": "11. Свештеник", "value": "прот. Саша Крстић", "top": 205, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field12", "label": "12. Кум", "value": "Јован Јовановић\nБеоград", "top": 217, "left": 99, "width": 100, "height": 12, "group": "table"},
    {"id": "field13", "label": "13. Домовник", "value": "", "top": 232, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "field14", "label": "14. Примедба", "value": "", "top": 242, "left": 99, "width": 100, "height": 8, "group": "table"},
    {"id": "footer_br", "label": "Бр.", "value": "11", "top": 264, "left": 14, "width": 15, "height": 6, "group": "footer"},
    {"id": "footer_godina", "label": "год", "value": "25", "top": 264, "left": 33, "width": 12, "height": 6, "group": "footer"},
    {"id": "footer_u", "label": "у", "value": "Београду", "top": 270, "left": 10, "width": 30, "height": 6, "group": "footer"},
    {"id": "footer_paroh", "label": "Парох", "value": "прот. Саша Крстић", "top": 264, "left": 145, "width": 55, "height": 6, "group": "footer"},
    {"id": "footer_parohija", "label": "парохије", "value": "Свете Петке", "top": 270, "left": 145, "width": 55, "height": 6, "group": "footer"},
]

VENCANJE_FIELDS = [
    {"id": "knjiga", "label": "Књига", "value": "1", "top": 12.5, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "strana", "label": "Страна", "value": "2", "top": 20.5, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "tekuci", "label": "Текући број", "value": "11", "top": 28.5, "left": 41, "width": 15, "height": 6, "group": "header"},
    {"id": "hram", "label": "храма", "value": "Храм Светог Ђорђа", "top": 53.9, "left": 121, "width": 50, "height": 6, "group": "header"},
    {"id": "eparhija", "label": "епархије", "value": "Београдско-Карловачке", "top": 53.2, "left": 27, "width": 55, "height": 6, "group": "header"},
    {"id": "mesto", "label": "у", "value": "Београду", "top": 60.8, "left": 27, "width": 50, "height": 6, "group": "header"},
    {"id": "godina", "label": "год", "value": "03", "top": 61.1, "left": 130, "width": 15, "height": 6, "group": "header"},
    {"id": "ime_zenika", "label": "1а) Женик", "value": "Немања, студент\n80. Нова 1\nправ. срб.", "top": 58, "left": 68, "width": 60, "height": 22, "group": "table"},
    {"id": "ime_neveste", "label": "1б) Невеста", "value": "Биљана, студент\n80. Нова 1\nправ. срб.", "top": 58, "left": 138, "width": 60, "height": 22, "group": "table"},
    {"id": "roditelji_zenika", "label": "2а) Родитељи женика", "value": "Дарко Поповић\nЛенка р. Арадовић", "top": 78, "left": 68, "width": 60, "height": 15, "group": "table"},
    {"id": "roditelji_neveste", "label": "2б) Родитељи невесте", "value": "Тодор Анђелић\nСлавица р. Јованов", "top": 78, "left": 138, "width": 60, "height": 15, "group": "table"},
    {"id": "rodjenje_zenika", "label": "3а) Рођење женика", "value": "1979, август 31 / 18\nУжице", "top": 96, "left": 68, "width": 60, "height": 15, "group": "table"},
    {"id": "rodjenje_neveste", "label": "3б) Рођење невесте", "value": "1978, новембар 22 / 9\nБеоград", "top": 96, "left": 138, "width": 60, "height": 15, "group": "table"},
    {"id": "brak_zenika", "label": "4а) Брак женика", "value": "1", "top": 114, "left": 68, "width": 60, "height": 10, "group": "table"},
    {"id": "brak_neveste", "label": "4б) Брак невесте", "value": "1", "top": 114, "left": 138, "width": 60, "height": 10, "group": "table"},
    {"id": "ispit", "label": "5) Испит", "value": "2003, април 27 / 14", "top": 128, "left": 68, "width": 130, "height": 8, "group": "table"},
    {"id": "datum_vencanja", "label": "6) Датум венчања", "value": "2003, мај 10 / април 27", "top": 138, "left": 68, "width": 130, "height": 8, "group": "table"},
    {"id": "mesto_hram", "label": "7) Место и храм", "value": "Београд, Храм Светог Ђорђа", "top": 148, "left": 68, "width": 130, "height": 8, "group": "table"},
    {"id": "svestenik", "label": "8) Свештеник", "value": "протојереј Саша Крстић", "top": 160, "left": 68, "width": 130, "height": 10, "group": "table"},
    {"id": "svedoci", "label": "9) Сведоци", "value": "Вељко Жарић, студент\nЈелена Павловић", "top": 174, "left": 68, "width": 130, "height": 15, "group": "table"},
    {"id": "razresenje", "label": "10) Разрешење", "value": "Не", "top": 192, "left": 68, "width": 130, "height": 12, "group": "table"},
    {"id": "primedba", "label": "11) Примедба", "value": "", "top": 210, "left": 68, "width": 130, "height": 8, "group": "table"},
    {"id": "footer_eparhija", "label": "епархије (потпис)", "value": "Београдске", "top": 221.7, "left": 99.5, "width": 50, "height": 6, "group": "footer"},
    {"id": "footer_hram", "label": "храма (потпис)", "value": "Храм Светог Ђорђа", "top": 229.9, "left": 123.4, "width": 55, "height": 6, "group": "footer"},
    {"id": "footer_datum", "label": "датум", "value": "15. јануар", "top": 257.4, "left": 10, "width": 30, "height": 6, "group": "footer"},
    {"id": "footer_godina", "label": "година", "value": "26", "top": 257.1, "left": 41.4, "width": 15, "height": 6, "group": "footer"},
    {"id": "footer_mesto", "label": "место", "value": "Београду", "top": 263.3, "left": 18.7, "width": 30, "height": 6, "group": "footer"},
    {"id": "footer_parohija", "label": "парохије", "value": "Светог Ђорђа", "top": 258.8, "left": 137, "width": 53, "height": 6, "group": "footer"},
    {"id": "footer_paroh", "label": "Парох", "value": "протојереј Саша Крстић", "top": 264.8, "left": 137, "width": 53, "height": 6, "group": "footer"},
]

CALIBRATIONS = {
    "krstenje": {
        "title": "Krstenica",
        "css": "registar/print/krstenica.css",
        "bg": "registar/slike/krstenica-nova.jpg",
        "prefix": "krst",
        "fields": KRSTENJE_FIELDS,
    },
    "vencanje": {
        "title": "Venčanica",
        "css": "registar/print/vencanica.css",
        "bg": "registar/slike/vencanica-nova.jpg",
        "prefix": "venc",
        "fields": VENCANJE_FIELDS,
    },
}