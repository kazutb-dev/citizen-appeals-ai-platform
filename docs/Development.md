# Development

## Local Startup

1. copy `.env.example` to `.env`
2. fill `SECRET_KEY`, `DB_PASSWORD`, and local LLM settings
3. run `docker compose up -d --build`
4. seed demo data if needed
5. for frontend-only iteration, use Vite dev mode on top of backend and worker containers

## Quality Gates

- Python formatting: Black + isort
- Python linting: Ruff
- frontend linting: ESLint
- repository formatting: Prettier
- hook automation: Husky + lint-staged + pre-commit

## Recommended Routine

- create a focused branch
- run local checks before opening a PR
- document schema changes and migration behavior
- keep generated local artifacts out of git
