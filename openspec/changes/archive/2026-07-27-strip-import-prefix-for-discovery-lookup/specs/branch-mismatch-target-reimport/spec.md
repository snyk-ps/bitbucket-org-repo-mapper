## MODIFIED Requirements

### Requirement: Delete-only script with manifest

The repository SHALL provide a delete script that accepts `diff.json`, deletes matched targets, writes a versioned delete report, and SHALL write an optional delete manifest containing reimport coordinates (`org_id`, `integration_id`, `project_key`, `repo_slug`, `production_branch`, `repository_name`) captured before each DELETE.

Delete matching SHALL use diff `repository_name` (Snyk target `display_name`), not discovery `repository_name`.

Coordinates SHALL be resolved in order: (1) target GET attributes (`projectKey` / `repoSlug` or snake_case equivalents, including `remote_repo_url` partial), (2) when `--discovery` is supplied, discovery row matched by diff `repository_name` (with `APP_TYPE_PREFIX` stripped when present) against discovery `repository_path` and disambiguated by `apm_code` when needed, using `repository_path` for `project_key` and `repo_slug`. The script SHALL NOT delete when coordinates cannot be resolved from any attempted source.

#### Scenario: Successful delete with manifest from target GET

- **WHEN** a target is matched and target GET includes `projectKey` and `repoSlug`
- **AND** `--manifest` is set
- **THEN** the manifest entry includes coordinates from target detail
- **AND** `coordinate_source` is `target`
- **AND** the delete report records the entry under `deleted`

#### Scenario: Successful delete with discovery fallback

- **WHEN** a target is matched and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document with a row whose `repository_path` matches diff `repository_name` after stripping `APP_TYPE_PREFIX` when present
- **THEN** the manifest entry includes `project_key` and `repo_slug` from discovery `repository_path`
- **AND** `coordinate_source` is `discovery`
- **AND** the target is deleted

#### Scenario: Coordinates missing and no discovery

- **WHEN** a target is matched and target GET omits coordinates
- **AND** `--discovery` is not supplied
- **THEN** the entry is recorded under `failed` with an error indicating missing coordinates and suggesting `--discovery`
- **AND** no DELETE is performed

#### Scenario: Dry run delete

- **WHEN** `--dry-run` is set and a target is matched
- **THEN** no DELETE request is issued
- **AND** the entry is recorded under `skipped` with reason `dry_run`

### Requirement: Discovery coordinate index for branch remediation

The implementation SHALL provide a helper that loads a version 1 discovery document and builds a lookup from `repository_path` (and `apm_code` when required) to `(project_key, repo_slug)` derived from each row's `repository_path`. The helper SHALL look up coordinates using diff `repository_name`, stripping `APP_TYPE_PREFIX` (`BB/`) from diff `repository_name` when present before matching against discovery `repository_path`. Discovery `repository_name` (Bitbucket slug) SHALL NOT be used for delete matching or coordinate lookup keys.

#### Scenario: Diff display name matches discovery path

- **GIVEN** diff `repository_name` is `tcannell-test/juice-shop`
- **AND** discovery row has `repository_path` `tcannell-test/juice-shop` and `repository_name` `juice-shop`
- **WHEN** coordinate resolution falls back to discovery
- **THEN** the helper returns project key and repo slug from `repository_path`

#### Scenario: Prefixed diff name matches unprefixed discovery path

- **GIVEN** diff `repository_name` is `BB/tcannell-test/juice-shop`
- **AND** discovery row has `repository_path` `tcannell-test/juice-shop` and `repository_name` `juice-shop`
- **WHEN** coordinate resolution falls back to discovery
- **THEN** the helper strips `APP_TYPE_PREFIX` from diff `repository_name` before lookup
- **AND** returns project key and repo slug from discovery `repository_path`

#### Scenario: Ambiguous discovery match disambiguated by apm_code

- **WHEN** multiple discovery rows share the same matched `repository_path` with different `apm_code` values
- **AND** the diff entry's `apm_code` matches exactly one row
- **THEN** the helper returns coordinates from the matching row

#### Scenario: No discovery match

- **WHEN** no discovery row has `repository_path` equal to diff `repository_name` (after stripping `APP_TYPE_PREFIX` when present)
- **THEN** coordinate resolution returns failure with reason `discovery_not_found`
