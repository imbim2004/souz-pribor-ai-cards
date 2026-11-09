"""CLI: python -m app.cli examples/product1.json [-o out.md] [--json]

Читает JSON о приборе (из файла или со stdin), печатает карточку в Markdown.
"""

import argparse
import json
import sys

from app import gemini, product, render
from app.generator import generate_card


def main() -> int:
    parser = argparse.ArgumentParser(description="Черновик карточки товара по данным о приборе")
    parser.add_argument("path", nargs="?", help="JSON-файл с данными; без него читается stdin")
    parser.add_argument("-o", "--out", help="куда записать результат (по умолчанию - в консоль)")
    parser.add_argument("--json", action="store_true", help="выводить JSON вместо Markdown")
    args = parser.parse_args()

    try:
        raw = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
    except OSError as exc:
        print(f"Не удалось прочитать файл: {exc}", file=sys.stderr)
        return 2

    try:
        item = product.build(product.parse_json(raw))
    except product.InputError as exc:
        print(f"Ошибка во входных данных: {exc}", file=sys.stderr)
        return 2

    if item.gaps:
        print("Во входных данных не хватает: " + "; ".join(item.gaps), file=sys.stderr)

    try:
        result = generate_card(item)
    except gemini.ApiError as exc:
        print(f"Ошибка LLM: {exc}", file=sys.stderr)
        return 3

    if args.json:
        payload = {
            "card": result["card"],
            "checks": {
                "gaps": result["gaps"],
                "invented": result["invented"],
                "lengths": result["lengths"],
                "title_length": result["title_length"],
                "description_length": result["description_length"],
            },
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = render.to_markdown(item, result)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"Записано: {args.out}", file=sys.stderr)
    else:
        print(text)

    # Ненулевой код, если проверки что-то нашли - удобно для скриптов.
    return 1 if (result["lengths"] or result["invented"]) else 0


if __name__ == "__main__":
    sys.exit(main())
