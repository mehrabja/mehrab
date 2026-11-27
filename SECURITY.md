# Security Policy

## Scope

This repository contains three educational engineering projects:

- ContextForge: source-grounded retrieval and optional LLM generation.
- RepoSentinel: local source/configuration hygiene checks.
- ModelOps Launchpad: a synthetic ML training and inference service.

These projects are demonstrations and starting points. They are not certified security products and are not approved for processing regulated or confidential data without independent review and appropriate controls.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for this repository if it is enabled. Do not publish live credentials, private data, or a working exploit in a public issue.

Include the affected project, file or endpoint, impact, reproduction steps in a local test environment, and any suggested mitigation.

## Secrets and test data

- Never commit API keys, tokens, database credentials, private keys, or production data.
- Rotate any credential that may have been exposed.
- Use synthetic or sanitized data in examples and tests.
