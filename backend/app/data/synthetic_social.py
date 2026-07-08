"""Синтетические посты социальных сетей для платформы MedHubHAQ (здравоохранение).

Тема — упоминания медицинской организации/системы здравоохранения в социальных
сетях: доступность лекарств, скорая помощь, качество медпомощи, санитария,
запись к врачу, ОСМС и др. Используется для демонстрации мониторинга соцсетей и
корреляции «соцсети ↔ обращения».

ВСЕ ДАННЫЕ ПОЛНОСТЬЮ ВЫМЫШЛЕНЫ И СИНТЕТИЧНЫ:
- аккаунты, имена источников, тексты, метрики и URL не относятся к реальным лицам
  или организациям; персональные данные не используются;
- в выборку намеренно заложен «резонансный всплеск» (coordinated resonance spike)
  по одной горячей теме — вспышка инфекции в стационаре, чтобы продемонстрировать
  связку с обращениями пациентов на ту же тему.
"""
import random
from datetime import datetime, timedelta

rng = random.Random(20260611)
NOW = datetime.utcnow()

# ---------------------------------------------------------------------------
# Допустимые значения (соответствуют интерфейсу модели SocialPost)
# ---------------------------------------------------------------------------
# category ∈ {"medicines","emergency","hospitalization","quality_of_care",
#             "access","medical_staff","diagnostics","preventive","financial",
#             "sanitary","documents","legal","other"}
# region   ∈ регионы РК (или None)
# risk_level ∈ {"low","medium","high","critical"}
# sentiment  ∈ {"positive","neutral","negative","alarming"}
# platform   ∈ {"telegram","tiktok","instagram","youtube","facebook","vk"}

SPIKE_TOPIC = "Вспышка инфекции в стационаре"
SPIKE_REGION = "Астана"

# ---------------------------------------------------------------------------
# Резонансный всплеск: вспышка инфекции / антисанитария в стационаре.
# Последние ~72 часа, высокая вовлечённость, негатив/тревога.
# ---------------------------------------------------------------------------
SPIKE_POSTS = [
    {
        "platform": "telegram",
        "source_account": "@astana_zdorovie",
        "source_name": "Здоровье Астаны | Чат пациентов",
        "post_text": "В стационаре третий день массово заболевают пациенты — рвота, "
        "температура. Похоже на кишечную инфекцию. Санитарные нормы не соблюдают! "
        "Оформляйте обращения через MedHubHAQ, иначе никто не отреагирует. Репост!",
        "views": 41200, "likes": 3600, "comments": 940, "shares": 1280,
        "risk_level": "high", "sentiment": "alarming",
        "tags": ["стационар", "инфекция", "санитария"],
    },
    {
        "platform": "instagram",
        "source_account": "@astana_mama",
        "source_name": "Мамы Астаны",
        "post_text": "Положили ребёнка в больницу, а там заразился ещё и инфекцией 🤒 "
        "В палате грязно, уборку не делают. Когда наведут порядок?? "
        "#больница #инфекция #санитария",
        "views": 28700, "likes": 2900, "comments": 610, "shares": 430,
        "risk_level": "high", "sentiment": "alarming",
        "tags": ["стационар", "инфекция", "дети"],
    },
    {
        "platform": "tiktok",
        "source_account": "@med_pravda",
        "source_name": "Медицина как есть",
        "post_text": "POV: лёг лечить одно, а подхватил инфекцию в больнице 🤢 Уже "
        "несколько человек с одинаковыми симптомами. Сделайте уже проверку санэпид!",
        "views": 132000, "likes": 11800, "comments": 2050, "shares": 4100,
        "risk_level": "high", "sentiment": "negative",
        "tags": ["стационар", "инфекция"],
    },
    {
        "platform": "vk",
        "source_account": "patients_astana",
        "source_name": "Пациенты стационара",
        "post_text": "Собираем номера палат, где есть заболевшие, чтобы передать одним "
        "списком в санэпидслужбу. Пишите отделение и палату в комментариях — так "
        "быстрее добьёмся проверки, чем поодиночке.",
        "views": 12400, "likes": 1100, "comments": 870, "shares": 240,
        "risk_level": "medium", "sentiment": "negative",
        "tags": ["стационар", "координация"],
    },
    {
        "platform": "telegram",
        "source_account": "@patient_council",
        "source_name": "Совет пациентов",
        "post_text": "По нашим данным, причина — нарушение санитарного режима в отделении. "
        "Санэпидслужба выехала на проверку. Просим всех пострадавших оформить "
        "обращение в MedHubHAQ, чтобы зафиксировать масштаб.",
        "views": 33800, "likes": 1900, "comments": 520, "shares": 780,
        "risk_level": "high", "sentiment": "negative",
        "tags": ["стационар", "санэпид", "проверка"],
    },
    {
        "platform": "facebook",
        "source_account": "@rodstvenniki.pacientov",
        "source_name": "Родственники пациентов",
        "post_text": "Мама лежит в стационаре, заболела инфекцией уже в больнице. Это не "
        "случайность — это антисанитария и бездействие. Просим руководство немедленно "
        "провести дезинфекцию и разобраться.",
        "views": 21300, "likes": 1950, "comments": 640, "shares": 410,
        "risk_level": "high", "sentiment": "alarming",
        "tags": ["стационар", "инфекция", "санитария"],
    },
    {
        "platform": "instagram",
        "source_account": "@astana_zdorovie_ig",
        "source_name": "Здоровье Астаны",
        "post_text": "Просим временно перевести пациентов из отделения, где вспышка "
        "инфекции, пока проводят дезинфекцию. Кому-нибудь уже предложили перевод?",
        "views": 18900, "likes": 1500, "comments": 350, "shares": 260,
        "risk_level": "medium", "sentiment": "negative",
        "tags": ["стационар", "перевод", "инфекция"],
    },
]

