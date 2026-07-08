# Security

## Non-Negotiable Rules

- no secrets in git
- no private certificates or keys in git
- no raw citizen identifiers in plaintext persistence
- no cloud LLM providers for protected government data

## Current Controls

- JWT in httpOnly cookies
- RBAC
- audit logging
- hashed requester identifiers
- environment-driven secrets
- background processing for heavy AI tasks

## Areas Requiring Ongoing Review

- webhook authenticity for future integrations
- upload validation and content scanning
- prompt and document poisoning resistance
- access review for admin functionality
