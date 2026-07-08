# Backend

## Stack

- FastAPI
- SQLAlchemy async ORM
- Alembic
- PostgreSQL + pgvector
- Redis + arq
- sentence-transformers embeddings

## Responsibilities

- accept and validate appeals
- enforce RBAC and session security
- orchestrate background AI pipelines
- manage knowledge documents and RAG indexing
- expose analytics, monitoring, integration, and admin endpoints

## Application Structure

- `app/routers/`: HTTP API surface
- `app/models/`: persistence models
- `app/schemas/`: Pydantic contracts
- `app/agents/`: AI orchestration and inference logic
- `app/core/`: auth, permissions, audit, events, exceptions
- `app/data/`: category dictionaries, seed data, geographic data

## Runtime Rules

- heavy AI analysis does not run inside synchronous request handlers
- schema changes are delivered through additive Alembic migrations where possible
- appeal actions must be audit-logged
- secrets come from environment variables only
