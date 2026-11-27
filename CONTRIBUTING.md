# Contributing

Contributions should keep the three projects independently runnable and preserve their documented safety boundaries.

## Development checks

### ContextForge

```bash
cd contextforge
pip install -r requirements.txt
pytest -q
PYTHONPATH=. python eval/run_eval.py
```

### RepoSentinel

```bash
cd reposentinel
pip install -e ".[dev]"
pytest -q
reposentinel reposentinel --format sarif --output reposentinel.sarif --fail-on critical
```

### ModelOps Launchpad

```bash
cd modelops-launchpad
pip install -r requirements-dev.txt
python scripts/train.py --output-dir artifacts
pytest -q
docker build -t modelops-launchpad:test .
```

## Expectations

- Add tests for new behavior and security-sensitive edge cases.
- Do not commit generated artifacts, secrets, customer data, or model files trained on private data.
- Keep GitHub Actions permissions minimal.
- Document optional provider configuration and any outbound data flow.
- Label experimental or simulated functionality accurately.
