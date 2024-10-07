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
            'A': 'А', 'a': 'а',
            'B': 'Б', 'b': 'б',
            'C': 'Ц', 'c': 'ц',
            'Č': 'Ч', 'č': 'ч',
            'D': 'Д', 'd': 'д',
            'E': 'Е', 'e': 'е',
            'F': 'Ф', 'f': 'ф',
            'G': 'Г', 'g': 'г',
            'H': 'Х', 'h': 'х',
            'I': 'И', 'i': 'и',
            'J': 'Ј', 'j': 'ј',
            'K': 'К', 'k': 'к',
            'L': 'Л', 'l': 'л',
            'M': 'М', 'm': 'м',
            'N': 'Н', 'n': 'н',
            'O': 'О', 'o': 'о',
            'P': 'П', 'p': 'п',
            'R': 'Р', 'r': 'р',
            'S': 'С', 's': 'с',
            'Š': 'Ш', 'š': 'ш',
            'T': 'Т', 't': 'т',
            'U': 'У', 'u': 'у',
            'V': 'В', 'v': 'в',
            'Z': 'З', 'z': 'з',
            'Ž': 'Ж', 'ž': 'ж',
            
            # Mapping serbian cyrillic characters
            'Q': 'Љ', 'q': 'љ',
            'W': 'Њ', 'w': 'њ',
            '[': 'Ш', '{': 'ш',
            '\\': 'Ђ','|': 'ђ',
            '^': 'Ч', '~': 'ч',
            ']': 'Ћ', '}': 'ћ',
            '@': 'Ž', '`': 'Ž',
            'X': 'Џ', 'x': 'џ',
            
        }
    
        # Convert each character using the mapping
        converted_text = ''.join(latin_to_cyrillic_map.get(char, char) for char in text)
    
        return converted_text

