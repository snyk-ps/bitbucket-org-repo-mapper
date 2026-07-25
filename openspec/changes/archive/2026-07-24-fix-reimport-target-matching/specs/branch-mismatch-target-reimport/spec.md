## ADDED Requirements

### Requirement: Targets API does not provide branch for delete matching

The implementation SHALL NOT read, require, or compare `attributes.target_reference` (or equivalent branch fields) on Target resources when matching targets for deletion. Branch information for diff generation SHALL be sourced only from the Projects API.

#### Scenario: Delete match without target branch

- **WHEN** listing or getting targets via the Targets REST API
- **THEN** delete matching uses only `attributes.display_name == diff.repository_name`
- **AND** the implementation does not depend on branch fields on the target resource

### Requirement: Integration type selection for monolithic reimport

The monolithic reimport script SHALL accept `--integration-type` with allowed values `bitbucket-server` (default) and `bitbucket-cloud`. It SHALL restrict target matching to targets linked to an integration of the requested type within the resolved org when the target list payload includes an integration relationship.

#### Scenario: Bitbucket Cloud test run

- **WHEN** the operator passes `--integration-type bitbucket-cloud`
- **THEN** only targets belonging to the org's bitbucket-cloud integration are candidates for delete matching

#### Scenario: Default Bitbucket Server production run

- **WHEN** the operator omits `--integration-type`
- **THEN** the script uses `bitbucket-server` integration filtering

### Requirement: Monolithic reimport discovery fallback

The monolithic reimport script SHALL accept `--discovery PATH` with the same coordinate-resolution semantics as the delete script: fallback to discovery `repository_path` for `projectKey`/`repoSlug` when target GET omits them.

#### Scenario: Reimport with discovery fallback

- **WHEN** a target is matched for delete and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document
- **THEN** the reimport payload uses coordinates from discovery `repository_path`
- **AND** the target is deleted and queued for reimport

## MODIFIED Requirements

### Requirement: Match target by repository_name only

For delete operations, the script SHALL list all targets in the resolved org via `GET /rest/orgs/{org_id}/targets` with query parameter `exclude_empty=false`, SHALL NOT rely on a server-side `display_name` filter, and SHALL find exactly one target where `attributes.display_name` equals diff `repository_name` (case-sensitive), matching client-side against the full paginated list. The script SHALL NOT read, require, or compare branch fields on the Target resource. The script SHALL delete the entire matched target.

#### Scenario: Single matching target found

- **WHEN** exactly one target matches diff `repository_name` by `display_name`
- **THEN** the script proceeds to GET target detail and DELETE the whole target (or dry-run skip)

#### Scenario: No matching target

- **WHEN** zero targets match diff `repository_name`
- **THEN** the entry is recorded under `not_found` with reason `target_not_found`

#### Scenario: Ambiguous match

- **WHEN** more than one target matches diff `repository_name`
- **THEN** the entry is recorded under `ambiguous`
- **AND** no delete is performed

#### Scenario: Already correct branch skipped

- **WHEN** `production_branch` equals `target_reference` in diff.json
- **THEN** the entry is recorded under `skipped` with reason `already_correct`
- **AND** no delete is performed

#### Scenario: Target found without branch on Targets API

- **WHEN** a target's `display_name` equals diff `repository_name`
- **AND** the Targets API response omits branch attributes
- **THEN** the script proceeds to delete (or dry-run skip) the entire target

### Requirement: Diff target_reference provenance

The `target_reference` field in `diff.json` and lookup output SHALL reflect the branch from the Snyk **Projects API** (`attributes.target_reference` on a project linked to the target via `relationships.target.data.id`). The implementation SHALL NOT use the Targets API target resource as the source of branch for diff generation or delete matching.

#### Scenario: Diff builder uses project branch

- **WHEN** `lookup_target_reference.py` (or equivalent) emits an entry for a Bitbucket target
- **THEN** `target_reference` is read from project `attributes.target_reference`
- **AND** the entry is joined to target `display_name` via shared target id

### Requirement: Delete-only script with manifest

The repository SHALL provide a delete script that accepts `diff.json`, deletes matched targets, writes a versioned delete report, and SHALL write an optional delete manifest containing reimport coordinates (`org_id`, `integration_id`, `project_key`, `repo_slug`, `production_branch`, `repository_name`) captured before each DELETE.

Delete matching SHALL use diff `repository_name` (Snyk target `display_name`), not discovery `repository_name`.

Coordinates SHALL be resolved in order: (1) target GET attributes (`projectKey` / `repoSlug` or snake_case equivalents, including `remote_repo_url` partial), (2) when `--discovery` is supplied, discovery row matched by diff `repository_name` against discovery `repository_path` and disambiguated by `apm_code` when needed, using `repository_path` for `project_key` and `repo_slug`. The script SHALL NOT delete when coordinates cannot be resolved from any attempted source.

#### Scenario: Successful delete with manifest from target GET

- **WHEN** a target is matched and target GET includes `projectKey` and `repoSlug`
- **AND** `--manifest` is set
- **THEN** the manifest entry includes coordinates from target detail
- **AND** `coordinate_source` is `target`
- **AND** the delete report records the entry under `deleted`

#### Scenario: Successful delete with discovery fallback

- **WHEN** a target is matched and target GET omits `projectKey` / `repoSlug`
- **AND** `--discovery` points to a valid discovery document with a row whose `repository_path` equals diff `repository_name`
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

The implementation SHALL provide a helper that loads a version 1 discovery document and builds a lookup from `repository_path` (and `apm_code` when required) to `(project_key, repo_slug)` derived from each row's `repository_path`. The helper SHALL look up coordinates using diff `repository_name`. Discovery `repository_name` (Bitbucket slug) SHALL NOT be used for delete matching or coordinate lookup keys.

#### Scenario: Diff display name matches discovery path

- **GIVEN** diff `repository_name` is `tcannell-test/juice-shop`
- **AND** discovery row has `repository_path` `tcannell-test/juice-shop` and `repository_name` `juice-shop`
- **WHEN** coordinate resolution falls back to discovery
- **THEN** the helper returns project key and repo slug from `repository_path`

#### Scenario: Ambiguous discovery match disambiguated by apm_code

- **WHEN** multiple discovery rows share the same `repository_path` with different `apm_code` values
- **AND** the diff entry's `apm_code` matches exactly one row
- **THEN** the helper returns coordinates from the matching row

#### Scenario: No discovery match

- **WHEN** no discovery row has `repository_path` equal to diff `repository_name`
- **THEN** coordinate resolution returns failure with reason `discovery_not_found`

## REMOVED Requirements

### Requirement: Match target by repository_name and target_reference

**Reason**: Renamed and replaced by "Match target by repository_name only". The Targets API does not expose branch for delete matching on any tenant; dual-field matching was never valid.

**Migration**: Use display-name-only matching. Branch in diff comes from Projects API only.
