"""Оргструктура медицинской организации для маршрутизации обращений MedHubHAQ.

Иерархия задаётся через parent_code. Коды соответствуют матрице маршрутизации
(см. categories.py). response_sla_hours — целевой срок ответа подразделения.

Демо-организация: многопрофильная городская больница / управление
общественного здравоохранения (в мультитенантной модели — один tenant).
"""

ORG_NAME_RU = "Городская многопрофильная больница (демо-организация MedHubHAQ)"
ORG_NAME_KZ = "Қалалық көппрофильді аурухана (MedHubHAQ демо-ұйымы)"
ORG_NAME_EN = "City Multidisciplinary Hospital (MedHubHAQ demo organization)"

ORG_CONTACT = {
    "phone": "+7 (7172) 700-100",
    "email": "info@medhubhaq.kz",
    "address": "Республика Казахстан, г. Астана",
    "site": "medhubhaq.kz",
}

# code, name, short_name, parent_code, department_type, categories[], response_sla_hours
DEPARTMENTS = [
    # --- Руководство ---
    {"code": "HEALTH_ADMIN", "name": "Управление здравоохранения", "short_name": "Упр. здравоохранения", "parent_code": None,
     "department_type": "executive", "categories": ["other", "legal"], "response_sla_hours": 72},
    {"code": "CHIEF", "name": "Главный врач", "short_name": "Главный врач", "parent_code": "HEALTH_ADMIN",
     "department_type": "executive", "categories": ["other"], "response_sla_hours": 48},

    # --- Заместители главного врача ---
    {"code": "DEP_MED", "name": "Заместитель главного врача по медицинской части", "short_name": "Замглавврача (мед.)",
     "parent_code": "CHIEF", "department_type": "deputy", "categories": [], "response_sla_hours": 48},
    {"code": "DEP_ADMIN", "name": "Заместитель главного врача по административно-хозяйственной части", "short_name": "Замглавврача (адм.)",
     "parent_code": "CHIEF", "department_type": "deputy", "categories": [], "response_sla_hours": 48},

    # --- Служба качества и безопасности медпомощи ---
    {"code": "QUALITY", "name": "Служба поддержки пациентов и качества медицинской помощи", "short_name": "Служба качества",
     "parent_code": "DEP_MED", "department_type": "quality", "categories": ["quality_of_care", "medical_staff"], "response_sla_hours": 48},

    # --- Экстренная помощь ---
    {"code": "EMERGENCY", "name": "Приёмное отделение и служба скорой помощи", "short_name": "Приёмное / скорая",
     "parent_code": "DEP_MED", "department_type": "emergency", "categories": ["emergency"], "response_sla_hours": 2},

    # --- Стационар и клинические отделения ---
    {"code": "INPATIENT", "name": "Стационар", "short_name": "Стационар",
     "parent_code": "DEP_MED", "department_type": "inpatient", "categories": ["hospitalization"], "response_sla_hours": 12},
    {"code": "THERAPY", "name": "Терапевтическое отделение", "short_name": "Терапия",
     "parent_code": "INPATIENT", "department_type": "clinical", "categories": ["hospitalization"], "response_sla_hours": 24},
    {"code": "SURGERY", "name": "Хирургическое отделение", "short_name": "Хирургия",
     "parent_code": "INPATIENT", "department_type": "clinical", "categories": ["hospitalization"], "response_sla_hours": 24},
    {"code": "PEDIATRY", "name": "Педиатрическое отделение", "short_name": "Педиатрия",
     "parent_code": "INPATIENT", "department_type": "clinical", "categories": ["hospitalization"], "response_sla_hours": 24},
    {"code": "CARDIO", "name": "Кардиологическое отделение", "short_name": "Кардиология",
     "parent_code": "INPATIENT", "department_type": "clinical", "categories": ["hospitalization"], "response_sla_hours": 24},
    {"code": "MATERNITY", "name": "Родильное отделение", "short_name": "Роддом",
     "parent_code": "INPATIENT", "department_type": "clinical", "categories": ["preventive"], "response_sla_hours": 24},

    # --- Амбулаторная помощь ---
    {"code": "POLYCLINIC", "name": "Поликлиника (амбулаторная помощь)", "short_name": "Поликлиника",
     "parent_code": "DEP_MED", "department_type": "outpatient", "categories": ["preventive"], "response_sla_hours": 48},
    {"code": "REGISTRY", "name": "Регистратура и запись на приём", "short_name": "Регистратура",
     "parent_code": "POLYCLINIC", "department_type": "registry", "categories": ["access", "documents"], "response_sla_hours": 24},

    # --- Диагностика ---
    {"code": "DIAGNOSTICS", "name": "Отделение лабораторной и лучевой диагностики", "short_name": "Диагностика",
     "parent_code": "DEP_MED", "department_type": "diagnostics", "categories": ["diagnostics"], "response_sla_hours": 24},

    # --- Аптека и лекарственное обеспечение ---
    {"code": "PHARMACY", "name": "Аптека и лекарственное обеспечение", "short_name": "Аптека",
     "parent_code": "DEP_MED", "department_type": "pharmacy", "categories": ["medicines"], "response_sla_hours": 24},

    # --- Санитарно-эпидемиологическая служба ---
    {"code": "EPID", "name": "Санитарно-эпидемиологическая служба", "short_name": "Санэпид",
     "parent_code": "DEP_MED", "department_type": "epidemiology", "categories": ["sanitary"], "response_sla_hours": 6},

    # --- Административно-хозяйственная часть ---
    {"code": "INSURANCE", "name": "Отдел ОСМС и платных услуг", "short_name": "ОСМС / платные",
     "parent_code": "DEP_ADMIN", "department_type": "insurance", "categories": ["financial"], "response_sla_hours": 48},
    {"code": "IT_MED", "name": "Отдел цифровизации и медицинских информационных систем", "short_name": "Цифровизация / МИС",
     "parent_code": "DEP_ADMIN", "department_type": "it", "categories": [], "response_sla_hours": 24},
    {"code": "HR_MED", "name": "Отдел кадров", "short_name": "Отдел кадров",
     "parent_code": "DEP_ADMIN", "department_type": "hr", "categories": [], "response_sla_hours": 48},
    {"code": "LEGAL", "name": "Юридический отдел", "short_name": "Юр. отдел",
     "parent_code": "DEP_ADMIN", "department_type": "legal", "categories": ["legal"], "response_sla_hours": 72},
    {"code": "SUPPLY", "name": "Отдел снабжения и медицинского оборудования", "short_name": "Снабжение",
     "parent_code": "DEP_ADMIN", "department_type": "supply", "categories": [], "response_sla_hours": 48},
]

# Регионы Республики Казахстан (для региональной аналитики; хранятся в колонке region)
KZ_REGIONS = [
    "Астана",
    "Алматы",
    "Шымкент",
    "Абайская область",
    "Акмолинская область",
    "Актюбинская область",
    "Алматинская область",
    "Атырауская область",
    "Восточно-Казахстанская область",
    "Жамбылская область",
    "Жетысуская область",
    "Западно-Казахстанская область",
    "Карагандинская область",
    "Костанайская область",
    "Кызылординская область",
    "Мангистауская область",
    "Павлодарская область",
    "Северо-Казахстанская область",
    "Туркестанская область",
    "Улытауская область",
]
REGIONS = KZ_REGIONS
CAMPUS_LOCATIONS = KZ_REGIONS  # обратная совместимость имён импорта
