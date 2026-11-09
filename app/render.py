"""Markdown-вывод: то, что контент-менеджер копирует в CMS."""

from app.config import DESCRIPTION_MAX, DESCRIPTION_MIN, TITLE_MAX


def to_markdown(product, result: dict) -> str:
    card = result["card"]
    out = [f"# Карточка товара: {product.name}", ""]

    title = card.get("seo_title", "")
    out += [
        "## SEO-заголовок",
        "",
        title,
        "",
        f"_{result['title_length']} символов из {TITLE_MAX}_",
        "",
        "## SEO-описание",
        "",
        card.get("seo_description", ""),
        "",
        f"_{result['description_length']} символов, требуется {DESCRIPTION_MIN}-{DESCRIPTION_MAX}_",
        "",
        "## Характеристики",
        "",
        "| Характеристика | Значение |",
        "| --- | --- |",
    ]
    for spec in card.get("specs") or []:
        if isinstance(spec, dict):
            name = str(spec.get("name", "")).replace("|", "/")
            value = str(spec.get("value", "")).replace("|", "/")
            out.append(f"| {name} | {value} |")

    out += ["", "## Поисковые запросы", ""]
    for query in card.get("search_queries") or []:
        out.append(f"- {query}")

    commercial = card.get("commercial") or {}
    out += ["", "## Для менеджера", ""]
    out += [f"**Кому подходит.** {commercial.get('fits', 'данных нет')}", ""]
    out += [f"**Какие задачи решает.** {commercial.get('tasks', 'данных нет')}", ""]
    if commercial.get("notes"):
        out += [f"**Что уточнить.** {commercial['notes']}", ""]

    out += ["## Проверки", ""]
    out.append(_block("Нет во входных данных", result["gaps"], "входные данные полные"))
    out.append(_block("Не подтверждено входными данными", result["invented"],
                      "все числа и единицы измерения совпадают с входными данными"))
    out.append(_block("Нарушения требований к длинам", result["lengths"],
                      "длины в норме"))

    missing = card.get("missing_data") or []
    if missing:
        out += ["**Модель отметила как требующее уточнения:** " + "; ".join(str(m) for m in missing), ""]
    out.append(f"_Запросов к модели: {result['attempts']}_")
    return "\n".join(out)


def _block(title: str, items: list, empty_text: str) -> str:
    if not items:
        return f"**{title}:** {empty_text}.\n"
    lines = [f"**{title}:**", ""] + [f"- {item}" for item in items] + [""]
    return "\n".join(lines)
