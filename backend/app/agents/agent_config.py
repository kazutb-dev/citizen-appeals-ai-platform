"""Настройки агентов из БД (agent_settings): включение, конфиг, промпты.

Админ-панель редактирует строки agent_settings; агенты читают их перед запуском.
Если строки нет — используются значения по умолчанию из кода агента.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_setting import AgentSetting

DEFAULT_AGENTS: dict[str, dict] = {
    "agent1": {
        "display_name": "Агент критичных обращений",
        "description": (
            "Выявляет критичные обращения: угроза жизни и здоровью пациентов, "
            "летальные исходы, отказ в помощи/госпитализации, отсутствие лекарств, "
            "вспышки инфекций, врачебная халатность и коррупция — и эскалирует "
            "руководству (главный врач / заместитель / заведующий отделением)."
        ),
    },
    "agent2": {
        "display_name": "Агент выявления кампаний",
        "description": (
            "Обнаруживает массовые и скоординированные обращения, в том числе "
            "кампании из социальных сетей против больницы, врача, отделения или региона."
        ),
    },
    "agent3": {
        "display_name": "Агент дубликатов",
        "description": "Находит повторные и семантически похожие обращения (pgvector).",
    },
    "agent4": {
        "display_name": "Агент подготовки ответов",
        "description": (
            "Готовит проекты официальных ответов с опорой на базу знаний "
            "(Кодекс о здоровье, приказы МЗ РК, клинические протоколы, "
            "внутренние регламенты) через RAG."
        ),
    },
    "agent5": {
        "display_name": "Агент анализа пациентов",
        "description": (
            "Анализирует историю обращений пациента: повторяющиеся темы, "
            "ранее решённые вопросы, частоту подачи; формирует профиль пациента."
        ),
    },
    "agent6": {
        "display_name": "Агент лекарственного обеспечения",
        "description": (
            "Выявляет обращения об отсутствии лекарств, льготных препаратов и "
            "проблемах аптек; маршрутизирует в аптеку/лекобеспечение."
        ),
    },
    "agent7": {
        "display_name": "Агент качества медицинской помощи",
        "description": (
            "Классифицирует жалобы на качество лечения, врачебные ошибки и работу "
            "персонала; маршрутизирует в службу качества и безопасности медпомощи."
        ),
    },
    "agent8": {
        "display_name": "Агент санитарно-эпидемиологического контроля",
        "description": (
            "Отслеживает обращения о вспышках инфекций, санитарном состоянии и "
            "инфекционной безопасности; маршрутизирует в санэпидслужбу."
        ),
    },
}


async def get_setting(db: AsyncSession, agent_key: str) -> AgentSetting | None:
    return (
        await db.execute(select(AgentSetting).where(AgentSetting.agent_key == agent_key))
    ).scalar_one_or_none()


async def ensure_defaults(db: AsyncSession) -> list[AgentSetting]:
    """Создаёт недостающие строки настроек агентов. Возвращает все настройки."""
    existing = {
        s.agent_key: s
        for s in (await db.execute(select(AgentSetting))).scalars()
    }
    for key, meta in DEFAULT_AGENTS.items():
        if key not in existing:
            setting = AgentSetting(
                agent_key=key,
                display_name=meta["display_name"],
                description=meta["description"],
                is_enabled=True,
                config={},
            )
            db.add(setting)
            existing[key] = setting
    await db.flush()
    return [existing[k] for k in sorted(existing)]


async def is_enabled(db: AsyncSession, agent_key: str) -> bool:
    setting = await get_setting(db, agent_key)
    return True if setting is None else bool(setting.is_enabled)


async def get_prompt(db: AsyncSession, agent_key: str, default: str) -> str:
    setting = await get_setting(db, agent_key)
    if setting is not None and setting.prompt_template:
        return setting.prompt_template
    return default


async def get_config(db: AsyncSession, agent_key: str, defaults: dict) -> dict:
    """Конфиг агента: значения из БД поверх значений по умолчанию."""
    setting = await get_setting(db, agent_key)
    merged = dict(defaults)
    if setting is not None and isinstance(setting.config, dict):
        merged.update(setting.config)
    return merged
