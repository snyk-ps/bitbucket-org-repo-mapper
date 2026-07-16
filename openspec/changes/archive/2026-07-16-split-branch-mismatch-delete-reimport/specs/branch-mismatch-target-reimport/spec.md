# branch-mismatch-target-reimport Specification (change delta)

## MODIFIED Requirements

### Requirement: Match target by repository_name and target_reference

For delete operations, the script SHALL list all targets in the resolved org via `GET /rest/orgs/{org_id}/targets` with query parameter `exclude_empty=false`, SHALL NOT rely on a server-side `display_name` filter, and SHALL find exactly one target where `attributes.display_name` equals `repository_name` (case-sensitive), matching client-side against the full paginated list. The script SHALL NOT require `attributes.target_reference` on the target resource for delete matching.

#### Scenario: Single matching target found

- **WHEN** exactly one target matches `repository_name`
- **THEN** the script proceeds to GET target detail and DELETE (or dry-run skip)

#### Scenario: No matching target

- **WHEN** zero targets match `repository_name`
- **THEN** the entry is recorded under `not_found` with reason `target_not_found`

#### Scenario: Ambiguous match

- **WHEN** more than one target matches `repository_name`
- **THEN** the entry is recorded under `ambiguous`
- **AND** no delete is performed

#### Scenario: Already correct branch skipped

- **WHEN** `production_branch` equals `target_reference` in diff.json
- **THEN** the entry is recorded under `skipped` with reason `already_correct`
- **AND** no delete is performed

### Requirement: Diff target_reference provenance

The `target_reference` field in `diff.json` and lookup output SHALL reflect the branch from the Snyk **Projects API** (`attributes.target_reference` on a project linked to the target via `relationships.target.data.id`), not from the Targets API target resource alone.

#### Scenario: Diff builder uses project branch

- **WHEN** `lookup_target_reference.py` (or equivalent) emits an entry for a Bitbucket Server target
- **THEN** `target_reference` is read from project `attributes.target_reference`
- **AND** the entry is joined to target `display_name` via shared target id

## ADDED Requirements

### Requirement: Projects API branch index

The implementation SHALL provide a helper that builds a map of target id to branch reference by iterating REST org projects and reading `attributes.target_reference` for projects with origin `bitbucket-server`.

#### Scenario: Index built from projects

- **WHEN** the helper processes an org's paginated projects list
- **THEN** it returns target id to branch reference mappings from project attributes
- **AND** ignores projects without a linked target id

### Requirement: Delete-only script with manifest

The repository SHALL provide a delete script that accepts `diff.json`, deletes matched targets, writes a versioned delete report, and SHALL write an optional delete manifest containing reimport coordinates (`org_id`, `integration_id`, `project_key`, `repo_slug`, `production_branch`, `repository_name`) captured from target GET before each DELETE.

#### Scenario: Successful delete with manifest

- **WHEN** a target is matched and delete succeeds
- **AND** `--manifest` is set
- **THEN** the manifest entry includes integration and repo coordinates from target detail
- **AND** the delete report records the entry under `deleted`

#### Scenario: Dry run delete

- **WHEN** `--dry-run` is set and a target is matched
- **THEN** no DELETE request is issued
- **AND** the entry is recorded under `skipped` with reason `dry_run`

### Requirement: Generate reimport targets script

The repository SHALL provide a script that accepts a delete manifest (or equivalent coordinate file) and emits a JSON document `{ "targets": [...] }` suitable for `snyk-api-import import`, with `target.branch` set to `production_branch` from the manifest or diff.

#### Scenario: Batch file generated

- **WHEN** the operator runs the generate script with a valid manifest
- **THEN** the output file contains one import payload per manifest entry
- **AND** each payload includes `orgId`, `integrationId`, and `target.projectKey`, `target.repoSlug`, `target.name`, `target.branch`

#### Scenario: Batch supports snyk-api-import

- **WHEN** the operator runs `snyk-api-import import --file=<output>`
- **THEN** the tool accepts the generated JSON shape

## REMOVED Requirements

### Requirement: Actionable target_not_found diagnostics

**Reason**: Delete matching no longer uses target branch; diagnostics keyed on `same_display_name_branches` from target `target_reference` are misleading when that field is absent on single-tenant.

**Migration**: Delete report uses `target_not_found` with `candidates_returned` and optional `near_match_display_names` only; branch-based diagnostic fields are not required for delete-by-display-name flow.
