"""Сервис embeddings (по умолчанию BAAI/bge-m3, 1024 dim).

Модель загружается лениво и один раз на процесс. Кодирование выполняется
в thread-pool, чтобы не блокировать event loop (модель — CPU-bound).
Для e5-моделей добавляются префиксы "query: " / "passage: "; для остальных
(например, bge-m3) текст кодируется как есть.
"""
import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def _prep(text: str, prefix: str) -> str:
    # Префиксы обязательны только для e5-моделей; bge-m3 кодирует текст как есть.
    if "e5" in settings.EMBEDDING_MODEL.lower():
        return f"{prefix}: {text}"
    return text


def encode_sync(text: str, *, prefix: str = "query") -> list[float]:
    model = _get_model()
    vector = model.encode(_prep(text, prefix), normalize_embeddings=True)
    return vector.tolist()


def encode_batch_sync(texts: list[str], *, prefix: str = "passage") -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(
        [_prep(t, prefix) for t in texts], normalize_embeddings=True, batch_size=16
    )
    return [v.tolist() for v in vectors]


async def encode(text: str, *, prefix: str = "query") -> list[float]:
    return await asyncio.to_thread(encode_sync, text, prefix=prefix)


async def encode_batch(texts: list[str], *, prefix: str = "passage") -> list[list[float]]:
    return await asyncio.to_thread(encode_batch_sync, texts, prefix=prefix)


@lru_cache(maxsize=1)
def _get_reranker():
    # Ленивая загрузка cross-encoder (bge-reranker-v2-m3) — только при включённом reranker.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.RERANKER_MODEL)


def rerank_sync(query: str, candidates: list[str]) -> list[tuple[int, float]]:
    """Индексы кандидатов, отсортированные по релевантности запросу."""
    if not candidates:
        return []
    model = _get_reranker()
    scores = model.predict([(query, c) for c in candidates])
    order = sorted(range(len(candidates)), key=lambda i: float(scores[i]), reverse=True)
    return [(i, float(scores[i])) for i in order]


async def rerank(query: str, candidates: list[str]) -> list[tuple[int, float]]:
    return await asyncio.to_thread(rerank_sync, query, candidates)
