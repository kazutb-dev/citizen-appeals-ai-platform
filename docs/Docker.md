# Docker

## Compose Files

- `docker-compose.yml`: base stack
- `docker-compose.dev.yml`: development overlay
- `docker-compose.prod.yml`: production overlay

## Operational Guidance

- use health checks for every long-running service
- prefer named volumes for stateful data
- keep API and worker images aligned to the same backend code revision
- avoid embedding secrets into images

## Local LLM Runtime

The repository now defines an `ollama` service and a one-shot `ollama-init` bootstrap container to pull the configured model into a shared volume.
