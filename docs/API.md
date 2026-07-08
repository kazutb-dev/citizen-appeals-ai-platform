# API

## Entry Point

The HTTP API is exposed under `/api` through Nginx.

## Main Domains

- authentication and sessions
- appeal intake and review
- draft responses
- requesters
- analytics and intelligence
- social monitoring
- integration center
- admin operations
- monitoring and health

## Contract Rules

- role-protected routes must use the RBAC hierarchy consistently
- public requester routes must not expose staff-only AI metadata
- any new schema field must be reflected in both backend and frontend contracts
- breaking changes require migration notes in pull requests and documentation
