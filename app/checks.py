"""Проверки готовой карточки: длины и сверка чисел с входными данными.

Идея простая и намеренно без «умных» слоёв: все числа и единицы измерения из
текста модели должны встречаться во входных данных. Что не встретилось - то
попадает в список расхождений, который видит контент-менеджер.
"""

import re

from app.config import DESCRIPTION_MAX, DESCRIPTION_MIN, TITLE_MAX

# Единицы, которые реально встречаются в карточках КИП.
UNITS = [
    "МПа", "кПа", "ГПа", "бар", "мбар", "кгс/см2", "кгс/см²", "атм", "мм вод.ст.",
    "°C", "°С", "К", "мм", "см", "м", "дюйм", "В", "кВ", "мА", "А", "Вт", "Гц",
    "кг", "г", "л/мин", "м3/ч", "м³/ч", "IP", "%", "ГОСТ", "Ом",
]

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(text: str) -> set:
    """Числа в тексте в нормализованном виде: 2,50 и 2.5 - одно и то же."""
    found = set()
    for raw in NUMBER_RE.findall(text or ""):
        value = raw.replace(",", ".")
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        found.add(value or "0")
    return found


def _units(text: str) -> set:
    lowered = (text or "").lower()
    return {u for u in UNITS if u.lower() in lowered}


def source_text(product) -> str:
    """Всё, что пришло на вход, одной строкой - эталон для сверки."""
    parts = [product.name, product.manufacturer, product.description]
    parts += [f"{k} {v}" for k, v in product.specs.items()]
    return "\n".join(p for p in parts if p)


def card_text(card: dict) -> str:
    """Весь текст, который сгенерировала модель, одной строкой."""
    parts = [card.get("seo_title", ""), card.get("seo_description", "")]
    for spec in card.get("specs") or []:
        if isinstance(spec, dict):
            parts.append(f"{spec.get('name', '')} {spec.get('value', '')}")
    parts += [str(q) for q in (card.get("search_queries") or [])]
    commercial = card.get("commercial") or {}
    if isinstance(commercial, dict):
        parts += [str(v) for v in commercial.values()]
    return "\n".join(parts)


def check_invented(product, card: dict) -> list:
    """Числа и единицы из вывода, которых нет во входных данных."""
    source = source_text(product)
    out = card_text(card)

    src_numbers, src_units = _numbers(source), _units(source)
    problems = []

    extra_numbers = sorted(_numbers(out) - src_numbers, key=lambda s: (len(s), s))
    if extra_numbers:
        problems.append("числа не из входных данных: " + ", ".join(extra_numbers))

    extra_units = sorted(_units(out) - src_units)
    if extra_units:
        problems.append("единицы измерения не из входных данных: " + ", ".join(extra_units))

    # Обратная сверка: значение характеристики из входа молча изменено или потеряно.
    specs_out = {
        str(s.get("name", "")).strip().lower(): str(s.get("value", ""))
        for s in (card.get("specs") or [])
        if isinstance(s, dict)
    }
    for key, value in product.specs.items():
        got = specs_out.get(key.strip().lower())
        if got is None:
            problems.append(f"характеристика «{key}» из входных данных не попала в карточку")
        elif _numbers(value) - _numbers(got):
            problems.append(
                f"значение «{key}» изменено: на входе «{value}», в карточке «{got}»"
            )
    return problems


def check_lengths(card: dict) -> list:
    """Требования задания к длинам заголовка и описания."""
    problems = []
    title = card.get("seo_title") or ""
    description = card.get("seo_description") or ""

    if not title.strip():
        problems.append("seo_title пустой")
    elif len(title) > TITLE_MAX:
        problems.append(f"seo_title содержит {len(title)} символов, допустимо до {TITLE_MAX}")

    if not description.strip():
        problems.append("seo_description пустой")
    elif len(description) < DESCRIPTION_MIN:
        problems.append(
            f"seo_description содержит {len(description)} символов, нужно не менее {DESCRIPTION_MIN}"
        )
    elif len(description) > DESCRIPTION_MAX:
        problems.append(
            f"seo_description содержит {len(description)} символов, нужно не более {DESCRIPTION_MAX}"
        )

    queries = card.get("search_queries") or []
    if not 3 <= len(queries) <= 5:
        problems.append(f"поисковых запросов {len(queries)}, нужно 3-5")
    return problems
