## Why

GitHub discovery (`discover github`) currently emits rows that mirror Bitbucket schema too literally: `bitbucket_project_name` is populated with the org **display name** (e.g. `Snyk Professional Services`) instead of the org **login** (`snyk-ps`), and `apm_code` is read from AppSec YAML—where most GitHub repos have no `security.apmCode`, yielding `null`. In practice, customers tag repos with GitHub topics like `apm-ABC1` to indicate the Snyk org (APM code). Discovery output should reflect GitHub-native semantics so Stage 2 (`snyk-orgs`) and Stage 3 (`snyk-import`) receive correct `apm_code` values without relying on YAML.

## What Changes

- **GitHub discovery rows:** Replace `bitbucket_project_name` with **`github_org`** (org login, matching the `{org}/{repo}` path prefix).
- **GitHub `apm_code`:** Derive from repository **topics** via a configurable regex. Default pattern matches topics like `apm-ABC1` and extracts `ABC1` as `apm_code`.
- **CLI:** Add **`--apm-topic-regex`** to `discover github` to override the default topic-matching regex.
- **AppSec YAML on GitHub:** Continue reading YAML for **`production_branch`** only; do **not** use YAML `security.apmCode` for GitHub rows.
- **Empty-repos sidecar (`github-empty-repos.json`):** Use `github_org` instead of `bitbucket_project_name` on GitHub entries.
- **README:** Update Stage 1 (GitHub) docs, discovery JSON example, and commands table.

**BREAKING:** Existing `source: github` discovery files using `bitbucket_project_name` and YAML-derived `apm_code` are superseded; operators must re-run discovery.

**Out of scope:**

- Renaming `bitbucket_project_name` on Bitbucket or spreadsheet discovery rows.
- Stage 2–4 logic changes (they already consume `apm_code` from discovery rows).
- Spreadsheet ingress for GitHub.
- New capabilities or new CLI commands.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `three-stage-snyk-pipeline`: GitHub discovery row schema (`github_org`, topic-derived `apm_code`, `--apm-topic-regex`).
- `github-empty-repos`: GitHub empty-repos entries use `github_org` instead of `bitbucket_project_name`.

## Impact

- **Code:** `src/common/github_mapper.py`, `src/integrations/github/client.py` (topics API), `src/commands/github_cli.py`, `src/common/empty_repos_document.py` (GitHub branch).
- **Tests:** `tests/test_github_mapper.py`, empty-repos document tests, CLI help/flag tests.
- **Docs:** `README.md` Stage 1 (GitHub), Discovery JSON example, commands reference.
- **Breaking:** GitHub discovery JSON schema change; re-run `discover github` after upgrade.
