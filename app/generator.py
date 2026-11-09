"""Сборка карточки: промпт -> модель -> проверки -> при нужде переписать."""

from app import checks, gemini, prompt
from app.config import LENGTH_RETRIES


def generate_card(product) -> dict:
    """Возвращает словарь: card (ответ модели), lengths, invented, gaps, attempts."""
    turns = [("user", prompt.build_user_message(product, product.gaps))]
    card, length_problems, raw = None, [], ""

    for attempt in range(LENGTH_RETRIES + 1):
        raw = gemini.generate(prompt.SYSTEM, turns)
        card = gemini.parse_card(raw)
        length_problems = checks.check_lengths(card)
        if not length_problems or attempt == LENGTH_RETRIES:
            break
        # Модель не удержала длины - показываем ей замеры и просим переписать.
        turns += [
            ("model", raw),
            ("user", prompt.build_length_fix(length_problems, raw)),
        ]

    return {
        "card": card,
        "lengths": length_problems,          # что осталось не по требованиям
        "invented": checks.check_invented(product, card),
        "gaps": product.gaps,                # чего не хватило во входных данных
        "attempts": attempt + 1,
        "title_length": len(card.get("seo_title") or ""),
        "description_length": len(card.get("seo_description") or ""),
    }
