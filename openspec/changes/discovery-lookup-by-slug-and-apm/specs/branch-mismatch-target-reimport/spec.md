## MODIFIED Requirements

### Requirement: Monolithic reimport discovery fallback

The monolithic reimport script SHALL accept `--discovery PATH` with the same coordinate-resolution semantics as the delete script: fallback to discovery row matched by repo slug extracted from diff `repository_name` and diff `apm_code` for `projectKey`/`repoSlug` when target GET omits them.

#### Scenario: Reimport with discovery fallback

- **WHEN** a target is matched for delete and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document with a row whose `repository_name` and `apm_code` match the diff entry's extracted slug and `apm_code`
- **THEN** the reimport payload uses coordinates from discovery `repository_path`
- **AND** the target is deleted and queued for reimport

### Requirement: Delete-only script with manifest

The repository SHALL provide a delete script that accepts `diff.json`, deletes matched targets, writes a versioned delete report, and SHALL write an optional delete manifest containing reimport coordinates (`org_id`, `integration_id`, `project_key`, `repo_slug`, `production_branch`, `repository_name`) captured before each DELETE.

Delete matching SHALL use diff `repository_name` (Snyk target `display_name`), not discovery `repository_name`.

Coordinates SHALL be resolved in order: (1) target GET attributes (`projectKey` / `repoSlug` or snake_case equivalents, including `remote_repo_url` partial), (2) when `--discovery` is supplied, discovery row matched by repo slug extracted from diff `repository_name` (strip `APP_TYPE_PREFIX` when present; take final `/` segment when applicable) together with diff `apm_code` against discovery `repository_name` and `apm_code`, using `repository_path` for `project_key` and `repo_slug`. The script SHALL NOT delete when coordinates cannot be resolved from any attempted source.

#### Scenario: Successful delete with manifest from target GET

- **WHEN** a target is matched and target GET includes `projectKey` and `repoSlug`
- **AND** `--manifest` is set
- **THEN** the manifest entry includes coordinates from target detail
- **AND** `coordinate_source` is `target`
- **AND** the delete report records the entry under `deleted`

#### Scenario: Successful delete with discovery fallback

- **WHEN** a target is matched and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document with a row whose `repository_name` and `apm_code` match the diff entry's extracted slug and `apm_code`
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

The implementation SHALL provide a helper that loads a version 1 discovery document and builds a lookup from `(repository_name, apm_code)` to `(project_key, repo_slug)` derived from each row's `repository_path`. The helper SHALL look up coordinates using the repo slug extracted from diff `repository_name` and diff `apm_code`. Discovery `repository_path` SHALL NOT be used as the lookup key.

#### Scenario: Prefixed slug-only diff matches discovery path

- **GIVEN** diff `repository_name` is `BB/juice-shop` and `apm_code` is `ABCD`
- **AND** discovery row has `repository_path` `tcannell-test/juice-shop`, `repository_name` `juice-shop`, and `apm_code` `ABCD`
- **WHEN** coordinate resolution falls back to discovery
- **THEN** the helper extracts slug `juice-shop` from diff `repository_name`
- **AND** returns project key `tcannell-test` and repo slug `juice-shop` from `repository_path`

#### Scenario: Unprefixed path diff matches by slug

- **GIVEN** diff `repository_name` is `tcannell-test/juice-shop` and `apm_code` is `ABCD`
- **AND** discovery row has `repository_path` `tcannell-test/juice-shop` and `repository_name` `juice-shop`
- **WHEN** coordinate resolution falls back to discovery
- **THEN** the helper extracts slug `juice-shop` and returns coordinates from `repository_path`

#### Scenario: Ambiguous discovery match disambiguated by apm_code

- **WHEN** multiple discovery rows share the same `repository_name` and `apm_code`
- **THEN** coordinate resolution returns failure with reason `ambiguous_discovery`

#### Scenario: No discovery match for wrong apm

- **WHEN** slug matches a discovery row but `apm_code` does not
- **THEN** coordinate resolution returns failure with reason `discovery_not_found`

#### Scenario: No discovery match

- **WHEN** no discovery row has `repository_name` equal to the slug extracted from diff `repository_name` with matching `apm_code`
- **THEN** coordinate resolution returns failure with reason `discovery_not_found`
