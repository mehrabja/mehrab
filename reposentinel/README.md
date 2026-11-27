# RepoSentinel

[![CI coverage 71% — 2026-11-27](https://img.shields.io/badge/CI%20coverage-71%25%20%7C%202026--11--27-7C3AED?style=flat-square&logo=pytest&logoColor=white)](https://github.com/mehrabja/mehrab/actions/runs/45964104271)
[![RepoSentinel CI](https://github.com/mehrabja/mehrab/actions/workflows/reposentinel-ci.yml/badge.svg?branch=main)](https://github.com/mehrabja/mehrab/actions/workflows/reposentinel-ci.yml)

<p align="center">
  <img src="https://img.shields.io/badge/DEFENSIVE%20SECURITY-LOCAL%20SCANNER-0891B2?style=for-the-badge" alt="Defensive security scanner" />
  <img src="https://img.shields.io/badge/OUTPUT-JSON%20%7C%20SARIF%202.1.0-8B5CF6?style=for-the-badge" alt="JSON and SARIF" />
</p>

RepoSentinel is a local-only repository hygiene scanner. It checks source files and deployment configuration for a focused set of high-signal patterns and can emit SARIF for CI integration.

## Checks included

| Rule | Severity | Check |
|---|---|---|
| RS001–RS004 | High | Token-like strings, AWS access-key IDs, private-key headers, hard-coded credential assignments |
| RS010 | High | Python `eval()` / `exec()` |
| RS011 | High | `subprocess` execution with `shell=True` |
| RS012 | High | Pickle deserialization calls |
| RS013 | Medium | `yaml.load()` without an explicit loader |
| RS014 | High | Requests calls with TLS verification disabled |
| RS020–RS022 | Medium / High | Floating Docker tags, remote scripts piped to a shell, no declared runtime user |
| RS030–RS031 | High / Medium | Broad or write-enabled GitHub Actions token permissions |
| RS040 | High | Live-looking `.env` files (sample templates are excluded) |

This is a deliberately small ruleset. Findings need human review and can produce false positives or miss vulnerabilities.

## Install and run

Requires Python 3.11+. No third-party runtime packages are required.

```bash
cd reposentinel
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Human-readable report
reposentinel ../contextforge

# Machine-readable JSON
reposentinel ../modelops-launchpad --format json --output report.json

# SARIF 2.1.0
reposentinel . --format sarif --output reposentinel.sarif

# Fail when a high or critical finding exists
reposentinel ../some-repository --fail-on high
```

Or run without installation:

```bash
PYTHONPATH=. python -m reposentinel ../some-repository --format text
```

## Hands-on scanner demo

A deliberately unsafe, non-production fixture lives in [examples/demo-repo/](./examples/demo-repo/). It contains two small patterns so you can see the scanner report both rule IDs without executing the fixture:

```bash
reposentinel examples/demo-repo --format json --fail-on none
```

The expected findings are **RS010** (dynamic evaluation) and **RS011** (shell-enabled subprocess). The fixture is scanned as text; do not run its functions. To see a SARIF report instead:

```bash
reposentinel examples/demo-repo --format sarif --output demo.sarif --fail-on none
```

## Design and safety boundaries

- Local files only: no network requests, port scans, payload delivery, or exploitation.
- Does not follow symlinks; skips common generated/vendor directories, binary files, and files larger than 1 MB.
- Secret findings report file and line, not the matched value.
- Not a complete SAST, DAST, SCA, secrets-management, or penetration-testing product.
- Does not claim comprehensive OWASP Top 10 coverage; the rules cover only a narrow set of detectable source/configuration patterns.

## CI

The workflow runs unit tests and scans the implementation package with a critical-only gate. The workflow token is read-only. Review and tune rules before making the scanner a required check.

The GitHub Actions workflow reports measured package coverage in its job summary; no minimum coverage threshold is claimed.

## Roadmap

- [ ] Add configurable TOML rule profiles and path exclusions.
- [ ] Add dependency inventory and lockfile auditing.
- [ ] Add SARIF fingerprints and baseline suppression.
- [ ] Integrate Semgrep/Bandit rather than duplicating their full rule sets.
- [ ] Add Kubernetes and Terraform configuration checks.

## References

- [OWASP Top 10:2025](https://top10.owasp.org/2025/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

Mehrab Jalilian · [GitHub](https://github.com/mehrabja)
