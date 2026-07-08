"""AI Executive Brief — утренняя управленческая сводка (локальный LLM).

Считает сводку по РЕАЛЬНЫМ агрегатам обращений (передаются вызывающим кодом) и
формулирует деловой текст через локальную модель. Синтетику не генерирует: если
данных нет — текст это отражает; если LLM недоступен — вызывающий код вернёт
агрегаты без текста (честный empty-state).
"""
from app.agents.llm_client import complete
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
