# ContextForge

[![CI coverage 85% — 2026-11-27](https://img.shields.io/badge/CI%20coverage-85%25%20%7C%202026--11--27-7C3AED?style=flat-square&logo=pytest&logoColor=white)](https://github.com/mehrabja/mehrab/actions/runs/45964099154)
[![ContextForge CI](https://github.com/mehrabja/mehrab/actions/workflows/contextforge-ci.yml/badge.svg?branch=main)](https://github.com/mehrabja/mehrab/actions/workflows/contextforge-ci.yml)

<p align="center">
  <img src="https://img.shields.io/badge/LLM-APPLICATIONS-8B5CF6?style=for-the-badge" alt="LLM applications" />
  <img src="https://img.shields.io/badge/RAG-SOURCE%20GROUNDED-0891B2?style=for-the-badge" alt="RAG" />
  <img src="https://img.shields.io/badge/EVALUATION-RECALL%40K%20%2B%20MRR-7C3AED?style=for-the-badge" alt="Retrieval evaluation" />
</p>

A compact source-grounded RAG API. ContextForge ingests text and Markdown, chunks and stores it locally, retrieves relevant passages, and returns answers with source references. An optional OpenAI-compatible chat-completions endpoint provides generated answers.

## Implemented

- Text/Markdown ingestion through `POST /v1/documents`.
- Persistent SQLite chunk store.
- Deterministic feature-hashing vectors and cosine retrieval for a credential-free local baseline. These are **not neural or semantic embeddings**.
- Optional OpenAI-compatible chat completions (including compatible local model servers).
- Source IDs (`[S1]`, `[S2]`) and passage quotes returned with each answer.
- System instructions that treat retrieved passages as untrusted evidence, not commands.
- Offline evaluation reporting Recall@K and MRR.
- Input size limits and API validation.

## Quick start

```bash
cd contextforge
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```


## Hands-on API demo

Start the API using the quick-start commands above, then open [examples/demo.http](./examples/demo.http) in VS Code with the REST Client extension. Send the document-ingestion request first, followed by the query request. The response includes the answer mode and a `sources` array containing source IDs, quoted passages, and retrieval scores.

The local baseline is extractive and uses deterministic feature hashing; it is not a neural embedding model. Configure an OpenAI-compatible endpoint only when you want generated answers.
API docs: http://127.0.0.1:8000/docs

### Ingest and query

```bash
curl -X POST http://127.0.0.1:8000/v1/documents \
  -H "Content-Type: application/json" \
  -d '{"source":"runbook.md","text":"A runbook defines an owner, trigger, recovery steps, and escalation path."}'

curl -X POST http://127.0.0.1:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What should a runbook define?","k":4}'
```

By default, the API returns an extractive response with retrieved source passages. Enable generation by configuring an OpenAI-compatible endpoint:

```bash
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_MODEL="your-local-chat-model"
# Set LLM_API_KEY only when required by your provider.
uvicorn app.main:app --reload
```

The provider must expose `POST /chat/completions`. No model or credentials are bundled. Documents are sent to an external service only when you explicitly configure a model endpoint.


The GitHub Actions workflow runs the API tests and reports measured line coverage in the workflow job summary. No minimum coverage threshold is claimed.
## Evaluation and tests

```bash
PYTHONPATH=. python eval/run_eval.py
pytest -q
```

The included fixture dataset is for regression checks, not a benchmark claim. Add task-specific relevance judgments before comparing embedding models.

## Security and limitations

Prompt instructions reduce but do not eliminate prompt-injection risk. The local feature-hashing vectorizer is a deterministic baseline, not semantic embedding. Review the [OWASP GenAI LLM Top 10 (2026)](https://genai.owasp.org/llm-top-10/) before extending this demo into an agentic or multi-tenant application. The demo has no authentication, tenant isolation, quotas, rate limiting, or document deletion. Do not expose it publicly with sensitive data without adding those controls.

## Roadmap

- [ ] Add a real embedding adapter and model versioning.
- [ ] Add PostgreSQL + pgvector persistence.
- [ ] Add tenant isolation, authentication, quotas, and deletion.
- [ ] Add reranking and a reviewed prompt-injection evaluation suite.

Mehrab Jalilian · [GitHub](https://github.com/mehrabja)
