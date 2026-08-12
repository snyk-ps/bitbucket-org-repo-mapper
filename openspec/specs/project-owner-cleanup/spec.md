# project-owner-cleanup Specification

## Purpose

One-off operational script to clear (unassign) the project owner on all Snyk projects in a group or explicit org list, using v1 PUT `{"owner": null}`.

## Requirements

### Requirement: Mutually exclusive scope flags

The script SHALL accept exactly one scope mode: `--group GROUP_ID` or `--orgs ORG_ID[,ORG_ID...]`.

#### Scenario: Group scope

- **WHEN** the user passes `--group <group-uuid>`
- **THEN** the script resolves all orgs in that group via the Snyk REST Groups API
- **AND** processes every project in each org

#### Scenario: Explicit org list

- **WHEN** the user passes `--orgs org-a,org-b`
- **THEN** the script processes only those org UUIDs
- **AND** does not require `SNYK_GROUP_ID`

#### Scenario: Invalid scope

- **WHEN** neither flag is set, or both are set
- **THEN** the script exits with a validation error before any API calls

### Requirement: Clear project owner via v1 PUT

For each project in scope, the script SHALL issue `PUT /v1/org/{orgId}/project/{projectId}` with JSON body `{"owner": null}` unless `--dry-run` is set.

#### Scenario: Successful clear

- **WHEN** the PUT succeeds
- **THEN** the project is recorded under `cleared`

#### Scenario: Dry run

- **WHEN** `--dry-run` is set
- **THEN** no PUT is issued
- **AND** matching projects are recorded under `skipped` with `reason: dry_run`

#### Scenario: Already unassigned

- **WHEN** the project has no owner and that can be determined from list or detail payload
- **THEN** no PUT is issued
- **AND** the project is recorded under `skipped` with `reason: already_unassigned`

#### Scenario: API failure

- **WHEN** the PUT returns a non-retriable error
- **THEN** the project is recorded under `failed` with error detail
- **AND** processing continues for remaining projects

### Requirement: List projects per org

The script SHALL list projects via the Snyk REST Projects API for each org in scope.

#### Scenario: Paginated org project list

- **WHEN** an org has more than one page of projects
- **THEN** the script follows pagination until all projects are processed

### Requirement: Versioned report output

The script SHALL write a versioned JSON report with sections `cleared`, `skipped`, and `failed`.

#### Scenario: Report on completion

- **WHEN** processing completes
- **THEN** the report is written to `--output` (default `clear-project-owner-report.json`)
- **AND** includes `version`, scope metadata (`group_id` or `org_ids`), and per-project outcomes

#### Scenario: Exit code on failure

- **WHEN** any project is recorded under `failed`
- **THEN** the script exits with status code 1

### Requirement: Require Snyk token

The script SHALL require `SNYK_TOKEN` (and honor `SNYK_API` for single-tenant origins).

#### Scenario: Missing token

- **WHEN** `SNYK_TOKEN` is unset
- **THEN** the script exits with a validation error before processing
