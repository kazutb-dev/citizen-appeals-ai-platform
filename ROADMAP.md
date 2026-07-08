# Roadmap

## Stage 1: Repository Foundation

- establish repository governance and contribution standards
- publish architecture and operational documentation
- add CI, issue templates, dependency automation, and CODEOWNERS

## Stage 2: Unified Intake Core

- persist source channel for every appeal
- require geolocation for portal-originated complaints
- support intake idempotency and cross-channel deduplication primitives

## Stage 3: Real Integration Layer

- replace mock integration center transports with real connector architecture
- add inbound normalization for E-Otinish, iKomek, CRM, and Damumed
- define health checks, retry strategy, and delivery status tracking

## Stage 4: AI Admin Platform

- per-agent model and generation parameters
- prompt and system prompt management
- agent and RAG testing tools
- queue, memory, CPU, GPU, and model-load observability

## Stage 5: Geographic Operations

- government facility registry sourced via Playwright and 2GIS workflows
- appeal map with precise incident coordinates
- region and organization-level geospatial analytics

## Stage 6: Social Monitoring Focus

- reduce supported platforms to Telegram and Instagram
- harden Instagram OAuth and polling flows
- build first-class Telegram monitoring for channels, groups, and comments

## Stage 7: Operational UX Simplification

- consolidate overlapping dashboards
- keep only decision-critical KPIs
- streamline workflows for operators, analysts, and administrators
