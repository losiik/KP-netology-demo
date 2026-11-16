"""Поля коммерческого предложения: проверка ввода и расчёт итоговой суммы.

Используется и при создании черновика, и при сохранении документа,
поэтому сервер никогда не доверяет сумме, присланной из браузера.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

MAX_SERVICES = 50
MAX_PRICE = Decimal("1000000000")
LIMITS = {"client": 200, "task": 2000, "deadline": 200, "extra_terms": 1000, "service_name": 200}


@dataclass
class Service:
    name: str
    price: Decimal


@dataclass
class OfferFields:
    client: str
    task: str
    services: list[Service]
    deadline: str
    extra_terms: str

    def to_dict(self) -> dict:
        return {
            "client": self.client,
            "task": self.task,
            "services": [{"name": s.name, "price": str(s.price)} for s in self.services],
            "deadline": self.deadline,
            "extra_terms": self.extra_terms,
        }


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def parse_price(raw) -> Decimal:
    """Принимает «30000», «30 000», «30 000,50» или число. Бросает ValueError с текстом ошибки."""
    if isinstance(raw, bool):
        raise ValueError("Цена должна быть числом")
    if isinstance(raw, (int, float)):
        raw = str(raw)
    if not isinstance(raw, str):
        raise ValueError("Укажите цену")
    cleaned = raw.replace(" ", "").replace(" ", "").replace("₽", "").replace(",", ".")
    if not cleaned:
        raise ValueError("Укажите цену")
    try:
        price = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError("Введите число") from None
    if not price.is_finite():
        raise ValueError("Введите число")
    if price <= 0:
        raise ValueError("Цена должна быть больше нуля")
    if price > MAX_PRICE:
        raise ValueError("Слишком большая цена")
    if price.as_tuple().exponent < -2:
        raise ValueError("Не больше двух знаков после запятой")
    return price.quantize(Decimal(1)) if price == price.to_integral() else price


def validate_offer_fields(payload) -> tuple[OfferFields | None, dict[str, str]]:
    """Возвращает (поля, {}) или (None, {имя_поля: текст_ошибки})."""
    if not isinstance(payload, dict):
        return None, {"form": "Некорректные данные формы"}

    errors: dict[str, str] = {}
    client = _text(payload.get("client"))
    task = _text(payload.get("task"))
    deadline = _text(payload.get("deadline"))
    extra_terms = _text(payload.get("extra_terms"))

    for key, value, message in (
        ("client", client, "Укажите клиента"),
        ("task", task, "Опишите задачу"),
        ("deadline", deadline, "Укажите срок"),
    ):
        if not value:
            errors[key] = message
        elif len(value) > LIMITS[key]:
            errors[key] = f"Не больше {LIMITS[key]} символов"
    if len(extra_terms) > LIMITS["extra_terms"]:
        errors["extra_terms"] = f"Не больше {LIMITS['extra_terms']} символов"

    raw_services = payload.get("services")
    services: list[Service] = []
    if not isinstance(raw_services, list) or not raw_services:
        errors["services"] = "Добавьте хотя бы одну услугу"
    elif len(raw_services) > MAX_SERVICES:
        errors["services"] = f"Не больше {MAX_SERVICES} услуг"
    else:
        for i, item in enumerate(raw_services):
            item = item if isinstance(item, dict) else {}
            name = _text(item.get("name"))
            if not name:
                errors[f"services.{i}.name"] = "Укажите название услуги"
            elif len(name) > LIMITS["service_name"]:
                errors[f"services.{i}.name"] = f"Не больше {LIMITS['service_name']} символов"
            try:
                price = parse_price(item.get("price"))
            except ValueError as exc:
                errors[f"services.{i}.price"] = str(exc)
                price = None
            if name and price is not None:
                services.append(Service(name=name, price=price))

    if errors:
        return None, errors
    return OfferFields(client, task, services, deadline, extra_terms), {}


def calculate_total(services: list[Service]) -> Decimal:
    return sum((s.price for s in services), Decimal(0))
