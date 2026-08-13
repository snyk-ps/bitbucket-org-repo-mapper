## Why

The repository directory is `snyk-org-repo-mapper`, and Stage 1 already supports **Bitbucket Server**, **spreadsheet-driven Bitbucket**, and **GitHub** discovery—with Stages 2–4 focused on Snyk org planning, broker setup, import, and post-import cleanup. The published name **`bitbucket-org-repo-mapper`** (PyPI/package name, README title, OpenSpec project context) misrepresents scope and confuses operators who onboard GitHub orgs. The product should be named and documented as **`snyk-org-repo-mapper`**: a staged tool for mapping SCM repositories to Snyk organizations, regardless of whether the SCM is Bitbucket or GitHub.

## What Changes

- **Project identity:** Rename the Python distribution from `bitbucket-org-repo-mapper` to **`snyk-org-repo-mapper`** in `pyproject.toml`; regenerate **`uv.lock`**.
- **Documentation:** Update **`README.md`** title, intro, and any Bitbucket-only framing so the primary narrative is **multi-SCM Snyk onboarding** with Bitbucket and GitHub called out as Stage 1 ingress options.
- **OpenSpec project context:** Update **`openspec/project.md`** title and summary to match.
- **Specification:** Fill in **`openspec/specs/three-stage-snyk-pipeline/spec.md`** **Purpose** (currently `TBD`) to describe the tool as **`snyk-org-repo-mapper`** and list supported Stage 1 sources (Bitbucket, spreadsheet/Bitbucket, GitHub). No behavioral requirement changes to pipeline stages.
- **Console script names:** Keep existing **`repo-mapper-*`** entry points unchanged. Update docstrings and README to refer to the application as **`snyk-org-repo-mapper`**, not `bitbucket-org-repo-mapper`.

**Out of scope:**

- Renaming **`repo-mapper-*`** console scripts.
- Editing **archived** OpenSpec changes under `openspec/changes/archive/`.
- Changing discovery JSON field names (`bitbucket_project_name`, etc.) or pipeline behavior.
- Git remote / hosting rename (directory already matches).

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- **`three-stage-snyk-pipeline`:** Replace placeholder **Purpose** with accurate product identity and Stage 1 ingress list; no new stage requirements.

## Impact

- **Packaging:** `pyproject.toml`, `uv.lock`
- **Docs:** `README.md`, `openspec/project.md`
- **Specs:** `openspec/specs/three-stage-snyk-pipeline/spec.md` (Purpose only)
- **Code:** Docstrings in `src/commands/dispatch.py`, `src/commands/bitbucket_cli.py` (help text only if needed)
- **Tests:** None expected (no behavior change)
- **Operators:** `pip install -e .` installs package **`snyk-org-repo-mapper`**; CLI commands and `repo-mapper-*` scripts unchanged
