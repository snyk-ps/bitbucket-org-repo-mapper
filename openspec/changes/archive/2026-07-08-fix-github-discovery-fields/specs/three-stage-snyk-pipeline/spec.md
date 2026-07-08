# three-stage-snyk-pipeline Specification (change delta)

## MODIFIED Requirements

### Requirement: Stage 1 discovery produces a versioned intermediate document

The discovery command SHALL support **three** ingress modes—Bitbucket Server, spreadsheet, and **GitHub**—and SHALL write a single **versioned** JSON document containing `rows` equivalent to the primary mapping semantics needed for Snyk Stages 2 and 3, including `apm_code`, `repository_path`, `repository_name`, `production_branch`, and `bitbucket_project_name` where applicable on Bitbucket and spreadsheet rows. For **Bitbucket** discovery (full crawl or spreadsheet-driven targeted list), each row SHALL include a boolean **`is_empty`**. For **GitHub** discovery, each row SHALL include the same boolean **`is_empty`** and the same committer metadata fields as Bitbucket. A repository SHALL be marked `is_empty: true` when it has zero commits **or** when repository metadata has **no usable default branch** (Bitbucket and GitHub each apply this rule to their respective API payloads).

For non-empty rows, the row SHALL include **`last_committer_name`**, **`last_committer_email`**, and **`last_commit_date`** from the latest commit when commits exist. When synthesizing a default branch ref from incomplete API metadata on Bitbucket, the implementation SHALL use **`master`** (not `main`) as the fallback display/ref. GitHub SHALL use `default_branch` from the GitHub repo object when YAML omits `productionBranch`.

**Spreadsheet** discovery SHALL read `bb-repo-mapping.xlsx`: row 1 headers **`ProjectKey`** and **`RepoName`**; column **A** is the project key; column **B** is a semicolon-delimited list of repository slugs. The command SHALL perform Bitbucket HTTP for each `(project_key, repo_slug)` to resolve YAML `apm_code` and row fields. The output document SHALL use **`source: bitbucket`** (not offline `spreadsheet`). The legacy apmcodes format (columns A=APM, B=`BB::…`, D=name) is **not** supported.

**GitHub** discovery SHALL require **`--orgs`** with a comma-separated list of organization logins. The command SHALL list repositories via the GitHub REST API for each org and SHALL write **`source: github`**. The command SHALL NOT provide a spreadsheet ingress mode. Each GitHub row SHALL include **`github_org`** (organization login) instead of `bitbucket_project_name`. The command SHALL derive **`apm_code`** from repository topics: the implementation SHALL fetch topics per repository and SHALL set `apm_code` from the first topic (lexicographic order) matching the configured regex, using the regex's first capture group as the APM code. The default regex SHALL match topics of the form `apm-*` (implementation default: `^apm-(.+)$`). The user SHALL be able to override the regex via **`--apm-topic-regex`** on `discover github`. For GitHub rows, AppSec YAML SHALL be used only for **`production_branch`**; YAML `security.apmCode` SHALL NOT populate `apm_code`.

#### Scenario: Bitbucket discovery writes intermediate

- **GIVEN** valid `BITBUCKET_*` configuration and repository access
- **WHEN** the user runs Stage 1 discovery for Bitbucket
- **THEN** the output document SHALL include `source` with value `bitbucket`
- **AND** each processed repository SHALL appear as a row with YAML-derived or defaulted branch and APM metadata per existing mapper rules
- **AND** each row SHALL include `is_empty` as defined above

#### Scenario: Spreadsheet-driven discovery uses Bitbucket

- **GIVEN** a valid `bb-repo-mapping.xlsx` and valid `BITBUCKET_*` configuration
- **WHEN** the user runs Stage 1 discovery for spreadsheet
- **THEN** the output document SHALL include `source` with value `bitbucket`
- **AND** each listed repository SHALL be resolved via Bitbucket HTTP
- **AND** each row SHALL include `apm_code` from AppSec YAML when not empty
- **AND** semicolon-separated slugs in column B SHALL expand to one row per slug

#### Scenario: Repository without default branch marked empty

- **GIVEN** a Bitbucket repository with no default branch in API metadata
- **WHEN** Stage 1 discovery processes that repository
- **THEN** the row SHALL have `is_empty` set to `true`
- **AND** the command SHALL NOT fail
- **AND** the implementation SHALL NOT fetch AppSec YAML for that repository

#### Scenario: Unknown repository slug fails

