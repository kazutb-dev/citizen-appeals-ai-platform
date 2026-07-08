"""Таксономия обращений MedHubHAQ: группа (category) + подкатегория
(subcategory) + маршрутизация в подразделение медицинской организации + SLA.

Домен — здравоохранение (обращения граждан по медицинским вопросам).
Коды подразделений — см. departments_data.py.
"""

CATEGORY_GROUPS: dict[str, dict] = {
    "medicines": {
        "label": "Лекарственное обеспечение",
        "subcategories": {
            "drug_shortage": "Отсутствие лекарств",
            "free_drugs": "Льготные и бесплатные лекарства",
            "pharmacy": "Работа аптеки",
            "prescription": "Выписка рецепта",
            "drug_quality": "Качество препаратов",
        },
    },
    "emergency": {
        "label": "Скорая и неотложная помощь",
        "subcategories": {
            "ambulance_delay": "Задержка скорой помощи",
            "ambulance_refusal": "Отказ в выезде",
            "emergency_care": "Экстренная помощь",
            "triage": "Сортировка в приёмном отделении",
        },
    },
    "hospitalization": {
        "label": "Госпитализация и стационар",
        "subcategories": {
            "admission_refusal": "Отказ в госпитализации",
            "discharge": "Выписка из стационара",
            "ward_conditions": "Условия пребывания в палате",
            "nutrition": "Питание в стационаре",
            "bed_shortage": "Отсутствие мест",
        },
    },
    "quality_of_care": {
        "label": "Качество медицинской помощи",
        "subcategories": {
            "misdiagnosis": "Ошибка диагностики",
            "treatment_quality": "Качество лечения",
            "malpractice": "Врачебная ошибка / халатность",
            "complications": "Осложнения после лечения",
            "care_refusal": "Отказ в оказании помощи",
        },
    },
    "access": {
        "label": "Доступность и запись к врачу",
        "subcategories": {
            "appointment": "Запись на приём",
            "queue": "Очереди и ожидание",
            "attachment": "Прикрепление к поликлинике",
            "referral": "Направление к специалисту",
            "remote_area": "Доступность в сельской местности",
        },
    },
    "medical_staff": {
        "label": "Работа медицинского персонала",
        "subcategories": {
            "ethics": "Этика и деонтология",
            "rudeness": "Грубость персонала",
            "competence": "Компетентность врача",
            "staff_shortage": "Нехватка специалистов",
        },
    },
    "diagnostics": {
        "label": "Диагностика и обследования",
        "subcategories": {
            "lab_tests": "Лабораторные анализы",
            "imaging": "КТ / МРТ / УЗИ / рентген",
            "results_delay": "Задержка результатов",
            "equipment": "Медицинское оборудование",
        },
    },
    "preventive": {
        "label": "Профилактика и вакцинация",
        "subcategories": {
            "vaccination": "Вакцинация",
            "screening": "Скрининг и диспансеризация",
            "maternal": "Охрана материнства и детства",
            "health_promotion": "Санитарное просвещение",
        },
    },
    "financial": {
        "label": "ОСМС и платные услуги",
        "subcategories": {
            "osms": "Обязательное соц. медстрахование (ОСМС)",
            "paid_services": "Платные услуги",
            "illegal_payment": "Неформальные платежи / поборы",
            "reimbursement": "Возмещение расходов",
        },
    },
    "sanitary": {
        "label": "Санитария и инфекционная безопасность",
        "subcategories": {
            "infection_outbreak": "Вспышка инфекции",
            "sanitary_conditions": "Санитарное состояние",
            "sterility": "Стерильность и дезинфекция",
            "waste": "Медицинские отходы",
        },
    },
    "documents": {
        "label": "Медицинские документы и справки",
        "subcategories": {
            "medical_certificate": "Медицинская справка",
            "sick_leave": "Больничный лист",
            "medical_record": "Медицинская карта / выписка",
            "disability": "Оформление инвалидности",
        },
    },
    "legal": {
        "label": "Права пациентов",
        "subcategories": {
            "complaint": "Жалоба",
            "patient_rights": "Нарушение прав пациента",
            "consent": "Информированное согласие",
            "data_privacy": "Врачебная тайна и данные",
        },
    },
    "other": {
        "label": "Прочее",
        "subcategories": {},
    },
}

VALID_CATEGORIES = set(CATEGORY_GROUPS)

# Тип заявителя (пациент и связанные лица)
REQUESTER_TYPES: dict[str, str] = {
    "patient": "Пациент",
    "relative": "Родственник пациента",
    "medical_worker": "Медицинский работник",
    "guardian": "Законный представитель",
    "external": "Внешний заявитель",
}

# Маршрутизация по группе → код подразделения (см. departments_data.py)
CATEGORY_ROUTING: dict[str, str] = {
    "medicines": "PHARMACY",
    "emergency": "EMERGENCY",
    "hospitalization": "INPATIENT",
    "quality_of_care": "QUALITY",
    "access": "REGISTRY",
    "medical_staff": "QUALITY",
    "diagnostics": "DIAGNOSTICS",
    "preventive": "POLYCLINIC",
    "financial": "INSURANCE",
    "sanitary": "EPID",
    "documents": "REGISTRY",
    "legal": "LEGAL",
    "other": "CHIEF",
}

# SLA на ответ по категории (часы)
CATEGORY_SLA_HOURS: dict[str, int] = {
    "medicines": 24,
    "emergency": 2,
    "hospitalization": 12,
    "quality_of_care": 48,
    "access": 24,
    "medical_staff": 48,
    "diagnostics": 24,
    "preventive": 72,
    "financial": 48,
    "sanitary": 6,
    "documents": 48,
    "legal": 72,
    "other": 72,
}

# Точечная маршрутизация по подкатегории (переопределяет групповую при необходимости)
SUBCATEGORY_ROUTING: dict[str, str] = {
    "infection_outbreak": "EPID",
    "vaccination": "POLYCLINIC",
    "maternal": "MATERNITY",
    "osms": "INSURANCE",
    "illegal_payment": "QUALITY",
    "equipment": "SUPPLY",
    "medical_record": "REGISTRY",
    "disability": "POLYCLINIC",
    "data_privacy": "LEGAL",
}


def route_department_code(category: str, subcategory: str | None) -> str:
    """Код подразделения, ответственного за обращение."""
    if subcategory and subcategory in SUBCATEGORY_ROUTING:
        return SUBCATEGORY_ROUTING[subcategory]
    return CATEGORY_ROUTING.get(category, "CHIEF")


def category_sla_hours(category: str) -> int:
    return CATEGORY_SLA_HOURS.get(category, 72)
