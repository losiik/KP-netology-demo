from fastapi.responses import JSONResponse


def validation_error(errors: dict[str, str]) -> JSONResponse:
    """Единый формат ошибок проверки: {"message": ..., "errors": {поле: текст}}."""
    return JSONResponse(
        status_code=422,
        content={"message": "Проверьте выделенные поля", "errors": errors},
    )


def generation_error(message: str, status: int) -> JSONResponse:
    """Ошибка подготовки черновика. Повтор запускает только пользователь."""
    return JSONResponse(status_code=status, content={"message": message, "retry": True, "errors": {}})
