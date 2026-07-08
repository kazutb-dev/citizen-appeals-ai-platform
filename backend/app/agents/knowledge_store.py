"""RAG-поиск по базе знаний (knowledge_chunks, pgvector)."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


@dataclass
class RelevantChunk:
    text: str
    document_title: str
    doc_type: str
    similarity: float


async def find_relevant(
    db: AsyncSession,
    embedding: list[float],
    *,
    limit: int = 5,
    threshold: float = 0.55,
    query_text: str | None = None,
) -> list[RelevantChunk]:
    """Фрагменты документов базы знаний, релевантные обращению.

    Если включён reranker (RERANKER_ENABLED) и передан query_text — расширяет
    выборку кандидатов и переранжирует их bge-reranker для точности.
    """
    from app.config import settings

    use_reranker = bool(settings.RERANKER_ENABLED and query_text)
    fetch_limit = max(limit, min(limit * 4, 20)) if use_reranker else limit

    distance = KnowledgeChunk.embedding.cosine_distance(embedding)
    similarity = (1 - distance).label("similarity")

    stmt = (
        select(KnowledgeChunk.text, KnowledgeDocument.title, KnowledgeDocument.doc_type, similarity)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(KnowledgeDocument.status == "ready")
        .where(KnowledgeChunk.embedding.is_not(None))
        .where(similarity >= threshold)
        .order_by(distance)
        .limit(fetch_limit)
    )
    rows = (await db.execute(stmt)).all()
    chunks = [
        RelevantChunk(
            text=row[0], document_title=row[1], doc_type=row[2], similarity=float(row[3])
        )
        for row in rows
    ]
    if use_reranker and len(chunks) > 1:
        try:
            from app.agents import embedding_service

            order = await embedding_service.rerank(query_text, [c.text for c in chunks])
            chunks = [chunks[i] for i, _ in order]
        except Exception:  # noqa: BLE001 — reranker недоступен: векторный порядок
            pass
    return chunks[:limit]
