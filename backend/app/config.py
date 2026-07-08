from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Префикс Redis-списков с событиями прогресса агент-лаборатории.
# Живёт здесь, чтобы API-процесс не импортировал worker (и torch вместе с ним).
LAB_QUEUE_PREFIX = "ncaip:lab:"


class Settings(BaseSettings):
    """Конфигурация приложения. Секреты — только из окружения, без дефолтов."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Безопасность — обязательные, без дефолтов
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False  # True за TLS-терминацией в продуктиве

    # Инфраструктура
    DATABASE_URL: str
    REDIS_URL: str

    # --- LLM-провайдер (абстракция LLMProvider) — только локальный инференс ---
    # ollama (по умолчанию) | vllm. Облачные API по умолчанию не используются.
    LLM_PROVIDER: str = "ollama"
    # Базовый URL локального инференса (ollama/vllm), напр. http://ollama:11434
    LLM_BASE_URL: str = "http://ollama:11434"
    # Имя локальной модели (ollama/vllm), напр. qwen2.5:7b-instruct
    LLM_LOCAL_MODEL: str = "qwen2.5:7b-instruct"
    # Путь к локальной модели (для vllm/llama.cpp/собственного контейнера)
    LOCAL_MODEL_PATH: str = ""

    # Embeddings — локальные (sentence-transformers), пример: BAAI/bge-m3
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    VECTOR_DB: str = "pgvector"
    # Reranker (bge-reranker-v2-m3) — переранжирование RAG-результатов (опционально)
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_ENABLED: bool = False

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Публичный адрес платформы (OAuth redirect, ссылки в уведомлениях)
    PUBLIC_BASE_URL: str = "http://localhost"

    # Файлы: вложения обращений и документы базы знаний
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_MB: int = 10

    # Пароли тестовых пользователей для seed (только dev/demo, в проде не задавать)
    SEED_ADMIN_PASSWORD: str = ""
    SEED_ANALYST_PASSWORD: str = ""
    SEED_OPERATOR_PASSWORD: str = ""
    SEED_PATIENT_PASSWORD: str = ""
    SEED_DOCTOR_PASSWORD: str = ""
    SEED_NURSE_PASSWORD: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