# ---------------------------------------------------------------------------
# Фоновые посты по всем категориям здравоохранения (более ранний период).
# ---------------------------------------------------------------------------
OTHER_POSTS = [
    {
        "platform": "tiktok",
        "source_account": "@lekarstva_kz",
        "source_name": "Лекарства по льготе",
        "post_text": "Опять нет льготного инсулина в аптеке при поликлинике! Диабетики "
        "остались без препаратов. Сколько можно? Оформляем обращения массово.",
        "views": 51000, "likes": 4300, "comments": 760, "shares": 1200,
        "category": "medicines", "region": "Шымкент",
        "topic": "Отсутствие льготных лекарств", "risk_level": "high", "sentiment": "negative",
        "tags": ["лекарства", "льготные", "инсулин"],
    },
    {
        "platform": "telegram",
        "source_account": "@skoraya_help",
        "source_name": "Скорая помощь | Чат",
        "post_text": "Скорая ехала почти два часа на вызов к пожилому человеку. Это "
        "недопустимо при болях в сердце. Нужна проверка работы службы.",
        "views": 33800, "likes": 2600, "comments": 520, "shares": 640,
        "category": "emergency", "region": "Карагандинская область",
        "topic": "Задержка скорой помощи", "risk_level": "high", "sentiment": "alarming",
        "tags": ["скорая", "задержка"],
    },
    {
        "platform": "instagram",
        "source_account": "@poliklinika_astana",
        "source_name": "Пациенты поликлиники",
        "post_text": "Огромные очереди в поликлинике по утрам, талонов не хватает, "
        "электронная запись висит. Просим наладить запись к врачу.",
        "views": 22100, "likes": 1800, "comments": 540, "shares": 380,
        "category": "access", "region": "Астана",
        "topic": "Очереди и запись к врачу", "risk_level": "medium", "sentiment": "negative",
        "tags": ["запись", "очереди"],
    },
    {
        "platform": "facebook",
        "source_account": "@pacient.prava",
        "source_name": "Права пациентов",
        "post_text": "Врач требовал оплату за операцию, которая положена бесплатно по "
        "ОСМС. Это поборы. Просим разобраться и вернуть деньги.",
        "views": 19800, "likes": 1500, "comments": 470, "shares": 300,
        "category": "financial", "region": "Алматы",
        "topic": "Поборы за бесплатную помощь", "risk_level": "high", "sentiment": "negative",
        "tags": ["осмс", "поборы", "оплата"],
    },
    {
        "platform": "telegram",
        "source_account": "@kachestvo_med",
        "source_name": "Качество медпомощи",
        "post_text": "Поставили неверный диагноз, лечение не помогло, потеряли время. "
        "Просим провести экспертизу качества оказанной помощи.",
        "views": 13900, "likes": 1100, "comments": 380, "shares": 190,
        "category": "quality_of_care", "region": "Восточно-Казахстанская область",
        "topic": "Ошибка диагностики", "risk_level": "medium", "sentiment": "negative",
        "tags": ["качество", "диагноз"],
    },
    {
        "platform": "instagram",
        "source_account": "@spasibo_vracham",
        "source_name": "Спасибо врачам",
        "post_text": "Огромная благодарность бригаде хирургов — операция прошла успешно, "
        "отношение внимательное и человечное. Побольше бы таких специалистов! 🙏",
        "views": 16400, "likes": 1900, "comments": 180, "shares": 340,
        "category": "quality_of_care", "region": "Астана",
        "topic": "Благодарность врачам", "risk_level": "low", "sentiment": "positive",
        "tags": ["благодарность", "врачи"],
    },
    {
        "platform": "tiktok",
        "source_account": "@vakcina_info",
        "source_name": "Вакцинация | Инфо",
        "post_text": "В поликлинике удобно организовали вакцинацию против гриппа — запись "
        "онлайн, без очередей. Быстро и спокойно. Рекомендую не откладывать 💉",
        "views": 31000, "likes": 2900, "comments": 220, "shares": 410,
        "category": "preventive", "region": "Астана",
        "topic": "Вакцинация против гриппа", "risk_level": "low", "sentiment": "positive",
        "tags": ["вакцинация", "профилактика"],
    },
    {
        "platform": "vk",
        "source_account": "diagnostika_kz",
        "source_name": "Диагностика | Пациенты",
        "post_text": "Аппарат МРТ не работает вторую неделю, обследование постоянно "
        "переносят. Люди с направлениями не могут пройти диагностику вовремя.",
        "views": 8400, "likes": 540, "comments": 210, "shares": 70,
        "category": "diagnostics", "region": "Павлодарская область",
        "topic": "Простой диагностического оборудования", "risk_level": "medium", "sentiment": "negative",
        "tags": ["мрт", "диагностика"],
    },
    {
        "platform": "telegram",
        "source_account": "@apteka_chat",
        "source_name": "Аптека | Чат",
        "post_text": "Аптека при больнице работает по сокращённому графику, вечером не "
        "получить лекарства по рецепту. Просим продлить часы работы.",
        "views": 7600, "likes": 480, "comments": 160, "shares": 60,
        "category": "medicines", "region": "Актюбинская область",
        "topic": "График работы аптеки", "risk_level": "low", "sentiment": "negative",
        "tags": ["аптека", "график"],
    },
    {
        "platform": "facebook",
        "source_account": "@materinstvo.kz",
        "source_name": "Материнство и детство",
        "post_text": "В роддоме внимательный персонал и чисто, всё объяснили и поддержали. "
        "Спасибо за заботу о мамах и малышах! Так и должно быть.",
        "views": 15200, "likes": 1750, "comments": 210, "shares": 260,
        "category": "preventive", "region": "Туркестанская область",
        "topic": "Охрана материнства", "risk_level": "low", "sentiment": "positive",
        "tags": ["роддом", "материнство"],
    },
    {
        "platform": "telegram",
        "source_account": "@medpersonal_etika",
        "source_name": "Этика в медицине",
        "post_text": "Сотрудник регистратуры нагрубил пожилому пациенту, отказался помочь "
        "с записью. Просим напомнить персоналу о нормах медицинской этики.",
        "views": 9700, "likes": 720, "comments": 200, "shares": 110,
        "category": "medical_staff", "region": "Кызылординская область",
        "topic": "Этика персонала", "risk_level": "low", "sentiment": "negative",
        "tags": ["этика", "персонал"],
    },
    {
        "platform": "youtube",
        "source_account": "@zdorovie_explained",
        "source_name": "Здоровье. Объясняем",
        "post_text": "Разбираем, как подать обращение в MedHubHAQ, чтобы его быстро "
        "рассмотрели: что указать, как описать проблему с записью, лекарствами или "
        "качеством помощи, куда прикрепить документы. Видео-инструкция.",
        "views": 16800, "likes": 1450, "comments": 130, "shares": 290,
        "category": "other", "region": None,
        "topic": "Как подать обращение", "risk_level": "low", "sentiment": "positive",
        "tags": ["medhubhaq", "обращения"],
    },
    {
        "platform": "instagram",
        "source_account": "@osms_help",
        "source_name": "ОСМС | Помощь",
        "post_text": "Напоминаем: статус в системе ОСМС и право на бесплатные услуги "
        "можно проверить онлайн. Рассказываем по шагам, что делать при отказе. Сохраняйте!",
        "views": 13600, "likes": 1200, "comments": 140, "shares": 230,
        "category": "financial", "region": None,
        "topic": "Проверка статуса ОСМС", "risk_level": "low", "sentiment": "positive",
        "tags": ["осмс", "инструкция"],
    },
    {
        "platform": "facebook",
        "source_account": "@obratnaya.svyaz.med",
        "source_name": "Обратная связь. Здравоохранение",
        "post_text": "Подвели итоги опроса пациентов: больше всего обращений — по "
        "лекарствам и записи к врачу, больше всего благодарностей — врачам скорой и "
        "хирургам. Часть предложений уже в работе.",
        "views": 9400, "likes": 620, "comments": 170, "shares": 120,
        "category": "other", "region": None,
        "topic": "Опрос пациентов", "risk_level": "low", "sentiment": "neutral",
        "tags": ["опрос", "обратнаясвязь"],
    },
]


def build_social_posts() -> list[dict]:
    """Собирает синтетические посты соцсетей для seed.py.

    Возвращает список словарей, ключи которых соответствуют колонкам SocialPost.
    """
    posts: list[dict] = []

    # 1) Резонансный всплеск по теме вспышки инфекции в стационаре (~72 часа).
    for i, base in enumerate(SPIKE_POSTS):
        post = dict(base)
        post["topic"] = SPIKE_TOPIC
        post["category"] = "sanitary"
        post["region"] = SPIKE_REGION
        post["post_date"] = NOW - timedelta(hours=rng.uniform(1, 72))
        post["post_url"] = f"https://example.invalid/seed/spike-{i}"
        posts.append(post)

    # 2) Остальные посты по всем категориям (более ранний период).
    for j, base in enumerate(OTHER_POSTS):
        post = dict(base)
        post["post_date"] = NOW - timedelta(hours=rng.uniform(6, 600))
        post["post_url"] = f"https://example.invalid/seed/post-{j}"
        posts.append(post)

    return posts
