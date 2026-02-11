#!/usr/bin/env python3
"""
Convert slave.sql to Django JSON fixture format.
Adds crveno_slovo markers based on official red letter days.
"""

import json

# Red letter days from https://crkvenikalendar.rs/crvena-slova-u-2025/
# Format: (day, month): "exact naziv match (using 'in' operator)"
RED_LETTER_FIXED = {
    (7, 1): "Рождество Христово",
    (8, 1): "Сабор Пресвете Богородице",
    (9, 1): "првомученик и архиЂакон Стефан",  # Note: архиЂакон
    (14, 1): "Василије Велики",
    (19, 1): "Богојављење",
    (20, 1): "Јована Крститеља",
    (27, 1): "Свети Сава",
    (12, 2): "Три Јерарха",
    (15, 2): "Сретење",
    (7, 4): "Благовести",
    (12, 5): "Василије Острошки",
    (24, 5): "Кирило и Методије",
    (3, 6): "Константин",  # Свети цар Константин
    (28, 6): "Кнез Лазар",
    (7, 7): "Јована Претече",  # РоЂење светог Јована Претече
    (12, 7): "Петар и Павле",
    (2, 8): "пророк Илија",
    (19, 8): "Преображење",
    (28, 8): "Успење Пресвете Богородице",
    (11, 9): "Усековање",
    (21, 9): "Богородице",  # РоЂење Пресвете Богородице
    (27, 9): "Воздвижење",
    (27, 10): "Параскева",  # Преподобна мати Параскева
    (31, 10): "Лука",  # Свети апостол и јеванЂелист Лука
    (8, 11): "Димитрије",
    (21, 11): "Михајла",  # Сабор светог Архангела Михајла (note: Михајла not Михаила)
    (4, 12): "Ваведење",
    (19, 12): "Никола",
}

# Moveable feasts (Easter-dependent) that are red letter days
MOVEABLE_RED_LETTER = [
    "Улазак Господа",  # Palm Sunday
    "Велики петак",
    "Васкрс",  # Pascha
    "Васкрсни понедељак",
    "Васкрсни уторак",
    "Вазнесење",
    "Силазак Светог Духа",  # Pentecost
    "Духовски понедељак",
    "Духовски уторак",
]


