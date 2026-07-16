# snyk-post-import-cleanup Specification (change delta)

## ADDED Requirements

### Requirement: Require user id for project settings PATCH

The stage SHALL require `SNYK_USER_ID` or `--user-id` before issuing live project settings PATCH requests. Dry-run SHALL NOT require `user_id`.

#### Scenario: Missing user id on live run

- **WHEN** the user runs `snyk-post-import-cleanup` without `--dry-run`
- **AND** neither `SNYK_USER_ID` nor `--user-id` is set
- **THEN** the CLI exits with a validation error before any PATCH requests

#### Scenario: User id provided on live run

- **WHEN** `SNYK_USER_ID` or `--user-id` is set
- **AND** `--dry-run` is not set
- **THEN** each project settings PATCH includes `relationships.owner` with that user id

### Requirement: Skip PATCH for deleted projects

When project settings PATCH returns HTTP 404, the stage SHALL record the project under `recurring_test_frequency.skipped` with reason `project_not_found` and SHALL continue processing other projects.

#### Scenario: Project deleted before PATCH

- **WHEN** a project was deleted in the dockerfile step or no longer exists
- **AND** PATCH returns HTTP 404
- **THEN** the entry is recorded under `recurring_test_frequency.skipped` with reason `project_not_found`
- **AND** the stage continues with remaining projects

## MODIFIED Requirements

### Requirement: Set recurring test frequency to never

For each org, after dockerfile deletion, the stage SHALL list all Snyk projects in the org via the REST Projects API and SHALL PATCH project settings so `attributes.settings.recurring_tests.frequency` is `never` on every remaining project, including `relationships.owner` referencing the configured user id.

#### Scenario: Successful frequency update

- **WHEN** the project settings PATCH succeeds for a project
- **THEN** the entry is recorded under `recurring_test_frequency.updated` with `org_id`, `project_id`, `project_name`, and `project_type`

#### Scenario: Frequency PATCH HTTP error

- **WHEN** the project settings PATCH returns a non-success HTTP status other than 404
- **THEN** the entry is recorded under `recurring_test_frequency.failed` with `org_id`, `project_id`, and error detail
- **AND** the stage continues processing other projects and orgs

#### Scenario: Dry run for frequency update

- **WHEN** `--dry-run` is set
- **THEN** no project settings PATCH requests are issued
- **AND** each eligible project appears under `recurring_test_frequency.skipped` with reason `dry_run`

### Requirement: SnykRestClient project API support

The implementation SHALL provide client methods for paginated REST org project listing, REST project deletion, and REST project settings PATCH with `relationships.owner`, using the same HTTP retry behavior as existing client methods.

#### Scenario: List projects with type filter

- **WHEN** the stage requests dockerfile projects for an org
- **THEN** the client uses `GET /rest/orgs/{orgId}/projects` with pagination
- **AND** filters to type `dockerfile` client-side

#### Scenario: Delete project via REST

- **WHEN** the stage deletes a project
- **THEN** the client issues a REST DELETE for that org and project id

#### Scenario: Update project settings via REST PATCH

- **WHEN** the stage sets recurring test frequency
- **THEN** the client issues a REST PATCH to `/rest/orgs/{orgId}/projects/{projectId}`
- **AND** the request body includes `attributes.settings.recurring_tests.frequency` and `relationships.owner`
