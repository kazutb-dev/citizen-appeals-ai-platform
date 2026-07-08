# Coding Standards

## General

- write production-oriented code, not demo code
- prefer explicit names over clever abstractions
- keep side effects and orchestration boundaries obvious
- preserve auditability and operational traceability

## Python

- follow Black formatting
- keep imports sorted with isort
- use Ruff to catch correctness and modernization issues
- prefer async-safe database and network flows

## TypeScript and React

- keep API access in dedicated client modules
- type all payloads crossing the network boundary
- avoid UI fallback data that can be mistaken for real operational information
- keep dashboards readable and decision-focused

## Documentation

- update docs when architecture, deployment, APIs, or operator workflows change
- explain migration and rollback impact when data behavior changes
