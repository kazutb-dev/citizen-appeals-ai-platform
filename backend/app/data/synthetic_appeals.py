"""Синтетические обращения MedHubHAQ (здравоохранение): демо-сценарии,
~257 обращений. Все данные вымышлены и сгенерированы детерминированно.

Сценарии:
  1. campaign_medicines  — координированная кампания (нет льготных лекарств), 50
  2. critical            — критические обращения (угроза жизни / отказ в помощи), 7
  3. care_quality        — жалобы на качество медпомощи (→ Служба качества), 12
  4. repeat_complainant  — хронический заявитель (запись/доступность), 27
  5. outbreak_resonance  — соц. резонанс (вспышка инфекции в стационаре), 15
  6. duplicates          — дубликаты (повторная подача), 8 пар = 16
  + normal               — фоновый поток по всем категориям, ~130
"""
import random
from datetime import datetime, timedelta

from app.data.departments_data import REGIONS

rng = random.Random(20260611)

FIRST_NAMES = [
    "Айдос", "Алибек", "Арман", "Бауыржан", "Дамир", "Ерлан", "Жанибек",
    "Кайрат", "Мади", "Нурлан", "Олжас", "Руслан", "Санжар", "Тимур",
    "Айгерим", "Альмира", "Асель", "Дана", "Динара", "Жанна", "Камила",
    "Лаура", "Мадина", "Назгуль", "Сауле", "Толкын", "Айнур", "Гульнара",
]
LAST_NAMES = [
    "Абдрахманов", "Байтурсынов", "Дюсембаев", "Ермеков", "Жумабаев",
    "Искаков", "Кенжебаев", "Мухамеджанов", "Нурпеисов", "Омаров",
    "Сапаров", "Тулегенов", "Утемуратов", "Шарипов", "Касымов",
    "Бекжанов", "Серикбаев", "Оразбаев", "Куанышев", "Темирбеков",
]
PATRONYMICS = [
    "Асылұлы", "Бекұлы", "Ерланұлы", "Кайратұлы", "Нурланұлы",
    "Асылқызы", "Бекқызы", "Ерланқызы", "Кайратқызы", "Нурланқызы",
]


def make_name(i: int) -> str:
    return (
        f"{LAST_NAMES[i % len(LAST_NAMES)]}"
        f" {FIRST_NAMES[(i * 7) % len(FIRST_NAMES)]}"
        f" {PATRONYMICS[(i * 3) % len(PATRONYMICS)]}"
    )


def region_for(i: int) -> str:
    return REGIONS[i % len(REGIONS)]


NOW = datetime.utcnow()


# ============================================================
# Сценарий 1: координированная кампания — нет льготных лекарств
# 50 обращений за 48 часов, шаблонные тексты
# ============================================================

CAMPAIGN_BASE_TEXTS = [
    "Требуем немедленно решить проблему с льготными лекарствами! Инсулин не выдают "
    "уже неделю. Так нельзя относиться к пациентам.",
    "В аптеке при поликлинике опять нет бесплатных препаратов для диабетиков. "
    "Требуем срочно восстановить обеспечение.",
    "Сколько можно?! Льготных лекарств снова нет. Требуем немедленных действий от "
    "руководства здравоохранения.",
    "Отсутствие льготных лекарств — это безобразие. Требую решить вопрос сегодня же.",
    "Пациенты требуют восстановить выдачу бесплатных лекарств. Это недопустимо.",
    "Опять нет препаратов по льготе! Ведомство бездействует. Требуем реакции!",
    "Лекарств по рецепту нет уже который день. Требуем обеспечить нас препаратами.",
    "Невозможно получить жизненно важные лекарства — их просто нет. Срочно примите меры!",
]
CAMPAIGN_PREFIXES = ["", "Здравствуйте! ", "Уважаемое руководство! ", "Срочно! "]


