# Engineering Flagships

<p align="center">
  <img src="https://img.shields.io/badge/AI%20%26%20LLM-RAG%20Engineering-8B5CF6?style=for-the-badge" alt="AI and LLM" />
  <img src="https://img.shields.io/badge/DEFENSIVE%20SECURITY-Repo%20Analysis-0891B2?style=for-the-badge" alt="Defensive security" />
  <img src="https://img.shields.io/badge/MLOps-Deploy%20%26%20Observe-7C3AED?style=for-the-badge" alt="MLOps" />
</p>

<p align="center">
  <strong>Three practical engineering projects — designed, tested, and documented as independent applications.</strong>
</p>

<p align="center">
  <a href="https://github.com/mehrabja">Mehrab Jalilian</a> ·
  <a href="https://mehrabjalilian.site/">Portfolio</a> ·
  <a href="https://www.linkedin.com/in/mehrab-jalilian">LinkedIn</a>
</p>

---

## Project constellation

| Project | Focus | What it demonstrates |
|---|---|---|
| [**ContextForge**](./contextforge/) | LLM / RAG engineering | Document ingestion, source-grounded retrieval, optional OpenAI-compatible generation, citations, evaluation |
| [**RepoSentinel**](./reposentinel/) | Defensive application security | Local repository checks, secret-pattern detection, insecure-code/configuration findings, JSON and SARIF reports |
| [**ModelOps Launchpad**](./modelops-launchpad/) | DevOps / MLOps | Reproducible model training, FastAPI inference, health/readiness, metrics, Docker, CI |

Each folder is independently runnable. No project requires credentials to run its local baseline. ContextForge's external LLM generation is optional and requires an explicitly configured OpenAI-compatible endpoint.

## 01 · ContextForge — source-grounded RAG

A compact retrieval-augmented generation service that ingests text and Markdown, stores chunk metadata locally, retrieves relevant passages, and returns answers with source references.

- Local deterministic retrieval baseline for repeatable demos.
- Optional OpenAI-compatible embeddings and chat-completions endpoints.
- Source IDs and quoted evidence are returned with each answer.
- Evaluation harness reports Recall@K and reciprocal rank on a small, versioned dataset.
- Retrieved documents are treated as untrusted data; the prompt tells the model not to follow instructions found inside them.

**Start:** [ContextForge README](./contextforge/README.md)

## 02 · RepoSentinel — defensive repository checks

A local-only security hygiene scanner for source repositories and deployment configuration.

- Detects common secret-like patterns, unsafe Python constructs, risky Dockerfile settings, and permissive GitHub Actions token permissions.
- Emits human-readable findings or machine-readable JSON / SARIF 2.1.0.
- Supports severity thresholds for CI gating.
- Skips common generated/vendor directories and enforces a per-file size limit.
- Does not contact remote hosts, exploit targets, or claim to replace a professional security review.

**Start:** [RepoSentinel README](./reposentinel/README.md)

## 03 · ModelOps Launchpad — train, serve, observe

A reproducible ML service template with a small deterministic classifier and a production-shaped HTTP interface.

- Deterministic local dataset and training script.
- Versioned model artifact and metadata.
- FastAPI prediction endpoint plus liveness/readiness endpoints.
- Prometheus-compatible request counters and latency histogram.
- Docker image, Compose stack, tests, and least-privilege GitHub Actions workflow.

**Start:** [ModelOps Launchpad README](./modelops-launchpad/README.md)

## Engineering principles

- **Reproducibility:** fixed seeds, explicit configuration, tests, and clear run commands.
- **Security by default:** no committed credentials; minimal workflow permissions; local-only security scanning.
- **Honest scope:** baseline implementations are labelled as such; optional integrations and production hardening are documented.
- **Observable behavior:** health checks, structured outputs, metrics, and evaluation reports.

## Repository layout

```text
.
├── contextforge/
│   ├── app/
│   ├── tests/
│   ├── eval/
│   └── .github/workflows/
├── reposentinel/
│   ├── reposentinel/
│   ├── tests/
│   └── .github/workflows/
└── modelops-launchpad/
    ├── app/
    ├── scripts/
    ├── tests/
    └── .github/workflows/
```

## About the author

**Mehrab Jalilian** · AI engineering · machine learning · backend systems · performance and security research.

- GitHub: https://github.com/mehrabja
- Website: https://mehrabjalilian.site/
- LinkedIn: https://www.linkedin.com/in/mehrab-jalilian
