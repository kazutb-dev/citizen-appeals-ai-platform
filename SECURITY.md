# Security Policy

## Supported Branch

Security fixes are applied to `main`.

## Reporting a Vulnerability

Do not disclose vulnerabilities publicly through GitHub issues.

Send a private report that includes:

- affected component
- reproduction steps
- impact assessment
- suggested mitigation, if known

If direct private security intake is not yet available on GitHub, contact the maintainers through the repository owners and clearly mark the report as `SECURITY`.

## Sensitive Areas

Security-sensitive areas include:

- authentication and session handling
- RBAC and audit logging
- integrations and webhook intake
- document upload and RAG ingestion
- background workers and queues
- LLM prompt handling and model configuration
- PII hashing and requester data flows

## Hard Requirements

- never commit secrets, private keys, TLS certificates, `.env`, database dumps, uploads, or logs
- keep LLM processing local-only; do not route government data to cloud AI APIs
- run AI inference asynchronously through workers for heavy processing paths
- document migration strategy before destructive data changes

## Security Review Expectations

Security-relevant pull requests should include:

- threat surface summary
- validation steps
- rollback or mitigation notes
- any new environment variables or operational prerequisites