- **GIVEN** a spreadsheet lists `project_key` / `repo_slug` that does not exist in Bitbucket
- **WHEN** Stage 1 spreadsheet discovery processes that entry
- **THEN** the command SHALL fail with a clear error naming `project_key/repo_slug`

#### Scenario: Empty repository marked in discovery

- **GIVEN** a Bitbucket repository with zero commits
- **WHEN** Stage 1 Bitbucket discovery processes that repository
- **THEN** the row SHALL appear in `rows` with `is_empty` set to `true`
- **AND** the implementation SHALL NOT fetch the configured AppSec YAML file for that repository

#### Scenario: Non-empty repository marked in discovery

- **GIVEN** a Bitbucket repository with at least one commit and a default branch
- **WHEN** Stage 1 Bitbucket discovery processes that repository
- **THEN** the row SHALL have `is_empty` set to `false`
- **AND** existing YAML and branch resolution behavior SHALL apply

#### Scenario: Empty-repos artifact written with file output

- **GIVEN** the user runs Bitbucket or spreadsheet discovery with a file output path
- **WHEN** discovery completes or flushes incremental output
- **THEN** the implementation SHALL write `bitbucket-empty-repos.json` (or the path from `--empty-repos-output`) listing every repository with `is_empty` true
- **AND** the file SHALL use document version 1 with a `repositories` array

#### Scenario: GitHub discovery writes intermediate

- **GIVEN** valid `GITHUB_TOKEN` and access to orgs listed in `--orgs`
- **WHEN** the user runs `discover github --orgs "org-a,org-b" -o discovery.json`
- **THEN** the output document SHALL include `source` with value `github`
- **AND** each processed repository under those orgs SHALL appear as a row with topic-derived or null `apm_code` and YAML- or default-derived `production_branch`
- **AND** each row SHALL include `is_empty` as defined above

#### Scenario: GitHub row includes github_org

- **GIVEN** org login `snyk-ps` with display name `Snyk Professional Services`
- **WHEN** GitHub discovery processes a repository under that org
- **THEN** the row SHALL include `github_org` with value `snyk-ps`
- **AND** the row SHALL NOT include `bitbucket_project_name`

#### Scenario: GitHub apm_code from topic

- **GIVEN** a non-empty GitHub repository with topic `apm-ABC1`
- **WHEN** GitHub discovery processes that repository with default `--apm-topic-regex`
- **THEN** the row SHALL have `apm_code` equal to `ABC1`

#### Scenario: GitHub apm_code null when no matching topic

- **GIVEN** a non-empty GitHub repository with no topic matching the configured regex
- **WHEN** GitHub discovery processes that repository
- **THEN** the row SHALL have `apm_code` null
- **AND** YAML `security.apmCode` SHALL NOT be used

#### Scenario: Custom apm topic regex

- **GIVEN** the user runs `discover github` with `--apm-topic-regex '^team-(.+)$'`
- **AND** a repository has topic `team-XYZ9`
- **WHEN** discovery processes that repository
- **THEN** the row SHALL have `apm_code` equal to `XYZ9`

#### Scenario: GitHub org list required

- **GIVEN** the user runs `discover github` without `--orgs`
- **WHEN** the command parses arguments
- **THEN** the command SHALL exit with validation error code 2 and a clear stderr message

#### Scenario: GitHub empty repository marked in discovery

- **GIVEN** a GitHub repository with zero commits
- **WHEN** Stage 1 GitHub discovery processes that repository
- **THEN** the row SHALL appear in `rows` with `is_empty` set to `true`
- **AND** the implementation SHALL NOT fetch the configured AppSec YAML file for that repository
- **AND** `last_committer_name`, `last_committer_email`, and `last_commit_date` SHALL be `null`

#### Scenario: GitHub discovery resumes from checkpoint

- **GIVEN** an existing discovery file with `source: github` and a non-null `checkpoint`
- **WHEN** the user re-runs `discover github` with the same `-o` path and `--orgs`
- **THEN** repositories at or before the checkpoint key SHALL be skipped
- **AND** new rows SHALL be appended without duplicating completed keys

#### Scenario: GitHub empty-repos artifact written with file output

- **GIVEN** the user runs GitHub discovery with a file output path
- **WHEN** discovery completes or flushes incremental output
- **THEN** the implementation SHALL write `github-empty-repos.json` (or the path from `--empty-repos-output`) listing every repository with `is_empty` true
- **AND** the file SHALL use document version 1 with `source: github` and a `repositories` array
