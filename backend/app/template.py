"""Сборка текста КП на сервере.

Формулировки задачи и обращения приходят от модели.
Перечень работ, цены, срок, итоговая сумма и условия берутся
только из проверенных полей заявки.
"""

from decimal import Decimal

from .offers import OfferFields

TERMS_SECTION = """

Условия
{terms}"""

SERVICE_LINE = "{name} — {price}"

# «Кофейня «Зерно»» → «для кофейни «Зерно»». Если тип организации
# не распознан, название подставляется как есть: «для ООО «Ромашка»».
CLIENT_TYPE_GENITIVE = {
    "кофейня": "кофейни",
    "пекарня": "пекарни",
    "компания": "компании",
    "студия": "студии",
    "клиника": "клиники",
    "школа": "школы",
    "фирма": "фирмы",
    "ресторан": "ресторана",
    "магазин": "магазина",
    "салон": "салона",
    "центр": "центра",
    "клуб": "клуба",
    "агентство": "агентства",
    "кафе": "кафе",
    "бюро": "бюро",
}


def compose_draft(fields: OfferFields, total: Decimal, wording: dict) -> str:
    """Собирает черновик: формулировки из wording, факты и суммы из заявки."""
    opening = _optional_sentence(wording.get("opening"))
    task = as_sentence(str(wording.get("task") or ""))
    services = "\n".join(
        SERVICE_LINE.format(name=service.name, price=format_rub(service.price)) for service in fields.services
    )
    terms_section = (
        TERMS_SECTION.format(terms=as_sentence(fields.extra_terms)) if fields.extra_terms else ""
    )
    head = f"Коммерческое предложение для {client_for_title(fields.client)}\n"
    if opening:
        head += f"\n{opening}\n"
    text = (
        f"{head}\n"
        f"Задача\n{task}\n\n"
        f"Работы\n{services}\n\n"
        f"Стоимость\nИтого {format_rub(total)}.\n\n"
        f"Срок\n{as_sentence(fields.deadline)}{terms_section}"
    )
    return text.strip()


def build_template_draft(fields: OfferFields, total: Decimal) -> str:
    """Черновик без модели: формулировка задачи совпадает с текстом заявки."""
    return compose_draft(fields, total, {"opening": "", "task": fields.task})


def client_for_title(client: str) -> str:
    first_word, _, rest = client.partition(" ")
    genitive = CLIENT_TYPE_GENITIVE.get(first_word.lower())
    return f"{genitive} {rest}" if genitive and rest else client


def as_sentence(value: str) -> str:
    value = value.strip()
    return value if value.endswith((".", "!", "?", "…")) else value + "."


def _optional_sentence(value) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return as_sentence(value)


def format_rub(amount: Decimal) -> str:
    """80000 → «80 000 ₽», 1234.5 → «1 234,50 ₽»."""
    integer, fraction = f"{amount:,.2f}".split(".")
    integer = integer.replace(",", " ")
    return f"{integer} ₽" if fraction == "00" else f"{integer},{fraction} ₽"
