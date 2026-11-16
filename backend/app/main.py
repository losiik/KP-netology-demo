"""Точка входа FastAPI: подключает роутеры и (если есть сборка) отдаёт фронтенд."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import auth, documents, drafts
from .db import init_db

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Коммерческие предложения", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(drafts.router)
app.include_router(documents.router)


@app.exception_handler(RequestValidationError)
async def bad_request(_request: Request, _exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"message": "Некорректный запрос", "errors": {}})


@app.get("/api/health")
def health():
    return {"ok": True}


# Режим «одной командой»: после `npm run build` бэкенд сам отдаёт интерфейс.
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        file = FRONTEND_DIST / path
        if path and file.is_file() and FRONTEND_DIST in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
