"""Tests for GitHub discovery CLI."""

from __future__ import annotations

from commands.github_cli import build_parser, main, parse_org_list


def test_parse_org_list_trims_and_splits() -> None:
    assert parse_org_list(" acme , labs ") == ["acme", "labs"]


def test_parse_org_list_rejects_empty() -> None:
    try:
        parse_org_list(" , ")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_github_cli_requires_orgs() -> None:
    assert main([]) == 2


def test_github_cli_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert main(["--orgs", "acme"]) == 2


def test_github_cli_help_includes_apm_topic_regex() -> None:
    parser = build_parser()
    action_dests = {action.dest for action in parser._actions}
    assert "apm_topic_regex" in action_dests


def test_github_cli_rejects_invalid_apm_topic_regex(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    assert main(["--orgs", "acme", "--apm-topic-regex", "["]) == 2


def test_github_cli_rejects_apm_topic_regex_without_capture_group(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    assert main(["--orgs", "acme", "--apm-topic-regex", "^apm-.+$"]) == 2
