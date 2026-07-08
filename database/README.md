# Database

## Engine

- PostgreSQL 16
- pgvector extension for semantic search

## Schema Management

- Alembic revisions live under `backend/alembic/versions/`
- all schema changes must be introduced through migrations
- destructive changes require migration notes and rollback strategy

## Core Tables

- appeals
- requesters
- draft_responses
- appeal_clusters
- knowledge_documents
- knowledge_chunks
- social_posts
- agent_settings
- tenants / regions / healthcare_organizations / hospitals
