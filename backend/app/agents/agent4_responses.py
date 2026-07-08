"""Агент 4: генерация проектов официальных ответов.

Источники знаний (по приоритету):
1. RAG — загруженные документы базы знаний (Кодекс о здоровье, приказы МЗ РК,
   клинические протоколы, внутренние регламенты)
2. Запасной синтетический справочник app/data/medical_knowledge.py
"""
import time

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import agent_config, knowledge_store
from app.agents.llm_client import complete
from app.core.i18n import language_directive
from app.data.medical_knowledge import MEDICAL_KNOWLEDGE_BASE
from app.models.appeal import Appeal

RESPONSE_PROMPT = """
Ты — специалист медицинской организации по работе с обращениями граждан
(MedHubHAQ).

Напиши официальный ОТВЕТ на обращение пациента.

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Официальный, вежливый и доброжелательный тон, с уважением к пациенту
2. Обязательно опирайся на предоставленные нормативные документы (Кодекс о здоровье народа и системе здравоохранения РК, приказы МЗ РК, клинические протоколы, внутренние регламенты)
3. Укажи конкретные сроки рассмотрения
4. Опиши конкретные шаги, которые будут предприняты
5. Соблюдай врачебную тайну и защиту персональных данных
6. Объём: 150-300 слов
7. Язык ответа задаётся отдельной инструкцией ниже — строго соблюдай его
8. Начни ответ с уважительного приветствия заявителя по имени ({requester_name})

ОБРАЩЕНИЕ:
{appeal_text}

КАТЕГОРИЯ: {category}
РЕГИОН: {region}

ВЫДЕРЖКИ ИЗ НОРМАТИВНЫХ ДОКУМЕНТОВ (база знаний):
{knowledge_excerpts}

НОРМАТИВНЫЕ ДОКУМЕНТЫ: {regulations}
СРОК РАССМОТРЕНИЯ: {response_time}
ОТВЕТСТВЕННОЕ ПОДРАЗДЕЛЕНИЕ: {responsible_body}

Напиши ответ:
"""

RAG_CONFIG = {
    "rag_chunks": 5,
    "rag_threshold": 0.55,
}


class DraftResult(BaseModel):
    text: str
    legal_refs: list[dict] = Field(default_factory=list)
    confidence: float = 0.0
    generation_time_ms: int = 0


def _confidence(chunks: list[knowledge_store.RelevantChunk]) -> float:
    """Уверенность ответа: выше, когда ответ опирается на документы базы знаний.

    Без RAG-подтверждения — базовые 0.6; с документами растёт с их релевантностью.
    """
    if not chunks:
        return 0.6
    avg_similarity = sum(c.similarity for c in chunks) / len(chunks)
    coverage = min(1.0, len(chunks) / 3)
    return round(min(0.95, 0.6 + 0.25 * avg_similarity + 0.1 * coverage), 2)


async def generate(appeal: Appeal, db: AsyncSession, lang: str = "ru") -> DraftResult | None:
    category_knowledge = MEDICAL_KNOWLEDGE_BASE.get(
        appeal.category, MEDICAL_KNOWLEDGE_BASE["other"]
    )
    config = await agent_config.get_config(db, "agent4", RAG_CONFIG)

    # RAG: релевантные фрагменты загруженных документов
    chunks: list[knowledge_store.RelevantChunk] = []
    if appeal.embedding is not None:
        chunks = await knowledge_store.find_relevant(
            db,
            list(appeal.embedding),
            limit=config["rag_chunks"],
            threshold=config["rag_threshold"],
            query_text=appeal.text[:1500],
        )
    if chunks:
        excerpts = "\n---\n".join(
            f"[{c.document_title}]\n{c.text[:600]}" for c in chunks
        )
    else:
        excerpts = "(документы базы знаний по теме не найдены — используй нормативные документы ниже)"

    requester_name = appeal.requester.full_name if appeal.requester else "заявитель"

    started = time.monotonic()
    prompt = await agent_config.get_prompt(db, "agent4", RESPONSE_PROMPT)
    prompt_text = prompt.format(
        requester_name=requester_name,
        appeal_text=appeal.text[:1500],
        category=appeal.category,
        region=appeal.region,
        knowledge_excerpts=excerpts,
        regulations="\n".join(
            category_knowledge.get("regulations", ["Нормативные документы (справочный корпус)"])
        ),
        response_time=category_knowledge.get("response_time", "10 рабочих дней"),
        responsible_body=category_knowledge.get(
            "responsible_body", "Профильное ведомство"
        ),
    )
    draft_text = await complete(
        f"{prompt_text}\n\n{language_directive(lang)}",
        max_tokens=800,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)

    refs = [
        {"document": c.document_title, "doc_type": c.doc_type, "similarity": round(c.similarity, 3)}
        for c in chunks
    ] + [{"document": reg} for reg in category_knowledge.get("regulations", [])]

    return DraftResult(
        text=draft_text,
        legal_refs=refs,
        confidence=_confidence(chunks),
        generation_time_ms=elapsed_ms,
    )
