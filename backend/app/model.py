"""Вызов DeepSeek для формулировок черновика.

Постоянная инструкция хранится здесь. Поля заявки уходят отдельным
сообщением. Цены, срок и условия в текст КП не переносятся из ответа
модели: их подставляет compose_draft из проверенных полей формы.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

import httpx

from .offers import OfferFields
from .template import format_rub

log = logging.getLogger("kp.model")

# Текущее имя DeepSeek V4 Flash. Документация: https://api-docs.deepseek.com/
MODEL = "deepseek-flash"
API_URL = "https://api.deepseek.com/chat/completions"
TIMEOUT = httpx.Timeout(40.0, connect=10.0)

SYSTEM_INSTRUCTION = (
    "Составь черновик коммерческого предложения на русском языке из переданных данных. "
    "Сохрани услуги, цены и сроки. Не добавляй скидки, гарантии и новые условия. "
    "Структура предложения: задача, работы, стоимость, срок, условия. "
    "Если дополнительные условия отсутствуют, пропусти этот раздел."
)

# Контракт ответа нужен, чтобы система сама подставила точные суммы и условия.
OUTPUT_CONTRACT = (
    "Ответь только JSON-объектом с двумя полями: "
    '{"opening": "одно приветственное предложение или пустая строка", '
    '"task": "формулировка задачи по переданным данным"}. '
    "Не включай в JSON перечень работ, цены, срок, итоговую сумму и условия: "
    "их подставит система из заявки. Не добавляй скидки, гарантии и новые условия."
)


class GenerationError(Exception):
    """Сбой подготовки черновика. В текст исключения не попадают ключ и ответ API."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def env_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def load_local_env() -> None:
    """Читает локальный .env, не затирая уже заданные переменные окружения."""
    path = env_path()
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or name in os.environ:
            continue
        os.environ[name] = value.strip().strip('"').strip("'")


def offer_payload(fields: OfferFields, total) -> dict:
    """Данные конкретной заявки. В инструкцию не подмешиваются."""
    return {
        "client": fields.client,
        "task": fields.task,
        "services": [{"name": service.name, "price": format_rub(service.price)} for service in fields.services],
        "deadline": fields.deadline,
        "extra_terms": fields.extra_terms or None,
        "total": format_rub(total),
    }


def build_messages(fields: OfferFields, total) -> list[dict]:
    return [
        {"role": "system", "content": f"{SYSTEM_INSTRUCTION}\n\n{OUTPUT_CONTRACT}"},
        {"role": "user", "content": json.dumps(offer_payload(fields, total), ensure_ascii=False)},
    ]


class GenerationGate:
    """Одна активная генерация на пользователя и ограничение частоты."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active: set[int] = set()
        self._starts: dict[int, list[float]] = {}
        self.window_seconds = 60.0
        self.max_per_window = 8

    def reset(self) -> None:
        with self._lock:
            self._active.clear()
            self._starts.clear()

    def try_acquire(self, user_id: int) -> str | None:
        """None — слот занят этим вызовом. Иначе код отказа: busy или rate."""
        now = time.monotonic()
        with self._lock:
            if user_id in self._active:
                return "busy"
            recent = [stamp for stamp in self._starts.get(user_id, []) if now - stamp < self.window_seconds]
            if len(recent) >= self.max_per_window:
                self._starts[user_id] = recent
                return "rate"
            self._active.add(user_id)
            recent.append(now)
            self._starts[user_id] = recent
            return None

    def release(self, user_id: int) -> None:
        with self._lock:
            self._active.discard(user_id)


gate = GenerationGate()


def generate_wording(fields: OfferFields, total) -> dict:
    """Просит модель сформулировать обращение и задачу. Суммы не принимает из ответа."""
    load_local_env()
    key = os.environ.get("AI_API_KEY", "").strip()
    if not key:
        log.warning("draft generation failed: missing_key")
        raise GenerationError("unavailable")

    body = {
        "model": MODEL,
        "messages": build_messages(fields, total),
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "temperature": 0.3,
        "max_tokens": 800,
        "stream": False,
    }
    try:
        payload = _post(key, body)
    except httpx.TimeoutException:
        log.warning("draft generation failed: timeout")
        raise GenerationError("timeout") from None
    except httpx.HTTPError:
        log.warning("draft generation failed: transport")
        raise GenerationError("unavailable") from None
    return _wording_from_response(payload)


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT)


def _post(key: str, body: dict) -> dict:
    with _client() as client:
        response = client.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}"},
            json=body,
        )
    if response.status_code != 200:
        log.warning("draft generation failed: status=%s", response.status_code)
        raise GenerationError("unavailable")
    try:
        return response.json()
    except ValueError:
        log.warning("draft generation failed: bad_response")
        raise GenerationError("unavailable") from None


def _wording_from_response(payload: dict) -> dict:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        log.warning("draft generation failed: empty_choice")
        raise GenerationError("unavailable") from None
    if not isinstance(content, str) or not content.strip():
        log.warning("draft generation failed: empty_content")
        raise GenerationError("unavailable")
    try:
        parsed = json.loads(content)
    except ValueError:
        log.warning("draft generation failed: content_not_json")
        raise GenerationError("unavailable") from None
    if not isinstance(parsed, dict):
        log.warning("draft generation failed: content_not_object")
        raise GenerationError("unavailable")

    task = parsed.get("task")
    opening = parsed.get("opening") or ""
    if not isinstance(task, str) or not task.strip():
        log.warning("draft generation failed: missing_task")
        raise GenerationError("unavailable")
    if not isinstance(opening, str):
        opening = ""
    task = task.strip()
    opening = opening.strip()
    if len(task) > 2000 or len(opening) > 500:
        log.warning("draft generation failed: wording_too_long")
        raise GenerationError("unavailable")
    return {"opening": opening, "task": task}
