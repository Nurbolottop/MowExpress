from django import template
from decimal import Decimal

register = template.Library()

ONES = [
    '', 'один', 'два', 'три', 'четыре', 'пять',
    'шесть', 'семь', 'восемь', 'девять', 'десять',
    'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
    'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать',
]
ONES_F = ['', 'одна', 'две']
TENS = [
    '', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят',
    'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто',
]
HUNDREDS = [
    '', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
    'шестьсот', 'семьсот', 'восемьсот', 'девятьсот',
]

THOUSANDS = ('тысяча', 'тысячи', 'тысяч')
MILLIONS = ('миллион', 'миллиона', 'миллионов')


def _plural(n, forms):
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    n = n % 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def _triplet(n, feminine=False):
    parts = []
    h = n // 100
    rest = n % 100
    if h:
        parts.append(HUNDREDS[h])
    if rest < 20:
        if rest > 0:
            if feminine and rest in (1, 2):
                parts.append(ONES_F[rest])
            else:
                parts.append(ONES[rest])
    else:
        t = rest // 10
        o = rest % 10
        parts.append(TENS[t])
        if o:
            if feminine and o in (1, 2):
                parts.append(ONES_F[o])
            else:
                parts.append(ONES[o])
    return ' '.join(parts)


def _int_to_words(n):
    if n == 0:
        return 'ноль'
    parts = []
    millions = n // 1_000_000
    thousands = (n % 1_000_000) // 1_000
    rest = n % 1_000

    if millions:
        parts.append(_triplet(millions))
        parts.append(_plural(millions, MILLIONS))
    if thousands:
        parts.append(_triplet(thousands, feminine=True))
        parts.append(_plural(thousands, THOUSANDS))
    if rest:
        parts.append(_triplet(rest))

    return ' '.join(parts)


@register.filter
def amount_in_words(value):
    """Convert a numeric amount to Russian words with rubles and kopecks."""
    try:
        d = Decimal(str(value))
    except Exception:
        return str(value)
    integer_part = int(d)
    fractional = int(round((d - integer_part) * 100))
    ruble_forms = ('рубль', 'рубля', 'рублей')
    kopeck_forms = ('копейка', 'копейки', 'копеек')
    words = _int_to_words(integer_part)
    words = words[0].upper() + words[1:]
    result = f"{words} {_plural(integer_part, ruble_forms)} {fractional:02d} {_plural(fractional, kopeck_forms)}"
    return result
