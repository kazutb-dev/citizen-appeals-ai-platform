# RAG

## Purpose

The Retrieval-Augmented Generation subsystem supports Agent 4 and other knowledge-driven assistants by grounding answers in uploaded legal and procedural documents.

## Current Pipeline

1. admin uploads a document
2. worker extracts text
3. document is chunked
4. chunks are embedded with `BAAI/bge-m3`
5. vectors are stored in PostgreSQL via pgvector
6. relevant chunks are retrieved and optionally reranked
7. the selected context is passed to the local LLM

## Storage

- `knowledge_documents`
- `knowledge_chunks`

## Operational Rules

- indexing happens asynchronously
- document failures must be visible to administrators
- generated answers must cite the legal basis where possible

## Improvement Path

The repository roadmap includes richer document metadata, usage metrics, retrieval-quality signals, and agent-to-document visibility.