def build_campaign_appeals() -> list[dict]:
    appeals = []
    for i in range(50):
        base = CAMPAIGN_BASE_TEXTS[i % len(CAMPAIGN_BASE_TEXTS)]
        text = CAMPAIGN_PREFIXES[i % len(CAMPAIGN_PREFIXES)] + base
        hours_ago = 2 + (i % 12) * 0.1 + (i // 12) * 11
        appeals.append({
            "scenario": "campaign_medicines",
            "requester_key": f"camp_{i}",
            "requester_name": make_name(100 + i),
            "requester_type": "patient",
            "affiliation": region_for(i),
            "title": "Отсутствие льготных лекарств",
            "text": text,
            "category": "medicines",
            "subcategory": "free_drugs",
            "region": region_for(i),
            "submitted_at": NOW - timedelta(hours=hours_ago),
            "status": "pending_review",
            "risk_level": "medium",
            "risk_score": 0.55,
            "risk_reasons": ["Часть скоординированной кампании обращений"],
            "tags": ["лекарства", "льготные", "кампания"],
            "is_campaign": True,
            "campaign_score": 0.82,
        })
    return appeals


# ============================================================
# Сценарий 5: социальный резонанс — вспышка инфекции в стационаре
# 15 обращений за ~72 часа, коррелируют со всплеском в соцсетях
# ============================================================

OUTBREAK_TEXTS = [
    "В стационаре третий день массово заболевают пациенты с кишечной инфекцией. "
    "Подозреваем нарушение санитарных норм. Прошу срочно провести проверку.",
    "В отделении вспышка инфекции: у нескольких пациентов рвота и температура. "
    "Санитарное состояние палат ужасное. Требуем реакции санэпидслужбы.",
    "После госпитализации заразился инфекцией прямо в больнице. В палате грязь, "
    "уборку не проводят. Когда наведут порядок?",
    "Массовое заражение в стационаре! Уже несколько человек с одинаковыми симптомами. "
    "Прошу немедленно принять меры.",
    "В больнице антисанитария, началась вспышка инфекции среди пациентов. "
    "Нужна срочная проверка и дезинфекция.",
]
OUTBREAK_PREFIXES = ["", "Здравствуйте! ", "Прошу помощи. ", "Крайне срочно! "]


def build_outbreak_appeals() -> list[dict]:
    appeals = []
    region = REGIONS[0]  # одна организация/регион (органичная массовая проблема)
    for i in range(15):
        base = OUTBREAK_TEXTS[i % len(OUTBREAK_TEXTS)]
        text = OUTBREAK_PREFIXES[i % len(OUTBREAK_PREFIXES)] + base
        hours_ago = 4 + i * 4.5
        appeals.append({
            "scenario": "outbreak_resonance",
            "requester_key": f"outbreak_{i}",
            "requester_name": make_name(200 + i),
            "requester_type": "patient",
            "affiliation": region,
            "title": "Вспышка инфекции в стационаре",
            "text": text,
            "category": "sanitary",
            "subcategory": "infection_outbreak",
            "region": region,
            "submitted_at": NOW - timedelta(hours=hours_ago),
            "status": "in_progress",
            "risk_level": "high",
            "risk_score": 0.78,
            "risk_reasons": ["Санитарно-эпидемиологический риск", "Массовая жалоба на одну проблему"],
            "tags": ["санитария", "инфекция", "стационар"],
        })
    return appeals


# ============================================================
# Сценарий 2: критические обращения (эскалация руководству)
# ============================================================

CRITICAL_CASES = [
    ("Скорая ехала более двух часов к пожилому человеку с сердечным приступом, "
     "а в приёмном отделении отказали в госпитализации. Состояние тяжёлое, есть угроза жизни.",
     "emergency", "ambulance_delay", "chief_doctor"),
    ("Отказали в экстренной госпитализации ребёнку с высокой температурой и судорогами. "
     "Ребёнок в тяжёлом состоянии. Прошу немедленно вмешаться.",
     "hospitalization", "admission_refusal", "chief_doctor"),
    ("В аптеке нет инсулина для ребёнка-диабетика, запасы закончились. Без препарата "
     "есть прямая угроза жизни. Срочно нужна помощь.",
     "medicines", "drug_shortage", "chief_doctor"),
    ("После операции у пациента развились тяжёлые осложнения из-за врачебной ошибки. "
     "Состояние критическое. Требуется срочный разбор.",
     "quality_of_care", "malpractice", "deputy_chief"),
    ("В отделении началась вспышка инфекции, заболели несколько пациентов, есть "
     "тяжёлые случаи. Санитарные нормы нарушены. Требуется экстренное реагирование.",
     "sanitary", "infection_outbreak", "chief_doctor"),
    ("Врач требует деньги за бесплатную по ОСМС операцию, иначе отказывается оперировать. "
     "Пациент в тяжёлом состоянии, время идёт. Это вымогательство.",
     "financial", "illegal_payment", "deputy_chief"),
    ("Пожилому пациенту отказали в приёме и выгнали из поликлиники, несмотря на боли в "
     "груди. По дороге домой ему стало плохо. Есть угроза жизни.",
     "quality_of_care", "care_refusal", "chief_doctor"),
]


def build_critical_appeals() -> list[dict]:
    appeals = []
    for i, (text, category, subcategory, level) in enumerate(CRITICAL_CASES):
        appeals.append({
            "scenario": "critical",
            "requester_key": f"crit_{i}",
            "requester_name": make_name(300 + i),
            "requester_type": "relative" if i % 2 else "patient",
            "affiliation": region_for(i),
            "title": "Критическое обращение — угроза жизни/здоровью",
            "text": text,
            "category": category,
            "subcategory": subcategory,
            "region": region_for(i),
            "submitted_at": NOW - timedelta(hours=1 + i * 3),
            "status": "escalated",
            "risk_level": "critical",
            "risk_score": 0.95,
            "risk_reasons": ["Угроза жизни или здоровью пациента", "Требует немедленной реакции"],
            "tags": ["критическое", "эскалация"],
            "is_escalated": True,
            "escalation_level": level,
            "escalation_reason": "Критическое обращение с риском для жизни/здоровья пациента",
        })
    return appeals


# ============================================================
# Сценарий 3: жалобы на качество медпомощи (→ Служба качества)
# ============================================================

CARE_QUALITY_TEXTS = [
    "Врач поставил неверный диагноз, из-за чего лечение не помогло и стало хуже.",
    "Медсестра нахамила и отказалась помочь с элементарной процедурой.",
    "Врач даже не осмотрел меня, выписал лекарства формально за минуту.",
    "После лечения возникли осложнения, врач отказывается признавать ошибку.",
    "Приём длился две минуты, врач не выслушал жалобы и отправил домой.",
    "Некомпетентный врач назначил лечение без обследования, стало только хуже.",
    "Грубое отношение персонала, никто не объясняет назначения и диагноз.",
    "Врач перепутал результаты анализов и назначил ненужное лечение.",
    "Отказали в консультации узкого специалиста без объяснения причин.",
    "Халатное отношение: капельницу поставили с нарушениями, стало плохо.",
    "Лечение назначено не по протоколу, эффекта нет уже месяц.",
    "Врач ведёт приём равнодушно, пациентов слишком много, времени не хватает.",
]


def build_care_quality_appeals() -> list[dict]:
    appeals = []
    for i, text in enumerate(CARE_QUALITY_TEXTS):
        resolved = i % 3 == 0
        appeals.append({
            "scenario": "care_quality",
            "requester_key": f"quality_{i}",
            "requester_name": make_name(400 + i),
            "requester_type": "patient",
            "affiliation": region_for(i + 2),
            "title": "Жалоба на качество медицинской помощи",
            "text": text,
            "category": "quality_of_care",
            "subcategory": "treatment_quality",
            "region": region_for(i + 2),
            "submitted_at": NOW - timedelta(days=1 + i, hours=i),
            "status": "resolved" if resolved else "in_progress",
            "risk_level": "medium",
            "risk_score": 0.45,
            "risk_reasons": ["Жалоба на качество медпомощи"],
            "tags": ["качество", "медпомощь"],
        })
    return appeals


# ============================================================
# Сценарий 4: хронический заявитель (доступность/запись)
# ============================================================

REPEAT_TEXTS = [
    "Опять не могу записаться к врачу — талонов нет уже неделю.",
    "Снова огромная очередь, ждал приёма больше трёх часов.",
    "Электронная запись не работает, дозвониться в регистратуру невозможно.",
    "Меня открепили от поликлиники без моего согласия, требую разобраться.",
    "Направление к специалисту не дают, гоняют по кабинетам.",
    "Записался на приём, но врача не было на месте. Потратил день зря.",
]


def build_repeat_appeals() -> list[dict]:
    appeals = []
    key = "repeat_patient_1"
    name = make_name(500)
    region = REGIONS[3]
    for i in range(27):
        days_ago = int(i * 6.5)
        text = REPEAT_TEXTS[i % len(REPEAT_TEXTS)]
        appeals.append({
            "scenario": "repeat_complainant",
            "requester_key": key,
            "requester_name": name,
            "requester_type": "patient",
            "affiliation": region,
            "title": "Проблема с записью и доступностью помощи",
            "text": text,
            "category": "access",
            "subcategory": "appointment",
            "region": region,
            "submitted_at": NOW - timedelta(days=days_ago),
            "status": "resolved" if i % 2 == 0 else "pending_review",
            "risk_level": "low",
            "risk_score": 0.2,
            "risk_reasons": ["Повторные обращения одного заявителя"],
            "tags": ["доступность", "запись"],
            "from_repeat_complainant": True,
        })
    return appeals


# ============================================================
# Сценарий 6: дубликаты (8 пар = 16 обращений)
# ============================================================

DUP_TEXTS = [
    ("Не пришёл результат анализа крови, жду уже две недели.", "diagnostics", "results_delay"),
    ("Прошу выдать выписку из медицинской карты для санатория.", "documents", "medical_record"),
    ("Не могу оформить больничный лист, отправляют из кабинета в кабинет.", "documents", "sick_leave"),
    ("Запишите меня к кардиологу, направление есть, талонов нет.", "access", "referral"),
    ("Прошу разъяснить, почему с меня взяли оплату за услугу по ОСМС.", "financial", "osms"),
    ("Аппарат УЗИ не работает, обследование постоянно переносят.", "diagnostics", "imaging"),
    ("Нет талонов на вакцинацию ребёнка, прошу помочь с записью.", "preventive", "vaccination"),
    ("Прошу прикрепить меня к поликлинике по месту жительства.", "access", "attachment"),
]


def build_duplicate_appeals() -> list[dict]:
    appeals = []
    for i, (text, category, subcategory) in enumerate(DUP_TEXTS):
        key = f"dup_{i}"
        name = make_name(600 + i)
        region = region_for(i + 1)
        for j in range(2):  # исходное + дубликат
            appeals.append({
                "scenario": "duplicates",
                "requester_key": key,
                "requester_name": name,
                "requester_type": "patient",
                "affiliation": region,
                "title": "Повторное обращение",
                "text": text if j == 0 else (text + " Повторно, ответа так и нет."),
                "category": category,
                "subcategory": subcategory,
                "region": region,
                "submitted_at": NOW - timedelta(days=3 * i, hours=6 * j),
                "status": "pending_review",
                "risk_level": "low",
                "risk_score": 0.15,
                "risk_reasons": ["Повторная подача того же вопроса"],
                "tags": ["дубликат"],
            })
    return appeals


# ============================================================
# Фоновый поток: нормальные обращения по всем категориям
# ============================================================

NORMAL_TEMPLATES = [
    ("medicines", "pharmacy", "Аптека работает по сокращённому графику, неудобно получать лекарства."),
    ("emergency", "emergency_care", "Долго ждал бригаду скорой, но помощь в итоге оказали."),
    ("hospitalization", "ward_conditions", "В палате душно и не хватает мест, прошу улучшить условия."),
    ("hospitalization", "nutrition", "Питание в стационаре однообразное, нет диетического меню."),
    ("quality_of_care", "treatment_quality", "В целом лечением доволен, но хотелось бы больше внимания."),
    ("access", "queue", "Большие очереди в поликлинике по утрам, прошу оптимизировать."),
    ("access", "appointment", "Не всегда удобное время записи, нет вечерних приёмов."),
    ("medical_staff", "rudeness", "Сотрудник регистратуры общался невежливо."),
    ("diagnostics", "lab_tests", "Результаты анализов приходят с задержкой."),
    ("preventive", "screening", "Прошу включить меня в программу диспансеризации."),
    ("preventive", "vaccination", "Уточните график вакцинации против гриппа."),
    ("financial", "paid_services", "Прошу разъяснить стоимость платной услуги."),
    ("documents", "medical_certificate", "Нужна медицинская справка для работы."),
    ("legal", "patient_rights", "Прошу разъяснить мои права как пациента."),
    ("sanitary", "sanitary_conditions", "В коридоре давно не проводили уборку."),
]

NORMAL_STATUSES = ["new", "pending_review", "in_progress", "resolved", "resolved"]
NORMAL_RISK = ["low", "low", "low", "medium"]


def build_normal_appeals() -> list[dict]:
    appeals = []
    for i in range(130):
        category, subcategory, base = NORMAL_TEMPLATES[i % len(NORMAL_TEMPLATES)]
        status = NORMAL_STATUSES[i % len(NORMAL_STATUSES)]
        risk = NORMAL_RISK[i % len(NORMAL_RISK)]
        appeals.append({
            "scenario": "normal",
            "requester_key": f"normal_{i}",
            "requester_name": make_name(700 + i),
            "requester_type": "patient" if i % 5 else "relative",
            "affiliation": region_for(i),
            "title": base[:60],
            "text": base,
            "category": category,
            "subcategory": subcategory,
            "region": region_for(i),
            "submitted_at": NOW - timedelta(days=i % 45, hours=(i * 3) % 24),
            "status": status,
            "risk_level": risk,
            "risk_score": 0.15 if risk == "low" else 0.4,
            "risk_reasons": [],
            "tags": [category],
        })
    return appeals


def build_all_appeals() -> list[dict]:
    return (
        build_campaign_appeals()
        + build_outbreak_appeals()
        + build_critical_appeals()
        + build_care_quality_appeals()
        + build_repeat_appeals()
        + build_duplicate_appeals()
        + build_normal_appeals()
    )
