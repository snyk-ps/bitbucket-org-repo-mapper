## Context

GitHub discovery was introduced with Bitbucket row parity: `mapping_row()` always emits `bitbucket_project_name`, and `apm_code` comes from AppSec YAML. For GitHub customers, org login (`snyk-ps`) is the meaningful scope identifier (used as `project_key` in checkpoint/import paths), and APM routing is expressed via repository **topics** (e.g. `apm-ABC1`), not `appsec.yaml`.

Current output (from `data/discovery.json`):

- `bitbucket_project_name`: `"Snyk Professional Services"` (display name)
- `repository_path`: `"snyk-ps/…"` (org login)
- `apm_code`: `null` (no YAML apmCode)

## Goals / Non-Goals

**Goals:**

- GitHub rows include `github_org` = org login.
- GitHub `apm_code` derived from repo topics matching `--apm-topic-regex` (default `^apm-(.+)$`); topic `apm-ABC1` yields `ABC1`.
- Bitbucket/spreadsheet rows unchanged (`bitbucket_project_name`, YAML `apmCode`).
- README documents new fields and flag.

**Non-Goals:**

- Renaming Bitbucket field names.
- Validating topic APM codes against the 4-char convention (keep existing warning helper when a code is extracted).
- Fetching topics for empty repos (leave `apm_code` null).
- Stage 2–4 code changes.

## Decisions

### 1. `github_org` is org login, not display name

| Field | GitHub value |
|-------|----------------|
| `github_org` | Org login from `--orgs` / `repository_path` prefix (e.g. `snyk-ps`) |
| `bitbucket_project_name` | **Omitted** on `source: github` rows |

**Rationale:** Aligns with checkpoint `project_key`, import `target.projectKey`, and `repository_path`. Display name is not needed downstream.

**Alternative considered:** Keep `bitbucket_project_name` with display name for schema stability — rejected because the field name and value are both misleading for GitHub.

### 2. Topic-derived `apm_code` with capture group

- **API:** `GET /repos/{owner}/{repo}/topics` → `{"names": ["apm-ABC1", …]}`.
- **Default regex:** `^apm-(.+)$` (user-facing description: topics matching `apm-*`).
- **Extraction:** First matching topic in **lexicographic sort order**; capture group 1 becomes `apm_code` (e.g. `apm-ABC1` → `ABC1`).
- **No match:** `apm_code: null`.
- **Multiple matches:** First after sort; log warning when more than one match.

`--apm-topic-regex` accepts a Python `re` pattern with **one capture group** for the APM code. Invalid regex → exit 2 with clear stderr.

**Alternative considered:** Use full topic name as `apm_code` — rejected; suffix matches existing 4-char APM convention and Snyk org naming.

### 3. YAML role on GitHub

Continue fetching AppSec YAML for **`production_branch`** only. Ignore `security.apmCode` on GitHub discovery rows so topic and YAML cannot conflict.

### 4. Empty-repos sidecar

For `source: github`, each entry includes `github_org` (from row or `project_key` fallback). Do not emit `bitbucket_project_name` on GitHub sidecar entries. Bitbucket sidecar unchanged.

### 5. Implementation shape

- Add `GitHubClient.repository_topics(owner, repo) -> list[str]`.
- Add `apm_code_from_topics(topics, pattern) -> str | None` in `github_mapper` or small helper.
- Extend `iter_github_mapping(..., apm_topic_regex: str)`; pass flag from CLI.
- GitHub-specific row builder to emit `github_org` instead of `bitbucket_project_name`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Extra API call per non-empty repo | Acceptable; crawl already does commits + contents |
| Token lacks topic read | Document in README; 403 surfaces as RuntimeError |
| Breaking existing github discovery JSON | Document re-run; pre-production fix |

## Migration Plan

1. Ship fix; operators re-run `discover github` to regenerate `discovery.json` and `github-empty-repos.json`.
2. No Stage 2/3 code changes required.

## Open Questions

_None — APM extraction confirmed: `apm-ABC1` → `ABC1`._
