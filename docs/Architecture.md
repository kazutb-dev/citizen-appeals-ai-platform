# Architecture

## Mission

Citizen Appeals AI Platform is a government-grade system for centralized intake, routing, monitoring, analytics, and AI-assisted processing of citizen appeals. The current domain focus is healthcare, but the architecture is designed to expand to additional public-sector agencies without rewriting the platform core.

## Core Principles

- local-only AI inference
- background-first AI execution
- centralized intake across channels
- deterministic audit trail for every important action
- real operational data, not demo analytics

## Major Components

- `frontend/`: React + TypeScript operator, analyst, admin, and requester portal
- `backend/`: FastAPI application, async ORM, RBAC, routing, analytics, and admin APIs
- `backend/app/agents/`: AI agents, orchestration, embeddings, vector search, executive briefs, and intelligence logic
- `worker`: arq background worker for AI analysis, RAG indexing, and social polling
- `postgres`: transactional storage + pgvector
- `redis`: queueing and SSE progress transport
- `nginx/`: public reverse proxy and TLS termination

## Key Data Domains

- appeals
- requesters
- departments
- draft responses
- social sources and posts
- knowledge documents and chunks
- clusters and duplicate relationships
- tenants, organizations, hospitals, and regions

## Diagrams

See the `architecture/` directory for Mermaid diagrams covering system context, containers, and data flow.
