"""Формирование текста КП из обычного текстового шаблона.

Это единственное место, где собирается текст черновика.
На следующем этапе сюда можно будет подключить модель — форма,
проверка полей и хранение документов от этого не зависят.
"""

from decimal import Decimal

from .offers import OfferFields

DRAFT_TEMPLATE = """\
Коммерческое предложение для {client}

Задача
{task}

Работы
{services}

Стоимость
Итого {total}.

Срок
{deadline}{terms_section}
"""

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


def build_template_draft(fields: OfferFields, total: Decimal) -> str:
    """Собирает текст черновика из проверенных полей формы и итоговой суммы."""
    text = DRAFT_TEMPLATE.format(
        client=client_for_title(fields.client),
        task=as_sentence(fields.task),
        services="\n".join(
            SERVICE_LINE.format(name=s.name, price=format_rub(s.price)) for s in fields.services
        ),
        total=format_rub(total),
        deadline=as_sentence(fields.deadline),
        terms_section=TERMS_SECTION.format(terms=as_sentence(fields.extra_terms))
        if fields.extra_terms
        else "",
    )
    return text.strip()


def client_for_title(client: str) -> str:
    first_word, _, rest = client.partition(" ")
    genitive = CLIENT_TYPE_GENITIVE.get(first_word.lower())
    return f"{genitive} {rest}" if genitive and rest else client


def as_sentence(value: str) -> str:
    value = value.strip()
    return value if value.endswith((".", "!", "?", "…")) else value + "."


def format_rub(amount: Decimal) -> str:
    """80000 → «80 000 ₽», 1234.5 → «1 234,50 ₽»."""
    integer, fraction = f"{amount:,.2f}".split(".")
    integer = integer.replace(",", " ")
    return f"{integer} ₽" if fraction == "00" else f"{integer},{fraction} ₽"
