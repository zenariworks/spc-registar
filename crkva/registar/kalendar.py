"""Заједничка логика календарских приказа (почетна + календар слава).

Извучено из `home_view.index` и `kalendar_view.kalendar` који су делили
исте константе (велики празници, ознаке дана, мапа поста) и изградњу ћелија.
"""

from registar.utils_fasting import tip_posta

# Ознаке дана у недељи (пон..нед), индекс = date.weekday()
WEEKDAY_LABELS = ["пон", "уто", "сре", "чет", "пет", "суб", "нед"]

# Велики (фиксни) празници: (месец, дан) → назив
MAJOR_FEASTS = {
    (1, 7): "Божић",
    (1, 19): "Богојављење",
    (8, 28): "Велика Госпојина",
    (9, 21): "Мала Госпојина",
    (11, 21): "Ваведење",
    (1, 27): "Свети Сава",
    (12, 19): "Свети Никола",
    (5, 19): "Ђурђевдан",
}

# Покретни велики празници — препознају се по кључним речима у називу славе
MAJOR_FEAST_KEYWORDS = ["васкрс", "спасовдан", "тројице", "духови", "вазнесењ"]

# Тип поста → CSS класа (за бојење ћелија)
FASTING_CSS_CLASS = {
    "вода": "water",
    "уље": "oil",
    "риба": "fish",
    "бели_мрс": "dairy",
}


def is_major_feast(d, day_slavas):
    """Да ли је дан велики празник — фиксни (MAJOR_FEASTS) или покретни (кључне речи)."""
    if (d.month, d.day) in MAJOR_FEASTS:
        return True
    return any(
        keyword in s.naziv.lower()
        for s in day_slavas
        for keyword in MAJOR_FEAST_KEYWORDS
    )


def build_day_cell(d, day_slavas, today):
    """Заједнички подаци ћелије за један дан.

    Приказ-специфичне кључеве (`day_label`, `is_yesterday`, `is_upcoming`,
    `is_placeholder`) додаје позивалац.
    """
    fasting_info = tip_posta(d)
    return {
        "date": d,
        "weekday_label": WEEKDAY_LABELS[d.weekday()],
        "je_post": fasting_info["je_post"],
        "fasting_type": fasting_info["type"],
        "fasting_class": FASTING_CSS_CLASS.get(fasting_info["type"]) or "",
        "fasting_display": fasting_info["display"],
        "fasting_description": fasting_info["description"],
        "slave": day_slavas,
        "fixed_slavas": [s for s in day_slavas if not s.pokretni],
        "moveable_slavas": [s for s in day_slavas if s.pokretni],
        "is_important": is_major_feast(d, day_slavas),
        "is_crveno_slovo": any(s.crveno_slovo for s in day_slavas),
        "is_today": d == today,
    }
