# github-empty-repos Specification (change delta)

## MODIFIED Requirements

### Requirement: Empty-repos document version 1 for GitHub

The GitHub discovery command SHALL be able to write a JSON document with `version` 1, `source` `github`, and a `repositories` array. Each entry SHALL include `repository_path`, `project_key` (org login), `repo_slug` (repo name), `repository_name`, and **`github_org`** (org login from the discovery row).

#### Scenario: Document lists only empty repositories

- **GIVEN** discovery rows where some have `is_empty` true and some false
- **WHEN** the empty-repos document is built for GitHub discovery
- **THEN** `repositories` SHALL contain only rows with `is_empty` true
- **AND** entries SHALL be sorted by `repository_path`

#### Scenario: No empty repositories

- **GIVEN** no discovery rows have `is_empty` true
- **WHEN** the empty-repos document is written
- **THEN** `repositories` SHALL be an empty array

#### Scenario: GitHub empty-repos entry uses github_org

- **GIVEN** a GitHub discovery row with `is_empty` true and `github_org` `snyk-ps`
- **WHEN** the empty-repos document is built
- **THEN** the corresponding entry SHALL include `github_org` with value `snyk-ps`
- **AND** the entry SHALL NOT include `bitbucket_project_name`
