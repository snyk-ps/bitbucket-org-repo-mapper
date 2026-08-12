#!/usr/bin/env python3
"""Clear project owner on all Snyk projects in a group or org list.

One-off cleanup after Stage 4 post-import cleanup, which assigns SNYK_USER_ID
as project owner when PATCHing recurring test frequency.

Example::

    export SNYK_TOKEN='...'
    export SNYK_GROUP_ID='...'
    PYTHONPATH=src python scripts/clear_project_owners.py \\
        --group "$SNYK_GROUP_ID" \\
        --dry-run

    PYTHONPATH=src python scripts/clear_project_owners.py \\
        --orgs org-uuid-1,org-uuid-2 \\
        --output clear-project-owner-report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from common.output_state import assert_safe_filesystem_path, atomic_write_json  # noqa: E402
from config import load_dotenv_file  # noqa: E402
from config.snyk_settings import load_snyk_settings  # noqa: E402
from integrations.snyk.client import SnykRestClient  # noqa: E402
from snyk.clear_project_owners import (  # noqa: E402
    ClearProjectOwnerOptions,
    parse_org_ids,
    run_clear_project_owners,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Clear project owner on all Snyk projects in a group or explicit org list "
            "(v1 PUT {\"owner\": null})."
        ),
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--group",
        metavar="GROUP_ID",
        default=None,
        help="Snyk group UUID; list all orgs in the group (or SNYK_GROUP_ID when omitted).",
    )
    scope.add_argument(
        "--orgs",
        metavar="ORG_IDS",
        default=None,
        help="Comma-separated org UUIDs to process (SNYK_GROUP_ID not required).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional path to a .env file (defaults to ./.env if present).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("clear-project-owner-report.json"),
        metavar="PATH",
        help="Output path for the cleanup report JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List projects that would be updated; do not issue PUT requests.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N projects across all orgs (UAT smoke tests).",
    )
    return parser


def _resolve_group_id(raw: str | None) -> str:
    import os

    if raw is not None and raw.strip():
        return raw.strip()
    env = os.environ.get("SNYK_GROUP_ID", "").strip()
    if env:
        return env
    msg = "--group requires GROUP_ID or SNYK_GROUP_ID"
    raise ValueError(msg)


def _report_has_failures(report: dict[str, object]) -> bool:
    failed = report.get("failed")
    return isinstance(failed, list) and bool(failed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    load_dotenv_file(args.env_file)

    org_ids: list[str] | None = None
    group_id: str | None = None
    if args.orgs is not None:
        try:
            org_ids = parse_org_ids(args.orgs)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        require_group = False
    else:
        try:
            group_id = _resolve_group_id(args.group)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        require_group = True

    try:
        settings = load_snyk_settings(require_group_id=require_group)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        assert_safe_filesystem_path(args.output)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    options = ClearProjectOwnerOptions(
        group_id=group_id,
        org_ids=org_ids,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    client = SnykRestClient(settings)
    try:
        report = run_clear_project_owners(client, options)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(report, indent=2))
    else:
        atomic_write_json(args.output, report)
        print(f"Wrote report to {args.output}")

    if _report_has_failures(report):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
