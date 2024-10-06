"""
Kod migracije podataka iz stare baza, svaki string koji je unet latinicom, konvertuje u cirilicu
"""

import random
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from registar.models import Hram, Narodnost, Parohijan, Veroispovest, Zanimanje


class ConvertUtils:

    @staticmethod
    def latin_to_cyrillic(text):
        # define a mapping from Serbian Latin to Cyrillic
        latin_to_cyrillic_map = {
            'a': 'а',
            'b': 'б',
            'c': 'ц',
            'č': 'ч',
            'd': 'д',
            'e': 'е',
            'f': 'ф',
            'g': 'г',
            'h': 'х',
            'i': 'и',
            'j': 'ј',
            'k': 'к',
            'l': 'л',
            'm': 'м',
            'n': 'н',
            'o': 'о',
            'p': 'п',
            'r': 'р',
            's': 'с',
            'š': 'ш',
            't': 'т',
            'u': 'у',
            'v': 'в',
            'z': 'з',
            'ž': 'ж',
            # Mapping special characters
            '{': 'ш',
            '}': 'ћ',

            '\\': 'Ђ',
            '|': 'ђ',

            'Q': 'Љ',
            'љ': 'љ',

            'W': 'Њ',
            'w': 'њ',

            '^': 'Ч',
            '~': 'ч',

            '@': 'Ž',
            '`': 'Ž',

            'A': 'А',
            'B': 'Б',
            'C': 'Ц',
            'Č': 'Ч',
            'D': 'Д',
            'E': 'Е',
            'F': 'Ф',
            'G': 'Г',
            'H': 'Х',
            'I': 'И',
            'J': 'Ј',
            'K': 'К',
            'L': 'Л',
            'M': 'М',
            'N': 'Н',
            'O': 'О',
            'P': 'П',
            'R': 'Р',
            'S': 'С',
            'Š': 'Ш',
            'T': 'Т',
            'U': 'У',
            'V': 'В',
            'Z': 'З',
            'Ž': 'Ж',
        }
    
        # Convert each character using the mapping
        converted_text = ''.join(latin_to_cyrillic_map.get(char, char) for char in text)
    
        return converted_text

