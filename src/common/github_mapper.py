"""Build discovery mapping rows for GitHub repositories."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Iterator
from typing import Any

from common.appsec_yaml import (
    parse_appsec_yaml,
    resolve_production_branch,
    warn_if_apm_code_unconventional,
)
from integrations.github.client import (
    GitHubClient,
    parse_committer_identity,
    parse_commit_timestamp,
    repository_has_default_branch,
)

_LOG = logging.getLogger(__name__)

DEFAULT_APM_TOPIC_REGEX = r"^apm-(.+)$"


def compile_apm_topic_regex(pattern: str) -> re.Pattern[str]:
    """Compile and validate an APM topic regex with one capture group."""
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        msg = f"invalid --apm-topic-regex: {exc}"
        raise ValueError(msg) from exc
    if compiled.groups != 1:
        msg = "--apm-topic-regex must include exactly one capture group for the APM code"
        raise ValueError(msg)
    return compiled


def apm_code_from_topics(topics: Iterable[str], pattern: re.Pattern[str]) -> str | None:
    """Return APM code from the first lexicographically sorted matching topic."""
    sorted_topics = sorted(topics)
    matches: list[str] = []
    for topic in sorted_topics:
        match = pattern.fullmatch(topic)
        if match is None:
            continue
        code = match.group(1).strip()
        if code:
            matches.append(code)
    if not matches:
        return None
    if len(matches) > 1:
        _LOG.warning(
            "Multiple APM topics matched %r; using first lexicographic match %r",
            sorted_topics,
            matches[0],
        )
    return matches[0]


def github_mapping_row(
    *,
    org_login: str,
    repo_slug: str,
    repo_name: str,
    file_bytes: bytes | None,
    default_display: str,
    is_empty: bool,
    apm_code: str | None,
    last_committer_name: str | None = None,
    last_committer_email: str | None = None,
    last_commit_date: str | None = None,
) -> dict[str, Any]:
    """Assemble one GitHub discovery row (YAML used for production branch only)."""
    yaml_branch: str | None = None
    if file_bytes is not None:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("utf-8", errors="replace")
        parsed = parse_appsec_yaml(text)
        yaml_branch = parsed.production_branch

    production_branch = resolve_production_branch(yaml_branch, default_display)
    repository_path = f"{org_login}/{repo_slug}"
    if apm_code is not None:
        warn_if_apm_code_unconventional(apm_code, repository_path=repository_path)
    return {
        "apm_code": apm_code,
        "repository_path": repository_path,
        "repository_name": repo_name,
        "production_branch": production_branch,
        "github_org": org_login,
        "is_empty": is_empty,
        "last_committer_name": last_committer_name,
        "last_committer_email": last_committer_email,
        "last_commit_date": last_commit_date,
    }


def _empty_mapping_row(*, org_login: str, repo_name: str) -> dict[str, Any]:
    return github_mapping_row(
        org_login=org_login,
        repo_slug=repo_name,
        repo_name=repo_name,
        file_bytes=None,
        default_display="main",
        is_empty=True,
        apm_code=None,
        last_committer_name=None,
        last_committer_email=None,
        last_commit_date=None,
    )


def _mapping_row_for_repository(
    client: GitHubClient,
    *,
    org_login: str,
    repo: dict[str, Any],
    file_path: str,
    apm_topic_pattern: re.Pattern[str],
) -> dict[str, Any]:
    name = repo.get("name")
    repo_name = name if isinstance(name, str) and name.strip() else org_login

    if not repository_has_default_branch(repo):
        return _empty_mapping_row(org_login=org_login, repo_name=repo_name)

    default_branch = repo.get("default_branch")
    branch_ref = default_branch if isinstance(default_branch, str) else "main"

    latest_commit = client.repository_latest_commit(org_login, repo_name, sha=branch_ref)
    if latest_commit is None:
        return _empty_mapping_row(org_login=org_login, repo_name=repo_name)

    committer_name, committer_email = parse_committer_identity(latest_commit)
    last_commit_date = parse_commit_timestamp(latest_commit)
    topics = client.repository_topics(org_login, repo_name)
    apm_code = apm_code_from_topics(topics, apm_topic_pattern)
    raw = client.fetch_file_contents(
        org_login,
        repo_name,
        file_path,
        ref=branch_ref,
    )
    return github_mapping_row(
        org_login=org_login,
        repo_slug=repo_name,
        repo_name=repo_name,
        file_bytes=raw,
        default_display=branch_ref,
        is_empty=False,
        apm_code=apm_code,
        last_committer_name=committer_name,
        last_committer_email=committer_email,
        last_commit_date=last_commit_date,
    )


def iter_github_mapping(
    client: GitHubClient,
    file_path: str,
    org_logins: Iterable[str],
    *,
    completed_keys: set[tuple[str, str]],
    apm_topic_pattern: re.Pattern[str],
    max_repos: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield mapping rows for repositories under the given GitHub org logins."""
    new_count = 0
    for org_login in org_logins:
        for repo in client.iter_org_repositories(org_login):
            name = repo.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            repo_name = name.strip()
            key = (org_login, repo_name)
            if key in completed_keys:
                continue
            if max_repos is not None and new_count >= max_repos:
                return
            row = _mapping_row_for_repository(
                client,
                org_login=org_login,
                repo=repo,
                file_path=file_path,
                apm_topic_pattern=apm_topic_pattern,
            )
            new_count += 1
            yield row
