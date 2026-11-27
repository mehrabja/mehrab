import pytest
import json

from reposentinel.scanner import scan, to_sarif


def test_detects_token_and_live_env_file(tmp_path):
    (tmp_path / "app.py").write_text(
        'TOKEN = "ghp_' + "A" * 28 + '"\n',
        encoding="utf-8",
    )
    (tmp_path / ".env.production").write_text("PASSWORD=not-for-git\n", encoding="utf-8")
    rules = {item.rule_id for item in scan(tmp_path)}
    assert "RS001" in rules
    assert "RS040" in rules


def test_detects_shell_enabled_subprocess(tmp_path):
    (tmp_path / "unsafe.py").write_text(
        "import subprocess\nsubprocess.run(user_input, shell=True)\n",
        encoding="utf-8",
    )
    assert any(item.rule_id == "RS011" and item.line == 2 for item in scan(tmp_path))


def test_dockerfile_checks(tmp_path):
    (tmp_path / "Dockerfile").write_text(
        "FROM python:latest\nRUN curl https://example.invalid/install.sh | sh\n",
        encoding="utf-8",
    )
    rules = {item.rule_id for item in scan(tmp_path)}
    assert {"RS020", "RS021", "RS022"} <= rules


def test_safe_python_has_no_findings(tmp_path):
    (tmp_path / "safe.py").write_text(
        "def add(left: int, right: int) -> int:\n    return left + right\n",
        encoding="utf-8",
    )
    assert scan(tmp_path) == []


def test_sarif_is_valid_json(tmp_path):
    (tmp_path / "unsafe.py").write_text(
        "import pickle\npickle.loads(payload)\n",
        encoding="utf-8",
    )
    document = json.loads(to_sarif(scan(tmp_path)))
    assert document["version"] == "2.1.0"
    assert document["runs"][0]["tool"]["driver"]["name"] == "RepoSentinel"
    assert document["runs"][0]["results"][0]["ruleId"] == "RS012"


def test_refuses_symlink_scan_root(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    (target / "safe.py").write_text("VALUE = 1\n", encoding="utf-8")
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic link"):
        scan(alias)
