"""
Migration converter utilities for data migration from legacy DBF files.

This module provides the Konvertor class with static methods for converting
legacy data formats to modern Django model field values.
"""

import logging
from datetime import date


logger = logging.getLogger(__name__)


class Konvertor:
    """
    Utility class for converting legacy DBF data to Django model formats.

    Provides static methods for:
    - Latin to Cyrillic string conversion (including legacy HramSP encoding)
    - Safe integer conversion with defaults
    - Date parsing with zero-component handling
    - Full name splitting for Cyrillic names
    """

    @staticmethod
    def int(value, default=0):
        """
        Safely converts a string to an integer.

        Args:
            value: The value to convert (string or None)
            default: The default value to return if conversion fails (default: 0)

        Returns:
            int: The converted integer or the default value
        """
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Warning: '{value}' cannot be converted to an integer.")
            return default

    @staticmethod
    def string(text):
        """
        Converts Serbian Latin text to Cyrillic, including legacy HramSP encoding.

        Handles:
        - Standard Serbian Latin characters (a-z, č, ć, š, ž, đ)
        - Legacy HramSP special encoding (q→љ, w→њ, ]→Ћ, }→ћ, \\→Ђ, |→ђ, x→џ)
        - Already Cyrillic text (passes through unchanged)

        Args:
            text (str): The text to convert

        Returns:
            str: Converted Cyrillic text or empty string
        """
        if not text:
            return ""

        text = text.strip()
        if not text:
            return ""

        # Define mapping from Serbian Latin to Cyrillic (including legacy HramSP encoding)
        latin_to_cyrillic_map = {
            "A": "А",
            "a": "а",
            "B": "Б",
            "b": "б",
            "C": "Ц",
            "c": "ц",
            "Č": "Ч",
            "č": "ч",
            "D": "Д",
            "d": "д",
            "E": "Е",
            "e": "е",
            "F": "Ф",
            "f": "ф",
            "G": "Г",
            "g": "г",
            "H": "Х",
            "h": "х",
            "I": "И",
            "i": "и",
            "J": "Ј",
            "j": "ј",
            "K": "К",
            "k": "к",
            "L": "Л",
            "l": "л",
            "M": "М",
            "m": "м",
            "N": "Н",
            "n": "н",
            "O": "О",
            "o": "о",
            "P": "П",
            "p": "п",
            "R": "Р",
            "r": "р",
            "S": "С",
            "s": "с",
            "Š": "Ш",
            "š": "ш",
            "T": "Т",
            "t": "т",
            "U": "У",
            "u": "у",
            "V": "В",
            "v": "в",
            "Z": "З",
            "z": "з",
            "Ž": "Ж",
            "ž": "ж",
            # Mapping serbian cyrillic characters (legacy HramSP encoding)
            "Q": "Љ",
            "q": "љ",
            "W": "Њ",
            "w": "њ",
            "[": "Ш",
            "{": "ш",
            "\\": "Ђ",
            "|": "ђ",
            "^": "Ч",
            "~": "ч",
            "]": "Ћ",
            "}": "ћ",
            "@": "Ж",
            "`": "ж",
            "X": "Џ",
            "x": "џ",
        }

        # Convert each character using the mapping
        converted_text = "".join(latin_to_cyrillic_map.get(char, char) for char in text)

        return converted_text

    @staticmethod
    def date(y, m, d):
        """
        Create a date from year/month/day components, replacing zeros with default values.

        Legacy DBF files often have zero values for missing date components.
        This method replaces them with safe defaults:
        - year=0 → 1900
        - month=0 → 1
        - day=0 → 1

        Args:
            y: Year (int or None)
            m: Month (int or None)
            d: Day (int or None)

        Returns:
            date: A valid date object with zero components replaced
        """
        # Handle None values by treating them as zeros
        year = y if y is not None else 0
        month = m if m is not None else 0
        day = d if d is not None else 0

        # Replace zero components with defaults
        if year == 0:
            year = 1900
        if month == 0:
            month = 1
        if day == 0:
            day = 1

        return date(year, month, day)

    @staticmethod
    def split_name(full_name):
        """
        Split a full Cyrillic name into first and last name.

        Handles two patterns:
        1. Space-separated: "Петар Петровић" → ("Петар", "Петровић")
        2. CamelCase Cyrillic (no space): "СлавицаЋуковић" → ("Славица", "Ћуковић")

        Args:
            full_name (str): The full name to split

        Returns:
            tuple: (first_name, last_name) or (None, None) if splitting fails
        """
        import re

        if not full_name or not (full_name := full_name.strip()):
            return None, None

        # 1. Standard split by space
        if " " in full_name:
            first, last = full_name.split(maxsplit=1)
            return first, last

        # 2. Split by uppercase Cyrillic letter in the middle (CamelCase)
        if match := re.match(
            r"^([А-ЯЂЈЉЊЋЏа-яђјљњћџ]+?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$", full_name
        ):
            return match.group(1), match.group(2)

        # Can't split - return None, None
        return None, None
