"""Запуск бэкенда одной кнопкой: откройте этот файл в PyCharm и нажмите Run (Shift+F10).

Работает из любой рабочей папки. API: http://localhost:8000, документация: http://localhost:8000/docs
"""

from pathlib import Path

import uvicorn

BACKEND_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        app_dir=str(BACKEND_DIR),
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR / "app")],
    )
