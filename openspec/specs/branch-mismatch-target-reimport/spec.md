# branch-mismatch-target-reimport Specification

## Purpose

Operational script to delete Snyk targets with mismatched branch references and reimport them with the correct `production_branch` from a `diff.json` artifact.

## Requirements

### Requirement: Accept diff.json input format

The script SHALL accept a JSON array where each element contains `apm_code`, `repository_name`, `production_branch`, and `target_reference` as non-empty strings.

#### Scenario: Valid diff file loaded

- **WHEN** the user passes `--input` pointing to a valid diff.json array
- **THEN** the script loads and validates all entries before processing

#### Scenario: Invalid diff entry rejected

- **WHEN** an entry is missing a required key or has an empty value
- **THEN** the script exits with a validation error before any API calls

### Requirement: Resolve Snyk org by apm_code

The script SHALL resolve `org_id` by matching `apm_code` to the Snyk organization **name** in the configured `SNYK_GROUP_ID`.

#### Scenario: Org found for apm_code

- **WHEN** an entry has `apm_code` that matches an org name in the group
- **THEN** the script uses that org's id for target lookup

#### Scenario: Org not found

- **WHEN** no org in the group has name equal to `apm_code`
- **THEN** the entry is recorded under `not_found` with reason `org_not_found`
- **AND** the script continues with remaining entries

### Requirement: Match target by repository_name and target_reference

For each entry, the script SHALL list all targets in the resolved org via `GET /rest/orgs/{org_id}/targets` with query parameter `exclude_empty=false`, SHALL NOT rely on a server-side `display_name` filter for matching, and SHALL find exactly one target where `attributes.display_name` equals `repository_name` and `attributes.target_reference` equals `target_reference` (case-sensitive), matching client-side against the full paginated list.

#### Scenario: Single matching target found

- **WHEN** exactly one target matches both fields
- **THEN** the script proceeds to delete (or dry-run skip) that target

#### Scenario: No matching target

- **WHEN** zero targets match
- **THEN** the entry is recorded under `not_found` with reason `target_not_found`

#### Scenario: Ambiguous match

- **WHEN** more than one target matches
- **THEN** the entry is recorded under `ambiguous`
- **AND** no delete is performed

#### Scenario: Already correct branch skipped

- **WHEN** `production_branch` equals `target_reference`
- **THEN** the entry is recorded under `skipped` with reason `already_correct`

#### Scenario: Same display name different branch

- **WHEN** zero targets match `target_reference`
- **AND** one or more targets share `repository_name` on other branches
- **THEN** the `not_found` entry includes `same_display_name_branches` listing those branch values

### Requirement: Diff target_reference provenance

The `target_reference` field in `diff.json` SHALL reflect the current branch on the Snyk **target** resource (`attributes.target_reference`), not project-level `target_reference` alone, so it matches the reimport lookup key.

#### Scenario: Diff builder uses target branch

- **WHEN** `lookup_target_reference.py` (or equivalent diff producer) emits an entry for a Bitbucket Server target
- **THEN** `target_reference` is read from the target resource `attributes.target_reference`

### Requirement: Actionable target_not_found diagnostics

When an entry is recorded under `not_found` with reason `target_not_found`, the report entry SHALL include `candidates_returned` (count of targets listed for the org) and MAY include `same_display_name_branches` and `near_match_display_names` to aid operator triage.

#### Scenario: Diagnostics on failed lookup

- **WHEN** no target matches `repository_name` and `target_reference`
- **THEN** the `not_found` entry includes `reason: target_not_found` and `candidates_returned`
- **AND** when applicable includes `same_display_name_branches` or `near_match_display_names`

### Requirement: Delete matched target via REST API

The script SHALL delete the matched target using `DELETE /rest/orgs/{org_id}/targets/{target_id}` unless `--dry-run` is set.

#### Scenario: Successful delete

- **WHEN** a target is matched and `--dry-run` is not set
- **THEN** the target is deleted via the Snyk REST Targets API
- **AND** the entry is recorded under `deleted`

#### Scenario: Dry run delete

- **WHEN** `--dry-run` is set and a target is matched
- **THEN** no DELETE request is issued
- **AND** the entry is recorded under `skipped` with reason `dry_run`

### Requirement: Reimport with production_branch via snyk-api-import

After a successful delete, the script SHALL reimport the target with `target.branch` set to `production_branch` using `snyk-api-import import`, unless `--dry-run` or `--skip-import` is set.

#### Scenario: Successful reimport

- **WHEN** delete succeeds and neither `--dry-run` nor `--skip-import` is set
- **THEN** the script appends an import payload to a batch file and invokes `snyk-api-import import`
- **AND** the entry is recorded under `reimported`

#### Scenario: Skip import flag

- **WHEN** `--skip-import` is set and delete succeeds
- **THEN** no `snyk-api-import` subprocess is invoked
- **AND** the entry is recorded under `deleted` only

### Requirement: Versioned report output

The script SHALL write a versioned JSON report with per-entry outcomes grouped under `deleted`, `reimported`, `skipped`, `not_found`, `ambiguous`, and `failed`.

#### Scenario: Report written on completion

- **WHEN** processing completes (success or partial failure)
- **THEN** the report is written to `--output` (default `branch-reimport-report.json`)
- **AND** includes `version`, `group_id`, and entry counts

### Requirement: Require Snyk credentials

The script SHALL require `SNYK_TOKEN` and `SNYK_GROUP_ID`.

#### Scenario: Missing credentials

- **WHEN** required environment variables are unset
- **THEN** the script exits with a validation error before processing
