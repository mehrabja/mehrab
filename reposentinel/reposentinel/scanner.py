from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
}
MAX_FILE_BYTES = 1_000_000
SEVERITY_ORDER = {"info": 10, "low": 20, "medium": 30, "high": 40, "critical": 50}

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    message: str
    path: str
    line: int

SECRET_PATTERNS = [
    ("RS001", "Possible GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("RS002", "Possible AWS access key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("RS003", "Private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("RS004", "Possible hard-coded credential", re.compile(
        r"""(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b\s*[:=]\s*["']([^"'<>]{12,})["']"""
    )),
]

def _iter_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    for current, dirs, filenames in os.walk(target, followlinks=False):
        dirs[:] = sorted(
            name for name in dirs
            if name not in SKIP_DIRS and not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.is_file() and not path.is_symlink():
                yield path

def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""

def _python_findings(text: str, relative: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        line = getattr(node, "lineno", 1)
        if name in {"eval", "exec"}:
            findings.append(Finding(
                "RS010", "high", "Dynamic code execution",
                f"{name}() executes dynamically supplied code; validate the data flow and use a safer alternative.",
                relative, line,
            ))
        if name in {"subprocess.run", "subprocess.call", "subprocess.Popen"}:
            if any(
                item.arg == "shell" and isinstance(item.value, ast.Constant) and item.value.value is True
                for item in node.keywords
            ):
                findings.append(Finding(
                    "RS011", "high", "Shell-enabled subprocess",
                    "shell=True can turn untrusted input into command execution. Prefer argument arrays and shell=False.",
                    relative, line,
                ))
        if name in {"pickle.load", "pickle.loads"}:
            findings.append(Finding(
                "RS012", "high", "Unsafe pickle deserialization",
                "Loading untrusted pickle data can execute code. Use a safer format for untrusted inputs.",
                relative, line,
            ))
        if name == "yaml.load" and not any(item.arg == "Loader" for item in node.keywords):
            findings.append(Finding(
                "RS013", "medium", "YAML loader without explicit safe loader",
                "Specify yaml.SafeLoader or use yaml.safe_load for untrusted YAML.",
                relative, line,
            ))
        if name in {"requests.get", "requests.post", "requests.put", "requests.delete"}:
            if any(
                item.arg == "verify" and isinstance(item.value, ast.Constant) and item.value.value is False
                for item in node.keywords
            ):
                findings.append(Finding(
                    "RS014", "high", "TLS certificate verification disabled",
                    "verify=False disables TLS certificate verification and can expose traffic to interception.",
                    relative, line,
                ))
    return findings

def _content_findings(text: str, path: Path, relative: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule_id, title, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            candidate = match.group(1) if rule_id == "RS004" else match.group(0)
            if rule_id == "RS004" and any(
                marker in candidate.casefold()
                for marker in ("example", "replace", "changeme", "your_", "dummy", "placeholder")
            ):
                continue
            findings.append(Finding(
                rule_id, "high", title,
                "A credential-like value appears in source text. Rotate exposed credentials and move secrets to a secret manager.",
                relative, number,
            ))

    if path.name == "Dockerfile":
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"(?i)^\s*FROM\s+\S+:latest\b", line):
                findings.append(Finding(
                    "RS020", "medium", "Floating Docker base image",
                    "Pin the base image to a version or digest for reproducible builds.", relative, number,
                ))
            if re.search(r"(?i)\b(curl|wget)\b[^|]*\|\s*(?:sh|bash)\b", line):
                findings.append(Finding(
                    "RS021", "high", "Remote script piped to shell",
                    "Download, verify, and inspect installation scripts instead of piping remote content directly to a shell.",
                    relative, number,
                ))
        if re.search(r"(?im)^\s*FROM\s+", text) and not re.search(r"(?im)^\s*USER\s+\S+", text):
            findings.append(Finding(
                "RS022", "medium", "Dockerfile does not declare a runtime user",
                "Consider selecting an unprivileged USER in the runtime stage.", relative, 1,
            ))

    if relative.startswith(".github/workflows/"):
        if re.search(r"(?im)^\s*permissions\s*:\s*write-all\s*$", text):
            findings.append(Finding(
                "RS030", "high", "Workflow grants write-all permissions",
                "Declare the minimum required GITHUB_TOKEN permissions per workflow or job.", relative, 1,
            ))
        for match in re.finditer(r"(?im)^\s*contents\s*:\s*write\s*$", text):
            findings.append(Finding(
                "RS031", "medium", "Workflow has repository content write access",
                "Review whether contents: write is necessary; prefer read-only access when possible.",
                relative, text.count("\n", 0, match.start()) + 1,
            ))

    name = path.name.casefold()
    if name == ".env" or (
        name.startswith(".env.")
        and name not in {".env.example", ".env.sample", ".env.template"}
    ):
        findings.append(Finding(
            "RS040", "high", "Environment file may contain secrets",
            "Do not commit live environment files. Keep a sanitized .env.example and rotate exposed values.",
            relative, 1,
        ))
    return findings

def scan(target: str | Path) -> list[Finding]:
    requested = Path(target).expanduser()
    if requested.is_symlink():
        raise ValueError("scan target must not be a symbolic link")
    root = requested.resolve()
    if not root.exists():
        raise FileNotFoundError(f"scan target does not exist: {root}")
    findings = []
    for path in _iter_files(root):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            raw = path.read_bytes()
            if b"\x00" in raw:
                continue
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        relative = (
            path.relative_to(root).as_posix()
            if root.is_dir() else path.name
        )
        findings.extend(_content_findings(text, path, relative))
        if path.suffix.casefold() == ".py":
            findings.extend(_python_findings(text, relative))
    findings.sort(key=lambda item: (
        -SEVERITY_ORDER.get(item.severity, 0), item.path, item.line, item.rule_id
    ))
    return findings

def to_sarif(findings: list[Finding]) -> str:
    rules, results = {}, []
    for item in findings:
        rules[item.rule_id] = {
            "id": item.rule_id,
            "shortDescription": {"text": item.title},
        }
        level = "error" if item.severity in {"high", "critical"} else (
            "warning" if item.severity == "medium" else "note"
        )
        results.append({
            "ruleId": item.rule_id,
            "level": level,
            "message": {"text": item.message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": item.path},
                    "region": {"startLine": item.line},
                }
            }],
        })
    return json.dumps({
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {
                "name": "RepoSentinel",
                "version": "0.1.0",
                "rules": list(rules.values()),
            }},
            "results": results,
        }],
    }, indent=2)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reposentinel",
        description="Run local defensive security hygiene checks against a repository.",
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    parser.add_argument("--output", help="write report to a file")
    parser.add_argument(
        "--fail-on", choices=("none", "info", "low", "medium", "high", "critical"),
        default="high",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        findings = scan(args.path)
    except (OSError, ValueError) as exc:
        print(f"RepoSentinel: {exc}", file=sys.stderr)
        return 2
    if args.format == "sarif":
        report = to_sarif(findings)
    elif args.format == "json":
        report = json.dumps([asdict(item) for item in findings], indent=2)
    else:
        report = "\n".join(
            f"{item.severity.upper():8} {item.rule_id} {item.path}:{item.line} {item.title} — {item.message}"
            for item in findings
        ) or "RepoSentinel: no findings."
        if findings:
            report += f"\n\n{len(findings)} finding(s)."
    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    if args.fail_on == "none":
        return 0
    threshold = SEVERITY_ORDER[args.fail_on]
    return int(any(SEVERITY_ORDER[item.severity] >= threshold for item in findings))

if __name__ == "__main__":
    raise SystemExit(main())
