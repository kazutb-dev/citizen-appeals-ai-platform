# Deployment

## Environments

- local development via Docker Compose and optional Vite dev server
- production-like deployment behind Nginx with TLS

## Core Services

- PostgreSQL
- Redis
- backend API
- worker
- frontend
- Nginx
- Ollama or vLLM

## Production Notes

- terminate TLS in Nginx
- keep certificates outside the repository
- mount persistent volumes for PostgreSQL, Redis, uploads, and local model cache
- apply migrations before serving traffic
- preload or pull the required local LLM model before opening the platform to users
