"""Вызов Google Gemini через REST API: повторы, таймауты, понятные ошибки."""

import json
import time

import requests

from app.config import API_RETRIES, API_ROOT, API_TIMEOUT, api_key, model_name

# Схема ответа: модель обязана вернуть JSON нужной формы, парсить markdown не надо.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "seo_title": {"type": "string"},
        "seo_description": {"type": "string"},
        "specs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                "required": ["name", "value"],
            },
        },
        "search_queries": {"type": "array", "items": {"type": "string"}},
        "commercial": {
            "type": "object",
            "properties": {
                "fits": {"type": "string"},
                "tasks": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["fits", "tasks"],
        },
        "missing_data": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["seo_title", "seo_description", "specs", "search_queries", "commercial"],
}


class ApiError(RuntimeError):
    """Любая проблема на стороне LLM: сеть, лимиты, отказ, нечитаемый ответ."""


def available_models() -> list:
    """Список моделей аккаунта - подсказка, если имя модели не принято (404)."""
    try:
        resp = requests.get(f"{API_ROOT}/models", params={"key": api_key()}, timeout=30)
        resp.raise_for_status()
        return [
            m["name"].removeprefix("models/")
            for m in resp.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
    except requests.RequestException:
        return []


def generate(system: str, turns: list) -> str:
    """turns - история реплик: [("user", текст), ("model", текст), ...]. Вернёт текст ответа."""
    model = model_name()
    url = f"{API_ROOT}/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": role, "parts": [{"text": text}]} for role, text in turns],
        "generationConfig": {
            "temperature": 0.3,  # черновик карточки - не место для фантазии
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }

    last_error = None
    for attempt in range(1, API_RETRIES + 1):
        try:
            resp = requests.post(
                url, params={"key": api_key()}, json=body, timeout=API_TIMEOUT
            )
        except requests.RequestException as exc:
            last_error = f"сеть недоступна: {exc}"
        else:
            if resp.status_code == 200:
                return _extract_text(resp.json())
            if resp.status_code == 404:
                models = available_models()
                hint = ("Доступные модели: " + ", ".join(models[:12])) if models else ""
                raise ApiError(
                    f"Модель {model} недоступна для этого ключа. "
                    f"Укажите другую в GEMINI_MODEL. {hint}"
                )
            if resp.status_code in (401, 403):
                raise ApiError(
                    f"API отклонил ключ ({resp.status_code}). Проверьте GEMINI_API_KEY."
                )
            if resp.status_code == 400:
                raise ApiError(f"API отклонил запрос (400): {_error_message(resp)}")
            # 429 и 5xx - временные, повторяем.
            last_error = f"HTTP {resp.status_code}: {_error_message(resp)}"

        if attempt < API_RETRIES:
            time.sleep(2 ** attempt)  # 2 с, затем 4 с

    raise ApiError(f"Не удалось получить ответ за {API_RETRIES} попытки. Последняя ошибка - {last_error}")


def _error_message(resp) -> str:
    try:
        return resp.json().get("error", {}).get("message", resp.text[:300])
    except ValueError:
        return resp.text[:300]


def _extract_text(data: dict) -> str:
    """Достаём текст ответа и внятно жалуемся, если модель его не дала."""
    candidates = data.get("candidates") or []
    if not candidates:
        reason = data.get("promptFeedback", {}).get("blockReason", "причина не указана")
        raise ApiError(f"Модель не вернула ответ (блокировка: {reason}).")
    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ApiError(
            f"Пустой ответ модели (finishReason: {candidate.get('finishReason', 'нет')}). "
            "Возможно, ответ обрезан по лимиту токенов - повторите запрос."
        )
    return text


def parse_card(text: str) -> dict:
    """Ответ модели -> словарь. responseSchema обычно даёт чистый JSON, но не всегда."""
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ApiError(f"Модель вернула не-JSON ({exc.msg}). Начало ответа: {cleaned[:200]}")
    if not isinstance(data, dict):
        raise ApiError("Модель вернула JSON не того вида: ожидался объект карточки.")
    return data