def parse_fixture():
    """Parse slave.sql and convert to JSON fixture."""
    fixtures = []
    pk = 1

    with open("fixtures/slave.sql", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ';' not in line:
                continue

            parts = line.split(";")

            # Parse format: naziv;[opsti_naziv];dan,mesec
            naziv = parts[0]

            if len(parts) == 4 and ',' in parts[3]:
                # naziv;opsti1;opsti2;dan,mesec
                opsti_naziv = f"{parts[1]}, {parts[2]}"
                day, month = map(int, parts[3].split(','))
            elif len(parts) == 3 and ',' in parts[2]:
                # naziv;opsti_naziv;dan,mesec
                opsti_naziv = parts[1]
                day, month = map(int, parts[2].split(','))
            elif len(parts) == 2 and ',' in parts[1]:
                # naziv;dan,mesec
                opsti_naziv = ""
                day, month = map(int, parts[1].split(','))
            else:
                continue

            # Check if this is a red letter day
            crveno_slovo = False
            if (day, month) in RED_LETTER_FIXED:
                search_term = RED_LETTER_FIXED[(day, month)]
                if search_term in naziv:
                    crveno_slovo = True

            # Create fixture entry
            fixture = {
                "model": "registar.slava",
                "pk": pk,
                "fields": {
                    "naziv": naziv,
                    "opsti_naziv": opsti_naziv,
                    "dan": day,
                    "mesec": month,
                    "pokretni": False,
                    "offset_dani": None,
                    "offset_nedelje": None,
                    "post": False,
                    "post_od": None,
                    "post_do": None,
                    "crveno_slovo": crveno_slovo
                }
            }

            fixtures.append(fixture)
            pk += 1

    return fixtures


def add_moveable_feasts(fixtures, start_pk):
    """Add moveable (Easter-dependent) feasts."""
    moveable_feasts = [
        {
            "naziv": "Лазарева субота",
            "opsti_naziv": "",
            "offset_dani": -8,
            "crveno_slovo": False
        },
        {
            "naziv": "Улазак Господа Исуса Христа у Јерусалим",
            "opsti_naziv": "Цвети",
            "offset_dani": -7,
            "crveno_slovo": True
        },
        {
            "naziv": "Велики четвртак (Велико бденије)",
            "opsti_naziv": "",
            "offset_dani": -3,
            "crveno_slovo": False
        },
        {
            "naziv": "Велики петак",
            "opsti_naziv": "",
            "offset_dani": -2,
            "crveno_slovo": True
        },
        {
            "naziv": "Велика субота",
            "opsti_naziv": "",
            "offset_dani": -1,
            "crveno_slovo": False
        },
        {
            "naziv": "Васкрсење Господа Исуса Христа",
            "opsti_naziv": "Васкрс",
            "offset_dani": 0,
            "crveno_slovo": True
        },
        {
            "naziv": "Васкрсни понедељак",
            "opsti_naziv": "",
            "offset_dani": 1,
            "crveno_slovo": True
        },
        {
            "naziv": "Васкрсни уторак",
            "opsti_naziv": "",
            "offset_dani": 2,
            "crveno_slovo": True
        },
        {
            "naziv": "Вазнесење Господње",
            "opsti_naziv": "Спасовдан",
            "offset_dani": 39,
            "crveno_slovo": True
        },
        {
            "naziv": "Силазак Светог Духа на апостоле",
            "opsti_naziv": "Педесетница",
            "offset_dani": 49,
            "crveno_slovo": True
        },
        {
            "naziv": "Духовски понедељак",
            "opsti_naziv": "",
            "offset_dani": 50,
            "crveno_slovo": True
        },
        {
            "naziv": "Духовски уторак",
            "opsti_naziv": "",
            "offset_dani": 51,
            "crveno_slovo": True
        },
    ]

    pk = start_pk
    for feast in moveable_feasts:
        fixture = {
            "model": "registar.slava",
            "pk": pk,
            "fields": {
                "naziv": feast["naziv"],
                "opsti_naziv": feast["opsti_naziv"],
                "dan": None,
                "mesec": None,
                "pokretni": True,
                "offset_dani": feast["offset_dani"],
                "offset_nedelje": 0,
                "post": False,
                "post_od": None,
                "post_do": None,
                "crveno_slovo": feast["crveno_slovo"]
            }
        }
        fixtures.append(fixture)
        pk += 1

    return fixtures


def main():
    print("Converting slave.sql to JSON fixture...")

    # Parse fixed feasts
    fixtures = parse_fixture()
    print(f"Parsed {len(fixtures)} fixed feasts")

    # Add moveable feasts
    fixtures = add_moveable_feasts(fixtures, len(fixtures) + 1)
    print(f"Added {len(fixtures) - len(parse_fixture())} moveable feasts")

    # Count red letter days
    red_count = sum(1 for f in fixtures if f["fields"]["crveno_slovo"])
    print(f"Total red letter days: {red_count}")

    # Write to JSONL file (one JSON object per line)
    output_file = "fixtures/slave.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for fixture in fixtures:
            f.write(json.dumps(fixture, ensure_ascii=False) + '\n')

    print(f"\nWrote {len(fixtures)} entries to {output_file}")

    # Show sample
    print("\nSample entries:")
    for fixture in fixtures[:5]:
        fields = fixture["fields"]
        crveno = " [CRVENO]" if fields["crveno_slovo"] else ""
        pokretni = " [POKRETNI]" if fields["pokretni"] else ""
        print(f"  {fields['naziv']}{crveno}{pokretni}")


if __name__ == "__main__":
    main()
