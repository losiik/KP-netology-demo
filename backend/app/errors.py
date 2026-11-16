from fastapi.responses import JSONResponse


def validation_error(errors: dict[str, str]) -> JSONResponse:
    """Единый формат ошибок проверки: {"message": ..., "errors": {поле: текст}}."""
    return JSONResponse(
        status_code=422,
        content={"message": "Проверьте выделенные поля", "errors": errors},
    )
