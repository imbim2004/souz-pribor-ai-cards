"""Настройки сервиса. Всё, что можно поменять без правки кода, живёт здесь."""

import os

from dotenv import load_dotenv

# .env читается, если он есть рядом с проектом; в репозиторий он не попадает.
load_dotenv()

# Модель по умолчанию. Если аккаунту она недоступна, код сам спросит у API
# список моделей и подскажет, что поставить в GEMINI_MODEL.
DEFAULT_MODEL = "gemini-3.5-flash"

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"

# Требования тестового задания к длинам.
TITLE_MAX = 70
DESCRIPTION_MIN = 800
DESCRIPTION_MAX = 1200

# Сколько раз пробуем позвать API при сетевой ошибке, 429 или 5xx (модель бывает
# перегружена и отвечает 503 - помогает пауза и повтор).
API_RETRIES = 4
API_TIMEOUT = 90  # секунд на один запрос

# Сколько раз просим модель переписать ответ, если не сошлись длины.
LENGTH_RETRIES = 2

# Поля, которые для карточки КИП-прибора считаем значимыми. Чего нет во входе,
# то попадает в отчёт о нехватке данных и в промпт как «данных нет».
EXPECTED_SPECS = [
    "диапазон измерений",
    "класс точности",
    "присоединение",
    "диаметр корпуса",
    "материал корпуса",
    "рабочая температура",
    "питание",
    "интерфейсы",
    "степень защиты",
]


class ConfigError(RuntimeError):
    """Сервис не настроен: нет ключа API."""


def api_key() -> str:
    """Ключ только из окружения: в коде и в репозитории его нет."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "Не задан GEMINI_API_KEY. Скопируйте .env.example в .env и впишите ключ "
            "или выполните: export GEMINI_API_KEY=..."
        )
    return key


def model_name() -> str:
    return os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
