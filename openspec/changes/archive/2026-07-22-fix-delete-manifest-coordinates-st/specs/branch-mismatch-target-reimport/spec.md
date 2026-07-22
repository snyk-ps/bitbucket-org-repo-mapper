# branch-mismatch-target-reimport Specification (change delta)

## MODIFIED Requirements

### Requirement: Delete-only script with manifest

The repository SHALL provide a delete script that accepts `diff.json`, deletes matched targets, writes a versioned delete report, and SHALL write an optional delete manifest containing reimport coordinates (`org_id`, `integration_id`, `project_key`, `repo_slug`, `production_branch`, `repository_name`) captured before each DELETE.

Coordinates SHALL be resolved in order: (1) target GET attributes (`projectKey` / `repoSlug` or snake_case equivalents, including `remote_repo_url` partial), (2) when `--discovery` is supplied, discovery row matched by `repository_name` and disambiguated by `apm_code` when needed, using `repository_path` for `project_key` and `repo_slug`. The script SHALL NOT delete when coordinates cannot be resolved from any attempted source.

#### Scenario: Successful delete with manifest from target GET

- **WHEN** a target is matched and target GET includes `projectKey` and `repoSlug`
- **AND** `--manifest` is set
- **THEN** the manifest entry includes coordinates from target detail
- **AND** `coordinate_source` is `target`
- **AND** the delete report records the entry under `deleted`

#### Scenario: Successful delete with discovery fallback

- **WHEN** a target is matched and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document with a matching row
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

## ADDED Requirements

### Requirement: Discovery coordinate index for branch remediation

The implementation SHALL provide a helper that loads a version 1 discovery document and builds a lookup from `repository_name` (and `apm_code` when required) to `(project_key, repo_slug)` derived from each row's `repository_path`.

#### Scenario: Unique repository name match

- **WHEN** exactly one discovery row has `repository_name` equal to the diff entry's `repository_name`
- **THEN** the helper returns that row's project key and repo slug

#### Scenario: Ambiguous discovery match disambiguated by apm_code

- **WHEN** multiple discovery rows share the same `repository_name` with different `apm_code` values
- **AND** the diff entry's `apm_code` matches exactly one row
- **THEN** the helper returns coordinates from the matching row

#### Scenario: No discovery match

- **WHEN** no discovery row matches the diff entry
- **THEN** coordinate resolution returns failure with reason `discovery_not_found`
