"""Integration Center — реестр адаптеров интеграций MedHubHAQ (Phase 2).

Каждый провайдер описывает канал приёма (inbound) или доставки (outbound)
обращений/уведомлений. Для внешних систем реализованы MOCK-провайдеры: они
возвращают детерминированные демонстрационные данные и помечены mode="mock",
чтобы платформу можно было показать без реальных ключей. Подключение реальных
ключей переводит провайдер в mode="live" (вне объёма демо).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

_NOW = datetime.utcnow()


@dataclass
class IntegrationProviderInfo:
    key: str
    name: str
    kind: str  # inbound_appeals | ehr | interop | messaging | api
    direction: str  # inbound | outbound | bidirectional
    description: str
    capabilities: list[str]
    mode: str = "mock"       # mock | live
    status: str = "available"  # available | not_configured | error


@dataclass
class IntegrationMessage:
    external_id: str
    channel: str
    author: str
    text: str
    received_at: datetime
    category_hint: str | None = None
    meta: dict = field(default_factory=dict)


PROVIDERS: dict[str, IntegrationProviderInfo] = {
    "damumed": IntegrationProviderInfo(
        key="damumed", name="Damumed (МИС)", kind="ehr", direction="inbound",
        description="Медицинская информационная система: обращения и события пациентов.",
        capabilities=["fetch_appeals", "patient_lookup"],
    ),
    "ikomek": IntegrationProviderInfo(
        key="ikomek", name="iKomek 109", kind="inbound_appeals", direction="inbound",
        description="Единый контакт-центр: обращения граждан по здравоохранению.",
        capabilities=["fetch_appeals"],
    ),
    "crm": IntegrationProviderInfo(
        key="crm", name="CRM обращений", kind="inbound_appeals", direction="inbound",
        description="CRM-система регистрации обращений медорганизации.",
        capabilities=["fetch_appeals", "status_sync"],
    ),
    "eotinish": IntegrationProviderInfo(
        key="eotinish", name="E-Otinish", kind="inbound_appeals", direction="inbound",
        description="Государственная платформа обращений граждан.",
        capabilities=["fetch_appeals"],
    ),
    "fhir": IntegrationProviderInfo(
        key="fhir", name="FHIR R4", kind="interop", direction="bidirectional",
        description="HL7 FHIR: обмен ресурсами Communication/Patient.",
        capabilities=["fetch_communication", "push_communication"],
    ),
    "hl7": IntegrationProviderInfo(
        key="hl7", name="HL7 v2", kind="interop", direction="inbound",
        description="HL7 v2 сообщения (ADT/ORM) из госпитальных систем.",
        capabilities=["fetch_messages"],
    ),
    "sms": IntegrationProviderInfo(
        key="sms", name="SMS-шлюз", kind="messaging", direction="outbound",
        description="Отправка SMS-уведомлений заявителям.",
        capabilities=["send"],
    ),
    "email": IntegrationProviderInfo(
        key="email", name="Email (SMTP)", kind="messaging", direction="outbound",
        description="Отправка email-уведомлений и официальных ответов.",
        capabilities=["send"],
    ),
    "telegram": IntegrationProviderInfo(
        key="telegram", name="Telegram Bot", kind="messaging", direction="bidirectional",
        description="Бот приёма обращений и уведомлений в Telegram.",
        capabilities=["send", "fetch_appeals"],
    ),
    "whatsapp": IntegrationProviderInfo(
        key="whatsapp", name="WhatsApp Business", kind="messaging", direction="bidirectional",
        description="Канал WhatsApp Business для обращений и уведомлений.",
        capabilities=["send", "fetch_appeals"],
    ),
    "rest": IntegrationProviderInfo(
        key="rest", name="REST API", kind="api", direction="bidirectional",
        description="Универсальный REST-вебхук приёма/выгрузки обращений.",
        capabilities=["fetch_appeals", "push"],
    ),
    "graphql": IntegrationProviderInfo(
        key="graphql", name="GraphQL API", kind="api", direction="bidirectional",
        description="GraphQL-эндпоинт интеграции внешних систем.",
        capabilities=["query", "mutation"],
    ),
}

# Демонстрационные (mock) входящие сообщения по каналам приёма обращений.
_MOCK_INBOUND: dict[str, list[tuple[str, str, str]]] = {
    "ikomek": [
        ("Айгүл Н.", "Не могу записаться к участковому врачу третий день, талонов нет.", "access"),
        ("Данияр С.", "В аптеке нет льготного препарата для мамы-диабетика.", "medicines"),
    ],
    "damumed": [
        ("Пациент #48213", "Жалоба на длительное ожидание результатов КТ.", "diagnostics"),
        ("Пациент #48291", "Отказали в плановой госпитализации без объяснения.", "hospitalization"),
    ],
    "crm": [
        ("Гүлнара Т.", "Грубое отношение персонала в регистратуре поликлиники.", "medical_staff"),
        ("Ержан К.", "С меня взяли оплату за приём, положенный по ОСМС.", "financial"),
    ],
    "eotinish": [
        ("Заявитель", "Скорая ехала более двух часов на вызов к пожилому человеку.", "emergency"),
        ("Заявитель", "В отделении антисанитария, есть заболевшие пациенты.", "sanitary"),
    ],
    "telegram": [
        ("@user_kz", "Прошу прикрепить меня к поликлинике по новому адресу.", "access"),
    ],
    "whatsapp": [
        ("+7 701 000 00 00", "Не выдают рецепт на нужное лекарство.", "medicines"),
    ],
    "rest": [
        ("external-system", "Обращение по вопросу качества оказанной помощи.", "quality_of_care"),
    ],
    "hl7": [
        ("HOSPITAL_ADT", "MSH|^~\\&|ADT|HOSP7|MEDHUB|... жалоба на маршрутизацию пациента.", "hospitalization"),
    ],
    "fhir": [
        ("Communication/1042", "FHIR Communication: пациент сообщает о недоступности лекарства.", "medicines"),
    ],
}


def list_providers() -> list[IntegrationProviderInfo]:
    return list(PROVIDERS.values())


def get_provider(key: str) -> IntegrationProviderInfo | None:
    return PROVIDERS.get(key)


def test_connection(key: str) -> dict:
    provider = get_provider(key)
    if provider is None:
        return {"ok": False, "message": f"Неизвестный провайдер: {key}"}
    return {
        "ok": True,
        "mode": provider.mode,
        "message": (
            f"{provider.name}: mock-соединение установлено. Готов к приёму/отправке "
            f"(демо-режим, без реальных ключей)."
        ),
    }


def mock_fetch(key: str, limit: int = 5) -> list[IntegrationMessage]:
    provider = get_provider(key)
    if provider is None:
        return []
    samples = _MOCK_INBOUND.get(key, [])
    messages: list[IntegrationMessage] = []
    for i, (author, text, hint) in enumerate(samples[:limit]):
        messages.append(
            IntegrationMessage(
                external_id=f"{key}-mock-{i + 1}",
                channel=provider.name,
                author=author,
                text=text,
                received_at=_NOW - timedelta(minutes=15 * (i + 1)),
                category_hint=hint,
                meta={"mode": "mock"},
            )
        )
    return messages


def mock_send(key: str, to: str, text: str) -> dict:
    provider = get_provider(key)
    if provider is None:
        return {"ok": False, "message": f"Неизвестный провайдер: {key}"}
    return {
        "ok": True,
        "mode": provider.mode,
        "provider": provider.name,
        "to": to,
        "delivered_at": datetime.utcnow().isoformat(),
        "preview": text[:120],
        "message": f"Сообщение поставлено в очередь ({provider.name}, демо-режим).",
    }
