# Contributing

## Scope

This repository contains the production codebase of the Citizen Appeals AI Platform. Contributions must preserve the platform as a real government-grade intake, routing, monitoring, and analytics system. Do not introduce demo-only code, fake analytics, hardcoded secrets, or cloud LLM integrations.

## Before You Start

- Read the project README and the documentation in `docs/`.
- Open an issue for substantial architectural work before starting implementation.
- Keep changes focused. Cross-cutting refactors must include rationale and migration notes.

## Development Workflow

1. Fork the repository and create a branch from `main`.
2. Set up the environment with `.env.example`.
3. Run the stack with Docker Compose.
4. Apply database migrations before testing.
5. Run formatting, linting, and build checks before opening a PR.

## Commit Messages

Use conventional, professional commit messages:

- `feat: add integration health model`
- `fix: correct SLA deadline calculation`
- `docs: describe RAG ingestion flow`
- `refactor: simplify appeal routing service`

Do not use vague messages such as `update`, `changes`, or `fix stuff`.

## Pull Requests

Every pull request must include:

- problem statement
- implementation summary
- validation steps
- migration notes, if schema or data behavior changes
- screenshots or API examples for visible product changes

## Engineering Rules

- LLM inference must remain local-only (`ollama`, `vllm`, or equivalent self-hosted runtime).
- Never commit secrets, dumps, certificates, logs, uploads, or generated local caches.
- Database schema changes require a new Alembic migration.
- Background AI work belongs in workers, not synchronous HTTP request handlers.
- Favor real integrations and real empty states over mocks and demo fallbacks.

## Code Review Expectations

Reviewers will look for:

- production safety
- clear ownership boundaries
- backward-compatible migrations where possible
- observability and operational impact
- correctness for Russian and Kazakh usage paths

## Reporting Security Issues

Do not open public issues for vulnerabilities. Follow `SECURITY.md`.
