"""AI Executive Brief — управленческие AI-сводки и рекомендации (локальный LLM).

Считает сводку по РЕАЛЬНЫМ агрегатам обращений (передаются вызывающим кодом) и
формулирует деловой текст через локальную модель. Синтетику не генерирует: если
данных нет — текст это отражает; если LLM недоступен — вызывающий код вернёт
агрегаты без текста (честный empty-state).
"""
from app.agents.llm_client import complete, complete_json
from app.core.i18n import language_directive

BRIEF_SYSTEM_BASE = (
    "Ты — аналитик национальной системы обращений граждан в сфере здравоохранения "
    "(MedHubHAQ). Пиши кратко, по-деловому, без выдумок — только по приведённым данным."
)

BRIEF_PROMPT = """Сформируй краткую управленческую сводку (executive brief) за сегодня
для руководителя здравоохранения на основе агрегированной статистики.

СТАТИСТИКА ЗА СУТКИ:
{stats_block}

ТОП КАТЕГОРИЙ ОБРАЩЕНИЙ:
{categories_block}

ТОП РЕГИОНОВ ПО КРИТИЧНЫМ ОБРАЩЕНИЯМ:
{regions_block}

Требования:
- 4–6 предложений, деловой тон;
- выдели главную проблему и наиболее вероятную причину;
- укажи регион или направление наибольшего риска;
- опирайся ТОЛЬКО на приведённые данные, ничего не выдумывай;
- ответь обычным текстом (без markdown, без списков)."""

ACTION_PROMPT = """Сформируй до 3 коротких ОПЕРАЦИОННЫХ рекомендаций для ситуационного центра.

СВОДКА:
{stats_block}

ПРОБЛЕМНЫЕ ТОЧКИ:
{hotspots_block}

КРИТИЧЕСКАЯ ОЧЕРЕДЬ:
{queue_block}

Требования:
- только конкретные действия, без поэзии и без общих фраз;
- каждая рекомендация должна иметь поля: problem, action, assignee;
- assignee = ответственная роль или подразделение;
- опирайся ТОЛЬКО на данные выше;
- верни строго JSON вида {{"items": [{{"problem": "...", "action": "...", "assignee": "..."}}]}}.
"""


def _fmt_stats(stats: dict) -> str:
    labels = {
        "appeals_today": "Обращений за сутки",
        "appeals_today_trend_pct": "Динамика к вчера, %",
        "critical_open": "Критичных открытых",
        "escalations": "Эскалаций",
        "sla_violations": "Нарушений SLA",
        "campaigns": "Кампаний",
        "duplicates": "Дубликатов",
        "medicine_shortage": "Обращений по лекарствам",
        "emergency_incidents": "Обращений по скорой/экстренной",
    }
    return "\n".join(f"- {labels.get(k, k)}: {v}" for k, v in stats.items())


async def generate_brief_text(
    stats: dict, categories: list[dict], regions: list[dict], lang: str = "ru"
) -> str:
    categories_block = "\n".join(
        f"- {c.get('label', c.get('category'))}: {c.get('count', 0)}"
        for c in categories[:6]
    ) or "- нет данных"
    regions_block = "\n".join(
        f"- {r.get('region')}: критичных {r.get('critical', 0)} из {r.get('total', 0)}"
        for r in regions[:5]
    ) or "- нет данных"
    prompt = BRIEF_PROMPT.format(
        stats_block=_fmt_stats(stats),
        categories_block=categories_block,
        regions_block=regions_block,
    )
    system = f"{BRIEF_SYSTEM_BASE} {language_directive(lang)}"
    return (await complete(prompt, max_tokens=400, system=system)).strip()


def _fmt_hotspots(hotspots: list[dict]) -> str:
    return "\n".join(
        f"- {item.get('name')}: критичных {item.get('critical', 0)}, просроченных {item.get('overdue', 0)}, всего {item.get('total', 0)}"
        for item in hotspots[:5]
    ) or "- нет данных"


def _fmt_queue(queue: list[dict]) -> str:
    return "\n".join(
        f"- #{item.get('id')}: {item.get('region')} / {item.get('category_label') or item.get('category')} / {item.get('status')} / ответственный: {item.get('responsible') or 'не назначен'} / приоритет: {item.get('priority')}"
        for item in queue[:6]
    ) or "- нет данных"


async def generate_action_recommendations(
    stats: dict, hotspots: list[dict], queue: list[dict], lang: str = "ru"
) -> list[dict]:
    prompt = ACTION_PROMPT.format(
        stats_block=_fmt_stats(stats),
        hotspots_block=_fmt_hotspots(hotspots),
        queue_block=_fmt_queue(queue),
    )
    system = (
        "Ты — операционный координатор ситуационного центра здравоохранения. "
        "Даёшь только короткие исполнимые рекомендации. "
        f"{language_directive(lang)}"
    )
    payload = await complete_json(prompt, max_tokens=500, system=system)
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    cleaned: list[dict] = []
    for item in items[:3]:
        if not isinstance(item, dict):
            continue
        problem = str(item.get("problem") or "").strip()
        action = str(item.get("action") or "").strip()
        assignee = str(item.get("assignee") or "").strip()
        if problem and action and assignee:
            cleaned.append({"problem": problem, "action": action, "assignee": assignee})
    return cleaned
