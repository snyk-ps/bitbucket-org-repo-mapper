## 1. GitHub topics API and APM extraction

- [ ] 1.1 Add `GitHubClient.repository_topics(owner, repo)` calling `GET /repos/{owner}/{repo}/topics`
- [ ] 1.2 Add `apm_code_from_topics(topics, regex)` with lexicographic first-match and capture group 1
- [ ] 1.3 Unit tests: matching topic (`apm-ABC1` → `ABC1`), no match, multiple matches, invalid regex

## 2. GitHub mapper row shape

- [ ] 2.1 Emit `github_org` (org login) on GitHub rows; omit `bitbucket_project_name`
- [ ] 2.2 Derive `apm_code` from topics; use YAML only for `production_branch`
- [ ] 2.3 Update `tests/test_github_mapper.py` for new fields and topic-based APM

## 3. CLI

- [ ] 3.1 Add `--apm-topic-regex` to `discover github` (default `^apm-(.+)$`)
- [ ] 3.2 Validate regex at parse time; pass through to mapper
- [ ] 3.3 CLI/help test for new flag

## 4. Empty-repos sidecar

- [ ] 4.1 GitHub entries use `github_org` instead of `bitbucket_project_name` in `empty_repos_document.py`
- [ ] 4.2 Update empty-repos tests for `source: github`

## 5. Documentation

- [ ] 5.1 README Stage 1 (GitHub): `github_org`, topic-derived `apm_code`, `--apm-topic-regex`
- [ ] 5.2 README Discovery JSON example: show `github_org` for `source: github` rows
- [ ] 5.3 README commands table: add `--apm-topic-regex`
- [ ] 5.4 README token permissions: note `GET /repos/{owner}/{repo}/topics` requirement
