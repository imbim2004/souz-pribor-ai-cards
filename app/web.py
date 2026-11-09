"""FastAPI: веб-форма на GET / и JSON-эндпоинт POST /generate.

Запуск: uvicorn app.web:api --reload
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from app import gemini, product, render
from app.config import model_name
from app.generator import generate_card
from app.web_form import FORM_PAGE

api = FastAPI(title="Черновик карточки товара (КИП)", docs_url="/docs")


@api.get("/", response_class=HTMLResponse)
def form() -> HTMLResponse:
    """Форма: вставить JSON о приборе и получить карточку. Отправляет в POST /generate."""
    return HTMLResponse(FORM_PAGE.replace("{{model}}", model_name()))


@api.post("/generate")
def generate(payload: dict) -> JSONResponse:
    """На вход - JSON о приборе, на выход - карточка, результаты проверок и Markdown."""
    try:
        item = product.build(payload)
    except product.InputError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    try:
        result = generate_card(item)
    except gemini.ApiError as exc:
        # 502: отказал внешний сервис, а не клиент прислал плохие данные.
        return JSONResponse({"error": str(exc)}, status_code=502)

    return JSONResponse(
        {
            "card": result["card"],
            "checks": {
                "gaps": result["gaps"],
                "invented": result["invented"],
                "lengths": result["lengths"],
                "title_length": result["title_length"],
                "description_length": result["description_length"],
                "attempts": result["attempts"],
            },
            "markdown": render.to_markdown(item, result),
        }
    )


@api.get("/health")
def health() -> dict:
    return {"status": "ok", "model": model_name()}
