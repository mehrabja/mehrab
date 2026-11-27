from pathlib import Path

from reposentinel.scanner import scan


def test_documented_demo_fixture_shows_expected_rules() -> None:
    fixture = Path(__file__).resolve().parents[1] / "examples" / "demo-repo"
    findings = scan(fixture)
    rule_ids = {finding.rule_id for finding in findings}

    assert {"RS010", "RS011"}.issubset(rule_ids)
