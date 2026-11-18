"""Вызов DeepSeek без сети: инструкция отдельно от данных заявки."""

import json

import httpx
import pytest

from app.model import GenerationError, build_messages, generate_wording
from app.offers import validate_offer_fields

SAMPLE = {
    "client": "Кофейня «Зерно»",
    "task": "Запустить сайт с меню и формой заказа.",
    "services": [{"name": "Дизайн", "price": "30000"}, {"name": "Разработка", "price": "50000"}],
    "deadline": "15 рабочих дней",
    "extra_terms": "Предоплата 50%",
}


def fields_and_total():
    fields, errors = validate_offer_fields(SAMPLE)
    assert errors == {}
    return fields, sum(service.price for service in fields.services)


def test_instruction_is_separate_from_offer_data():
    fields, total = fields_and_total()
    system, user = build_messages(fields, total)
    assert system["role"] == "system"
    assert "Составь черновик коммерческого предложения" in system["content"]
    assert "Кофейня" not in system["content"]
    data = json.loads(user["content"])
    assert data["client"] == "Кофейня «Зерно»"
    assert data["deadline"] == "15 рабочих дней"
    assert data["extra_terms"] == "Предоплата 50%"
    assert data["total"] == "80 000 ₽"
    assert [item["name"] for item in data["services"]] == ["Дизайн", "Разработка"]


def test_api_call_uses_key_and_returns_wording(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("AI_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.setattr("app.model.env_path", lambda: env)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps({"opening": "", "task": "Сделать сайт"})}}]},
        )

    monkeypatch.setattr("app.model._client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    fields, total = fields_and_total()
    wording = generate_wording(fields, total)
    assert wording == {"opening": "", "task": "Сделать сайт"}
    assert seen["url"] == "https://api.deepseek.com/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["model"] == "deepseek-flash"
    assert seen["body"]["messages"][0]["role"] == "system"
    assert seen["body"]["messages"][1]["role"] == "user"
    assert "test-key" not in seen["body"]["messages"][1]["content"]


def test_timeout_is_a_generation_error(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("AI_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.setattr("app.model.env_path", lambda: env)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    monkeypatch.setattr("app.model._client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    fields, total = fields_and_total()
    with pytest.raises(GenerationError) as caught:
        generate_wording(fields, total)
    assert caught.value.code == "timeout"
    assert "test-key" not in str(caught.value)


def test_missing_key(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.setattr("app.model.env_path", lambda: tmp_path / "absent.env")
    fields, total = fields_and_total()
    with pytest.raises(GenerationError) as caught:
        generate_wording(fields, total)
    assert caught.value.code == "unavailable"
