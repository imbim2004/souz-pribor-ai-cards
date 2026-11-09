"""Разбор и нормализация входных данных о приборе."""

import json
from dataclasses import dataclass, field

from app.config import EXPECTED_SPECS


class InputError(ValueError):
    """Вход непригоден: это не JSON, не объект или нет названия прибора."""


@dataclass
class Product:
    name: str
    manufacturer: str
    specs: dict          # только непустые характеристики
    description: str
    empty_specs: list = field(default_factory=list)   # ключи пришли, но пустые
    missing_specs: list = field(default_factory=list)  # ожидаемых ключей нет вовсе
    missing_fields: list = field(default_factory=list)  # нет производителя/описания

    @property
    def gaps(self) -> list:
        """Единый список того, чего не хватает — для отчёта и для промпта."""
        return self.missing_fields + sorted(set(self.empty_specs + self.missing_specs))


def _clean(value) -> str:
    """Любое значение к строке; пустое — к пустой строке."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_clean(v) for v in value if _clean(v))
    if isinstance(value, bool):
        return "да" if value else "нет"
    return str(value).strip()


def parse_json(raw: str) -> dict:
    """Текст -> словарь, с понятным сообщением при битом JSON."""
    if not raw or not raw.strip():
        raise InputError("Входные данные пусты: ожидается JSON-объект с полем name.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"Некорректный JSON: {exc.msg} (строка {exc.lineno}, символ {exc.colno}).")
    if not isinstance(data, dict):
        raise InputError("Ожидается JSON-объект вида {\"name\": ..., \"specs\": {...}}.")
    return data


def build(data: dict) -> Product:
    """Словарь -> Product. Пустые и отсутствующие поля фиксируются, а не выдумываются."""
    if not isinstance(data, dict):
        raise InputError("Ожидается JSON-объект.")

    name = _clean(data.get("name"))
    if not name:
        raise InputError("Поле name обязательно: без названия прибора карточку не собрать.")

    raw_specs = data.get("specs") or {}
    if not isinstance(raw_specs, dict):
        raise InputError("Поле specs должно быть объектом: {\"характеристика\": \"значение\"}.")

    specs, empty = {}, []
    for key, value in raw_specs.items():
        key = _clean(key)
        value = _clean(value)
        if not key:
            continue
        # «данных нет», «-», «n/a» во входе — это тоже отсутствие данных.
        if not value or value.lower() in {"-", "—", "n/a", "na", "нет данных", "данных нет"}:
            empty.append(key)
        else:
            specs[key] = value

    manufacturer = _clean(data.get("manufacturer"))
    description = _clean(data.get("description"))

    missing_fields = []
    if not manufacturer:
        missing_fields.append("производитель")
    if not description:
        missing_fields.append("описание / фрагмент технического паспорта")

    known = {k.lower() for k in list(specs) + empty}
    missing_specs = [k for k in EXPECTED_SPECS if k.lower() not in known]

    return Product(
        name=name,
        manufacturer=manufacturer,
        specs=specs,
        description=description,
        empty_specs=empty,
        missing_specs=missing_specs,
        missing_fields=missing_fields,
    )


def load_file(path: str) -> Product:
    with open(path, encoding="utf-8") as fh:
        return build(parse_json(fh.read()))
