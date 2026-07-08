# Docker Assets

This directory documents repository-level container conventions.

- root `docker-compose.yml` is the primary runtime entry point
- `docker-compose.dev.yml` and `docker-compose.prod.yml` provide overlays
- `backend/Dockerfile` and `frontend/Dockerfile` remain the source of truth for application images
- `nginx/` holds reverse proxy configuration consumed by Compose

Future environment-specific Compose fragments or image build assets should live here if the repository grows beyond the current base/overlay pattern.
