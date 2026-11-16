"""Проверки критериев готовности на уровне API. Запуск: python -m pytest"""

import pytest
from fastapi.testclient import TestClient

SAMPLE = {
    "client": "Кофейня «Зерно»",
    "task": "Запустить сайт с меню и формой заказа.",
    "services": [
        {"name": "Дизайн", "price": "30000"},
        {"name": "Разработка", "price": "50 000"},
    ],
    "deadline": "15 рабочих дней",
    "extra_terms": "Предоплата 50%",
}

EXPECTED_TEXT = """Коммерческое предложение для кофейни «Зерно»

Задача
Запустить сайт с меню и формой заказа.

Работы
Дизайн — 30 000 ₽
Разработка — 50 000 ₽

Стоимость
Итого 80 000 ₽.

Срок
15 рабочих дней.

Условия
Предоплата 50%."""


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("KP_DB_PATH", str(tmp_path / "test.sqlite3"))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def login(client, user, password):
    response = client.post("/api/auth/login", json={"login": user, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_sample_draft(client):
    headers = login(client, "anna", "anna123")
    response = client.post("/api/drafts", json=SAMPLE, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == "80000"
    assert response.json()["text"] == EXPECTED_TEXT


def test_total_comes_from_form(client):
    headers = login(client, "anna", "anna123")
    data = {**SAMPLE, "services": [{"name": "Дизайн", "price": "30000"}, {"name": "Разработка", "price": "60000"}]}
    body = client.post("/api/drafts", json=data, headers=headers).json()
    assert body["total"] == "90000"
    assert "Итого 90 000 ₽." in body["text"]


def test_other_client_without_terms(client):
    headers = login(client, "anna", "anna123")
    data = {
        "client": "ООО «Ромашка»",
        "task": "Настроить рекламу",
        "services": [{"name": "Аудит", "price": "12500,50"}, {"name": "Настройка", "price": "20000"}, {"name": "Отчёт", "price": 5000}],
        "deadline": "2 недели",
        "extra_terms": "  ",
    }
    body = client.post("/api/drafts", json=data, headers=headers).json()
    assert body["text"].startswith("Коммерческое предложение для ООО «Ромашка»")
    assert "Итого 37 500,50 ₽." in body["text"]
    assert "Условия" not in body["text"]


def test_validation_errors(client):
    headers = login(client, "anna", "anna123")
    data = {**SAMPLE, "client": " ", "services": [{"name": "Дизайн", "price": "abc"}, {"name": "", "price": "-5"}]}
    response = client.post("/api/drafts", json=data, headers=headers)
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert set(errors) == {"client", "services.0.price", "services.1.name", "services.1.price"}


def test_requires_login(client):
    assert client.post("/api/drafts", json=SAMPLE).status_code == 401
    assert client.get("/api/documents").status_code == 401


def test_save_edit_reopen_and_owner_check(client):
    anna = login(client, "anna", "anna123")
    boris = login(client, "boris", "boris123")

    created = client.post("/api/documents", json={"fields": SAMPLE, "text": "Черновик"}, headers=anna)
    assert created.status_code == 201
    doc_id = created.json()["id"]
    assert created.json()["total"] == "80000"

    updated = client.put(f"/api/documents/{doc_id}", json={"fields": SAMPLE, "text": "Правка вручную"}, headers=anna)
    assert updated.status_code == 200
    assert updated.json()["id"] == doc_id

    reopened = client.get(f"/api/documents/{doc_id}", headers=anna).json()
    assert reopened["text"] == "Правка вручную"
    assert reopened["fields"]["client"] == "Кофейня «Зерно»"
    assert [d["id"] for d in client.get("/api/documents", headers=anna).json()["documents"]] == [doc_id]

    assert client.get(f"/api/documents/{doc_id}", headers=boris).status_code == 404
    assert client.put(f"/api/documents/{doc_id}", json={"fields": SAMPLE, "text": "x"}, headers=boris).status_code == 404
    assert client.get("/api/documents", headers=boris).json()["documents"] == []
    assert client.get(f"/api/documents/{doc_id}", headers=anna).json()["text"] == "Правка вручную"
