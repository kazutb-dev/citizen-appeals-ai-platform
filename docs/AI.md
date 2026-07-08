# AI

## Local-Only Inference Policy

The platform is restricted to self-hosted inference runtimes such as Ollama and vLLM. Cloud AI APIs are out of scope for production use because citizen appeal data must stay within state-controlled infrastructure.

## Current Agent Set

- Agent 1: critical escalation
- Agent 2: campaign and mass-appeal detection
- Agent 3: semantic duplicate detection
- Agent 4: response draft generation with RAG
- Agent 5: requester history and repeat-pattern analysis
- Agent 6: medicine supply routing
- Agent 7: care quality routing
- Agent 8: sanitary and epidemiological routing

## Execution Model

Agents run in background workers after intake. The orchestrator coordinates embeddings, similarity lookup, escalation, clustering, response drafting, and domain-specific routing.

## Planned Enhancements

- per-agent model selection and generation controls
- test harness and quality metrics
- per-agent runtime logs and confidence tuning
- retraining and evaluation workflow
